from __future__ import annotations

from src.security.input_sanitizer import sanitize_input, sanitize_request_params, validate_input


def test_input_sanitizer_rejects_script_payloads() -> None:
    result = sanitize_input({"bio": "<script>alert('xss')</script>"})
    assert result["errors"]
    assert "<script" not in str(result["value"]).lower()


def test_request_param_sanitizer_keeps_safe_values() -> None:
    result = sanitize_request_params({"q": "premium property marketing"})
    assert result["errors"] == []
    assert result["value"]["q"] == "premium property marketing"
    assert validate_input("calm mediterranean copy")["valid"] is True

