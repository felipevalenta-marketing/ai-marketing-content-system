"""Structured result helpers for the content generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PipelineResult:
    """Reusable pipeline result container."""

    success: bool
    brand: str
    platform: str
    content_type: str
    input_request: dict[str, Any]
    context_summary: dict[str, Any]
    prompt_payload: dict[str, Any] | None
    ai_response: dict[str, Any] | None
    parsed_output: dict[str, Any] | None
    formatted_output: dict[str, Any] | None
    validation_result: dict[str, Any] | None
    image_prompt_result: dict[str, Any] | None
    enhanced_image_prompt: str | None
    negative_prompt: str | None
    visual_style: str | None
    cinematic_rules_applied: list[str]
    image_prompt_validation: dict[str, Any] | None
    video_script_result: dict[str, Any] | None
    video_type: str | None
    video_duration: str | None
    scene_sequence: list[dict[str, Any]]
    storyboard: list[dict[str, Any]]
    voiceover: str | None
    camera_direction: dict[str, Any] | None
    music_mood: str | None
    video_script_validation: dict[str, Any] | None
    creative_direction_result: dict[str, Any] | None
    creative_direction_type: str | None
    visual_identity: dict[str, Any] | None
    moodboard: dict[str, Any] | None
    color_palette: dict[str, Any] | None
    platform_creative_guidelines: dict[str, Any] | None
    media_guidelines: dict[str, Any] | None
    creative_validation: dict[str, Any] | None
    adaptation_result: dict[str, Any] | None
    platform_variants: dict[str, Any]
    governance_result: dict[str, Any] | None
    approval_status: str
    overall_quality_score: float | None
    governance_warnings: list[str]
    governance_errors: list[str]
    campaign_result: dict[str, Any] | None
    campaign_strategy: dict[str, Any] | None
    campaign_assets: dict[str, Any]
    campaign_governance_summary: dict[str, Any] | None
    campaign_export_paths: dict[str, str]
    asset_coordination_result: dict[str, Any] | None
    asset_plan: dict[str, Any]
    asset_requirements: dict[str, Any]
    missing_assets: list[str]
    asset_export_paths: dict[str, str]
    execution_report: dict[str, Any] | None
    governance_report: dict[str, Any] | None
    campaign_report: dict[str, Any] | None
    asset_report: dict[str, Any] | None
    export_report: dict[str, Any] | None
    consolidated_report: dict[str, Any] | None
    report_export_paths: dict[str, str]
    rendered_markdown: str | None
    rendered_text: str | None
    exported_files: dict[str, str]
    output_metadata: dict[str, Any]
    token_usage: dict[str, Any] | None
    execution_token_summary: dict[str, Any] | None
    module_token_summary: dict[str, Any] | None
    provider_token_summary: dict[str, Any] | None
    estimated_token_usage: dict[str, Any] | None
    cost_usage: dict[str, Any] | None
    execution_cost_summary: dict[str, Any] | None
    module_cost_summary: dict[str, Any] | None
    provider_cost_summary: dict[str, Any] | None
    model_cost_summary: dict[str, Any] | None
    metadata: dict[str, Any]
    error: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result into a JSON-friendly dictionary."""

        return {
            "success": self.success,
            "brand": self.brand,
            "platform": self.platform,
            "content_type": self.content_type,
            "input_request": self.input_request,
            "context_summary": self.context_summary,
            "prompt_payload": self.prompt_payload,
            "ai_response": self.ai_response,
            "parsed_output": self.parsed_output,
            "formatted_output": self.formatted_output,
            "validation_result": self.validation_result,
            "image_prompt_result": self.image_prompt_result,
            "enhanced_image_prompt": self.enhanced_image_prompt,
            "negative_prompt": self.negative_prompt,
            "visual_style": self.visual_style,
            "cinematic_rules_applied": self.cinematic_rules_applied,
            "image_prompt_validation": self.image_prompt_validation,
            "video_script_result": self.video_script_result,
            "video_type": self.video_type,
            "video_duration": self.video_duration,
            "scene_sequence": self.scene_sequence,
            "storyboard": self.storyboard,
            "voiceover": self.voiceover,
            "camera_direction": self.camera_direction,
            "music_mood": self.music_mood,
            "video_script_validation": self.video_script_validation,
            "creative_direction_result": self.creative_direction_result,
            "creative_direction_type": self.creative_direction_type,
            "visual_identity": self.visual_identity,
            "moodboard": self.moodboard,
            "color_palette": self.color_palette,
            "platform_creative_guidelines": self.platform_creative_guidelines,
            "media_guidelines": self.media_guidelines,
            "creative_validation": self.creative_validation,
            "adaptation_result": self.adaptation_result,
            "platform_variants": self.platform_variants,
            "governance_result": self.governance_result,
            "approval_status": self.approval_status,
            "overall_quality_score": self.overall_quality_score,
            "governance_warnings": self.governance_warnings,
            "governance_errors": self.governance_errors,
            "campaign_result": self.campaign_result,
            "campaign_strategy": self.campaign_strategy,
            "campaign_assets": self.campaign_assets,
            "campaign_governance_summary": self.campaign_governance_summary,
            "campaign_export_paths": self.campaign_export_paths,
            "asset_coordination_result": self.asset_coordination_result,
            "asset_plan": self.asset_plan,
            "asset_requirements": self.asset_requirements,
            "missing_assets": self.missing_assets,
            "asset_export_paths": self.asset_export_paths,
            "execution_report": self.execution_report,
            "governance_report": self.governance_report,
            "campaign_report": self.campaign_report,
            "asset_report": self.asset_report,
            "export_report": self.export_report,
            "consolidated_report": self.consolidated_report,
            "report_export_paths": self.report_export_paths,
            "rendered_markdown": self.rendered_markdown,
            "rendered_text": self.rendered_text,
            "exported_files": self.exported_files,
            "output_metadata": self.output_metadata,
            "token_usage": self.token_usage,
            "execution_token_summary": self.execution_token_summary,
            "module_token_summary": self.module_token_summary,
            "provider_token_summary": self.provider_token_summary,
            "estimated_token_usage": self.estimated_token_usage,
            "cost_usage": self.cost_usage,
            "execution_cost_summary": self.execution_cost_summary,
            "module_cost_summary": self.module_cost_summary,
            "provider_cost_summary": self.provider_cost_summary,
            "model_cost_summary": self.model_cost_summary,
            "metadata": self.metadata,
            "error": self.error,
            "warnings": self.warnings,
        }


