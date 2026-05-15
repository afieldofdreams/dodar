# Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Build backend
FROM python:3.11-slim
WORKDIR /app

COPY backend/ ./backend/
RUN pip install --no-cache-dir -e ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV PORT=8000

EXPOSE 8000

CMD uvicorn dodar.main:app --host 0.0.0.0 --port ${PORT}
