from __future__ import annotations

from scripts import ci_quality_gates


def test_quality_gates_report_passed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(ci_quality_gates, "_run_command", lambda args, cwd=None: {"passed": True, "returncode": 0, "stdout": "", "stderr": ""})
    monkeypatch.setattr(ci_quality_gates, "check_docker", lambda root: {"success": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_quality_gates, "scan_repository", lambda root: {"success": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_quality_gates, "check_documentation", lambda root: {"documentation_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_quality_gates, "check_structure", lambda root: {"structure_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_quality_gates, "check_dependencies", lambda root: {"dependencies_valid": True, "warnings": [], "errors": []})

    result = ci_quality_gates.evaluate_quality_gates(tmp_path)

    assert result["quality_gate_status"] == "passed"
    assert result["checks_passed"] == 7
    assert result["checks_failed"] == 0
    assert all(gate["passed"] for gate in result["gates"].values())
