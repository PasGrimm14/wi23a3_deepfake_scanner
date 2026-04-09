"""GET /health – liveness check."""
 
from fastapi import APIRouter
 
from app.core.config import settings
from app.schemas.responses import HealthResponse
 
router = APIRouter(tags=["Health"])
 
 
@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=settings.app_version)