# Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Runtime image
FROM python:3.11-slim
WORKDIR /app

COPY backend/ ./backend/
RUN pip install --no-cache-dir -e ./backend/

# Copy built frontend into the location main.py expects
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Persist run/score data across container restarts
VOLUME ["/app/backend/data/runs", "/app/backend/data/scores"]

ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

CMD uvicorn dodar.main:app --host 0.0.0.0 --port ${PORT}
