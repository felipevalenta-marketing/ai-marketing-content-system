#!/usr/bin/env sh
set -eu

python - <<'PY'
import json
import urllib.request

try:
    payload = json.loads(urllib.request.urlopen("http://localhost:8000/health", timeout=5).read().decode())
    print("Health:", payload.get("data", {}).get("status", "unknown"))
except Exception as exc:
    print(f"Health check failed: {exc}")
    raise SystemExit(1)
PY
