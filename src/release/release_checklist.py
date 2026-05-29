"""Release checklist generation."""

from __future__ import annotations

from typing import Any


CHECKLIST_CATEGORIES: dict[str, list[str]] = {
    "functional": [f"Functional check {index:02d}" for index in range(1, 26)],
    "technical": [f"Technical check {index:02d}" for index in range(1, 26)],
    "security": [f"Security check {index:02d}" for index in range(1, 26)],
    "deployment": [f"Deployment check {index:02d}" for index in range(1, 21)],
    "observability": [f"Observability check {index:02d}" for index in range(1, 21)],
    "ci_cd": [f"CI/CD check {index:02d}" for index in range(1, 16)],
    "documentation": [f"Documentation check {index:02d}" for index in range(1, 21)],
}


def _category_status(section: dict[str, Any] | bool | None) -> bool:
    if isinstance(section, bool):
        return section
    if not isinstance(section, dict):
        return False
    if "passed" in section:
        return bool(section.get("passed"))
    if "ready" in section:
        return bool(section.get("ready"))
    if "valid" in section:
        return bool(section.get("valid"))
    return False


def build_release_checklist(sections: dict[str, Any] | None = None) -> dict[str, Any]:
    sections = dict(sections or {})
    section_aliases = {
        "functional": "functional_ready",
        "technical": "technical_ready",
        "security": "security_ready",
        "deployment": "deployment_ready",
        "observability": "observability_ready",
        "ci_cd": "ci_ready",
        "documentation": "documentation_ready",
    }
    checklist: list[dict[str, Any]] = []
    passed = 0
    failed = 0
    warnings = 0
    for category, items in CHECKLIST_CATEGORIES.items():
        section_value = sections.get(category)
        if section_value is None:
            section_value = sections.get(section_aliases.get(category, category))
        category_passed = _category_status(section_value) if sections else False
        for item in items:
            passed_item = bool(category_passed)
            checklist.append({"category": category, "item": item, "passed": passed_item})
            if passed_item:
                passed += 1
            else:
                failed += 1
    total_checks = len(checklist)
    return {
        "total_checks": total_checks,
        "passed": passed,
        "failed": failed,
        "warnings": warnings,
        "items": checklist,
        "total": total_checks,
        "completed": passed,
        "pending": failed,
        "blocked": 0,
    }
