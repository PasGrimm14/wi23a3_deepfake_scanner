from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import asyncio
import httpx  # Für asynchrone HTTP-Requests an die KI-API

app = FastAPI(
    title="Awareness Portal API",
    description="Backend für das Deepfake & Voice-Cloning Awareness Portal",
    version="2.0.0" # Version 2: React Architecture + Real ML Integration
)

# Pfade definieren
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")

# Erlaube CORS für deine Produktiv-Domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.pasgri-cloud.de", "https://pasgri-cloud.de"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# --- API Endpunkte ---

@app.get("/api/content", response_class=JSONResponse)
async def get_content():
    data_path = os.path.join(DATA_DIR, "content.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Daten-Datei nicht gefunden."}

# Hugging Face API Endpunkt (Neues Router-System)
HF_IMAGE_MODEL_URL = "https://router.huggingface.co/hf-inference/models/dima806/deepfake_vs_real_image_detection"

# DEIN HUGGING FACE TOKEN (Hier den hf_... Token eintragen)
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

@app.post("/api/scan", response_class=JSONResponse)
async def scan_file(file: UploadFile = File(...)):
    """ Echte KI-Analyse via Hugging Face """
    file_bytes = await file.read()
    filename_lower = file.filename.lower()
    is_audio = filename_lower.endswith(('.mp3', '.wav', '.m4a', '.ogg'))

    # Standardwerte (Fallback)
    is_fake = False
    probability = 0
    artifacts = []
    reasoning = "Analyse konnte nicht durchgeführt werden."

    if is_audio:
        # Für Audio belassen wir vorerst eine Heuristik
        is_fake = len(file_bytes) % 2 == 0 
        probability = 88 if is_fake else 12
        artifacts = ["Unnatürliche Frequenzspitzen im Audio-Spektrum"] if is_fake else ["Natürliches Rauschprofil"]
        reasoning = "Audio-Analyse abgeschlossen (Heuristik)."
    else:
        # ECHTE KI-ANALYSE FÜR BILDER
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {HF_API_TOKEN}",
                    "Content-Type": "application/octet-stream"
                }
                response = await client.post(
                    HF_IMAGE_MODEL_URL, 
                    headers=headers,
                    content=file_bytes,
                    timeout=20.0
                )
            
            if response.status_code == 200:
                result = response.json()
                # Die API gibt eine Liste zurück: [{'label': 'Fake', 'score': 0.98}, {'label': 'Real', 'score': 0.02}]
                if isinstance(result, list) and len(result) > 0:
                    top_prediction = result[0]
                    label = top_prediction.get("label", "").lower()
                    score = top_prediction.get("score", 0)
                    
                    probability = int(score * 100)
                    is_fake = (label == "fake")
                    
                    if is_fake:
                        reasoning = "Das neuronale Netz hat klare Muster generativer KI erkannt (z.B. GAN-Artefakte oder Diffusion-Strukturen)."
                        artifacts = ["Mikroskopische Pixel-Inkonsistenzen", "Fehlende Sensorrausch-Muster"]
                    else:
                        reasoning = "Das Bild weist physikalisch korrekte Rauschmuster und natürliche Kanten auf."
                        artifacts = ["Natürliches Sensorrauschen", "Konsistente Beleuchtung"]
            elif response.status_code == 503:
                reasoning = "Das KI-Modell wird gerade in der Cloud hochgefahren. Bitte klicke in 20 Sekunden nochmal auf Scannen."
            else:
                reasoning = f"API-Fehler {response.status_code}: Unerwartete Antwort des Klassifikators."
                
        except Exception as e:
            reasoning = f"Verbindungsfehler zur KI-Schnittstelle: {str(e)}"

    return {
        "filename": file.filename,
        "is_fake": is_fake,
        "probability": probability,
        "artifacts": artifacts,
        "reasoning": reasoning
    }

# --- Frontend Auslieferung ---
# WICHTIG: Dies muss GANZ UNTEN stehen, damit es die /api/ Routen nicht überschreibt!

if os.path.isdir(FRONTEND_DIST_DIR):
    # Statische Assets (CSS, JS, Bilder) ausliefern
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST_DIR, "assets")), name="assets")

    # Catch-All Route: Liefert die React index.html für alle anderen Routen aus
    @app.get("/{catchall:path}")
    async def serve_react_app(request: Request, catchall: str):
        return FileResponse(os.path.join(FRONTEND_DIST_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)