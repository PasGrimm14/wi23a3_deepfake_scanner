"""
Tests for the /health and /models endpoints.
Run with: pytest backend/app/tests/ -v
"""
 
from __future__ import annotations
 
from unittest.mock import MagicMock, patch
 
import pytest
from fastapi.testclient import TestClient
 
from app.main import create_app
 
 
@pytest.fixture()
def client():
    """TestClient with mocked ML services to avoid loading real models."""
    app = create_app()
 
    mock_inference = MagicMock()
    mock_inference.model_info.return_value = [
        {
            "name": "xception",
            "backbone": "XceptionNet",
            "weights_loaded": False,
            "input_size": 299,
            "description": "Test model",
        }
    ]
 
    app.state.inference_service = mock_inference
    app.state.explainability_service = MagicMock()
    app.state.region_service = MagicMock()
 
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
 
 
def test_health_returns_ok(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
 
 
def test_models_returns_list(client: TestClient):
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    assert "models" in body
    assert isinstance(body["models"], list)
    assert body["models"][0]["name"] == "xception"