"""Release validation orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.configuration.config_manager import ConfigManager
from src.observability.observability_health import build_observability_health
from src.security.security_health import build_security_baseline, build_security_health


RELEASE_DOMAINS = [
    "functionality",
    "frontend",
    "api",
    "storage",
    "reporting",
    "analytics",
    "authentication",
    "rbac",
    "organizations",
    "deployment",
    "observability",
    "security",
    "ci_cd",
    "documentation",
]


def _root(root: Path | None = None) -> Path:
    return root or Path(__file__).resolve().parents[2]


def _module_status(name: str, passed: bool, detail: str = "") -> dict[str, Any]:
    return {"module": name, "status": "pass" if passed else "fail", "detail": detail}


def _section_status(section: dict[str, Any] | bool | None) -> bool:
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


def _build_domain_statuses(sections: dict[str, Any]) -> list[dict[str, Any]]:
    functional = sections.get("functional", {})
    modules = functional.get("modules", []) if isinstance(functional, dict) else []
    module_map = {str(module.get("module", "")).strip().lower(): str(module.get("status", "")).strip().lower() == "pass" for module in modules if isinstance(module, dict)}
    checks = {
        "functionality": bool(sections.get("functional_ready")),
        "frontend": module_map.get("frontend", False) or bool(sections.get("functional_ready")),
        "api": module_map.get("api", False) or bool(sections.get("functional_ready")),
        "storage": module_map.get("storage", False) or bool(sections.get("functional_ready")),
        "reporting": module_map.get("reports", False) or bool(sections.get("documentation_ready")),
        "analytics": module_map.get("analytics", False) or bool(sections.get("observability_ready")),
        "authentication": module_map.get("authentication", False) or bool(sections.get("functional_ready")),
        "rbac": module_map.get("rbac", False) or bool(sections.get("security_ready")),
        "organizations": module_map.get("organizations", False) or bool(sections.get("functional_ready")),
        "deployment": bool(sections.get("deployment_ready")),
        "observability": bool(sections.get("observability_ready")),
        "security": bool(sections.get("security_ready")),
        "ci_cd": bool(sections.get("ci_ready")),
        "documentation": bool(sections.get("documentation_ready")),
    }
    return [{"domain": domain, "status": "pass" if checks.get(domain, False) else "fail"} for domain in RELEASE_DOMAINS]


def list_domains() -> list[str]:
    return list(RELEASE_DOMAINS)


def get_domain_status(domain: str, summary: dict[str, Any] | None = None, app: Any | None = None, root: Path | None = None) -> dict[str, Any]:
    domain_name = str(domain or "").strip().lower()
    if summary is None:
        summary = validate_release(app=app, root=root)
    domain_map = {item["domain"]: item["status"] for item in _build_domain_statuses(summary)}
    return {"domain": domain_name, "status": domain_map.get(domain_name, "fail")}


def validate_functional(app: Any | None = None, root: Path | None = None) -> dict[str, Any]:
    services = getattr(getattr(app, "state", None), "services", {}) if app is not None else {}
    service_names = set(services.keys()) if isinstance(services, dict) else set()
    if services.get("configuration") is None:
        ConfigManager()
    modules = [
        _module_status("authentication", "auth" in service_names, "Authentication service available."),
        _module_status("rbac", "rbac" in service_names, "RBAC service available."),
        _module_status("organizations", "organizations" in service_names, "Organizations service available."),
        _module_status("teams", "teams" in service_names, "Teams service available."),
        _module_status("brands", "brands" in service_names, "Brand service available."),
        _module_status("workflows", "workflow" in service_names or "workflows" in service_names, "Workflow service available."),
        _module_status("reports", "reporting" in service_names or "markdown_report" in service_names, "Reporting service available."),
        _module_status("analytics", "analytics" in service_names, "Analytics service available."),
        _module_status("storage", "storage" in service_names, "Storage service available."),
        _module_status("configuration", True, "Configuration service available."),
        _module_status("api", app is not None, "API application importable."),
        _module_status("frontend", Path(_root(root) / "frontend" / "dist").exists(), "Frontend production build present."),
    ]
    return {"functional_ready": all(item["status"] == "pass" for item in modules), "modules": modules, "warnings": [], "errors": []}


def validate_technical(root: Path | None = None) -> dict[str, Any]:
    from scripts.ci_pipeline_health import build_pipeline_health

    result = build_pipeline_health(_root(root))
    return {
        "technical_ready": bool(result.get("release_ready", False)),
        "pipeline_health": result,
        "warnings": result.get("warnings", []),
        "errors": [],
    }


def validate_security(root: Path | None = None, app: Any | None = None) -> dict[str, Any]:
    from scripts.ci_security_check import scan_repository

    security_health = build_security_health(app)
    baseline = build_security_baseline(app)
    scan = scan_repository(_root(root))
    return {
        "security_ready": bool(scan.get("security_ready", False) and baseline.get("baseline_ready", False)),
        "security_score": int(scan.get("security_score", 0)),
        "baseline_ready": bool(baseline.get("baseline_ready", False)),
        "baseline_score": int(baseline.get("baseline_score", 0)),
        "scan": scan,
        "health": security_health,
        "warnings": list(scan.get("warnings", [])) + list(baseline.get("warnings", [])) + list(security_health.get("warnings", [])),
        "errors": list(scan.get("errors", [])) + list(baseline.get("errors", [])) + list(security_health.get("errors", [])),
    }


def validate_deployment(root: Path | None = None) -> dict[str, Any]:
    root = _root(root)
    required = ["Dockerfile", "docker-compose.yml", ".env.example", "deployment/README.md"]
    missing = [rel for rel in required if not (root / rel).exists()]
    return {"deployment_ready": not missing, "missing": missing, "warnings": [], "errors": [f"Missing {item}" for item in missing]}


def validate_observability(app: Any | None = None) -> dict[str, Any]:
    health = build_observability_health(app)
    ready = health.get("health_status") in {"healthy", "warning"} and bool(health.get("health_score", 0) >= 60)
    return {"observability_ready": ready, "health": health, "warnings": health.get("warnings", []), "errors": health.get("errors", [])}


def validate_ci(root: Path | None = None) -> dict[str, Any]:
    from scripts.ci_pipeline_health import build_pipeline_health
    from scripts.ci_quality_gates import evaluate_quality_gates

    pipeline = build_pipeline_health(_root(root))
    gates = evaluate_quality_gates(_root(root))
    ready = bool(pipeline.get("release_ready", False) and gates.get("quality_gate_status") == "passed")
    return {"ci_ready": ready, "pipeline_health": pipeline, "quality_gates": gates, "warnings": gates.get("warnings", []), "errors": gates.get("errors", [])}


def validate_documentation(root: Path | None = None) -> dict[str, Any]:
    root = _root(root)
    required_docs = [
        "README.md",
        "deployment/README.md",
        "docs/CI_CD.md",
        "docs/MVP_ACCEPTANCE.md",
        "docs/RELEASE_NOTES.md",
        "docs/DEPLOYMENT_GUIDE.md",
        "docs/MVP_EXECUTIVE_SUMMARY.md",
        "docs/RELEASE_ARTIFACTS.md",
    ]
    warnings: list[str] = []
    errors: list[str] = []
    missing = [rel for rel in required_docs if not (root / rel).exists()]
    if missing:
        errors.append(f"Missing required release documentation: {', '.join(missing)}.")
    return {
        "documentation_ready": not errors,
        "documentation": {"required_docs": required_docs, "missing": missing},
        "warnings": warnings,
        "errors": errors,
    }


def validate_release(app: Any | None = None, root: Path | None = None) -> dict[str, Any]:
    root = _root(root)
    functional = validate_functional(app, root)
    technical = validate_technical(root)
    security = validate_security(root, app)
    deployment = validate_deployment(root)
    observability = validate_observability(app)
    ci = validate_ci(root)
    documentation = validate_documentation(root)
    release_ready = bool(
        functional.get("functional_ready")
        and technical.get("technical_ready")
        and security.get("security_ready")
        and deployment.get("deployment_ready")
        and observability.get("observability_ready")
        and ci.get("ci_ready")
        and documentation.get("documentation_ready")
        and not (
            functional.get("errors")
            or technical.get("errors")
            or security.get("errors")
            or deployment.get("errors")
            or observability.get("errors")
            or ci.get("errors")
            or documentation.get("errors")
        )
    )
    sections = {
        "functional_ready": bool(functional.get("functional_ready", False)),
        "technical_ready": bool(technical.get("technical_ready", False)),
        "security_ready": bool(security.get("security_ready", False)),
        "deployment_ready": bool(deployment.get("deployment_ready", False)),
        "observability_ready": bool(observability.get("observability_ready", False)),
        "ci_ready": bool(ci.get("ci_ready", False)),
        "documentation_ready": bool(documentation.get("documentation_ready", False)),
        "functional": functional,
        "technical": technical,
        "security": security,
        "deployment": deployment,
        "observability": observability,
        "ci": ci,
        "documentation": documentation,
    }
    domains = _build_domain_statuses(sections)
    return {
        "release_ready": release_ready,
        "functional_ready": sections["functional_ready"],
        "technical_ready": sections["technical_ready"],
        "security_ready": sections["security_ready"],
        "deployment_ready": sections["deployment_ready"],
        "observability_ready": sections["observability_ready"],
        "ci_ready": sections["ci_ready"],
        "documentation_ready": sections["documentation_ready"],
        "mvp_ready": bool(release_ready and security.get("security_ready", False) and deployment.get("deployment_ready", False)),
        "functional": functional,
        "technical": technical,
        "security": security,
        "deployment": deployment,
        "observability": observability,
        "ci": ci,
        "documentation": documentation,
        "domains": domains,
        "readiness_domains": domains,
        "warnings": list(functional.get("warnings", [])) + list(technical.get("warnings", [])) + list(security.get("warnings", [])) + list(deployment.get("warnings", [])) + list(observability.get("warnings", [])) + list(ci.get("warnings", [])) + list(documentation.get("warnings", [])),
        "errors": list(functional.get("errors", [])) + list(technical.get("errors", [])) + list(security.get("errors", [])) + list(deployment.get("errors", [])) + list(observability.get("errors", [])) + list(ci.get("errors", [])) + list(documentation.get("errors", [])),
    }
