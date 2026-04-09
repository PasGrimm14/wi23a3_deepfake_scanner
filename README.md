# Deepfake Detection API
 
Explainable AI-image / deepfake detection backend built with **FastAPI**, **PyTorch**, **Grad-CAM**, and **LIME**.
 
## Project structure
 
```
backend/
├── app/
│   ├── main.py                        # App factory + lifespan
│   ├── api/
│   │   ├── dependencies.py            # FastAPI Depends() helpers
│   │   ├── error_handlers.py          # Centralised HTTP error handling
│   │   └── routes/
│   │       ├── health.py              # GET /api/v1/health
│   │       ├── models.py              # GET /api/v1/models
│   │       └── analyze.py             # POST /api/v1/analyze-image
│   ├── core/
│   │   ├── config.py                  # Settings via pydantic-settings + .env
│   │   └── logging.py                 # Structured logging setup
│   ├── models/
│   │   ├── base.py                    # Abstract ModelLoader / Predictor
│   │   ├── xception.py                # XceptionNet (standalone PyTorch impl)
│   │   └── densenet.py                # DenseNet121 (torchvision)
│   ├── services/
│   │   ├── inference_service.py       # Model registry + inference orchestration
│   │   ├── explainability_service.py  # Grad-CAM + LIME implementations
│   │   └── region_explainer_service.py# Face-landmark / grid region mapping
│   ├── utils/
│   │   └── image_utils.py             # Load, validate, preprocess, encode
│   ├── schemas/
│   │   ├── requests.py                # Pydantic form-param models
│   │   └── responses.py               # Pydantic response models
│   └── tests/
│       ├── test_health.py
│       └── test_analyze.py
├── weights/
│   ├── xception/                      # Place weights.pth here
│   └── densenet/                      # Place weights.pth here
├── .env.example
└── requirements.txt
```
 
---
 
## Setup
 
### 1. Python environment
 
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```
 
### 2. Configuration
 
```bash
cp backend/.env.example backend/.env
# Edit backend/.env as needed (device, upload limits, CORS origins, …)
```
 
### 3. (Optional) MediaPipe
 
MediaPipe enables face-landmark region detection. If installation fails on your
platform, remove it from `requirements.txt`; the API falls back to a grid-based
region explanation automatically.
 
---
 
## Starting the server
 
From the repository root:
 
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
 
API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc:      http://localhost:8000/redoc
 
---
 
## Example API calls
 
### Health check
 
```bash
curl http://localhost:8000/api/v1/health
```
 
```json
{"status": "ok", "version": "1.0.0"}
```
 
### List available models
 
```bash
curl http://localhost:8000/api/v1/models
```
 
### Analyse an image (minimal)
 
```bash
curl -X POST http://localhost:8000/api/v1/analyze-image \
  -F "file=@/path/to/image.jpg" \
  -F "model_name=xception" \
  -F "explanation_methods=gradcam,lime" \
  -F "return_overlay=true" \
  -F "return_region_scores=true"
```
 
### Response structure
 
```json
{
  "filename": "image.jpg",
  "model_used": "xception",
  "prediction": {
    "label": "AI-generated",
    "confidence": 0.92,
    "class_probabilities": {"real": 0.08, "fake": 0.92}
  },
  "explanations": {
    "gradcam": {
      "available": true,
      "heatmap_base64": "<base64 PNG>",
      "overlay_base64": "<base64 PNG>",
      "top_regions": [
        {"region_name": "Mund", "score": 0.81, "bbox": [120, 200, 180, 240]}
      ]
    },
    "lime": {
      "available": true,
      "segments_base64": "<base64 PNG>",
      "top_superpixels": [{"segment_id": 4, "weight": 0.73}]
    },
    "region_text_explanation": [
      "Hohe Modellaktivierung in: Mund (0.81), linke Wange (0.67).",
      "Auffällige Muster vor allem im Bereich Mund und linke Wange."
    ]
  },
  "meta": {
    "processing_time_ms": 1234.5,
    "image_size": {"width": 512, "height": 512}
  }
}
```
 
---
 
## Loading your own model weights
 
### XceptionNet
 
```python
# After training:
torch.save(model.state_dict(), "backend/weights/xception/weights.pth")
# Or with full checkpoint:
torch.save({"model": model.state_dict(), "epoch": 50}, "backend/weights/xception/weights.pth")
```
 
Set `MODEL_DIR=backend/weights` in `.env`. The loader picks up the file at startup automatically.
 
The XceptionNet architecture is defined in `backend/app/models/xception.py` with `num_classes=2`.
If your trained model has a different head (e.g. sigmoid + 1 output), adjust the `XceptionNet` class
and update `XceptionPredictor.predict()` accordingly.
 
### DenseNet121
 
```python
torch.save(model.state_dict(), "backend/weights/densenet/weights.pth")
```
 
The loader replaces the ImageNet head with a 2-class head before loading your weights.
 
### Using a completely different architecture
 
1. Create `backend/app/models/mymodel.py` with subclasses of `ModelLoader` and `Predictor`.
2. Register it in `backend/app/services/inference_service.py`:
   ```python
   _REGISTRY["mymodel"] = (MyModelLoader, MyModelPredictor)
   ```
3. Restart the server.
 
---
 
## Running tests
 
```bash
pytest backend/app/tests/ -v
```
 
---
 
## Research extension points
 
| Goal | Where to extend |
|------|----------------|
| Additional CAM variants (Grad-CAM++, Score-CAM) | `explainability_service.py` – subclass `GradCamExplainer` |
| Pointing Game evaluation | Add `pointing_game(heatmap, gt_bbox)` in `explainability_service.py` |
| IoU with GT masks | Add `heatmap_iou(heatmap, gt_mask)` in `explainability_service.py` |
| Cross-dataset evaluation | Pass dataset name in request metadata; group results in evaluation scripts |
| Additional models | Add loader + predictor in `app/models/`, register in `_REGISTRY` |
| Accuracy / F1 / AUC metrics | Add evaluation scripts in `backend/evaluation/` using the `Predictor` interface |
 
---
 
## Docker
 
```bash
docker compose up --build
```
 
The backend is exposed on port 8000. See `docker-compose.yml` for configuration.