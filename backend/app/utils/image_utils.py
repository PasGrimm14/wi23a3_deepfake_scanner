"""
Image loading, validation, and preprocessing utilities.
 
Kept framework-agnostic: input is raw bytes, output is either a PIL Image
or a PyTorch tensor ready for inference.
"""
 
from __future__ import annotations
 
import io
from typing import Optional
 
import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image, ImageOps
 
from app.core.config import settings
from app.core.logging import get_logger
 
log = get_logger(__name__)
 
# ImageNet mean/std – used by both XceptionNet and DenseNet pretrained on ImageNet.
# TODO: Replace with dataset-specific statistics once you have computed them from
#       your deepfake training corpus (e.g. FaceForensics++, DFDC, etc.).
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD  = (0.229, 0.224, 0.225)
 
 
# ── Validation ────────────────────────────────────────────────────────────────
 
class ImageValidationError(ValueError):
    """Raised for invalid uploads; becomes HTTP 422 in the route handler."""
 
 
def validate_upload(
    content_type: Optional[str],
    content_length: Optional[int],
    data: bytes,
) -> None:
    """
    Validate MIME type and file size before heavy processing.
 
    Raises
    ------
    ImageValidationError
        With a human-readable message suitable for the API response.
    """
    if content_type and content_type not in settings.allowed_content_types:
        raise ImageValidationError(
            f"Unsupported content type '{content_type}'. "
            f"Allowed: {sorted(settings.allowed_content_types)}"
        )
 
    byte_size = content_length if content_length is not None else len(data)
    if byte_size > settings.max_upload_bytes:
        raise ImageValidationError(
            f"File too large ({byte_size / 1_048_576:.1f} MB). "
            f"Maximum allowed: {settings.max_upload_mb} MB."
        )
 
 
# ── Loading ───────────────────────────────────────────────────────────────────
 
def load_image(data: bytes) -> Image.Image:
    """
    Decode raw bytes into a PIL RGB image.
    Handles EXIF orientation and mode conversion robustly.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)  # honour EXIF rotation
        img = img.convert("RGB")
        return img
    except Exception as exc:
        raise ImageValidationError(f"Cannot decode image: {exc}") from exc
 
 
# ── Preprocessing ─────────────────────────────────────────────────────────────
 
def pil_to_tensor(
    image: Image.Image,
    target_size: int,
    mean: tuple[float, ...] = IMAGENET_MEAN,
    std: tuple[float, ...] = IMAGENET_STD,
) -> torch.Tensor:
    """
    Resize → center-crop → [0,1] float → normalise → add batch dim.
 
    Returns
    -------
    torch.Tensor
        Shape (1, 3, target_size, target_size)
    """
    # Resize shortest side to target_size, then center-crop to square
    img = image.resize((target_size, target_size), Image.BILINEAR)
    tensor = TF.to_tensor(img)                     # (3, H, W), [0, 1]
    tensor = TF.normalize(tensor, mean=list(mean), std=list(std))
    return tensor.unsqueeze(0)                     # (1, 3, H, W)
 
 
def tensor_to_numpy_hwc(tensor: torch.Tensor) -> np.ndarray:
    """
    Convert a (1, 3, H, W) or (3, H, W) normalised tensor to (H, W, 3) uint8
    array in [0, 255] for OpenCV / PIL operations.
    """
    t = tensor.squeeze(0).cpu().detach()
    # Undo normalisation
    mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
    std  = torch.tensor(IMAGENET_STD).view(3, 1, 1)
    t = t * std + mean
    t = t.clamp(0.0, 1.0)
    return (t.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
 
 
# ── Overlay helpers ───────────────────────────────────────────────────────────
 
def apply_colormap_on_image(
    original_rgb: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.45,
) -> np.ndarray:
    """
    Blend a single-channel float heatmap (H, W) in [0, 1] onto the original
    image using the JET colormap.
 
    Returns
    -------
    np.ndarray
        RGB uint8 overlay, same spatial size as `original_rgb`.
    """
    import cv2
 
    h, w = original_rgb.shape[:2]
    heatmap_resized = cv2.resize(heatmap, (w, h))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
 
    overlay = (
        (1 - alpha) * original_rgb.astype(np.float32)
        + alpha * heatmap_colored.astype(np.float32)
    ).clip(0, 255).astype(np.uint8)
 
    return overlay
 
 
# ── Base64 encode helpers ─────────────────────────────────────────────────────
 
def numpy_to_base64_png(array: np.ndarray) -> str:
    """Encode an (H, W, 3) uint8 numpy array as a base64 PNG string."""
    import base64
 
    img = Image.fromarray(array.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
 
 
def pil_to_base64_png(image: Image.Image) -> str:
    import base64
 
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")