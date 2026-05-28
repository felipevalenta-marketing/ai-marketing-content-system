"""Tests for response parsing and normalization."""

from __future__ import annotations

from src.llm.response_parser import ResponseParser


def test_text_response_parses_correctly():
    parser = ResponseParser()
    result = parser.parse_text_response({
        "content": "Hook: Discover Mallorca\nCaption: Calm living with style.\nCTA: Request a viewing\n#Mallorca #RealEstate",
        "raw_response": {"content": "Hook: Discover Mallorca"},
    })

    assert result["content"]
    assert result["raw_content"]
    assert result["parser_warnings"] is not None


def test_hashtags_are_extracted():
    parser = ResponseParser()
    hashtags = parser.extract_hashtags("Hello #Mallorca and #RealEstate")

    assert hashtags == ["#mallorca", "#realestate"]


def test_cta_is_extracted_when_present():
    parser = ResponseParser()
    cta = parser.extract_cta("CTA: Request a viewing")

    assert cta == "Request a viewing"


def test_json_like_output_is_parsed_safely():
    parser = ResponseParser()
    parsed = parser.try_parse_json('{"title": "Property", "cta": "Request a viewing"}')

    assert parsed == {"title": "Property", "cta": "Request a viewing"}


def test_malformed_json_returns_warning_instead_of_crash():
    parser = ResponseParser()
    result = parser.parse_text_response({"content": "```json\n{not valid json}\n```", "raw_response": {"content": "```json\n{not valid json}\n```"}})

    assert "parser_warnings" in result
    assert result["parser_warnings"]


def test_empty_response_returns_structured_warning():
    parser = ResponseParser()
    result = parser.parse_text_response({"content": "", "raw_response": {"content": ""}})

    assert result["content"] == ""
    assert result["parser_warnings"]
