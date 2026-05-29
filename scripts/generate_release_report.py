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


def main() -> int:
    app = create_app(ApiConfig())
    manager = ReleaseManager()
    summary = manager.build_release_summary(app=app, root=ROOT)
    report = manager.generate_release_report(summary, root=ROOT)
    executive_summary = summary.get("executive_summary", "")
    artifact_index = summary.get("release_artifacts", "")
    print(json.dumps({"success": True, **report, "executive_summary": executive_summary, "artifact_index": artifact_index}, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
