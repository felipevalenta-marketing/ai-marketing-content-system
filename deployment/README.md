# Deployment Guide

This FR provides local development, Docker production-like deployment, and future cloud-ready structure only.
It does not deploy to a cloud provider, configure HTTPS, implement CI/CD, or add monitoring.

## Prerequisites

- Docker
- Docker Compose
- Node.js 20+ for local frontend development or manual builds

## Setup

1. Copy `.env.example` to `.env`.
2. Set a real `OPENAI_API_KEY` if you want live generation.
3. Set a secure `JWT_SECRET_KEY` for authentication.
4. Set `VITE_API_BASE_URL` if you want the frontend build to point at a non-default API host.
5. Run `python scripts/check_env.py` to confirm required environment values before starting containers.

## Run

Validate the Compose file first:

```bash
docker compose config
```

Start the container stack:

```bash
docker compose up --build
```

API:

- `http://localhost:8000/health`
- `http://localhost:8000/health/ready`
- `http://localhost:8000/health/live`
- `http://localhost:8000/docs`

Frontend:

- `http://localhost:5173`

If you use the optional static frontend service in Docker Compose, it serves the production build through Nginx. Local frontend development still uses `npm run dev`.

## Local Frontend Development

```bash
cd frontend
npm install
npm run dev
npm run build
```

The frontend honors `VITE_API_BASE_URL=http://localhost:8000` for local and Docker-backed environments.

You can also run the deployment smoke check directly:

```bash
python scripts/production_smoke.py
```

## Troubleshooting

- Missing env values: run `python scripts/check_env.py`.
- Port already in use: stop the process on ports `8000` or `5173`.
- Docker not running: start Docker Desktop or the Docker service.
- Frontend cannot reach the API: confirm `CORS_ORIGINS` includes the frontend origin.
- `docker compose config` fails: ensure Docker Compose is installed and available in your shell.
- Smoke check fails: confirm `STORAGE_ROOT` is writable and `JWT_SECRET_KEY` is set.
