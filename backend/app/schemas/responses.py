"""
Pydantic response models – strictly typed, frontend-friendly.
"""
 
from __future__ import annotations
 
from typing import Optional
 
from pydantic import BaseModel, Field
 
 
# ── Sub-models ────────────────────────────────────────────────────────────────
 
class ClassProbabilities(BaseModel):
    real: float
    fake: float
 
 
class Prediction(BaseModel):
    label: str  # "real" | "AI-generated"
    confidence: float = Field(ge=0.0, le=1.0)
    class_probabilities: ClassProbabilities
 
 
class RegionScore(BaseModel):
    region_name: str
    score: float = Field(ge=0.0, le=1.0)
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
 
 
class GradCamExplanation(BaseModel):
    available: bool
    heatmap_base64: Optional[str] = None    # PNG encoded as base64
    overlay_base64: Optional[str] = None    # original + heatmap blend
    top_regions: list[RegionScore] = Field(default_factory=list)
 
 
class SuperpixelWeight(BaseModel):
    segment_id: int
    weight: float
 
 
class LimeExplanation(BaseModel):
    available: bool
    segments_base64: Optional[str] = None  # coloured superpixel mask
    top_superpixels: list[SuperpixelWeight] = Field(default_factory=list)
 
 
class Explanations(BaseModel):
    gradcam: GradCamExplanation
    lime: LimeExplanation
    region_text_explanation: list[str] = Field(default_factory=list)
 
 
class ImageSize(BaseModel):
    width: int
    height: int
 
 
class Meta(BaseModel):
    processing_time_ms: float
    image_size: ImageSize
 
 
# ── Top-level response ────────────────────────────────────────────────────────
 
class AnalyzeResponse(BaseModel):
    filename: str
    model_used: str
    prediction: Prediction
    explanations: Explanations
    meta: Meta
 
 
# ── Health / model-info ───────────────────────────────────────────────────────
 
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
 
 
class ModelInfoEntry(BaseModel):
    name: str
    backbone: str
    weights_loaded: bool
    input_size: int
    description: str
 
 
class ModelInfoResponse(BaseModel):
    models: list[ModelInfoEntry]
    default_model: str
    device: str