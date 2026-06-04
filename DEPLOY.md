# Deploying HouseAccount

The app ships as a **single service**: the FastAPI backend serves the built React
app on the same origin (`/` = UI, `/api/*` = API). One container, one URL, no CORS.

Default mode is `HA_MODE=mock` — fully offline, deterministic, free. Ideal for a
review link. (For live Claude Opus, set `HA_MODE=live` + `ANTHROPIC_API_KEY`.)

## Option A — Render (recommended, persistent free URL)

1. Push this project to its own GitHub repo (see below).
2. On https://render.com → **New → Blueprint** → connect the repo.
   Render reads [`render.yaml`](render.yaml) and builds the [`Dockerfile`](Dockerfile).
3. First build ~3–5 min → you get `https://houseaccount.onrender.com` to share.
   Health check: `/api/health`. (Free tier sleeps when idle; first hit ~30s.)

## Option B — Any Docker host (Railway / Fly.io / Cloud Run)

The image is host-agnostic. It listens on `$PORT` (default 8000).

```bash
docker build -t houseaccount .
docker run -p 8000:8000 houseaccount      # http://localhost:8000
# Fly:      fly launch --dockerfile Dockerfile
# Railway:  new project → deploy from repo (auto-detects Dockerfile)
# Cloud Run: gcloud run deploy --source .
```

## Create the GitHub repo

```bash
# from this folder
git init -b main
git add .
git commit -m "HouseAccount platform"
gh repo create houseaccount-platform --private --source=. --push
```

## Live (Claude Opus) instead of mock

Set on the host: `HA_MODE=live` and `ANTHROPIC_API_KEY=sk-ant-...`.
Mock stays the default so a missing key never breaks the deploy.

## What's NOT included (by design, for a review build)

- Data is in-memory and resets on restart (seeded corpus + reviews are deterministic).
- No auth on the review link — treat the URL as shareable-but-unlisted.
