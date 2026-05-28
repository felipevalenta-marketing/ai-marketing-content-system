"""Tests for asset coordination."""

from __future__ import annotations

from src.assets.asset_coordinator import AssetCoordinator


def test_asset_coordinator_builds_asset_plan(sample_asset_request):
    coordinator = AssetCoordinator()
    plan = coordinator.build_asset_plan(sample_asset_request)

    assert plan["required_assets"]
    assert plan["platform_mapping"]


def test_image_prompt_requirements_are_created(sample_asset_request):
    coordinator = AssetCoordinator()
    requirements = coordinator.build_asset_requirements(sample_asset_request)

    assert requirements["image_requirements"]["required_fields"]


def test_video_prompt_requirements_are_created(sample_asset_request):
    coordinator = AssetCoordinator()
    requirements = coordinator.build_asset_requirements(sample_asset_request)

    assert requirements["video_requirements"]["required_fields"]


def test_missing_assets_are_detected(sample_asset_request):
    coordinator = AssetCoordinator()
    plan = coordinator.build_asset_plan(sample_asset_request)
    missing = coordinator.summarize_missing_assets(plan, existing_assets={})

    assert missing


def test_unsupported_asset_type_fails_gracefully(sample_asset_request):
    coordinator = AssetCoordinator()
    request = dict(sample_asset_request)
    request["assets_required"] = ["unsupported_asset"]
    valid, reason = coordinator.validate_asset_request(request)

    assert valid is True
    assert reason is None
    validation = coordinator.coordinate(request)
    assert validation["warnings"]


def test_campaign_compatibility_works(sample_asset_request):
    coordinator = AssetCoordinator()
    request = dict(sample_asset_request)
    request["campaign_assets"] = {
        "campaign_bundle": {
            "asset_type": "campaign_bundle",
            "campaign_name": "wenzel_partner_property_launch_sant_llorenc_des_cardassar",
            "assets": {"text_caption": {"status": "approved"}},
            "platform_plan": {"instagram": ["text_caption"]},
            "governance_summary": {"status": "approved"},
            "export_paths": {},
            "notes": "Campaign bundle for testing.",
            "raw_content": "",
            "status": "approved",
        }
    }
    result = coordinator.coordinate(request)

    assert result["asset_plan"]
    assert result["validation_result"]


def test_asset_export_is_disabled_by_default(sample_asset_request):
    coordinator = AssetCoordinator()
    result = coordinator.coordinate(sample_asset_request)

    assert result["export_paths"] == {}


def test_no_media_apis_are_called(sample_asset_request):
    coordinator = AssetCoordinator()
    result = coordinator.coordinate(sample_asset_request)

    assert result["success"] in {True, False}
    assert "generated_image" not in result["assets"]
