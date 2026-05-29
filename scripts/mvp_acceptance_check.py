from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.api_config import ApiConfig
from src.api.main import create_app
from src.release.mvp_acceptance import build_mvp_acceptance


def main() -> int:
    app = create_app(ApiConfig())
    result = build_mvp_acceptance(app=app, root=ROOT)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0 if result.get("status") == "approved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
