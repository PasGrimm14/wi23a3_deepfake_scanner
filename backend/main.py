from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import asyncio
import random

app = FastAPI(
    title="Awareness Portal API",
    description="Backend für das Deepfake & Voice-Cloning Awareness Portal",
    version="2.0.0" # Version 2: React Architecture
)

# Pfade definieren
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")

# Erlaube CORS (wichtig für die lokale Entwicklung, wenn React auf Port 5173 und FastAPI auf 8000 läuft)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In Produktion auf ["https://svschefflenz.online"] einschränken
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

@app.post("/api/scan", response_class=JSONResponse)
async def scan_file(file: UploadFile = File(...)):
    """ KI-Scanner Simulation (ohne Speicherung auf Festplatte) """
    await asyncio.sleep(2.0)
    is_fake = random.choice([True, False])
    filename_lower = file.filename.lower()
    is_audio = filename_lower.endswith(('.mp3', '.wav', '.m4a', '.ogg'))
    
    if is_fake:
        probability = random.randint(75, 98)
        if is_audio:
            artifacts = [
                "Unnatürliche Frequenzspitzen im Audio-Spektrum erkannt.",
                "Synthetische Überbetonung von Zischlauten."
            ]
            reasoning = "Klare Muster synthetischer Sprachgenerierung."
        else:
            artifacts = [
                "Asymmetrische Lichtreflexionen in den Pupillen.",
                "Lokale Pixel-Glättung und fehlende Mikroporen."
            ]
            reasoning = "Visuelle Inkonsistenzen und physikalische Fehler erkannt."
        selected_artifacts = artifacts
    else:
        probability = random.randint(2, 25)
        selected_artifacts = ["Natürliche Strukturen", "Konsistentes Rauschprofil"]
        reasoning = "Keine typischen KI-Artefakte gefunden."

    return {
        "filename": file.filename,
        "is_fake": is_fake,
        "probability": probability,
        "artifacts": selected_artifacts,
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