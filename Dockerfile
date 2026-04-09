# --- STAGE 1: Build React Frontend ---
# Wir nutzen Node.js, um die React-App zu bauen
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend
# Kopiere Konfigurationsdateien
COPY frontend/package.json frontend/vite.config.js ./
# Kopiere den Quellcode
COPY frontend/ ./
# Installiere Abhängigkeiten und baue das Projekt
RUN npm install
RUN npm run build


# --- STAGE 2: Setup FastAPI Backend ---
# Wir nutzen Python für das Backend
FROM python:3.11-slim

WORKDIR /project

# Verhindert, dass Python .pyc Dateien schreibt
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OPENCV_IO_ENABLE_OPENEXR=0
ENV PYTHONPATH=/project/backend
# System deps required by OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
 
# Install Python deps from backend-specific requirements
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere das Backend und die Daten
COPY backend/ ./backend/
COPY data/ ./data/

# WICHTIG: Kopiere das FERTIG GEBAUTE React-Frontend aus Stage 1
# FastAPI liefert diese statischen Dateien dann aus
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Port freigeben und Server starten
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
