"""
Application entry point.
 
Start with:
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
 
The lifespan context manager loads all ML models once at startup so every
subsequent request hits an already-warm model.
"""
 
from __future__ import annotations
 
from contextlib import asynccontextmanager
from typing import AsyncIterator
 
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
 
from app.api.error_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.routes import analyze, health, models
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.services.explainability_service import ExplainabilityService
from app.services.inference_service import InferenceService
from app.services.region_explainer_service import RegionExplainerService
 
 
# ── Lifespan ──────────────────────────────────────────────────────────────────
 
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    log = get_logger(__name__)
    log.info("Starting %s v%s", settings.app_title, settings.app_version)
 
    # Initialise services
    inference_svc = InferenceService()
    inference_svc.load_all_models()
 
    explain_svc = ExplainabilityService()
    region_svc = RegionExplainerService()
 
    # Attach to app.state so dependency functions can retrieve them
    app.state.inference_service = inference_svc
    app.state.explainability_service = explain_svc
    app.state.region_service = region_svc
 
    log.info("All services ready.")
    yield  # ← application runs here
 
    log.info("Shutting down.")
 
 
# ── Application factory ───────────────────────────────────────────────────────
 
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description=(
            "Explainable Deepfake / AI-Image Detection API. "
            "Provides Grad-CAM heatmaps, LIME superpixel explanations, "
            "and semantic region-level text reasoning."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
 
    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
 
    # ── Exception handlers ────────────────────────────────────────────────────
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
 
    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(models.router, prefix=prefix)
    app.include_router(analyze.router, prefix=prefix)
    app.mount("/data", StaticFiles(directory="data"), name="data")
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
    return app
 
 
app = create_app()