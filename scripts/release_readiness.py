from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.api_config import ApiConfig
from src.api.main import create_app
from src.release.release_manager import ReleaseManager


def build_release_readiness(root: Path | None = None) -> dict[str, object]:
    root = root or ROOT
    app = create_app(ApiConfig())
    manager = ReleaseManager()
    summary = manager.build_release_summary(app=app, root=root)
    report = manager.generate_release_report(summary, root=root)
    return {
        "mvp_complete": bool(summary.get("mvp_ready", False) and summary.get("release_ready", False)),
        "version": summary.get("version", "1.0.0"),
        "release_status": "approved" if summary.get("mvp_ready") and summary.get("release_ready") else summary.get("release_status", "blocked"),
        "release_score": int(summary.get("release_score", 0)),
        "production_ready": bool(summary.get("mvp_ready", False) and summary.get("release_ready", False)),
        "summary": summary,
        "report": report,
        "warnings": summary.get("warnings", []),
        "errors": summary.get("errors", []),
    }


def main() -> int:
    result = build_release_readiness()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0 if result.get("production_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
