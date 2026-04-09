"""
DenseNet121 wrapper for binary deepfake detection.
 
torchvision ships DenseNet121 with ImageNet weights (IMAGENET1K_V1).
We replace the classifier head for 2-class output and optionally load
your custom fine-tuned weights.
 
HOW TO USE YOUR OWN TRAINED WEIGHTS
────────────────────────────────────
1. Fine-tune DenseNet121 on your deepfake dataset and save:
       torch.save(model.state_dict(), "<MODEL_DIR>/densenet/weights.pth")
2. Set MODEL_DIR in .env.
3. The loader picks up the file at app start.
 
GRAD-CAM TARGET LAYER
─────────────────────
DenseNet's final feature map comes from `features.norm5` (BatchNorm after the
last dense block).  We hook onto the preceding ReLU via `features.denseblock4`.
Adjust `gradcam_target_layer` if you modify the architecture.
"""
 
from __future__ import annotations
 
from pathlib import Path
 
import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import DenseNet121_Weights
 
from app.models.base import ModelLoader, Predictor, PredictionResult
 
 
class DenseNetLoader(ModelLoader):
 
    @property
    def name(self) -> str:
        return "densenet"
 
    @property
    def input_size(self) -> int:
        # DenseNet accepts 224 natively; we use 299 (same as Xception) so that
        # the same preprocessing pipeline applies to both models.
        return 299
 
    @property
    def gradcam_target_layer(self) -> nn.Module:
        # Last dense block – richest spatial features before global pooling.
        return self._model.features.denseblock4  # type: ignore[union-attr]
 
    def build(self) -> nn.Module:
        if self.weights_loaded():
            # Custom weights: build bare architecture (no pretrained head needed)
            base = models.densenet121(weights=None)
        else:
            # No custom weights: start from ImageNet pretrained
            base = models.densenet121(weights=DenseNet121_Weights.IMAGENET1K_V1)
 
        # Replace classifier for binary detection
        in_features = base.classifier.in_features
        base.classifier = nn.Linear(in_features, 2)
 
        self.load_weights(base)
        base.to(self.device)
        base.eval()
        self._model = base
        return base
 
 
class DenseNetPredictor(Predictor):
 
    def predict(self, tensor: torch.Tensor) -> PredictionResult:
        tensor = tensor.to(self.loader.device)
        with torch.no_grad():
            logits = self.loader.model(tensor)
            probs = torch.softmax(logits, dim=1)
 
        predicted_class = int(probs.argmax(dim=1).item())
        confidence = float(probs[0, predicted_class].item())
 
        return PredictionResult(
            logits=logits,
            probabilities=probs,
            predicted_class=predicted_class,
            confidence=confidence,
        )