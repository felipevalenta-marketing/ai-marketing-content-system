"""Tests for the OpenAI integration client."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import src.llm.openai_client as openai_client_module
from src.llm.openai_client import MAX_OPENAI_METADATA_KEYS, OpenAIClient, OpenAIClientConfig


class DummyResponses:
    def __init__(self, response=None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc is not None:
            raise self.exc
        return self.response


class DummyOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        self.responses = DummyResponses(SimpleNamespace(output_text="Hello from Responses API", model_dump=lambda: {"ok": True}))


def test_client_initializes_without_api_key(monkeypatch):
    monkeypatch.setattr(openai_client_module, "OpenAI", DummyOpenAI)
    client = OpenAIClient(config=OpenAIClientConfig(api_key=None, default_model="gpt-4o-mini", default_temperature=0.7, default_max_output_tokens=1200, timeout_seconds=60, app_env="test"))

    assert client.validate_configuration() is False


def test_missing_api_key_returns_structured_failure(monkeypatch):
    monkeypatch.setattr(openai_client_module, "OpenAI", DummyOpenAI)
    client = OpenAIClient(config=OpenAIClientConfig(api_key=None, default_model="gpt-4o-mini", default_temperature=0.7, default_max_output_tokens=1200, timeout_seconds=60, app_env="test"))
    result = client.generate_text({"system_prompt": "sys", "user_prompt": "user", "content_type": "instagram_post", "brand": "brand", "metadata": {}})

    assert not result["success"]
    assert result["provider"] == "openai"
    assert result["content"] == ""
    assert result["raw_response"] is None
    assert "OPENAI_API_KEY" in result["error"]


def test_generate_text_returns_structured_success_when_mocked(monkeypatch):
    monkeypatch.setattr(openai_client_module, "OpenAI", DummyOpenAI)
    client = OpenAIClient(config=OpenAIClientConfig(api_key="test-key", default_model="gpt-4o-mini", default_temperature=0.7, default_max_output_tokens=1200, timeout_seconds=60, app_env="test"))
    client.validate_configuration = lambda: True  # type: ignore[assignment]
    dummy_response = SimpleNamespace(output_text="Generated content", model_dump=lambda: {"ok": True})
    client._client = SimpleNamespace(responses=DummyResponses(dummy_response))  # type: ignore[assignment]

    result = client.generate_text({
        "system_prompt": "sys",
        "user_prompt": "user",
        "content_type": "instagram_post",
        "brand": "brand",
        "metadata": {"brand": "brand", "platform": "instagram", "content_type": "instagram_post"},
    })

    assert result["success"] is True
    assert result["content"] == "Generated content"
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-4o-mini"
    assert result["token_usage"]["source"] in {"provider_usage", "estimator"}


def test_generate_text_returns_token_usage_when_mocked(monkeypatch):
    monkeypatch.setattr(openai_client_module, "OpenAI", DummyOpenAI)
    client = OpenAIClient(config=OpenAIClientConfig(api_key="test-key", default_model="gpt-4o-mini", default_temperature=0.7, default_max_output_tokens=1200, timeout_seconds=60, app_env="test"))
    client.validate_configuration = lambda: True  # type: ignore[assignment]
    dummy_response = SimpleNamespace(
        output_text="Generated content",
        usage=SimpleNamespace(input_tokens=12, output_tokens=8, total_tokens=20, model_dump=lambda: {"input_tokens": 12, "output_tokens": 8, "total_tokens": 20}),
        model_dump=lambda: {"ok": True},
    )
    client._client = SimpleNamespace(responses=DummyResponses(dummy_response))  # type: ignore[assignment]

    result = client.generate_text({
        "system_prompt": "sys",
        "user_prompt": "user",
        "content_type": "instagram_post",
        "brand": "brand",
        "metadata": {"brand": "brand", "platform": "instagram", "content_type": "instagram_post"},
    })

    assert result["token_usage"]["provider"] == "openai"
    assert result["token_usage"]["input_tokens"] == 12
    assert result["token_usage"]["output_tokens"] == 8
    assert result["token_usage"]["total_tokens"] == 20


def test_generate_text_returns_structured_failure_on_mocked_error(monkeypatch, caplog):
    secret = "super-secret-key"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setattr(openai_client_module, "OpenAI", DummyOpenAI)
    client = OpenAIClient(config=OpenAIClientConfig(api_key=secret, default_model="gpt-4o-mini", default_temperature=0.7, default_max_output_tokens=1200, timeout_seconds=60, app_env="test"))
    client.validate_configuration = lambda: True  # type: ignore[assignment]
    client._client = SimpleNamespace(responses=DummyResponses(exc=RuntimeError(f"boom {secret}")))  # type: ignore[assignment]

    with caplog.at_level("ERROR"):
        result = client.generate_text({"system_prompt": "sys", "user_prompt": "user", "content_type": "instagram_post", "brand": "brand", "metadata": {}})

    assert not result["success"]
    assert secret not in result["error"]
    assert secret not in caplog.text


def test_metadata_is_sanitized_to_max_16_keys(monkeypatch):
    monkeypatch.setattr(openai_client_module, "OpenAI", DummyOpenAI)
    client = OpenAIClient(config=OpenAIClientConfig(api_key="test-key", default_model="gpt-4o-mini", default_temperature=0.7, default_max_output_tokens=1200, timeout_seconds=60, app_env="test"))
    metadata = {f"key_{index}": {"nested": index} for index in range(24)}
    metadata.update({
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "property_description",
        "objective": "generate_leads",
        "model": "gpt-4o-mini",
        "provider": "openai",
        "request_id": "req-1",
        "generation_mode": "batch",
        "template_version": "v1",
        "route": "default",
        "pipeline_stage": "generation",
        "user_locale": "en-US",
        "target_audience": "relocation_clients",
        "campaign_type": "property_launch",
        "asset_type": "property_description",
        "timestamp": "2026-05-28T12:00:00Z",
        "long_value": "x" * 500,
    })

    sanitized = client._sanitize_metadata(metadata)

    assert len(sanitized) <= MAX_OPENAI_METADATA_KEYS
    for field in ("brand", "platform", "content_type", "objective", "model", "provider", "request_id", "generation_mode", "template_version", "route", "pipeline_stage", "user_locale", "target_audience", "campaign_type", "asset_type", "timestamp"):
        assert field in sanitized
    assert "long_value" not in sanitized
    assert all(not isinstance(value, dict) for value in sanitized.values())
