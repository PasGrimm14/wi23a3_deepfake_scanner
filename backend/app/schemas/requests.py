"""
Request-side schemas and helpers.
The actual multipart form parameters are declared inline in the route handler;
this module provides validated wrapper types and defaults.
"""
 
from __future__ import annotations
 
from enum import Enum
from typing import Annotated
 
from pydantic import BaseModel, Field
 
 
class ModelName(str, Enum):
    xception = "xception"
    densenet = "densenet"
 
 
class ExplanationMethod(str, Enum):
    gradcam = "gradcam"
    lime = "lime"
 
 
class AnalyzeFormParams(BaseModel):
    """Mirrors the form-data fields accepted by POST /analyze-image."""
 
    model_name: ModelName = ModelName.xception
    explanation_methods: list[ExplanationMethod] = Field(
        default_factory=lambda: [ExplanationMethod.gradcam, ExplanationMethod.lime]
    )
    return_overlay: bool = True
    return_region_scores: bool = True