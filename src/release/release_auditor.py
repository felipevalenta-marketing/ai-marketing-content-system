"""Release audit summary helpers."""

from __future__ import annotations

from typing import Any

from .release_validator import validate_release


def build_release_audit(app: Any | None = None, root=None) -> dict[str, Any]:
    validation = validate_release(app=app, root=root)
    modules = {
        "platform": validation.get("functional", {}).get("modules", []),
        "api": validation.get("technical", {}),
        "frontend": validation.get("deployment", {}),
        "deployment": validation.get("deployment", {}),
        "observability": validation.get("observability", {}),
        "ci_cd": validation.get("ci", {}),
        "security": validation.get("security", {}),
        "documentation": validation.get("documentation", {}),
    }
    return {"audit_passed": not validation.get("errors"), "modules": modules, "warnings": validation.get("warnings", []), "errors": validation.get("errors", [])}

