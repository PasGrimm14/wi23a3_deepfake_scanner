"""
ExplainabilityService – Grad-CAM and LIME explanation generation.
 
Abstract interfaces (GradCamExplainer, LimeExplainer) allow alternative
implementations without touching the service layer.
 
RESEARCH EXTENSION POINTS
──────────────────────────
- Grad-CAM++ / Score-CAM: replace GradCamExplainerImpl with a new subclass.
- Evaluation metrics:
    - Pointing Game: check whether the highest-activation pixel falls within
      the ground-truth bounding box.  Add `pointing_game(heatmap, gt_bbox)`.
    - IoU with human annotations: compare binarised heatmap to GT mask.
  Both can be added as static methods here and called from a dedicated
  evaluation script without changing the API.
"""
 
from __future__ import annotations
 
from abc import ABC, abstractmethod
from typing import Optional
 
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
 
from app.core.config import settings
from app.core.logging import get_logger
from app.models.base import ModelLoader
from app.utils.image_utils import (
    apply_colormap_on_image,
    numpy_to_base64_png,
    tensor_to_numpy_hwc,
)
 
log = get_logger(__name__)
 
 
# ── Abstract interfaces ───────────────────────────────────────────────────────
 
class GradCamExplainer(ABC):
    @abstractmethod
    def explain(
        self,
        tensor: torch.Tensor,
        target_class: int,
    ) -> np.ndarray:
        """
        Return a (H, W) float32 heatmap in [0, 1] aligned to `tensor` spatial dims.
        """
 
 
class LimeExplainer(ABC):
    @abstractmethod
    def explain(
        self,
        image_rgb: np.ndarray,
        predict_fn,
        num_samples: int,
        num_features: int,
    ) -> tuple[np.ndarray, list[tuple[int, float]]]:
        """
        Return (segment_mask, [(segment_id, weight), ...]).
        segment_mask: (H, W) int array with superpixel labels.
        """
 
 
# ── Grad-CAM implementation ───────────────────────────────────────────────────
 
