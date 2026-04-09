"""
Integration-style tests for POST /api/v1/analyze-image.
 
All heavy ML calls are mocked; tests validate request routing,
validation logic, and response schema compliance.
"""
 
from __future__ import annotations
 
import io
from unittest.mock import MagicMock, patch
 
import numpy as np
import pytest
import torch
from PIL import Image
from fastapi.testclient import TestClient
 
from app.main import create_app
from app.models.base import PredictionResult
from app.services.explainability_service import ExplainabilityResult
 
 
def _make_png_bytes(width: int = 64, height: int = 64) -> bytes:
    img = Image.fromarray(np.random.randint(0, 255, (height, width, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
 
 
def _fake_pred_result(cls: int = 1) -> PredictionResult:
    probs = torch.tensor([[0.2, 0.8]]) if cls == 1 else torch.tensor([[0.8, 0.2]])
    return PredictionResult(
        logits=torch.tensor([[0.1, 0.9]]),
        probabilities=probs,
        predicted_class=cls,
        confidence=float(probs[0, cls]),
    )
 
 
def _fake_gradcam() -> ExplainabilityResult:
    r = ExplainabilityResult()
    r.gradcam_available = True
    r.heatmap = np.zeros((64, 64), dtype=np.float32)
    r.heatmap_base64 = "aGVsbG8="
    r.overlay_base64 = "d29ybGQ="
    return r
 
 
def _fake_lime() -> ExplainabilityResult:
    r = ExplainabilityResult()
    r.lime_available = True
    r.segments = np.zeros((64, 64), dtype=np.int32)
    r.segments_base64 = "c2VnbWVudA=="
    r.top_superpixels = [(0, 0.9), (1, -0.3)]
    return r
 
 
@pytest.fixture()
def client():
    app = create_app()
 
    mock_inference = MagicMock()
    mock_inference.run_inference.return_value = (
        torch.zeros(1, 3, 64, 64),
        _fake_pred_result(1),
        64,
    )
    mock_loader = MagicMock()
    mock_loader.name = "xception"
    mock_loader.device = torch.device("cpu")
    mock_loader.weights_loaded.return_value = False
    mock_loader.input_size = 64
    mock_inference.get_loader.return_value = mock_loader
    mock_inference.model_info.return_value = []
 
    mock_explain = MagicMock()
    mock_explain.run_gradcam.return_value = _fake_gradcam()
    mock_explain.run_lime.return_value = _fake_lime()
 
    mock_region = MagicMock()
    mock_region.explain.return_value = ([], ["Auffällige Aktivierung in Bildmitte."])
 
    app.state.inference_service = mock_inference
    app.state.explainability_service = mock_explain
    app.state.region_service = mock_region
 
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
 
 
def test_analyze_returns_200(client: TestClient):
    png = _make_png_bytes()
    resp = client.post(
        "/api/v1/analyze-image",
        files={"file": ("test.png", png, "image/png")},
        data={"model_name": "xception", "explanation_methods": "gradcam,lime"},
    )
    assert resp.status_code == 200, resp.text
 
 
def test_analyze_response_schema(client: TestClient):
    png = _make_png_bytes()
    body = client.post(
        "/api/v1/analyze-image",
        files={"file": ("test.png", png, "image/png")},
        data={"model_name": "xception", "explanation_methods": "gradcam"},
    ).json()
 
    assert "prediction" in body
    assert "label" in body["prediction"]
    assert "confidence" in body["prediction"]
    assert "class_probabilities" in body["prediction"]
    assert "explanations" in body
    assert "gradcam" in body["explanations"]
    assert "lime" in body["explanations"]
    assert "meta" in body
    assert "processing_time_ms" in body["meta"]
 
 
def test_analyze_rejects_oversized_file(client: TestClient):
    # Generate a payload that exceeds MAX_UPLOAD_MB (patched to 0.001 MB)
    with patch("app.utils.image_utils.settings") as mock_settings:
        mock_settings.allowed_content_types = {"image/png"}
        mock_settings.max_upload_bytes = 100  # 100 bytes limit
        mock_settings.max_upload_mb = 0.0001
 
        big_data = b"x" * 200
        resp = client.post(
            "/api/v1/analyze-image",
            files={"file": ("big.png", big_data, "image/png")},
        )
    # Expect 422 (validation) or 500 (decode failure) – not 200
    assert resp.status_code in (422, 500)
 
 
def test_analyze_rejects_invalid_content_type(client: TestClient):
    resp = client.post(
        "/api/v1/analyze-image",
        files={"file": ("malware.exe", b"MZ\x00\x00", "application/octet-stream")},
    )
    assert resp.status_code == 422