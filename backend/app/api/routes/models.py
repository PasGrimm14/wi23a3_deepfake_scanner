"""GET /models – metadata about loaded model architectures."""
 
from fastapi import APIRouter, Depends
 
from app.core.config import settings
from app.schemas.responses import ModelInfoEntry, ModelInfoResponse
from app.services.inference_service import InferenceService
from app.api.dependencies import get_inference_service
 
router = APIRouter(tags=["Models"])
 
 
@router.get("/models", response_model=ModelInfoResponse, summary="List loaded models")
async def get_models(
    svc: InferenceService = Depends(get_inference_service),
) -> ModelInfoResponse:
    entries = [ModelInfoEntry(**m) for m in svc.model_info()]
    return ModelInfoResponse(
        models=entries,
        default_model=settings.default_model,
        device=settings.device,
    )