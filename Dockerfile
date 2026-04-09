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

# Installiere Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere das Backend und die Daten
COPY backend/ ./backend/
COPY data/ ./data/

# WICHTIG: Kopiere das FERTIG GEBAUTE React-Frontend aus Stage 1
# FastAPI liefert diese statischen Dateien dann aus
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Port freigeben und Server starten
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]