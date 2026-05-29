"""Tests for the workflow engine."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from src.cli.cli_app import build_parser
from src.pipeline.pipeline_config import PipelineConfig
from src.workflows.workflow_engine import WorkflowEngine


def test_workflow_engine_creates_dry_run_result(sample_workflow_request):
    engine = WorkflowEngine(config=PipelineConfig(enable_persistence=False), pipeline=SimpleNamespace())
    request = dict(sample_workflow_request)
    request["dry_run"] = True

    result = engine.create_workflow(request)

    assert result["status"] == "dry_run"
    assert result["workflow_id"]
    assert result["workflow_type"] == "full_campaign_package"


def test_workflow_engine_persistence_uses_tmp_path(sample_workflow_request, tmp_path: Path):
    engine = WorkflowEngine(
        config=PipelineConfig(enable_persistence=True, workflow_persistence_enabled=True, storage_root=str(tmp_path), persist_markdown=False),
        pipeline=SimpleNamespace(),
    )
    state = {
        "workflow_id": "wf-persist-1",
        "workflow_type": "single_content_generation",
        "step_outputs": {"step_01_load_context": {"context": {"loaded": True}}},
        "step_statuses": {"step_01_load_context": "completed"},
        "warnings": [],
        "errors": [],
    }
    request = dict(sample_workflow_request)
    request["dry_run"] = False

    persistence = engine._persist_workflow(state, request)

    assert persistence["success"] is True
    assert persistence["summary"]["records_saved"] >= 1
    assert Path(persistence["storage_paths"]["workflow"]).exists()
    assert Path(persistence["storage_paths"]["workflow_state"]).exists()


def test_workflow_cli_parser_accepts_workflow_command():
    parser = build_parser()
    args = parser.parse_args([
        "workflow",
        "--workflow-type",
        "full_campaign_package",
        "--brand",
        "wenzel_partner",
        "--platform",
        "instagram",
        "--content-type",
        "instagram_post",
        "--dry-run",
    ])

    assert args.command == "workflow"
    assert args.workflow_type == "full_campaign_package"


def test_generate_command_accepts_workflow_flag():
    parser = build_parser()
    args = parser.parse_args([
        "generate",
        "--workflow",
        "--brand",
        "wenzel_partner",
        "--platform",
        "instagram",
        "--content-type",
        "instagram_post",
    ])

    assert args.workflow is True
