"""
RegionExplainerService – maps Grad-CAM activations to semantic image regions.
 
Two modes
─────────
1. Face-landmark mode (MediaPipe Face Mesh):
   Maps activations to 11 facial regions (eyes, mouth, nose, forehead, etc.)
   when at least one face is detected in the image.
 
2. Grid fallback mode:
   Divides the image into a 3×3 grid and names cells by position
   (top-left, top-centre, …) when no face is detected.
 
RESEARCH EXTENSION
──────────────────
For evaluation with localisation datasets (e.g. DFDCP with bounding boxes):
- Add `evaluate_region_iou(heatmap, gt_mask)` to compare activated regions
  against ground-truth face manipulations.
- For cross-dataset evaluation, pass dataset name metadata into the explanation
  context so results can be grouped in analysis scripts.
"""
 
from __future__ import annotations
 
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
 
import cv2
import numpy as np
 
from app.core.logging import get_logger
 
log = get_logger(__name__)
 
 
# ── Data containers ───────────────────────────────────────────────────────────
 
@dataclass
class RegionScore:
    region_name: str
    score: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
 
 
# ── Abstract interface ────────────────────────────────────────────────────────
 
class RegionExplainer(ABC):
    @abstractmethod
    def explain(
        self,
        heatmap: np.ndarray,   # (H, W) float [0, 1]
        image_rgb: np.ndarray, # (H, W, 3) uint8
    ) -> tuple[list[RegionScore], list[str]]:
        """
        Returns
        -------
        region_scores : list[RegionScore]
            Scored regions with bounding boxes, sorted descending by score.
        text_explanation : list[str]
            Human-readable sentences summarising the activation pattern.
        """
 
 
# ── Face-landmark region explainer ───────────────────────────────────────────
 
# Mediapipe Face Mesh landmark indices for 11 facial regions.
# Source: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
_FACE_REGION_LANDMARKS: dict[str, list[int]] = {
    "forehead":      [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109],
    "left_eye":      [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
    "right_eye":     [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398],
    "nose":          [1, 2, 5, 4, 19, 94, 2, 164, 0, 11, 12, 13, 14, 15, 16, 17, 18],
    "mouth":         [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185],
    "left_cheek":    [116, 123, 147, 213, 192, 214, 210, 211, 32, 208],
    "right_cheek":   [345, 352, 376, 433, 416, 434, 430, 431, 262, 428],
    "chin":          [152, 377, 400, 378, 379, 365, 397, 288, 361, 323],
    "left_eyebrow":  [70, 63, 105, 66, 107, 55, 65, 52, 53, 46],
    "right_eyebrow": [300, 293, 334, 296, 336, 285, 295, 282, 283, 276],
    "jaw":           [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338],
}
 
_REGION_LABELS_HUMAN: dict[str, str] = {
    "forehead":      "Stirn",
    "left_eye":      "linkes Auge",
    "right_eye":     "rechtes Auge",
    "nose":          "Nase",
    "mouth":         "Mund",
    "left_cheek":    "linke Wange",
    "right_cheek":   "rechte Wange",
    "chin":          "Kinn",
    "left_eyebrow":  "linke Augenbraue",
    "right_eyebrow": "rechte Augenbraue",
    "jaw":           "Kiefer",
}
 
 
class FaceLandmarkRegionExplainer(RegionExplainer):
    """Uses MediaPipe Face Mesh to map heatmap activations to facial regions."""
 
    def __init__(self) -> None:
        self._mp_available: Optional[bool] = None
        self._face_mesh = None
 
    def _init_mediapipe(self) -> bool:
        if self._mp_available is not None:
            return self._mp_available
        try:
            import mediapipe as mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
            )
            self._mp_available = True
        except ImportError:
            log.warning("MediaPipe not installed – face landmark mode disabled.")
            self._mp_available = False
        return self._mp_available
 
    def _detect_landmarks(
        self, image_rgb: np.ndarray
    ) -> Optional[list]:
        if not self._init_mediapipe():
            return None
        results = self._face_mesh.process(image_rgb)
        if not results.multi_face_landmarks:
            return None
        return results.multi_face_landmarks[0].landmark
 
    def explain(
        self,
        heatmap: np.ndarray,
        image_rgb: np.ndarray,
    ) -> tuple[list[RegionScore], list[str]]:
        h, w = image_rgb.shape[:2]
 
        landmarks = self._detect_landmarks(image_rgb)
        if landmarks is None:
            return [], []
 
        # Resize heatmap to match image
        hm = cv2.resize(heatmap, (w, h)).astype(np.float32)
 
        region_scores: list[RegionScore] = []
        for region_key, indices in _FACE_REGION_LANDMARKS.items():
            pts = []
            for idx in indices:
                if idx < len(landmarks):
                    lm = landmarks[idx]
                    pts.append((int(lm.x * w), int(lm.y * h)))
            if not pts:
                continue
 
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            x1, y1 = max(min(xs) - 5, 0), max(min(ys) - 5, 0)
            x2, y2 = min(max(xs) + 5, w), min(max(ys) + 5, h)
 
            region_hm = hm[y1:y2, x1:x2]
            if region_hm.size == 0:
                continue
            score = float(region_hm.mean())
 
            human_name = _REGION_LABELS_HUMAN.get(region_key, region_key)
            region_scores.append(RegionScore(
                region_name=human_name,
                score=round(score, 4),
                bbox=(x1, y1, x2, y2),
            ))
 
        region_scores.sort(key=lambda r: r.score, reverse=True)
        text = _build_face_text(region_scores)
        return region_scores, text
 
 
