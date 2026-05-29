from __future__ import annotations

import json
from pathlib import Path


def _contains_any(text: str, fragments: list[str]) -> bool:
    lowered = text.lower()
    return all(fragment.lower() in lowered for fragment in fragments)


def check_docker(root: Path | None = None) -> dict[str, object]:
    root = root or Path(__file__).resolve().parents[1]
    dockerfile = root / "Dockerfile"
    compose_file = root / "docker-compose.yml"
    dockerignore = root / ".dockerignore"
    warnings: list[str] = []
    errors: list[str] = []

    if not dockerfile.exists():
        errors.append("Dockerfile is missing.")
    if not compose_file.exists():
        errors.append("docker-compose.yml is missing.")
    if not dockerignore.exists():
        errors.append(".dockerignore is missing.")

    if dockerfile.exists():
        dockerfile_text = dockerfile.read_text(encoding="utf-8", errors="ignore")
        if "uvicorn src.api.main:app" not in dockerfile_text and "src.api.main:app" not in dockerfile_text:
            errors.append("Dockerfile does not run the FastAPI app with uvicorn.")
        if ".env" in dockerfile_text:
            errors.append("Dockerfile appears to reference .env.")

    if compose_file.exists():
        compose_text = compose_file.read_text(encoding="utf-8", errors="ignore")
        if not _contains_any(compose_text, ["healthcheck", "/health"]):
            warnings.append("docker-compose.yml does not declare an API healthcheck.")
        if "data:/app/data" not in compose_text and "data:/app/data" not in compose_text.replace(" ", ""):
            warnings.append("docker-compose.yml does not mount the data volume.")

    if dockerignore.exists():
        dockerignore_text = dockerignore.read_text(encoding="utf-8", errors="ignore")
        required_excludes = [".env", "data/", "outputs/", "frontend/node_modules/", "frontend/dist/", "__pycache__/", ".pytest_cache/"]
        missing = [entry for entry in required_excludes if entry not in dockerignore_text]
        if missing:
            warnings.append(f".dockerignore is missing excludes: {', '.join(missing)}.")

    return {
        "success": not errors,
        "dockerfile_present": dockerfile.exists(),
        "compose_present": compose_file.exists(),
        "dockerignore_present": dockerignore.exists(),
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    result = check_docker()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