class GradCamExplainerImpl(GradCamExplainer):
    """
    Gradient-weighted Class Activation Mapping (Selvaraju 2017).
 
    Registers forward/backward hooks on `target_layer`, runs one forward pass
    with gradient tracking, then computes the weighted activation map.
    """
 
    def __init__(self, model: nn.Module, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self._activations: Optional[torch.Tensor] = None
        self._gradients: Optional[torch.Tensor] = None
 
        self._fwd_hook = target_layer.register_forward_hook(self._save_activation)
        self._bwd_hook = target_layer.register_full_backward_hook(self._save_gradient)
 
    def _save_activation(self, _module, _input, output):
        self._activations = output.detach()
 
    def _save_gradient(self, _module, _grad_input, grad_output):
        self._gradients = grad_output[0].detach()
 
    def explain(self, tensor: torch.Tensor, target_class: int) -> np.ndarray:
        self.model.eval()
 
        inp = tensor.clone().requires_grad_(True)
        inp = inp.to(next(self.model.parameters()).device)
 
        logits = self.model(inp)
        self.model.zero_grad()
        logits[0, target_class].backward()
 
        if self._activations is None or self._gradients is None:
            log.warning("Grad-CAM hooks did not fire – returning zero heatmap.")
            h, w = tensor.shape[-2], tensor.shape[-1]
            return np.zeros((h, w), dtype=np.float32)
 
        # Global-average-pool gradients → channel weights
        weights = self._gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        cam = (weights * self._activations).sum(dim=1, keepdim=True)  # (1, 1, h', w')
        cam = F.relu(cam)
 
        # Normalise to [0, 1]
        cam_np = cam.squeeze().cpu().numpy().astype(np.float32)
        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max > cam_min:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
 
        return cam_np
 
    def remove_hooks(self) -> None:
        self._fwd_hook.remove()
        self._bwd_hook.remove()
 
 
# ── LIME implementation ───────────────────────────────────────────────────────
 
class LimeExplainerImpl(LimeExplainer):
    """
    Local Interpretable Model-agnostic Explanations (Ribeiro 2016).
 
    Uses scikit-image SLIC superpixels + lime library.
    Falls back gracefully if LIME is not installed.
    """
 
    def explain(
        self,
        image_rgb: np.ndarray,
        predict_fn,
        num_samples: int = 64,
        num_features: int = 10,
    ) -> tuple[np.ndarray, list[tuple[int, float]]]:
        try:
            from lime import lime_image
            from skimage.segmentation import mark_boundaries
        except ImportError:
            log.warning("lime / scikit-image not installed – LIME unavailable.")
            h, w = image_rgb.shape[:2]
            return np.zeros((h, w), dtype=np.int32), []
 
        explainer = lime_image.LimeImageExplainer(verbose=False)
        explanation = explainer.explain_instance(
            image_rgb,
            predict_fn,
            top_labels=2,
            hide_color=0,
            num_samples=num_samples,
        )
 
        # Use weights for the predicted class (label 1 = fake)
        label = explanation.top_labels[0]
        segments = explanation.segments
        _, weights_map = explanation.get_image_and_mask(
            label,
            positive_only=False,
            num_features=num_features,
            hide_rest=False,
        )
 
        # Collect per-superpixel weights
        local_exp = explanation.local_exp.get(label, [])
        top_superpixels = sorted(local_exp, key=lambda x: abs(x[1]), reverse=True)[:num_features]
 
        return segments, [(int(sid), float(w)) for sid, w in top_superpixels]
 
 
# ── Orchestrating service ─────────────────────────────────────────────────────
 
class ExplainabilityResult:
    """Carries all artefacts produced by one explainability pass."""
 
    def __init__(self) -> None:
        # Grad-CAM
        self.gradcam_available: bool = False
        self.heatmap: Optional[np.ndarray] = None         # (H, W) float [0,1]
        self.heatmap_base64: Optional[str] = None
        self.overlay_base64: Optional[str] = None
 
        # LIME
        self.lime_available: bool = False
        self.segments: Optional[np.ndarray] = None        # (H, W) int superpixel mask
        self.segments_base64: Optional[str] = None
        self.top_superpixels: list[tuple[int, float]] = []
 
 
class ExplainabilityService:
    """
    Facade that coordinates Grad-CAM and LIME for a single analysis request.
    Instantiated once; stateless between calls.
    """
 
    def __init__(self) -> None:
        self._gradcam_cache: dict[str, GradCamExplainerImpl] = {}
 
    def _get_gradcam_explainer(self, loader: ModelLoader) -> GradCamExplainerImpl:
        """Cache explainer per model name (hooks must persist between calls)."""
        name = loader.name
        if name not in self._gradcam_cache:
            self._gradcam_cache[name] = GradCamExplainerImpl(
                model=loader.model,
                target_layer=loader.gradcam_target_layer,
            )
        return self._gradcam_cache[name]
 
    def run_gradcam(
        self,
        loader: ModelLoader,
        tensor: torch.Tensor,
        target_class: int,
        return_overlay: bool = True,
    ) -> ExplainabilityResult:
        result = ExplainabilityResult()
        try:
            explainer = self._get_gradcam_explainer(loader)
            heatmap = explainer.explain(tensor, target_class)
 
            # Heatmap as PNG (grayscale encoded as jet colormap for readability)
            original_rgb = tensor_to_numpy_hwc(tensor)
            heatmap_colored = apply_colormap_on_image(
                np.zeros_like(original_rgb), heatmap, alpha=1.0
            )
            result.heatmap = heatmap
            result.heatmap_base64 = numpy_to_base64_png(heatmap_colored)
 
            if return_overlay:
                overlay = apply_colormap_on_image(original_rgb, heatmap, alpha=0.45)
                result.overlay_base64 = numpy_to_base64_png(overlay)
 
            result.gradcam_available = True
        except Exception:
            log.exception("Grad-CAM generation failed.")
 
        return result
 
    def run_lime(
        self,
        loader: ModelLoader,
        image_rgb: np.ndarray,
        num_samples: int = settings.lime_num_samples,
        num_features: int = settings.lime_num_features,
    ) -> ExplainabilityResult:
        result = ExplainabilityResult()
 
        def _predict_fn(images: np.ndarray) -> np.ndarray:
            """LIME calls this with a batch of perturbed uint8 images (N, H, W, 3)."""
            from app.utils.image_utils import pil_to_tensor, IMAGENET_MEAN, IMAGENET_STD
            from PIL import Image
            import torchvision.transforms.functional as TF
 
            batch_tensors = []
            for img_arr in images:
                pil = Image.fromarray(img_arr.astype(np.uint8))
                t = TF.to_tensor(pil)
                t = TF.normalize(t, mean=list(IMAGENET_MEAN), std=list(IMAGENET_STD))
                batch_tensors.append(t)
 
            batch = torch.stack(batch_tensors).to(loader.device)
            with torch.no_grad():
                logits = loader.model(batch)
                probs = torch.softmax(logits, dim=1)
            return probs.cpu().numpy()
 
        try:
            lime_impl = LimeExplainerImpl()
            segments, top_superpixels = lime_impl.explain(
                image_rgb, _predict_fn, num_samples=num_samples, num_features=num_features
            )
 
            # Colour-code: positive weight → green, negative → red
            segment_overlay = self._colour_segments(image_rgb, segments, top_superpixels)
            result.segments = segments
            result.segments_base64 = numpy_to_base64_png(segment_overlay)
            result.top_superpixels = top_superpixels
            result.lime_available = True
        except Exception:
            log.exception("LIME generation failed.")
 
        return result
 
    @staticmethod
    def _colour_segments(
        image_rgb: np.ndarray,
        segments: np.ndarray,
        weights: list[tuple[int, float]],
    ) -> np.ndarray:
        """Overlay LIME superpixels with green/red colouring on the original image."""
        overlay = image_rgb.copy().astype(np.float32)
        weight_map = dict(weights)
        max_abs = max((abs(w) for _, w in weights), default=1.0)
 
        for seg_id, w in weight_map.items():
            mask = segments == seg_id
            alpha = min(abs(w) / max_abs, 1.0) * 0.5
            if w > 0:
                overlay[mask] = (1 - alpha) * overlay[mask] + alpha * np.array([0, 200, 0])
            else:
                overlay[mask] = (1 - alpha) * overlay[mask] + alpha * np.array([200, 0, 0])
 
        return overlay.clip(0, 255).astype(np.uint8)