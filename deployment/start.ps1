Write-Host "AI Marketing Content System deployment start"
if (-not (Test-Path ".env")) {
  Write-Host "Warning: .env not found. Copy .env.example to .env before production use."
}
python scripts/check_env.py
docker compose config
docker compose up --build
