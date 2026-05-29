# Deployment Guide

## Installation

Install the project dependencies and create a local `.env` from `.env.example`.

## Deployment

Run the local production-like deployment with Docker Compose:

```bash
docker compose up --build
```

## Environment Setup

Set the required runtime variables in `.env` or the environment:

- `JWT_SECRET_KEY`
- `OPENAI_API_KEY`
- `APP_ENV`
- `STORAGE_ROOT`

## Troubleshooting

- Verify the backend health endpoint at `/health`.
- Verify the readiness endpoint at `/health/ready`.
- Check the frontend build with `npm run build`.

