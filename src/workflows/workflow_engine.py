"""System-level workflow orchestration engine."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from src.assets.asset_coordinator import AssetCoordinator
from src.campaigns.campaign_composer import CampaignComposer
from src.brands.brand_manager import BrandManager
from src.creative.creative_direction_engine import CreativeDirectionEngine
from src.governance.content_governance import ContentGovernanceEngine
from src.llm.openai_client import OpenAIClient
from src.media.image_prompt_engine import ImagePromptEngine
from src.media.image_prompt_validator import ImagePromptValidator
from src.media.video_script_engine import VideoScriptEngine
from src.media.video_script_validator import VideoScriptValidator
from src.output.output_formatter import OutputFormatter
from src.output.output_validator import OutputValidator
from src.pipeline.pipeline_config import PipelineConfig
from src.reporting.reporting_engine import ReportingEngine
from src.storage.storage_manager import StorageManager
from src.tracking.cost_tracker import CostTracker
from src.tracking.token_tracker import TokenTracker
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context, log_warning
from src.workflows.workflow_plan import build_workflow_plan
from src.workflows.workflow_registry import get_workflow_template, is_supported_workflow_type, list_workflow_templates
from src.workflows.workflow_result import build_failure_result, build_success_result, build_validation_failure_result, normalize_workflow_status
from src.workflows.workflow_runner import WorkflowRunner
from src.workflows.workflow_state import serialize_state
from src.workflows.workflow_validator import validate_workflow_plan
from src.reporting.report_metrics import safe_text


class WorkflowEngine:
    """Coordinate structured multi-step workflows using existing services."""

    def __init__(
        self,
        config: PipelineConfig | None = None,
        pipeline: Any | None = None,
        storage_manager: StorageManager | None = None,
        reporting_engine: ReportingEngine | None = None,
        logger: Any | None = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.logger = logger or get_logger(self.__class__.__name__)
        self.brand_manager = BrandManager(
            brand_root=self.config.brand_root,
            default_brand=self.config.default_brand,
            require_valid_brand=self.config.require_valid_brand,
            logger=self.logger,
        )
        self.pipeline = pipeline or self._build_pipeline()
        self.reporting_engine = reporting_engine or getattr(
            self.pipeline,
            "reporting_engine",
            ReportingEngine(output_root=self.config.report_output_root, markdown_output_root=self.config.markdown_report_output_root, logger=self.logger),
        )
        self.storage_manager = storage_manager or getattr(self.pipeline, "storage_manager", None) or StorageManager(storage_root=self.config.storage_root, logger=self.logger)
        self.token_tracker = getattr(self.pipeline, "token_tracker", TokenTracker(logger=self.logger))
        self.cost_tracker = getattr(self.pipeline, "cost_tracker", CostTracker(logger=self.logger))
        self.output_formatter = getattr(self.pipeline, "output_formatter", OutputFormatter(logger=self.logger))
        self.output_validator = getattr(self.pipeline, "output_validator", OutputValidator(logger=self.logger))
        self.openai_client = getattr(self.pipeline, "client", OpenAIClient(logger=self.logger))
        self.governance_engine = getattr(self.pipeline, "governance_engine", ContentGovernanceEngine(logger=self.logger))
        self.campaign_composer = getattr(self.pipeline, "campaign_composer", CampaignComposer(logger=self.logger))
        self.asset_coordinator = getattr(self.pipeline, "asset_coordinator", AssetCoordinator(output_root=self.config.asset_output_root, logger=self.logger))
        self.image_prompt_engine = getattr(self.pipeline, "image_prompt_engine", ImagePromptEngine(logger=self.logger))
        self.image_prompt_validator = getattr(self.pipeline, "image_prompt_validator", ImagePromptValidator())
        self.video_script_engine = getattr(self.pipeline, "video_script_engine", VideoScriptEngine(logger=self.logger))
        self.video_script_validator = getattr(self.pipeline, "video_script_validator", VideoScriptValidator())
        self.creative_direction_engine = getattr(self.pipeline, "creative_direction_engine", CreativeDirectionEngine(logger=self.logger))
        self.workflow_runner = WorkflowRunner(self)
        self._started_at: str | None = None

    def _build_pipeline(self) -> Any:
        from src.pipeline.content_generation_pipeline import ContentGenerationPipeline

        return ContentGenerationPipeline(config=self.config, logger=self.logger)

    def create_workflow(self, request: dict[str, Any]) -> dict[str, Any]:
        brand_resolution = self._resolve_brand_context(request)
        if not brand_resolution.get("success", False):
            return build_validation_failure_result(
                errors=list(brand_resolution.get("errors", [])),
                warnings=list(brand_resolution.get("warnings", [])),
                workflow_id="",
                workflow_type=safe_text(request.get("workflow_type"), limit=80),
                metadata={"brand_resolution": brand_resolution},
            )
        plan = self.plan_workflow(request)
        validation = self.validate_workflow(plan)
        if not validation["valid"]:
            return build_validation_failure_result(
                errors=validation.get("errors", []),
                warnings=validation.get("warnings", []),
                workflow_id=plan.get("workflow_id", ""),
                workflow_type=plan.get("workflow_type", ""),
                metadata={"plan": plan, "validation": validation},
            )
        if bool(request.get("dry_run")):
            return self.run_workflow(plan, request)
        return self.run_workflow(plan, request)

    def plan_workflow(self, request: dict[str, Any]) -> dict[str, Any]:
        workflow_type = normalize_key(str(request.get("workflow_type") or self.config.default_workflow_type))
        plan = build_workflow_plan({**request, "workflow_type": workflow_type}, default_workflow_type=self.config.default_workflow_type)
        plan.setdefault("metadata", {})
        plan["metadata"].update({"supported_workflow_types": list_workflow_templates()})
        return plan

    def validate_workflow(self, plan: dict[str, Any]) -> dict[str, Any]:
        return validate_workflow_plan(plan)

    def run_workflow(self, plan: dict[str, Any], request: dict[str, Any] | None = None) -> dict[str, Any]:
        request_payload = dict(request or plan.get("metadata", {}).get("request", {}) or {})
        request_payload.setdefault("workflow_type", plan.get("workflow_type", ""))
        brand_resolution = self._resolve_brand_context(request_payload)
        request_payload.update(
            {
                "brand": brand_resolution.get("brand_id") or request_payload.get("brand", ""),
                "brand_id": brand_resolution.get("brand_id") or request_payload.get("brand", ""),
                "brand_profile": brand_resolution.get("brand_profile", {}),
                "brand_validation": brand_resolution.get("brand_validation", {}),
                "brand_defaults": brand_resolution.get("defaults", {}),
            }
        )
        request_payload.setdefault("dry_run", bool(request_payload.get("dry_run")))
        if not brand_resolution.get("success", False):
            return build_validation_failure_result(
                errors=list(brand_resolution.get("errors", [])),
                warnings=list(brand_resolution.get("warnings", [])),
                workflow_id=plan.get("workflow_id", ""),
                workflow_type=plan.get("workflow_type", ""),
                metadata={"brand_resolution": brand_resolution, "plan": plan},
            )
        if bool(request_payload.get("dry_run")):
            return self.build_result(
                workflow_id=plan.get("workflow_id", ""),
                workflow_type=plan.get("workflow_type", ""),
                status="dry_run",
                steps=[{"step_id": step.get("step_id", ""), "step_type": step.get("step_type", ""), "status": "planned"} for step in plan.get("steps", [])],
                summary={"mode": "dry_run", "planned_steps": len(plan.get("steps", []))},
                results={},
                token_summary={},
                cost_summary={},
                report_summary={},
                storage_summary={},
                warnings=list(plan.get("warnings", [])),
                errors=list(plan.get("errors", [])),
                metadata={"plan": plan, "request": request_payload},
                brand_id=request_payload.get("brand_id", ""),
                brand_profile=request_payload.get("brand_profile", {}),
                brand_validation=request_payload.get("brand_validation", {}),
            )
        self._started_at = datetime.now(timezone.utc).isoformat()
        return self.workflow_runner.run(plan, request_payload)

    def run_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        step_type = str(step.get("step_type", "")).strip()
        request = deepcopy(state.get("request", {}))
        content_type = normalize_key(str(request.get("content_type", "") or self.config.default_content_type))
        platforms = list(request.get("platforms") or ([request.get("platform")] if request.get("platform") else []))
        if step_type == "load_context":
            context = self.pipeline.load_context(str(request.get("brand", "")))
            return {"status": "completed", "context": context, "warnings": list(context.get("warnings", [])), "errors": list(context.get("errors", []))}
        if step_type == "build_prompt":
            context = self._get_step_output(state, "load_context") or {}
            prompt_payload = self.pipeline.build_prompt(request, context)
            return {"status": "completed", "prompt_payload": prompt_payload.get("prompt_payload"), "warnings": list(prompt_payload.get("warnings", [])), "errors": list(prompt_payload.get("errors", []))}
        if step_type == "generate_content":
            if bool(request.get("dry_run")):
                return {"status": "completed", "ai_response": {"success": True, "content": "", "provider": "", "model": "", "token_usage": {}}, "warnings": ["Dry run skipped content generation."], "errors": []}
            prompt_payload = self._get_step_output(state, "build_prompt") or self._get_step_output(state, "prompt_payload") or {}
            ai_response = self.pipeline.generate_ai_response(prompt_payload or {})
            return {"status": "completed", "ai_response": ai_response, "warnings": list(ai_response.get("warnings", [])), "errors": list(ai_response.get("errors", []))}
        if step_type == "parse_response":
            ai_response = self._get_step_output(state, "generate_content").get("ai_response") if isinstance(self._get_step_output(state, "generate_content"), dict) else self._get_step_output(state, "ai_response") or {}
            parsed_output = self.pipeline.parse_response(ai_response or {})
            return {"status": "completed", "parsed_output": parsed_output, "warnings": list(parsed_output.get("warnings", [])), "errors": list(parsed_output.get("errors", []))}
        if step_type == "format_output":
            parsed_output = self._get_step_output(state, "parse_response").get("parsed_output") if isinstance(self._get_step_output(state, "parse_response"), dict) else self._get_step_output(state, "parsed_output") or {}
            formatted_output = self.output_formatter.format(parsed_output or {}, content_type)
            validation = self.output_validator.validate(formatted_output, content_type)
            return {"status": "completed", "formatted_output": formatted_output, "validation_result": validation, "warnings": list(validation.get("warnings", [])), "errors": list(validation.get("errors", []))}
        if step_type == "adapt_platform":
            formatted_output = self._resolve_output(state, "format_output", "formatted_output")
            adapter = getattr(self.pipeline, "adapter", None)
            if adapter is None:
                from src.adapters.platform_adapter import PlatformAdapter

                adapter = PlatformAdapter(logger=self.logger)
            adaptation_result = adapter.adapt({"content_type": content_type, "formatted_output": formatted_output, "metadata": request}, platforms)
            return {"status": "completed", "adaptation_result": adaptation_result, "warnings": list(adaptation_result.get("warnings", [])), "errors": list(adaptation_result.get("errors", []))}
        if step_type == "run_governance":
            formatted_output = self._resolve_output(state, "format_output", "formatted_output")
            platform_variants = self._resolve_output(state, "adapt_platform", "adaptation_result") or {}
            governance_payload = {"brand": request.get("brand", ""), "platform": request.get("platform", ""), "content_type": content_type, "formatted_output": formatted_output, "platform_variants": platform_variants, "metadata": request}
            governance_result = self.governance_engine.evaluate(governance_payload)
            return {"status": "completed", "governance_result": governance_result, "warnings": list(governance_result.get("warnings", [])), "errors": list(governance_result.get("errors", []))}
        if step_type == "compose_campaign":
            campaign_assets = deepcopy(request.get("assets") or request.get("campaign_assets") or {})
            campaign_result = self.campaign_composer.compose(request, assets=campaign_assets)
            return {"status": "completed", "campaign_result": campaign_result, "campaign_strategy": campaign_result.get("strategy"), "campaign_assets": campaign_result.get("assets", {}), "warnings": list(campaign_result.get("warnings", [])), "errors": list(campaign_result.get("errors", []))}
        if step_type == "coordinate_assets":
            asset_request = {**request, "campaign_result": self._get_step_output(state, "compose_campaign").get("campaign_result") if isinstance(self._get_step_output(state, "compose_campaign"), dict) else self._get_step_output(state, "campaign_result")}
            asset_result = self.asset_coordinator.coordinate(asset_request)
            return {"status": "completed", "asset_coordination_result": asset_result, "asset_plan": asset_result.get("asset_plan", {}), "asset_requirements": asset_result.get("asset_requirements", {}), "missing_assets": asset_result.get("missing_assets", []), "warnings": list(asset_result.get("warnings", [])), "errors": list(asset_result.get("errors", []))}
        if step_type == "generate_image_prompt":
            image_request = self._build_image_request(request, state)
            image_prompt_result = self.image_prompt_engine.generate_image_prompt(image_request)
            validation = self.image_prompt_validator.validate(image_prompt_result)
            return {"status": "completed", "image_prompt_result": image_prompt_result, "enhanced_image_prompt": image_prompt_result.get("prompt"), "negative_prompt": image_prompt_result.get("negative_prompt"), "visual_style": image_prompt_result.get("visual_style"), "cinematic_rules_applied": image_prompt_result.get("metadata", {}).get("cinematic_rules_applied", []), "image_prompt_validation": validation, "warnings": list(image_prompt_result.get("warnings", [])) + list(validation.get("warnings", [])), "errors": list(image_prompt_result.get("errors", [])) + list(validation.get("errors", []))}
        if step_type == "generate_video_script":
            video_request = self._build_video_request(request, state)
            video_script_result = self.video_script_engine.generate_video_script(video_request)
            validation = self.video_script_validator.validate(video_script_result)
            return {"status": "completed", "video_script_result": video_script_result, "video_type": video_script_result.get("video_type"), "video_duration": video_script_result.get("duration"), "scene_sequence": video_script_result.get("scene_sequence", []), "storyboard": video_script_result.get("storyboard", []), "voiceover": video_script_result.get("voiceover"), "camera_direction": video_script_result.get("camera_direction"), "music_mood": video_script_result.get("music_mood"), "video_script_validation": validation, "warnings": list(video_script_result.get("warnings", [])) + list(validation.get("warnings", [])), "errors": list(video_script_result.get("errors", [])) + list(validation.get("errors", []))}
        if step_type == "generate_creative_direction":
            creative_request = self._build_creative_request(request, state)
            creative_result = self.creative_direction_engine.generate_creative_direction(creative_request)
            validation = creative_result.get("validation", {})
            return {"status": "completed", "creative_direction_result": creative_result, "creative_direction_type": creative_result.get("creative_direction_type"), "visual_identity": creative_result.get("visual_identity"), "moodboard": creative_result.get("moodboard"), "color_palette": creative_result.get("color_palette"), "platform_creative_guidelines": creative_result.get("platform_guidelines"), "media_guidelines": creative_result.get("media_guidelines"), "creative_validation": validation, "warnings": list(creative_result.get("warnings", [])) + list(validation.get("warnings", [])) if isinstance(validation, dict) else list(creative_result.get("warnings", [])), "errors": list(creative_result.get("errors", [])) + list(validation.get("errors", [])) if isinstance(validation, dict) else list(creative_result.get("errors", []))}
        if step_type == "track_tokens":
            token_usage = self._build_token_usage(request, state)
            records = [token_usage] if token_usage else []
            execution_summary = self.token_tracker.aggregate_execution(records)
            module_summary = self.token_tracker.aggregator.aggregate_by_module(records)
            provider_summary = self.token_tracker.aggregator.aggregate_by_provider(records)
            result = {"status": "completed", "token_usage": token_usage, "execution_token_summary": execution_summary, "module_token_summary": module_summary, "provider_token_summary": provider_summary, "estimated_token_usage": token_usage if token_usage.get("estimated") else {}}
            return result
        if step_type == "track_costs":
            token_usage = self._resolve_output(state, "track_tokens", "token_usage")
            cost_usage = self.cost_tracker.track_cost(token_usage or {}, metadata={"workflow_id": state.get("workflow_id", ""), "workflow_type": state.get("workflow_type", "")})
            records = [cost_usage] if cost_usage else []
            execution_summary = self.cost_tracker.aggregate_execution_cost(records)
            module_summary = self.cost_tracker.aggregator.aggregate_by_module(records)
            provider_summary = self.cost_tracker.aggregator.aggregate_by_provider(records)
            model_summary = self.cost_tracker.aggregator.aggregate_by_model(records)
            return {"status": "completed", "cost_usage": cost_usage, "execution_cost_summary": execution_summary, "module_cost_summary": module_summary, "provider_cost_summary": provider_summary, "model_cost_summary": model_summary, "warnings": list(cost_usage.get("warnings", [])), "errors": list(cost_usage.get("errors", []))}
        if step_type == "build_report":
            reporting_payload = self._build_reporting_payload(state, request)
            report_bundle = self.reporting_engine.generate(
                reporting_payload,
                export=bool(request.get("report_export")),
                formats=["markdown", "json"],
                render_format="markdown" if request.get("report_markdown") or request.get("markdown") else "terminal",
                report_name=state.get("workflow_id", "workflow"),
                markdown=bool(request.get("markdown") or request.get("report_markdown") or request.get("report")),
                export_markdown=bool(request.get("export_markdown_report")),
                markdown_report_type=str(request.get("report_type") or self.config.default_markdown_report_type),
            )
            return {"status": "completed", "reporting": report_bundle, "execution_report": report_bundle.get("execution_report"), "governance_report": report_bundle.get("governance_report"), "campaign_report": report_bundle.get("campaign_report"), "asset_report": report_bundle.get("asset_report"), "export_report": report_bundle.get("export_report"), "consolidated_report": report_bundle.get("consolidated_report"), "report_export_paths": report_bundle.get("exported_files", {}), "rendered_markdown": report_bundle.get("rendered_markdown"), "rendered_text": report_bundle.get("rendered_text"), "warnings": list(report_bundle.get("warnings", [])), "errors": list(report_bundle.get("errors", []))}
        if step_type == "persist_results":
            persistence_result = self._persist_workflow(state, request)
            return {"status": "completed" if persistence_result.get("success") else "failed", "persistence_result": persistence_result, "storage_summary": persistence_result.get("summary", {}), "warnings": list(persistence_result.get("warnings", [])), "errors": list(persistence_result.get("errors", []))}
        if step_type == "approval_gate":
            governance_result = self._resolve_output(state, "run_governance", "governance_result")
            status = "requires_approval" if isinstance(governance_result, dict) and str(governance_result.get("status", "")).lower() in {"needs_review", "rejected"} else "completed"
            return {"status": status, "approval_status": status, "warnings": [], "errors": []}
        if step_type == "export_outputs":
            return {"status": "completed", "export_summary": {"exported": False, "reason": "Export is coordinated by existing export layers."}, "warnings": [], "errors": []}
        return {"status": "completed", "warnings": [], "errors": [], "metadata": {"noop": True}}

    def aggregate_results(self, step_results: list[dict[str, Any]]) -> dict[str, Any]:
        status = "completed"
        warnings: list[str] = []
        errors: list[str] = []
        completed_steps = 0
        failed_steps = 0
        skipped_steps = 0
        token_records: list[dict[str, Any]] = []
        cost_records: list[dict[str, Any]] = []
        report_summary = {}
        markdown_report = {}
        markdown_report_path = ""
        markdown_sections: list[dict[str, Any]] = []
        markdown_validation = {}
        rendered_markdown = ""
        rendered_text = ""
        storage_summary = {}
        for step_result in step_results:
            step_status = str(step_result.get("status", "")).lower()
            if step_status == "failed":
                failed_steps += 1
                status = "failed"
            elif step_status == "skipped":
                skipped_steps += 1
            else:
                completed_steps += 1
            warnings.extend(step_result.get("warnings", []))
            errors.extend(step_result.get("errors", []))
            raw_result = step_result.get("result") if isinstance(step_result.get("result"), dict) else {}
            if step_result.get("step_type") == "track_tokens":
                token_record = deepcopy(raw_result.get("token_usage") or raw_result.get("estimated_token_usage") or {})
                if token_record:
                    token_records.append(token_record)
            if step_result.get("step_type") == "track_costs":
                cost_record = deepcopy(raw_result.get("cost_usage") or {})
                if cost_record:
                    cost_records.append(cost_record)
            if step_result.get("step_type") == "build_report":
                report_summary = deepcopy(raw_result)
                markdown_report = deepcopy(raw_result.get("markdown_report") or {})
                markdown_report_path = safe_text(raw_result.get("markdown_report_path"), limit=260)
                markdown_sections = deepcopy(raw_result.get("markdown_sections") or [])
                markdown_validation = deepcopy(raw_result.get("markdown_validation") or {})
                rendered_markdown = safe_text(raw_result.get("rendered_markdown"), limit=100000)
                rendered_text = safe_text(raw_result.get("rendered_text"), limit=100000)
            if step_result.get("step_type") == "persist_results":
                storage_summary = deepcopy(raw_result)
                if isinstance(raw_result.get("markdown_report"), dict):
                    markdown_report = deepcopy(raw_result.get("markdown_report") or {})
                markdown_report_path = safe_text(raw_result.get("markdown_report_path") or markdown_report_path, limit=260)
        if warnings and status == "completed":
            status = "completed_with_warnings"
        if any(str(step.get("status", "")).lower() == "requires_approval" for step in step_results):
            status = "requires_approval"
        summary = {
            "step_count": len(step_results),
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "skipped_steps": skipped_steps,
            "duration_seconds": 0.0,
        }
        token_summary = self.token_tracker.get_total_usage(token_records) if hasattr(self, "token_tracker") else {}
        cost_summary = self.cost_tracker.get_total_cost(cost_records) if hasattr(self, "cost_tracker") else {}
        if token_records:
            token_summary["provider"] = token_records[0].get("provider", "")
            token_summary["model"] = token_records[0].get("model", "")
        if cost_records:
            cost_summary["provider"] = cost_records[0].get("provider", "")
            cost_summary["model"] = cost_records[0].get("model", "")
        return {
            "status": status,
            "summary": summary,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "token_summary": token_summary,
            "cost_summary": cost_summary,
            "report_summary": report_summary,
            "markdown_report": markdown_report,
            "markdown_report_path": markdown_report_path,
            "markdown_sections": markdown_sections,
            "markdown_validation": markdown_validation,
            "rendered_markdown": rendered_markdown,
            "rendered_text": rendered_text,
            "storage_summary": storage_summary,
        }

    def build_result(self, **kwargs: Any) -> dict[str, Any]:
        result = build_success_result(**kwargs)
        metadata = kwargs.get("metadata", {}) if isinstance(kwargs.get("metadata"), dict) else {}
        request = deepcopy(metadata.get("request", {})) if isinstance(metadata.get("request"), dict) else {}
        organization_id = safe_text(kwargs.get("organization_id") or metadata.get("organization_id") or request.get("organization_id"), limit=120)
        team_id = safe_text(kwargs.get("team_id") or metadata.get("team_id") or request.get("team_id"), limit=120)
        if organization_id:
            result["organization_id"] = organization_id
        if team_id:
            result["team_id"] = team_id
        status = normalize_workflow_status(result.get("status"))
        result["status"] = status
        result["success"] = status not in {"failed"}
        result["workflow_step_summary"] = deepcopy(result.get("summary", {}))
        result["workflow_storage_summary"] = deepcopy(result.get("storage_summary", {}))
        result["started_at"] = self._started_at or kwargs.get("started_at", "")
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        if result.get("started_at"):
            try:
                start = datetime.fromisoformat(str(result["started_at"]).replace("Z", "+00:00"))
                end = datetime.fromisoformat(str(result["completed_at"]).replace("Z", "+00:00"))
                result["duration_seconds"] = round((end - start).total_seconds(), 3)
            except Exception:
                result["duration_seconds"] = 0.0
        return result

    def _resolve_brand_context(self, request: dict[str, Any]) -> dict[str, Any]:
        brand_value = safe_text(request.get("brand") or self.config.default_brand, limit=120)
        return self.brand_manager.resolve_request_brand(brand_value)

    def _get_step_output(self, state: dict[str, Any], step_type: str) -> Any:
        for key, value in state.get("step_outputs", {}).items():
            if key.endswith(step_type):
                return value
        return {}

    def _resolve_output(self, state: dict[str, Any], step_type: str, key: str) -> Any:
        output = self._get_step_output(state, step_type)
        if isinstance(output, dict):
            return output.get(key, {})
        return {}

    def _build_reporting_payload(self, state: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        workflow_state = serialize_state(state)
        payload = {
            **deepcopy(request),
            **deepcopy(state.get("request", {})),
            **deepcopy(state.get("step_outputs", {})),
        }
        payload.setdefault("brand", request.get("brand", ""))
        payload.setdefault("platform", request.get("platform", ""))
        payload.setdefault("content_type", request.get("content_type", ""))
        payload.setdefault("organization_id", request.get("organization_id", ""))
        payload.setdefault("team_id", request.get("team_id", ""))
        payload.setdefault("workflow_id", state.get("workflow_id", ""))
        payload.setdefault("workflow_type", state.get("workflow_type", ""))
        payload.setdefault("workflow_status", state.get("step_statuses", {}).get("approval_gate", "completed"))
        payload.setdefault("metadata", {})
        payload["metadata"] = {
            **deepcopy(payload.get("metadata", {})),
            "workflow_id": state.get("workflow_id", ""),
            "workflow_type": state.get("workflow_type", ""),
            "workflow_status": state.get("step_statuses", {}).get("approval_gate", "completed"),
            "workflow": workflow_state,
        }
        payload["workflow_state"] = workflow_state
        payload["workflow_snapshot"] = deepcopy(workflow_state)
        payload["workflow_state_history"] = deepcopy(workflow_state.get("history", []))
        payload["workflow_timeline"] = deepcopy(workflow_state.get("timeline", []))
        payload["workflow_status_transitions"] = deepcopy(workflow_state.get("status_transitions", []))
        return payload

    def _persist_workflow(self, state: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        if not self.config.workflow_persistence_enabled or not self.config.enable_persistence or bool(request.get("dry_run")):
            return {"success": True, "enabled": False, "persistence_status": "disabled", "warnings": [], "errors": [], "summary": {"records_saved": 0, "storage_root": self.config.storage_root}, "stored_record_ids": [], "storage_paths": {}}
        workflow_result = {
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": request.get("content_type", ""),
            "campaign_type": request.get("campaign_type", ""),
            "workflow_id": state.get("workflow_id", ""),
            "workflow_type": state.get("workflow_type", ""),
            "workflow_status": state.get("step_statuses", {}).get("approval_gate", "completed"),
            "results": serialize_state(state),
            "metadata": {"workflow": serialize_state(state), "request": deepcopy(request)},
            "warnings": list(state.get("warnings", [])),
            "errors": list(state.get("errors", [])),
        }
        workflow_save = self.storage_manager.save_workflow(workflow_result, overwrite=self.config.storage_overwrite, write_markdown=self.config.persist_markdown)
        state_save = self.storage_manager.save_workflow_state({"workflow_id": state.get("workflow_id", ""), "workflow_type": state.get("workflow_type", ""), "state": serialize_state(state), "metadata": {"request": deepcopy(request)}}, overwrite=self.config.storage_overwrite, write_markdown=self.config.persist_markdown)
        report_save = self.storage_manager.save_report({
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": request.get("content_type", ""),
            "campaign_type": request.get("campaign_type", ""),
            "metadata": {"workflow_id": state.get("workflow_id", ""), "workflow_type": state.get("workflow_type", ""), "request": deepcopy(request)},
            "consolidated_report": self._safe_report_from_state(state),
        }, overwrite=self.config.storage_overwrite, write_markdown=self.config.persist_markdown)
        saved = [item for item in (workflow_save, state_save, report_save) if item.get("success")]
        paths = {
            "workflow": workflow_save.get("path", ""),
            "workflow_state": state_save.get("path", ""),
            "report": report_save.get("path", ""),
        }
        record_ids = [item.get("record_id", "") for item in saved if item.get("record_id")]
        warnings = list(workflow_save.get("warnings", [])) + list(state_save.get("warnings", [])) + list(report_save.get("warnings", []))
        errors = list(workflow_save.get("errors", [])) + list(state_save.get("errors", [])) + list(report_save.get("errors", []))
        report_markdown = {}
        if isinstance(state.get("step_outputs"), dict):
            build_report_output = state.get("step_outputs", {}).get("build_report", {})
            if isinstance(build_report_output, dict):
                reporting = build_report_output.get("reporting")
                if isinstance(reporting, dict):
                    report_markdown = dict(reporting.get("markdown_report", {}) or {})
                elif isinstance(build_report_output.get("markdown_report"), dict):
                    report_markdown = dict(build_report_output.get("markdown_report", {}) or {})
        if report_markdown:
            metadata = dict(report_markdown.get("metadata", {})) if isinstance(report_markdown.get("metadata"), dict) else {}
            metadata["persistence"] = {
                "records_saved": len(saved),
                "storage_root": str(self.storage_manager.storage_root),
                "stored_record_ids": record_ids,
                "storage_paths": paths,
                "markdown_saved": bool(self.config.persist_markdown),
                "persistence_status": "saved" if saved else "failed",
            }
            report_markdown["metadata"] = metadata
            markdown_text = str(report_markdown.get("markdown", "") or "")
            if "## Storage" not in markdown_text:
                from src.reports.markdown_sections import build_storage_section

                storage_section = build_storage_section({"storage_summary": metadata["persistence"]})
                if storage_section:
                    markdown_text = f"{markdown_text}\n\n{storage_section}".strip()
            report_markdown["markdown"] = markdown_text
            report_markdown["word_count"] = len(markdown_text.split())
        return {
            "success": not errors,
            "enabled": True,
            "persistence_status": "saved" if saved else "failed",
            "warnings": warnings,
            "errors": errors,
            "summary": {
                "records_saved": len(saved),
                "storage_root": str(self.storage_manager.storage_root),
                "stored_record_ids": record_ids,
                "storage_paths": paths,
                "markdown_saved": bool(self.config.persist_markdown),
            },
            "stored_record_ids": record_ids,
            "storage_paths": paths,
            "markdown_report": report_markdown,
            "markdown_report_path": safe_text(report_markdown.get("export_path"), limit=260) if isinstance(report_markdown, dict) else "",
        }

    def _safe_report_from_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "workflow_id": state.get("workflow_id", ""),
            "workflow_type": state.get("workflow_type", ""),
            "status": state.get("step_statuses", {}).get("approval_gate", "completed"),
            "step_count": len(state.get("step_statuses", {})),
            "completed_steps": sum(1 for value in state.get("step_statuses", {}).values() if value == "completed"),
            "failed_steps": sum(1 for value in state.get("step_statuses", {}).values() if value == "failed"),
            "skipped_steps": sum(1 for value in state.get("step_statuses", {}).values() if value == "skipped"),
        }

    def _build_image_request(self, request: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        creative = deepcopy(state.get("step_outputs", {}).get("generate_creative_direction", {}))
        return {
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": "image_prompt",
            "campaign_type": request.get("campaign_type", ""),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "visual_style": creative.get("visual_identity", {}).get("name") or request.get("visual_style") or self.config.default_visual_style,
            "creative_direction": request.get("creative_direction", ""),
            "image_type": request.get("image_type", "property_exterior"),
            "aspect_ratio": request.get("aspect_ratio", self.config.default_image_aspect_ratio),
            "extra_notes": request.get("extra_notes", ""),
            "creative_direction_result": creative,
        }

    def _build_video_request(self, request: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        creative = deepcopy(state.get("step_outputs", {}).get("generate_creative_direction", {}))
        return {
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": "video_script",
            "campaign_type": request.get("campaign_type", ""),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "visual_style": creative.get("visual_identity", {}).get("name") or request.get("visual_style") or self.config.default_visual_style,
            "creative_direction": request.get("creative_direction", ""),
            "video_type": request.get("video_type", self.config.default_video_type),
            "duration": request.get("duration", self.config.default_video_duration),
            "tone": request.get("tone", ""),
            "extra_notes": request.get("extra_notes", ""),
            "creative_direction_result": creative,
        }

    def _build_creative_request(self, request: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        return {
            "brand": request.get("brand", ""),
            "campaign_type": request.get("campaign_type", self.config.default_campaign_type),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "platforms": request.get("platforms") or ([request.get("platform")] if request.get("platform") else []),
            "visual_style": request.get("visual_style") or self.config.default_visual_style,
            "tone": request.get("tone", ""),
            "creative_direction": request.get("creative_direction", ""),
            "extra_notes": request.get("extra_notes", ""),
        }

    def _build_token_usage(self, request: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        ai_response = self._get_step_output(state, "generate_content")
        if isinstance(ai_response, dict):
            ai_response = ai_response.get("ai_response", ai_response)
        token_usage = {}
        if isinstance(ai_response, dict):
            token_usage = deepcopy(ai_response.get("token_usage") or {})
        if token_usage:
            return self.token_tracker.track_usage(token_usage, metadata={"workflow_id": state.get("workflow_id", ""), "workflow_type": state.get("workflow_type", ""), "module": "workflow", "operation": "generate_content", "campaign_id": request.get("campaign_type", ""), "asset_type": request.get("content_type", "")})
        prompt_payload = self._get_step_output(state, "build_prompt")
        prompt_text = ""
        if isinstance(prompt_payload, dict):
            prompt_text = str(prompt_payload.get("prompt_payload", {}).get("user_prompt", "") or prompt_payload.get("prompt_payload", {}).get("prompt", "") or "")
        output_text = ""
        parsed_output = self._get_step_output(state, "parse_response")
        if isinstance(parsed_output, dict):
            output_text = str(parsed_output.get("parsed_output", {}).get("content", "") or parsed_output.get("parsed_output", {}).get("raw_content", "") or "")
        return self.token_tracker.record_estimated_usage(prompt_text, output_text, metadata={"workflow_id": state.get("workflow_id", ""), "workflow_type": state.get("workflow_type", ""), "module": "workflow", "operation": "generate_content", "campaign_id": request.get("campaign_type", ""), "asset_type": request.get("content_type", "")})


__all__ = ["WorkflowEngine"]
