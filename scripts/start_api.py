from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    host = os.getenv("API_HOST", "0.0.0.0")
    port = os.getenv("API_PORT", "8000")
    print("Starting API")
    print(f"uvicorn src.api.main:app --host {host} --port {port}")
    return subprocess.call([sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", host, "--port", port])


if __name__ == "__main__":
    raise SystemExit(main())