def _build_face_text(regions: list[RegionScore]) -> list[str]:
    if not regions:
        return ["Keine Gesichtsregionen erkannt."]
 
    top = [r for r in regions if r.score > 0.3][:3]
    if not top:
        top = regions[:2]
 
    names = [r.region_name for r in top]
    score_str = ", ".join(f"{r.region_name} ({r.score:.2f})" for r in top)
    sentences = [
        f"Hohe Modellaktivierung in: {score_str}.",
    ]
    if len(top) >= 2:
        sentences.append(
            f"Auffällige Muster vor allem im Bereich {names[0]} und {names[1]}."
        )
    return sentences
 
 
# ── Grid fallback explainer ───────────────────────────────────────────────────
 
_GRID_LABELS = [
    ["oben links",   "oben Mitte",   "oben rechts"],
    ["Mitte links",  "Bildmitte",    "Mitte rechts"],
    ["unten links",  "unten Mitte",  "unten rechts"],
]
 
 
class GridRegionExplainer(RegionExplainer):
    """3×3 grid fallback when no face is detected."""
 
    def __init__(self, rows: int = 3, cols: int = 3) -> None:
        self.rows = rows
        self.cols = cols
 
    def explain(
        self,
        heatmap: np.ndarray,
        image_rgb: np.ndarray,
    ) -> tuple[list[RegionScore], list[str]]:
        h, w = image_rgb.shape[:2]
        hm = cv2.resize(heatmap, (w, h)).astype(np.float32)
 
        cell_h = h // self.rows
        cell_w = w // self.cols
 
        region_scores: list[RegionScore] = []
        for r in range(self.rows):
            for c in range(self.cols):
                y1, y2 = r * cell_h, (r + 1) * cell_h
                x1, x2 = c * cell_w, (c + 1) * cell_w
                score = float(hm[y1:y2, x1:x2].mean())
                name = _GRID_LABELS[r][c]
                region_scores.append(RegionScore(
                    region_name=name,
                    score=round(score, 4),
                    bbox=(x1, y1, x2, y2),
                ))
 
        region_scores.sort(key=lambda r: r.score, reverse=True)
        text = _build_grid_text(region_scores)
        return region_scores, text
 
 
def _build_grid_text(regions: list[RegionScore]) -> list[str]:
    if not regions:
        return ["Keine Regionsinformationen verfügbar."]
    top = regions[:3]
    names = [r.region_name for r in top]
    score_str = ", ".join(f"{r.region_name} ({r.score:.2f})" for r in top)
    return [
        f"Auffällige Muster in: {score_str}.",
        f"Schwerpunkt der Modellaktivierung: {names[0]}.",
    ]
 
 
# ── Facade ────────────────────────────────────────────────────────────────────
 
class RegionExplainerService:
    """
    Tries face-landmark explanation first; falls back to grid if no face found.
    """
 
    def __init__(self) -> None:
        self._face_explainer = FaceLandmarkRegionExplainer()
        self._grid_explainer = GridRegionExplainer()
 
    def explain(
        self,
        heatmap: np.ndarray,
        image_rgb: np.ndarray,
    ) -> tuple[list[RegionScore], list[str]]:
        scores, text = self._face_explainer.explain(heatmap, image_rgb)
        if scores:
            return scores, text
 
        log.debug("No face landmarks found – using grid fallback.")
        return self._grid_explainer.explain(heatmap, image_rgb)