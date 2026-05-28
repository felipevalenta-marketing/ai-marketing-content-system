"""Tests for campaign composition."""

from __future__ import annotations

from src.campaigns.campaign_composer import CampaignComposer


def test_property_launch_campaign_composes_successfully(sample_campaign_request):
    composer = CampaignComposer()
    result = composer.compose(sample_campaign_request, assets={})

    assert result["success"] is True
    assert result["campaign_type"] == "property_launch"
    assert result["strategy"]


def test_relocation_campaign_composes_successfully(sample_campaign_request):
    composer = CampaignComposer()
    request = dict(sample_campaign_request)
    request["campaign_type"] = "relocation_campaign"
    result = composer.compose(request, assets={})

    assert result["campaign_type"] == "relocation_campaign"
    assert result["content_sequence"]


def test_neighborhood_spotlight_composes_successfully(sample_campaign_request):
    composer = CampaignComposer()
    request = dict(sample_campaign_request)
    request["campaign_type"] = "neighborhood_spotlight"
    result = composer.compose(request, assets={})

    assert result["campaign_type"] == "neighborhood_spotlight"
    assert result["platform_plan"]


def test_unsupported_campaign_type_fails_gracefully(sample_campaign_request):
    composer = CampaignComposer()
    request = dict(sample_campaign_request)
    request["campaign_type"] = "unsupported_campaign_type"
    result = composer.compose(request, assets={})

    assert result["success"] is False
    assert result["errors"]


def test_campaign_asset_plan_is_created(sample_campaign_request):
    composer = CampaignComposer()
    result = composer.build_asset_plan(sample_campaign_request)

    assert result["required_assets"]
    assert result["platform_plan"]


def test_platform_plan_is_created(sample_campaign_request):
    composer = CampaignComposer()
    result = composer.build_platform_plan(sample_campaign_request)

    assert result


def test_content_sequence_is_created(sample_campaign_request):
    composer = CampaignComposer()
    sequence = composer.build_content_sequence(sample_campaign_request)

    assert sequence


def test_governance_summary_is_included(sample_campaign_request):
    composer = CampaignComposer()
    result = composer.compose(sample_campaign_request, assets={})

    assert result["governance_summary"]


def test_campaign_export_is_disabled_by_default(sample_campaign_request):
    composer = CampaignComposer()
    result = composer.compose(sample_campaign_request, assets={})

    assert result["export_paths"] == {}
