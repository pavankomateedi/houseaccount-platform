# syntax=docker/dockerfile:1

# ---- Stage 1: build the React frontend ----
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/pnpm-lock.yaml* ./
# Pin pnpm to the version that produced the lockfile (corepack reads packageManager).
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
RUN pnpm install --no-frozen-lockfile
COPY frontend/ ./
RUN pnpm build          # -> /fe/dist

# ---- Stage 2: Python backend that also serves the built frontend ----
FROM python:3.12-slim AS app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HA_MODE=mock \
    HA_STATIC_DIR=/app/frontend/dist
WORKDIR /app

COPY backend/ ./backend/
RUN pip install -e ./backend
# Pre-generate the seeded corpus + golden set so the first request is instant.
RUN python -m houseaccount.cli gen

COPY --from=frontend /fe/dist ./frontend/dist

EXPOSE 8000
# Hosts inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn houseaccount.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
