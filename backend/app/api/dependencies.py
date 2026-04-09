"""
FastAPI dependency functions.
 
Services are stored on `app.state` during the lifespan and retrieved here.
Using Depends() keeps route handlers decoupled from the service singletons.
"""
 
from __future__ import annotations
 
from fastapi import Request
 
from app.services.explainability_service import ExplainabilityService
from app.services.inference_service import InferenceService
from app.services.region_explainer_service import RegionExplainerService
 
 
def get_inference_service(request: Request) -> InferenceService:
    return request.app.state.inference_service
 
 
def get_explainability_service(request: Request) -> ExplainabilityService:
    return request.app.state.explainability_service
 
 
def get_region_service(request: Request) -> RegionExplainerService:
    return request.app.state.region_service