def build_success_result(
    brand: str,
    platform: str,
    content_type: str,
    input_request: dict[str, Any],
    context_summary: dict[str, Any],
    prompt_payload: dict[str, Any],
    ai_response: dict[str, Any],
    parsed_output: dict[str, Any],
    formatted_output: dict[str, Any] | None,
    validation_result: dict[str, Any] | None,
    image_prompt_result: dict[str, Any] | None = None,
    enhanced_image_prompt: str | None = None,
    negative_prompt: str | None = None,
    visual_style: str | None = None,
    cinematic_rules_applied: list[str] | None = None,
    image_prompt_validation: dict[str, Any] | None = None,
    video_script_result: dict[str, Any] | None = None,
    video_type: str | None = None,
    video_duration: str | None = None,
    scene_sequence: list[dict[str, Any]] | None = None,
    storyboard: list[dict[str, Any]] | None = None,
    voiceover: str | None = None,
    camera_direction: dict[str, Any] | None = None,
    music_mood: str | None = None,
    video_script_validation: dict[str, Any] | None = None,
    creative_direction_result: dict[str, Any] | None = None,
    creative_direction_type: str | None = None,
    visual_identity: dict[str, Any] | None = None,
    moodboard: dict[str, Any] | None = None,
    color_palette: dict[str, Any] | None = None,
    platform_creative_guidelines: dict[str, Any] | None = None,
    media_guidelines: dict[str, Any] | None = None,
    creative_validation: dict[str, Any] | None = None,
    adaptation_result: dict[str, Any] | None = None,
    platform_variants: dict[str, Any] | None = None,
    governance_result: dict[str, Any] | None = None,
    approval_status: str = "unknown",
    overall_quality_score: float | None = None,
    governance_warnings: list[str] | None = None,
    governance_errors: list[str] | None = None,
    campaign_result: dict[str, Any] | None = None,
    campaign_strategy: dict[str, Any] | None = None,
    campaign_assets: dict[str, Any] | None = None,
    campaign_governance_summary: dict[str, Any] | None = None,
    campaign_export_paths: dict[str, str] | None = None,
    asset_coordination_result: dict[str, Any] | None = None,
    asset_plan: dict[str, Any] | None = None,
    asset_requirements: dict[str, Any] | None = None,
    missing_assets: list[str] | None = None,
    asset_export_paths: dict[str, str] | None = None,
    execution_report: dict[str, Any] | None = None,
    governance_report: dict[str, Any] | None = None,
    campaign_report: dict[str, Any] | None = None,
    asset_report: dict[str, Any] | None = None,
    export_report: dict[str, Any] | None = None,
    consolidated_report: dict[str, Any] | None = None,
    report_export_paths: dict[str, str] | None = None,
    rendered_markdown: str | None = None,
    rendered_text: str | None = None,
    exported_files: dict[str, str] | None = None,
    output_metadata: dict[str, Any] | None = None,
    token_usage: dict[str, Any] | None = None,
    execution_token_summary: dict[str, Any] | None = None,
    module_token_summary: dict[str, Any] | None = None,
    provider_token_summary: dict[str, Any] | None = None,
    estimated_token_usage: dict[str, Any] | None = None,
    cost_usage: dict[str, Any] | None = None,
    execution_cost_summary: dict[str, Any] | None = None,
    module_cost_summary: dict[str, Any] | None = None,
    provider_cost_summary: dict[str, Any] | None = None,
    model_cost_summary: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build a successful pipeline response."""

    return PipelineResult(
        success=True,
        brand=brand,
        platform=platform,
        content_type=content_type,
        input_request=input_request,
        context_summary=context_summary,
        prompt_payload=prompt_payload,
        ai_response=ai_response,
        parsed_output=parsed_output,
        formatted_output=formatted_output,
        validation_result=validation_result,
        image_prompt_result=image_prompt_result,
        enhanced_image_prompt=enhanced_image_prompt,
        negative_prompt=negative_prompt,
        visual_style=visual_style,
        cinematic_rules_applied=cinematic_rules_applied or [],
        image_prompt_validation=image_prompt_validation,
        video_script_result=video_script_result,
        video_type=video_type,
        video_duration=video_duration,
        scene_sequence=scene_sequence or [],
        storyboard=storyboard or [],
        voiceover=voiceover,
        camera_direction=camera_direction,
        music_mood=music_mood,
        video_script_validation=video_script_validation,
        creative_direction_result=creative_direction_result,
        creative_direction_type=creative_direction_type,
        visual_identity=visual_identity,
        moodboard=moodboard,
        color_palette=color_palette,
        platform_creative_guidelines=platform_creative_guidelines,
        media_guidelines=media_guidelines,
        creative_validation=creative_validation,
        adaptation_result=adaptation_result,
        platform_variants=platform_variants or {},
        governance_result=governance_result,
        approval_status=approval_status,
        overall_quality_score=overall_quality_score,
        governance_warnings=governance_warnings or [],
        governance_errors=governance_errors or [],
        campaign_result=campaign_result,
        campaign_strategy=campaign_strategy,
        campaign_assets=campaign_assets or {},
        campaign_governance_summary=campaign_governance_summary,
        campaign_export_paths=campaign_export_paths or {},
        asset_coordination_result=asset_coordination_result,
        asset_plan=asset_plan or {},
        asset_requirements=asset_requirements or {},
        missing_assets=missing_assets or [],
        asset_export_paths=asset_export_paths or {},
        execution_report=execution_report,
        governance_report=governance_report,
        campaign_report=campaign_report,
        asset_report=asset_report,
        export_report=export_report,
        consolidated_report=consolidated_report,
        report_export_paths=report_export_paths or {},
        rendered_markdown=rendered_markdown,
        rendered_text=rendered_text,
        exported_files=exported_files or {},
        output_metadata=output_metadata or {},
        token_usage=token_usage,
        execution_token_summary=execution_token_summary,
        module_token_summary=module_token_summary,
        provider_token_summary=provider_token_summary,
        estimated_token_usage=estimated_token_usage,
        cost_usage=cost_usage,
        execution_cost_summary=execution_cost_summary,
        module_cost_summary=module_cost_summary,
        provider_cost_summary=provider_cost_summary,
        model_cost_summary=model_cost_summary,
        metadata=metadata or {},
        error=None,
        warnings=warnings or [],
    ).to_dict()


def build_failure_result(
    brand: str,
    platform: str,
    content_type: str,
    input_request: dict[str, Any],
    context_summary: dict[str, Any],
    metadata: dict[str, Any],
    error: str,
    prompt_payload: dict[str, Any] | None = None,
    ai_response: dict[str, Any] | None = None,
    parsed_output: dict[str, Any] | None = None,
    formatted_output: dict[str, Any] | None = None,
    validation_result: dict[str, Any] | None = None,
    image_prompt_result: dict[str, Any] | None = None,
    enhanced_image_prompt: str | None = None,
    negative_prompt: str | None = None,
    visual_style: str | None = None,
    cinematic_rules_applied: list[str] | None = None,
    image_prompt_validation: dict[str, Any] | None = None,
    video_script_result: dict[str, Any] | None = None,
    video_type: str | None = None,
    video_duration: str | None = None,
    scene_sequence: list[dict[str, Any]] | None = None,
    storyboard: list[dict[str, Any]] | None = None,
    voiceover: str | None = None,
    camera_direction: dict[str, Any] | None = None,
    music_mood: str | None = None,
    video_script_validation: dict[str, Any] | None = None,
    creative_direction_result: dict[str, Any] | None = None,
    creative_direction_type: str | None = None,
    visual_identity: dict[str, Any] | None = None,
    moodboard: dict[str, Any] | None = None,
    color_palette: dict[str, Any] | None = None,
    platform_creative_guidelines: dict[str, Any] | None = None,
    media_guidelines: dict[str, Any] | None = None,
    creative_validation: dict[str, Any] | None = None,
    adaptation_result: dict[str, Any] | None = None,
    platform_variants: dict[str, Any] | None = None,
    governance_result: dict[str, Any] | None = None,
    approval_status: str = "unknown",
    overall_quality_score: float | None = None,
    governance_warnings: list[str] | None = None,
    governance_errors: list[str] | None = None,
    campaign_result: dict[str, Any] | None = None,
    campaign_strategy: dict[str, Any] | None = None,
    campaign_assets: dict[str, Any] | None = None,
    campaign_governance_summary: dict[str, Any] | None = None,
    campaign_export_paths: dict[str, str] | None = None,
    asset_coordination_result: dict[str, Any] | None = None,
    asset_plan: dict[str, Any] | None = None,
    asset_requirements: dict[str, Any] | None = None,
    missing_assets: list[str] | None = None,
    asset_export_paths: dict[str, str] | None = None,
    execution_report: dict[str, Any] | None = None,
    governance_report: dict[str, Any] | None = None,
    campaign_report: dict[str, Any] | None = None,
    asset_report: dict[str, Any] | None = None,
    export_report: dict[str, Any] | None = None,
    consolidated_report: dict[str, Any] | None = None,
    report_export_paths: dict[str, str] | None = None,
    rendered_markdown: str | None = None,
    rendered_text: str | None = None,
    exported_files: dict[str, str] | None = None,
    output_metadata: dict[str, Any] | None = None,
    token_usage: dict[str, Any] | None = None,
    execution_token_summary: dict[str, Any] | None = None,
    module_token_summary: dict[str, Any] | None = None,
    provider_token_summary: dict[str, Any] | None = None,
    estimated_token_usage: dict[str, Any] | None = None,
    cost_usage: dict[str, Any] | None = None,
    execution_cost_summary: dict[str, Any] | None = None,
    module_cost_summary: dict[str, Any] | None = None,
    provider_cost_summary: dict[str, Any] | None = None,
    model_cost_summary: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build a failure pipeline response."""

    return PipelineResult(
        success=False,
        brand=brand,
        platform=platform,
        content_type=content_type,
        input_request=input_request,
        context_summary=context_summary,
        prompt_payload=prompt_payload,
        ai_response=ai_response,
        parsed_output=parsed_output,
        formatted_output=formatted_output,
        validation_result=validation_result,
        image_prompt_result=image_prompt_result,
        enhanced_image_prompt=enhanced_image_prompt,
        negative_prompt=negative_prompt,
        visual_style=visual_style,
        cinematic_rules_applied=cinematic_rules_applied or [],
        image_prompt_validation=image_prompt_validation,
        video_script_result=video_script_result,
        video_type=video_type,
        video_duration=video_duration,
        scene_sequence=scene_sequence or [],
        storyboard=storyboard or [],
        voiceover=voiceover,
        camera_direction=camera_direction,
        music_mood=music_mood,
        video_script_validation=video_script_validation,
        creative_direction_result=creative_direction_result,
        creative_direction_type=creative_direction_type,
        visual_identity=visual_identity,
        moodboard=moodboard,
        color_palette=color_palette,
        platform_creative_guidelines=platform_creative_guidelines,
        media_guidelines=media_guidelines,
        creative_validation=creative_validation,
        adaptation_result=adaptation_result,
        platform_variants=platform_variants or {},
        governance_result=governance_result,
        approval_status=approval_status,
        overall_quality_score=overall_quality_score,
        governance_warnings=governance_warnings or [],
        governance_errors=governance_errors or [],
        campaign_result=campaign_result,
        campaign_strategy=campaign_strategy,
        campaign_assets=campaign_assets or {},
        campaign_governance_summary=campaign_governance_summary,
        campaign_export_paths=campaign_export_paths or {},
        asset_coordination_result=asset_coordination_result,
        asset_plan=asset_plan or {},
        asset_requirements=asset_requirements or {},
        missing_assets=missing_assets or [],
        asset_export_paths=asset_export_paths or {},
        execution_report=execution_report,
        governance_report=governance_report,
        campaign_report=campaign_report,
        asset_report=asset_report,
        export_report=export_report,
        consolidated_report=consolidated_report,
        report_export_paths=report_export_paths or {},
        rendered_markdown=rendered_markdown,
        rendered_text=rendered_text,
        exported_files=exported_files or {},
        output_metadata=output_metadata or {},
        token_usage=token_usage,
        execution_token_summary=execution_token_summary,
        module_token_summary=module_token_summary,
        provider_token_summary=provider_token_summary,
        estimated_token_usage=estimated_token_usage,
        cost_usage=cost_usage,
        execution_cost_summary=execution_cost_summary,
        module_cost_summary=module_cost_summary,
        provider_cost_summary=provider_cost_summary,
        model_cost_summary=model_cost_summary,
        metadata=metadata,
        error=error,
        warnings=warnings or [],
    ).to_dict()
