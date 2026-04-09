"""
Abstract base classes for model loading and prediction.
 
Every concrete model wrapper must subclass ModelLoader and Predictor.
This enforces a clean interface that lets the rest of the system stay
model-agnostic – swapping XceptionNet for a new architecture only
requires a new subclass, not any changes to services or routes.
"""
 
from __future__ import annotations
 
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
 
import torch
import torch.nn as nn
 
 
# ── Data containers ───────────────────────────────────────────────────────────
 
@dataclass
class PredictionResult:
    """Raw output from a single forward pass."""
    logits: torch.Tensor           # shape (1, num_classes)
    probabilities: torch.Tensor    # softmax applied, shape (1, num_classes)
    predicted_class: int           # index of winning class
    confidence: float              # probability of winning class
 
 
# ── Abstract interfaces ───────────────────────────────────────────────────────
 
class ModelLoader(ABC):
    """
    Responsible for building the model architecture and loading weights.
 
    HOW TO ADD YOUR OWN WEIGHTS
    ───────────────────────────
    1. Train your XceptionNet / DenseNet121 and save with:
           torch.save(model.state_dict(), "weights/xception/weights.pth")
    2. The concrete ModelLoader subclass (XceptionLoader / DenseNetLoader)
       calls `self.load_weights(path)` during `build()`.
    3. Set MODEL_DIR in .env to the parent directory containing xception/
       and densenet/ subdirectories.
    """
 
    def __init__(self, model_dir: Path, device: torch.device) -> None:
        self.model_dir = model_dir
        self.device = device
        self._model: Optional[nn.Module] = None
 
    @abstractmethod
    def build(self) -> nn.Module:
        """
        Build the architecture.
        If a weights file exists in `model_dir / <name> / weights.pth`
        the concrete implementation should load it here.
        """
 
    @property
    def model(self) -> nn.Module:
        if self._model is None:
            raise RuntimeError("Model not built yet – call build() first.")
        return self._model
 
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier, e.g. 'xception' or 'densenet'."""
 
    @property
    @abstractmethod
    def gradcam_target_layer(self) -> nn.Module:
        """
        Return the nn.Module that Grad-CAM should hook onto.
        Typically the last convolutional / activation layer before pooling.
        """
 
    @property
    @abstractmethod
    def input_size(self) -> int:
        """Expected square input resolution (pixels)."""
 
    def weights_path(self) -> Path:
        return self.model_dir / self.name / "weights.pth"
 
    def weights_loaded(self) -> bool:
        return self.weights_path().is_file()
 
    def load_weights(self, model: nn.Module) -> None:
        """Load state-dict from `weights_path()` if the file exists."""
        path = self.weights_path()
        if path.is_file():
            state = torch.load(path, map_location=self.device, weights_only=True)
            # Support both raw state-dicts and checkpoints with a "model" key
            if isinstance(state, dict) and "model" in state:
                state = state["model"]
            model.load_state_dict(state)
        # If no weights file exists the model runs with ImageNet-pretrained or
        # random weights – useful during development.
 
 
class Predictor(ABC):
    """
    Wraps a loaded model and exposes a single `predict` method.
    Heavy preprocessing is delegated to image_utils so this class stays lean.
    """
 
    def __init__(self, loader: ModelLoader) -> None:
        self.loader = loader
 
    @abstractmethod
    def predict(self, tensor: torch.Tensor) -> PredictionResult:
        """
        Run a forward pass.
 
        Parameters
        ----------
        tensor : torch.Tensor
            Pre-processed image tensor, shape (1, 3, H, W), values in [0, 1]
            after normalization.
 
        Returns
        -------
        PredictionResult
        """
 
    # Class index mapping – override in subclass if your training used a
    # different label order.
    CLASS_NAMES: list[str] = ["real", "fake"]