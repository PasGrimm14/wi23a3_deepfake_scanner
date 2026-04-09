"""
POST /analyze-image – core deepfake detection endpoint.
 
Accepts a multipart/form-data upload plus optional control parameters.
Heavy ML work is executed synchronously in a thread-pool executor so the
async event loop is not blocked.
"""
 
from __future__ import annotations
 
import asyncio
import time
from typing import Annotated, Optional
 
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
 
from app.api.dependencies import get_explainability_service, get_inference_service, get_region_service
from app.core.config import settings
from app.core.logging import get_logger
from app.models.base import Predictor
from app.schemas.requests import ExplanationMethod, ModelName
from app.schemas.responses import (
    AnalyzeResponse,
    ClassProbabilities,
    Explanations,
    GradCamExplanation,
    ImageSize,
    LimeExplanation,
    Meta,
    Prediction,
    RegionScore,
    SuperpixelWeight,
)
from app.services.explainability_service import ExplainabilityService
from app.services.inference_service import InferenceService
from app.services.region_explainer_service import RegionExplainerService
from app.utils.image_utils import (
    ImageValidationError,
    load_image,
    tensor_to_numpy_hwc,
    validate_upload,
)
 
log = get_logger(__name__)
router = APIRouter(tags=["Analysis"])
 
 
@router.post(
    "/analyze-image",
    response_model=AnalyzeResponse,
    summary="Analyse an image for deepfake / AI-generation artefacts",
)
async def analyze_image(
    file: Annotated[UploadFile, File(description="Image file (JPEG, PNG, WEBP, BMP, TIFF)")],
    model_name: Annotated[
        ModelName,
        Form(description="Model backbone to use: 'xception' (default) or 'densenet'"),
    ] = ModelName.xception,
    explanation_methods: Annotated[
        str,
        Form(description="Comma-separated list of methods: 'gradcam', 'lime', or 'gradcam,lime'"),
    ] = "gradcam,lime",
    return_overlay: Annotated[
        bool,
        Form(description="Include original-image + heatmap overlay in response"),
    ] = True,
    return_region_scores: Annotated[
        bool,
        Form(description="Include per-region activation scores in response"),
    ] = True,
    inference_svc: InferenceService = Depends(get_inference_service),
    explain_svc: ExplainabilityService = Depends(get_explainability_service),
    region_svc: RegionExplainerService = Depends(get_region_service),
) -> AnalyzeResponse:
 
    t_start = time.perf_counter()
 
    # ── Parse explanation_methods form field ──────────────────────────────────
    requested_methods: set[str] = {
        m.strip().lower() for m in explanation_methods.split(",") if m.strip()
    }
 
    # ── Read and validate upload ──────────────────────────────────────────────
    raw_bytes = await file.read()
    try:
        validate_upload(
            content_type=file.content_type,
            content_length=len(raw_bytes),
            data=raw_bytes,
        )
    except ImageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
 
    # ── Run ML pipeline in thread pool (avoids blocking async event loop) ─────
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(
            None,
            _run_pipeline,
            raw_bytes,
            model_name.value,
            requested_methods,
            return_overlay,
            return_region_scores,
            file.filename or "upload",
            inference_svc,
            explain_svc,
            region_svc,
            t_start,
        )
    except ImageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        log.exception("Unexpected error during analysis.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        )
 
    return response
 
 
# ── Synchronous pipeline (runs in thread pool) ────────────────────────────────
 
def _run_pipeline(
    raw_bytes: bytes,
    model_name: str,
    requested_methods: set[str],
    return_overlay: bool,
    return_region_scores: bool,
    filename: str,
    inference_svc: InferenceService,
    explain_svc: ExplainabilityService,
    region_svc: RegionExplainerService,
    t_start: float,
) -> AnalyzeResponse:
 
    # ── Inference ─────────────────────────────────────────────────────────────
    tensor, pred_result, input_size = inference_svc.run_inference(raw_bytes, model_name)
    loader = inference_svc.get_loader(model_name)
    class_names = Predictor.CLASS_NAMES  # ["real", "fake"]
    label = class_names[pred_result.predicted_class]
    display_label = "AI-generated" if label == "fake" else "real"
 
    probs = pred_result.probabilities[0].tolist()
    class_probs = ClassProbabilities(
        real=round(probs[0], 4),
        fake=round(probs[1], 4),
    )
 
    # ── Load original image for overlays / region detection ──────────────────
    pil_img = load_image(raw_bytes)
    img_w, img_h = pil_img.size
    import numpy as np
    from PIL import Image
    image_rgb = np.array(pil_img.resize((input_size, input_size), Image.BILINEAR))
 
    # ── Grad-CAM ──────────────────────────────────────────────────────────────
    gradcam_result = None
    if "gradcam" in requested_methods:
        gradcam_result = explain_svc.run_gradcam(
            loader=loader,
            tensor=tensor,
            target_class=pred_result.predicted_class,
            return_overlay=return_overlay,
        )
 
    # ── Region scores (requires heatmap) ─────────────────────────────────────
    region_scores_out: list[RegionScore] = []
    region_text: list[str] = []
    if return_region_scores and gradcam_result and gradcam_result.gradcam_available and gradcam_result.heatmap is not None:
        raw_regions, region_text = region_svc.explain(gradcam_result.heatmap, image_rgb)
        region_scores_out = [
            RegionScore(
                region_name=r.region_name,
                score=r.score,
                bbox=list(r.bbox),
            )
            for r in raw_regions[:5]
        ]
 
    # ── LIME ──────────────────────────────────────────────────────────────────
    lime_result = None
    if "lime" in requested_methods:
        lime_result = explain_svc.run_lime(
            loader=loader,
            image_rgb=image_rgb,
        )
 
    # ── Assemble response ─────────────────────────────────────────────────────
    elapsed_ms = (time.perf_counter() - t_start) * 1000
 
    gradcam_resp = GradCamExplanation(
        available=gradcam_result.gradcam_available if gradcam_result else False,
        heatmap_base64=gradcam_result.heatmap_base64 if gradcam_result else None,
        overlay_base64=gradcam_result.overlay_base64 if gradcam_result else None,
        top_regions=region_scores_out,
    )
 
    lime_resp = LimeExplanation(
        available=lime_result.lime_available if lime_result else False,
        segments_base64=lime_result.segments_base64 if lime_result else None,
        top_superpixels=(
            [SuperpixelWeight(segment_id=sid, weight=w) for sid, w in lime_result.top_superpixels]
            if lime_result else []
        ),
    )
 
    return AnalyzeResponse(
        filename=filename,
        model_used=model_name,
        prediction=Prediction(
            label=display_label,
            confidence=round(pred_result.confidence, 4),
            class_probabilities=class_probs,
        ),
        explanations=Explanations(
            gradcam=gradcam_resp,
            lime=lime_resp,
            region_text_explanation=region_text,
        ),
        meta=Meta(
            processing_time_ms=round(elapsed_ms, 1),
            image_size=ImageSize(width=img_w, height=img_h),
        ),
    )