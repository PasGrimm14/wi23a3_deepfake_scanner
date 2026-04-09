"""
InferenceService – central registry for model loaders and predictors.
 
Responsibilities
────────────────
- Build and hold all model instances at application startup.
- Provide a single `run_inference` method used by the route handler.
- Keep ML state off the request/response cycle (no model loading per request).
 
Adding a new model
──────────────────
1. Create a new loader in app/models/ (subclass ModelLoader + Predictor).
2. Register it in `_REGISTRY` below.
3. Place weights in MODEL_DIR/<name>/weights.pth.
"""
 
from __future__ import annotations
 
import time
from typing import Optional
 
import torch
 
from app.core.config import settings
from app.core.logging import get_logger
from app.models.base import ModelLoader, Predictor, PredictionResult
from app.models.densenet import DenseNetLoader, DenseNetPredictor
from app.models.xception import XceptionLoader, XceptionPredictor
from app.utils.image_utils import pil_to_tensor, load_image
 
log = get_logger(__name__)
 
 
# ── Registry: name → (loader class, predictor class) ─────────────────────────
 
_REGISTRY: dict[str, tuple[type[ModelLoader], type[Predictor]]] = {
    "xception": (XceptionLoader, XceptionPredictor),
    "densenet": (DenseNetLoader, DenseNetPredictor),
    # TODO: add future architectures here, e.g.:
    # "efficientnet": (EfficientNetLoader, EfficientNetPredictor),
}
 
 
class InferenceService:
    """
    Singleton-style service; instantiated once in `main.py` lifespan and
    injected via FastAPI dependency.
    """
 
    def __init__(self) -> None:
        self._device = torch.device(settings.device)
        self._loaders: dict[str, ModelLoader] = {}
        self._predictors: dict[str, Predictor] = {}
 
    # ── Startup ───────────────────────────────────────────────────────────────
 
    def load_all_models(self) -> None:
        """
        Build every registered model.  Called once at app startup so the first
        request is not penalised with model-loading latency.
        """
        for name, (loader_cls, predictor_cls) in _REGISTRY.items():
            log.info("Loading model: %s on device=%s", name, self._device)
            loader = loader_cls(model_dir=settings.model_dir, device=self._device)
            try:
                loader.build()
                self._loaders[name] = loader
                self._predictors[name] = predictor_cls(loader)
                weights_status = "custom weights" if loader.weights_loaded() else "ImageNet/random weights"
                log.info("Model '%s' ready (%s).", name, weights_status)
            except Exception:
                log.exception("Failed to load model '%s' – it will be unavailable.", name)
 
    # ── Public interface ───────────────────────────────────────────────────────
 
    def available_models(self) -> list[str]:
        return list(self._loaders.keys())
 
    def get_loader(self, name: str) -> ModelLoader:
        if name not in self._loaders:
            raise ValueError(f"Model '{name}' is not available. Loaded: {self.available_models()}")
        return self._loaders[name]
 
    def get_predictor(self, name: str) -> Predictor:
        return self._predictors[name]
 
    def model_info(self) -> list[dict]:
        """Return metadata for all registered models (used by /models endpoint)."""
        infos = []
        for name, (loader_cls, _) in _REGISTRY.items():
            loader = self._loaders.get(name)
            infos.append({
                "name": name,
                "backbone": loader_cls.__name__.replace("Loader", ""),
                "weights_loaded": loader.weights_loaded() if loader else False,
                "input_size": loader.input_size if loader else settings.input_size,
                "description": _MODEL_DESCRIPTIONS.get(name, ""),
            })
        return infos
 
    def run_inference(
        self,
        image_bytes: bytes,
        model_name: Optional[str] = None,
    ) -> tuple[torch.Tensor, PredictionResult, int]:
        """
        Validate, preprocess, and run inference.
 
        Returns
        -------
        tensor : torch.Tensor
            Input tensor (1, 3, H, W) – needed downstream by Grad-CAM.
        result : PredictionResult
        input_size : int
            The square resolution used for the tensor.
        """
        name = model_name or settings.default_model
        loader = self.get_loader(name)
        predictor = self.get_predictor(name)
 
        pil_img = load_image(image_bytes)
        tensor = pil_to_tensor(pil_img, target_size=loader.input_size)
 
        result = predictor.predict(tensor)
        return tensor, result, loader.input_size
 
 
_MODEL_DESCRIPTIONS: dict[str, str] = {
    "xception": (
        "XceptionNet (Chollet 2017) with depthwise separable convolutions. "
        "Primary model for deepfake detection."
    ),
    "densenet": (
        "DenseNet121 (Huang 2017) with dense skip connections. "
        "Comparison architecture for cross-model evaluation."
    ),
}