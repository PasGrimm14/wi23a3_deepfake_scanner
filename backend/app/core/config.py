"""
Central application configuration via pydantic-settings.
All values can be overridden through a .env file or environment variables.
"""
 
from __future__ import annotations
 
from pathlib import Path
from typing import Literal
 
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
 
 
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
 
    # ── Server ────────────────────────────────────────────────────────────────
    app_title: str = "Deepfake Detection API"
    app_version: str = "1.0.0"
    debug: bool = False
 
    # ── CORS (comma-separated origins) ───────────────────────────────────────
    cors_origins: str = "*"
 
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
 
    # ── Model ─────────────────────────────────────────────────────────────────
    # Directory that contains subdirs: xception/, densenet/
    # Each subdir may contain a weights.pth file loaded at startup.
    model_dir: Path = Path("backend/weights")
    default_model: Literal["xception", "densenet"] = "xception"
 
    # ── Inference ─────────────────────────────────────────────────────────────
    device: Literal["cpu", "cuda", "mps"] = "cpu"
    # Input resolution fed to both models
    input_size: int = 299  # XceptionNet native; DenseNet121 also handles this fine
 
    # ── Upload limits ─────────────────────────────────────────────────────────
    max_upload_mb: float = 10.0
 
    @property
    def max_upload_bytes(self) -> int:
        return int(self.max_upload_mb * 1024 * 1024)
 
    allowed_content_types: set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff",
    }
 
    # ── Explainability ────────────────────────────────────────────────────────
    gradcam_layer_xception: str = "block14_sepconv2_act"   # logical name; mapped in model wrapper
    gradcam_layer_densenet: str = "features_norm5"          # logical name; mapped in model wrapper
    lime_num_samples: int = 64       # LIME perturbation samples (lower → faster, less accurate)
    lime_num_features: int = 10      # top superpixels returned by LIME
 
    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_json: bool = False           # set True for structured JSON logs in prod
 
    # ── Temp / Artifact storage ───────────────────────────────────────────────
    # If set, heatmaps are also written to disk (useful for debugging).
    artifact_dir: Path | None = None
 
    @field_validator("model_dir", "artifact_dir", mode="before")
    @classmethod
    def _to_path(cls, v):
        return Path(v) if v is not None else v
 
 
# Singleton – import and use `settings` everywhere
settings = Settings()