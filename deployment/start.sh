#!/usr/bin/env sh
set -eu

echo "AI Marketing Content System deployment start"
if [ ! -f .env ]; then
  echo "Warning: .env not found. Copy .env.example to .env before production use."
fi
python scripts/check_env.py
docker compose config
docker compose up --build
