"""
XceptionNet wrapper for binary deepfake detection.
 
PyTorch's torchvision does NOT include XceptionNet natively.
We implement a clean, standalone version here following the original paper
(Chollet 2017) with one modification: the final FC layer outputs 2 classes
(real vs. fake) instead of 1000.
 
HOW TO USE YOUR OWN TRAINED WEIGHTS
────────────────────────────────────
1. Save your checkpoint:
       torch.save(model.state_dict(), "<MODEL_DIR>/xception/weights.pth")
   If you saved a full checkpoint dict use the key "model":
       torch.save({"model": model.state_dict(), "epoch": 42, ...}, path)
2. Set MODEL_DIR in .env.
3. The loader picks up the file automatically at app start.
 
ARCHITECTURE NOTE
─────────────────
The Grad-CAM target layer is `model.block14.rep[-1]` (the final depthwise
separable convolution block's activation).  If you replace the backbone,
update `gradcam_target_layer` accordingly.
"""
 
from __future__ import annotations
 
from pathlib import Path
 
import torch
import torch.nn as nn
import torch.nn.functional as F
 
from app.models.base import ModelLoader, Predictor, PredictionResult
 
 
# ── Building blocks ───────────────────────────────────────────────────────────
 
class SeparableConv2d(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 0,
        bias: bool = False,
    ) -> None:
        super().__init__()
        self.depthwise = nn.Conv2d(
            in_channels, in_channels, kernel_size,
            stride=stride, padding=padding, groups=in_channels, bias=bias,
        )
        self.pointwise = nn.Conv2d(in_channels, out_channels, 1, bias=bias)
        self.bn = nn.BatchNorm2d(out_channels)
 
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.bn(self.pointwise(self.depthwise(x)))
 
 
class XceptionBlock(nn.Module):
    """Middle-flow and exit-flow block with optional residual projection."""
 
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        reps: int,
        stride: int = 1,
        start_with_relu: bool = True,
        grow_first: bool = True,
    ) -> None:
        super().__init__()
 
        self.skip: nn.Module
        if out_channels != in_channels or stride != 1:
            self.skip = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.skip = nn.Identity()
 
        layers: list[nn.Module] = []
        filters = in_channels
        for i in range(reps):
            if grow_first:
                out = out_channels if i == 0 else out_channels
            else:
                out = in_channels if i < reps - 1 else out_channels
 
            if start_with_relu or i > 0:
                layers.append(nn.ReLU(inplace=False))
            layers.append(SeparableConv2d(filters, out, 3, padding=1))
            filters = out
 
        if stride != 1:
            layers.append(nn.MaxPool2d(3, stride=stride, padding=1))
 
        self.rep = nn.Sequential(*layers)
 
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.rep(x) + self.skip(x)
 
 
class XceptionNet(nn.Module):
    """
    Xception architecture (Chollet 2017) adapted for binary classification.
    Input: (B, 3, 299, 299)  Output: (B, num_classes)
    """
 
    def __init__(self, num_classes: int = 2, dropout_rate: float = 0.5) -> None:
        super().__init__()
 
        # ── Entry flow ────────────────────────────────────────────────────────
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=0, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )
        self.block1 = XceptionBlock(64, 128, reps=2, stride=2, start_with_relu=False, grow_first=True)
        self.block2 = XceptionBlock(128, 256, reps=2, stride=2, start_with_relu=True, grow_first=True)
        self.block3 = XceptionBlock(256, 728, reps=2, stride=2, start_with_relu=True, grow_first=True)
 
        # ── Middle flow (8 identical blocks) ─────────────────────────────────
        self.middle_flow = nn.Sequential(
            *[XceptionBlock(728, 728, reps=3, stride=1, start_with_relu=True, grow_first=True)
              for _ in range(8)]
        )
 
        # ── Exit flow ─────────────────────────────────────────────────────────
        self.block12 = XceptionBlock(728, 1024, reps=2, stride=2, start_with_relu=True, grow_first=False)
        self.block13 = nn.Sequential(
            nn.ReLU(inplace=False),
            SeparableConv2d(1024, 1536, 3, padding=1),
            nn.ReLU(inplace=False),
        )
        self.block14 = nn.Sequential(
            SeparableConv2d(1536, 2048, 3, padding=1),
            nn.ReLU(inplace=False),   # ← Grad-CAM hooks here
        )
 
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(p=dropout_rate)
        self.fc = nn.Linear(2048, num_classes)
 
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.middle_flow(x)
        x = self.block12(x)
        x = self.block13(x)
        x = self.block14(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        return self.fc(x)
 
 
# ── Loader ────────────────────────────────────────────────────────────────────
 
class XceptionLoader(ModelLoader):
 
    @property
    def name(self) -> str:
        return "xception"
 
    @property
    def input_size(self) -> int:
        return 299
 
    @property
    def gradcam_target_layer(self) -> nn.Module:
        # The last ReLU in block14 – final spatial feature map before pooling.
        return self._model.block14[-1]  # type: ignore[union-attr]
 
    def build(self) -> nn.Module:
        model = XceptionNet(num_classes=2)
        self.load_weights(model)
        model.to(self.device)
        model.eval()
        self._model = model
        return model
 
 
# ── Predictor ─────────────────────────────────────────────────────────────────
 
class XceptionPredictor(Predictor):
 
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