"""Reusable markdown section builders."""

from __future__ import annotations

from typing import Any

from src.reports.markdown_renderer import render_bullets, render_code_block, render_heading, render_table
from src.reports.markdown_utils import compact_value, safe_bool, safe_dict, safe_float, safe_int, safe_list, safe_text, unique_strings


def build_title_section(data: dict[str, Any]) -> str:
    title = safe_text(data.get("title") or data.get("report_title") or "Report", limit=160)
    brand = safe_text(data.get("brand"), limit=80)
    platform = safe_text(data.get("platform"), limit=80)
    campaign_type = safe_text(data.get("campaign_type"), limit=80)
    content_type = safe_text(data.get("content_type"), limit=80)
    subtitle_items = [item for item in [brand, platform, campaign_type, content_type] if item]
    lines = [render_heading("Overview", level=2)]
    if title:
        lines.append(f"**{title}**")
    if subtitle_items:
        lines.extend(render_bullets([{"Context": ", ".join(subtitle_items)}]).splitlines())
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_executive_summary_section(data: dict[str, Any]) -> str:
    summary = safe_dict(data.get("summary") or data.get("report_summary"))
    if not summary:
        summary = {
            "status": data.get("status", data.get("workflow_status", "unknown")),
            "report_type": data.get("report_type", ""),
        }
    workflow = safe_dict(data.get("workflow_result"))
    campaign = safe_dict(data.get("campaign_result"))
    asset = safe_dict(data.get("asset_coordination_result") or data.get("asset_result"))
    governance = safe_dict(data.get("governance_result"))
    token_usage = safe_dict(data.get("token_summary") or data.get("execution_token_summary") or data.get("token_usage"))
    cost_usage = safe_dict(data.get("cost_summary") or data.get("execution_cost_summary") or data.get("cost_usage"))
    warnings = unique_strings(safe_list(data.get("warnings")) + safe_list(governance.get("warnings")) + safe_list(asset.get("warnings")))
    errors = unique_strings(safe_list(data.get("errors")) + safe_list(governance.get("errors")) + safe_list(asset.get("errors")))
    generated_assets = safe_list(asset.get("generated_assets") or asset.get("asset_plan", {}).get("required_assets") or campaign.get("assets"))
    next_actions = safe_text(
        summary.get("next_steps")
        or summary.get("recommended_next_steps")
        or data.get("recommended_next_steps")
        or data.get("next_steps")
        or "",
        limit=220,
    )
    rows = [
        {"Metric": "Status", "Value": safe_text(summary.get("status") or data.get("status") or "unknown", limit=80)},
        {"Metric": "Primary Outcome", "Value": safe_text(summary.get("primary_outcome") or summary.get("headline") or data.get("headline") or "", limit=180)},
        {"Metric": "Approval", "Value": safe_text(summary.get("approval_status") or data.get("approval_status") or data.get("governance_status") or "", limit=80)},
        {"Metric": "Workflow Status", "Value": safe_text(data.get("workflow_status") or workflow.get("status") or summary.get("workflow_status") or "", limit=80)},
        {"Metric": "Generated Assets", "Value": ", ".join(safe_list(generated_assets))},
        {"Metric": "Next Steps", "Value": next_actions},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=240)]
    extras: list[str] = []
    if token_usage:
        extras.append(
            f"Token usage: {safe_int(token_usage.get('input_tokens'), 0)} input / {safe_int(token_usage.get('output_tokens'), 0)} output / {safe_int(token_usage.get('total_tokens'), 0)} total."
        )
    if cost_usage:
        extras.append(
            f"Cost summary: {safe_text(cost_usage.get('currency'), limit=32)} {safe_float(cost_usage.get('total_cost'), 0.0):.6f} total, estimated={safe_bool(cost_usage.get('estimated_cost'))}."
        )
    if warnings:
        extras.append(f"Warnings: {len(warnings)}")
    if errors:
        extras.append(f"Critical errors: {len(errors)}")
    lines = [render_heading("Executive Summary", level=2), render_table(rows)]
    if extras:
        lines.append("")
        lines.append(render_bullets(extras))
    if warnings:
        lines.extend(["", render_heading("Key Warnings", level=3), render_bullets(warnings[:5])])
    if errors:
        lines.extend(["", render_heading("Critical Errors", level=3), render_bullets(errors[:5])])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_context_section(data: dict[str, Any]) -> str:
    context = _resolve_context(data)
    rows = [
        {"Field": "Brand", "Value": context.get("brand", "")},
        {"Field": "Platform", "Value": context.get("platform", "")},
        {"Field": "Campaign Type", "Value": context.get("campaign_type", "")},
        {"Field": "Content Type", "Value": context.get("content_type", "")},
        {"Field": "Objective", "Value": context.get("objective", "")},
        {"Field": "Audience", "Value": context.get("audience", "")},
        {"Field": "Location", "Value": context.get("location", "")},
        {"Field": "Property Type", "Value": context.get("property_type", "")},
        {"Field": "Visual Style", "Value": context.get("visual_style", "")},
        {"Field": "Creative Direction", "Value": context.get("creative_direction", "")},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=240)]
    if not rows:
        return ""
    return "\n".join([render_heading("Context", level=2), render_table(rows)]).strip()


def build_workflow_summary_section(data: dict[str, Any]) -> str:
    workflow = safe_dict(data.get("workflow_result"))
    if not workflow and not data.get("workflow_id") and not data.get("workflow_type"):
        return ""
    summary = safe_dict(workflow.get("summary") or data.get("workflow_step_summary"))
    steps = safe_list(workflow.get("steps") or data.get("steps"))
    rows = [
        {"Metric": "Workflow ID", "Value": safe_text(data.get("workflow_id") or workflow.get("workflow_id") or "", limit=120)},
        {"Metric": "Workflow Type", "Value": safe_text(data.get("workflow_type") or workflow.get("workflow_type") or "", limit=120)},
        {"Metric": "Status", "Value": safe_text(data.get("workflow_status") or workflow.get("status") or summary.get("status") or "", limit=80)},
        {"Metric": "Step Count", "Value": safe_int(summary.get("step_count") or len(steps), 0)},
        {"Metric": "Completed Steps", "Value": safe_int(summary.get("completed_steps"), 0)},
        {"Metric": "Failed Steps", "Value": safe_int(summary.get("failed_steps"), 0)},
        {"Metric": "Skipped Steps", "Value": safe_int(summary.get("skipped_steps"), 0)},
        {"Metric": "Duration Seconds", "Value": safe_float(summary.get("duration_seconds") or workflow.get("duration_seconds"), 0.0)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=120)]
    if not rows:
        return ""
    lines = [render_heading("Workflow Overview", level=2), render_table(rows)]
    if steps:
        step_rows = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            step_rows.append(
                {
                    "Step": safe_text(step.get("name") or step.get("step_type") or step.get("step_id"), limit=120),
                    "Type": safe_text(step.get("step_type"), limit=120),
                    "Status": safe_text(step.get("status"), limit=80),
                }
            )
        if step_rows:
            lines.extend(["", render_heading("Step Summary", level=3), render_table(step_rows)])
    if safe_list(workflow.get("timeline") or workflow.get("history") or data.get("workflow_state_history")):
        timeline_rows = []
        for item in safe_list(workflow.get("timeline") or workflow.get("history") or data.get("workflow_state_history")):
            if not isinstance(item, dict):
                continue
            timeline_rows.append(
                {
                    "Timestamp": safe_text(item.get("timestamp") or item.get("at") or item.get("created_at"), limit=80),
                    "State": safe_text(item.get("state") or item.get("status") or item.get("step_status"), limit=80),
                    "Detail": compact_value(item.get("detail") or item.get("description") or item, limit=180),
                }
            )
        if timeline_rows:
            lines.extend(["", render_heading("Workflow Timeline", level=3), render_table(timeline_rows)])
    if safe_list(workflow.get("status_transitions") or data.get("workflow_status_transitions")):
        transition_rows = []
        for item in safe_list(workflow.get("status_transitions") or data.get("workflow_status_transitions")):
            if not isinstance(item, dict):
                continue
            transition_rows.append(
                {
                    "From": safe_text(item.get("from") or item.get("previous_status"), limit=80),
                    "To": safe_text(item.get("to") or item.get("status"), limit=80),
                    "Reason": compact_value(item.get("reason") or item.get("notes") or "", limit=180),
                }
            )
        if transition_rows:
            lines.extend(["", render_heading("Status Transitions", level=3), render_table(transition_rows)])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_workflow_snapshot_section(data: dict[str, Any]) -> str:
    workflow = safe_dict(data.get("workflow_result"))
    state = safe_dict(data.get("workflow_state") or workflow.get("state"))
    if not workflow and not state:
        return ""
    lines = [render_heading("Workflow Snapshot", level=2)]
    rows = [
        {"Field": "Workflow ID", "Value": safe_text(data.get("workflow_id") or workflow.get("workflow_id") or state.get("workflow_id"), limit=120)},
        {"Field": "Workflow Type", "Value": safe_text(data.get("workflow_type") or workflow.get("workflow_type") or state.get("workflow_type"), limit=120)},
        {"Field": "Current Status", "Value": safe_text(data.get("workflow_status") or workflow.get("status") or state.get("status"), limit=80)},
        {"Field": "Started At", "Value": safe_text(workflow.get("started_at") or state.get("metadata", {}).get("created_at"), limit=80)},
        {"Field": "Completed At", "Value": safe_text(workflow.get("completed_at") or state.get("metadata", {}).get("updated_at"), limit=80)},
        {"Field": "Duration Seconds", "Value": safe_float(workflow.get("duration_seconds"), 0.0)},
        {"Field": "State History", "Value": compact_value(state.get("history") or state.get("timeline"), limit=180)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=240)]
    if rows:
        lines.append(render_table(rows))
    step_outputs = safe_dict(state.get("step_outputs"))
    if step_outputs:
        step_rows = []
        for step_id, output in step_outputs.items():
            if not isinstance(output, dict):
                continue
            step_rows.append(
                {
                    "Step": safe_text(step_id, limit=120),
                    "Status": safe_text(output.get("status"), limit=80),
                    "Warnings": len(safe_list(output.get("warnings"))),
                    "Errors": len(safe_list(output.get("errors"))),
                }
            )
        if step_rows:
            lines.extend(["", render_heading("State History", level=3), render_table(step_rows)])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_generation_output_section(data: dict[str, Any]) -> str:
    formatted = safe_dict(data.get("formatted_output"))
    parsed = safe_dict(data.get("parsed_output"))
    prompt = safe_dict(data.get("prompt_payload"))
    if not formatted and not parsed and not prompt:
        return ""
    lines = [render_heading("Generation Output", level=2)]
    source = formatted or parsed or prompt
    rows = []
    for key in ("hook", "caption", "cta", "hashtags", "title", "short_description", "long_description", "script", "voiceover", "music_mood"):
        value = source.get(key)
        if safe_text(value, limit=240):
            rows.append({"Field": key.replace("_", " ").title(), "Value": value})
    if rows:
        lines.append(render_table(rows))
    else:
        lines.append("No structured generation output was available.")
    if prompt.get("system_prompt") or prompt.get("user_prompt"):
        lines.extend(["", render_heading("Prompt Summary", level=3)])
        prompt_rows = [
            {"Field": "System Prompt", "Value": safe_text(prompt.get("system_prompt"), limit=240)},
            {"Field": "User Prompt", "Value": safe_text(prompt.get("user_prompt"), limit=240)},
        ]
        lines.append(render_table([row for row in prompt_rows if row["Value"]]))
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_campaign_section(data: dict[str, Any]) -> str:
    campaign = safe_dict(data.get("campaign_result"))
    strategy = safe_dict(data.get("campaign_strategy") or campaign.get("strategy"))
    if not campaign and not strategy and not data.get("campaign_type"):
        return ""
    lines = [render_heading("Campaign", level=2)]
    rows = [
        {"Field": "Campaign Name", "Value": safe_text(campaign.get("campaign_name") or data.get("campaign_name"), limit=160)},
        {"Field": "Campaign Type", "Value": safe_text(campaign.get("campaign_type") or data.get("campaign_type"), limit=120)},
        {"Field": "Objective", "Value": safe_text(campaign.get("objective") or data.get("objective"), limit=120)},
        {"Field": "Platforms", "Value": ", ".join(safe_list(campaign.get("platform_plan") or data.get("platforms")))},
        {"Field": "Content Sequence", "Value": compact_value(campaign.get("content_sequence") or data.get("content_sequence"), limit=240)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=240)]
    if rows:
        lines.append(render_table(rows))
    if strategy:
        lines.extend(["", render_heading("Strategy", level=3), render_bullets([{"Strategy": compact_value(strategy, limit=500)}])])
    assets = safe_dict(campaign.get("assets"))
    if assets:
        lines.extend(["", render_heading("Deliverables", level=3), render_bullets([{"Assets": compact_value(assets, limit=500)}])])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_asset_section(data: dict[str, Any]) -> str:
    asset = safe_dict(data.get("asset_coordination_result"))
    asset_plan = safe_dict(data.get("asset_plan") or asset.get("asset_plan"))
    asset_requirements = safe_dict(data.get("asset_requirements") or asset.get("asset_requirements"))
    missing_assets = unique_strings(data.get("missing_assets") or asset.get("missing_assets"))
    if not asset and not asset_plan and not asset_requirements and not missing_assets:
        return ""
    lines = [render_heading("Assets", level=2)]
    rows = [
        {"Field": "Asset Count", "Value": safe_int(asset.get("asset_count") or len(safe_list(asset_plan.get("required_assets"))), 0)},
        {"Field": "Missing Assets", "Value": ", ".join(missing_assets)},
        {"Field": "Visual Style", "Value": safe_text(asset_plan.get("visual_style") or data.get("visual_style"), limit=120)},
        {"Field": "Image Type", "Value": safe_text(asset_plan.get("image_type") or data.get("image_type"), limit=120)},
        {"Field": "Video Type", "Value": safe_text(asset_plan.get("video_type") or data.get("video_type"), limit=120)},
        {"Field": "Aspect Ratio", "Value": safe_text(asset_plan.get("aspect_ratio") or data.get("aspect_ratio"), limit=80)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=240)]
    if rows:
        lines.append(render_table(rows))
    if asset_plan:
        lines.extend(["", render_heading("Asset Plan", level=3), render_bullets([{"Plan": compact_value(asset_plan, limit=500)}])])
    if asset_requirements:
        lines.extend(["", render_heading("Requirements", level=3), render_bullets([{"Requirements": compact_value(asset_requirements, limit=500)}])])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_creative_direction_section(data: dict[str, Any]) -> str:
    creative = safe_dict(data.get("creative_direction_result"))
    if not creative:
        creative = safe_dict(data.get("creative_validation"))
    visual_identity = safe_dict(creative.get("visual_identity") or data.get("visual_identity"))
    moodboard = safe_dict(creative.get("moodboard") or data.get("moodboard"))
    color_palette = safe_dict(creative.get("color_palette") or data.get("color_palette"))
    if not visual_identity and not moodboard and not color_palette and not data.get("creative_direction_type"):
        return ""
    lines = [render_heading("Creative Direction", level=2)]
    rows = [
        {"Field": "Direction Type", "Value": safe_text(creative.get("creative_direction_type") or data.get("creative_direction_type"), limit=120)},
        {"Field": "Visual Identity", "Value": safe_text(visual_identity.get("name"), limit=120)},
        {"Field": "Mood", "Value": safe_text(visual_identity.get("mood") or moodboard.get("mood"), limit=180)},
        {"Field": "Lighting", "Value": safe_text(creative.get("lighting_direction") or visual_identity.get("lighting"), limit=180)},
        {"Field": "Camera Style", "Value": safe_text(creative.get("camera_style") or visual_identity.get("camera_style"), limit=180)},
        {"Field": "Color Palette", "Value": safe_text(color_palette.get("name"), limit=120)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=240)]
    if rows:
        lines.append(render_table(rows))
    if moodboard.get("rules"):
        lines.extend(["", render_heading("Moodboard Rules", level=3), render_bullets([{"Rules": compact_value(moodboard.get("rules"), limit=500)}])])
    if color_palette:
        lines.extend(["", render_heading("Palette", level=3), render_bullets([{"Palette": compact_value(color_palette, limit=500)}])])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_media_section(data: dict[str, Any]) -> str:
    image_prompt = safe_dict(data.get("image_prompt_result"))
    image_validation = safe_dict(data.get("image_prompt_validation"))
    storyboard = safe_list(data.get("storyboard") or safe_dict(data.get("video_script_result")).get("storyboard"))
    video_script = safe_dict(data.get("video_script_result"))
    video_validation = safe_dict(data.get("video_script_validation"))
    creative = safe_dict(data.get("creative_direction_result"))
    if not image_prompt and not image_validation and not video_script and not video_validation and not creative and not storyboard:
        return ""
    lines = [render_heading("Media", level=2)]
    if image_prompt:
        lines.extend(["", render_heading("Image Prompt", level=3)])
        rows = [
            {"Field": "Image Type", "Value": safe_text(image_prompt.get("image_type") or image_prompt.get("visual_direction"), limit=120)},
            {"Field": "Visual Style", "Value": safe_text(image_prompt.get("visual_style"), limit=120)},
            {"Field": "Aspect Ratio", "Value": safe_text(image_prompt.get("aspect_ratio"), limit=80)},
            {"Field": "Negative Prompt", "Value": compact_value(image_prompt.get("negative_prompt"), limit=240)},
        ]
        rows = [row for row in rows if safe_text(row["Value"], limit=240)]
        if rows:
            lines.append(render_table(rows))
        if image_validation:
            lines.extend(["", render_heading("Image Validation", level=3), render_table([{"Valid": safe_bool(image_validation.get("valid")), "Warnings": len(safe_list(image_validation.get("warnings"))), "Errors": len(safe_list(image_validation.get("errors")))}])])
            scores = safe_dict(image_validation.get("scores"))
            if scores:
                lines.extend(["", render_heading("Image Validation Scores", level=3), render_table([
                    {"Metric": "Realism", "Value": safe_float(scores.get("realism"), 0.0)},
                    {"Metric": "Completeness", "Value": safe_float(scores.get("completeness"), 0.0)},
                    {"Metric": "Brand Fit", "Value": safe_float(scores.get("brand_fit"), 0.0)},
                    {"Metric": "Platform Fit", "Value": safe_float(scores.get("platform_fit"), 0.0)},
                    {"Metric": "Conciseness", "Value": safe_float(scores.get("conciseness"), 0.0)},
                ])])
    elif image_validation:
        lines.extend(["", render_heading("Image Validation", level=3), render_table([{"Valid": safe_bool(image_validation.get("valid")), "Warnings": len(safe_list(image_validation.get("warnings"))), "Errors": len(safe_list(image_validation.get("errors")))}])])
        scores = safe_dict(image_validation.get("scores"))
        if scores:
            lines.extend(["", render_heading("Image Validation Scores", level=3), render_table([
                {"Metric": "Realism", "Value": safe_float(scores.get("realism"), 0.0)},
                {"Metric": "Completeness", "Value": safe_float(scores.get("completeness"), 0.0)},
                {"Metric": "Brand Fit", "Value": safe_float(scores.get("brand_fit"), 0.0)},
                {"Metric": "Platform Fit", "Value": safe_float(scores.get("platform_fit"), 0.0)},
                {"Metric": "Conciseness", "Value": safe_float(scores.get("conciseness"), 0.0)},
            ])])
    if creative:
        lines.extend(["", render_heading("Visual Direction", level=3)])
        rows = [
            {"Field": "Creative Direction Type", "Value": safe_text(creative.get("creative_direction_type"), limit=120)},
            {"Field": "Visual Identity", "Value": safe_text(safe_dict(creative.get("visual_identity")).get("name"), limit=120)},
            {"Field": "Lighting", "Value": safe_text(creative.get("lighting_direction"), limit=180)},
            {"Field": "Camera Style", "Value": safe_text(creative.get("camera_style"), limit=180)},
        ]
        rows = [row for row in rows if safe_text(row["Value"], limit=240)]
        if rows:
            lines.append(render_table(rows))
    if video_script:
        lines.extend(["", render_heading("Video Script", level=3)])
        rows = [
            {"Field": "Video Type", "Value": safe_text(video_script.get("video_type"), limit=120)},
            {"Field": "Duration", "Value": safe_text(video_script.get("duration"), limit=80)},
            {"Field": "Hook", "Value": safe_text(video_script.get("hook"), limit=240)},
            {"Field": "CTA", "Value": safe_text(video_script.get("cta"), limit=240)},
            {"Field": "Music Mood", "Value": safe_text(video_script.get("music_mood"), limit=180)},
        ]
        rows = [row for row in rows if safe_text(row["Value"], limit=240)]
        if rows:
            lines.append(render_table(rows))
        storyboard_rows = []
        for frame in storyboard or safe_list(video_script.get("storyboard")):
            if not isinstance(frame, dict):
                continue
            storyboard_rows.append(
                {
                    "Frame": safe_text(frame.get("frame_number") or frame.get("scene_number"), limit=80),
                    "Shot Type": safe_text(frame.get("shot_type"), limit=120),
                    "Visual": compact_value(frame.get("visual_description"), limit=180),
                    "Text": compact_value(frame.get("on_screen_text"), limit=160),
                }
            )
        if storyboard_rows:
            lines.extend(["", render_heading("Storyboard", level=3), render_table(storyboard_rows)])
        if video_validation:
            lines.extend(["", render_heading("Video Validation", level=3), render_table([{"Valid": safe_bool(video_validation.get("valid")), "Warnings": len(safe_list(video_validation.get("warnings"))), "Errors": len(safe_list(video_validation.get("errors")))}])])
            scores = safe_dict(video_validation.get("scores"))
            if scores:
                lines.extend(["", render_heading("Video Validation Scores", level=3), render_table([
                    {"Metric": "Structure", "Value": safe_float(scores.get("structure"), 0.0)},
                    {"Metric": "Pacing", "Value": safe_float(scores.get("pacing"), 0.0)},
                    {"Metric": "Brand Fit", "Value": safe_float(scores.get("brand_fit"), 0.0)},
                    {"Metric": "Platform Fit", "Value": safe_float(scores.get("platform_fit"), 0.0)},
                    {"Metric": "Factual Safety", "Value": safe_float(scores.get("factual_safety"), 0.0)},
                ])])
    elif video_validation:
        lines.extend(["", render_heading("Video Validation", level=3), render_table([{"Valid": safe_bool(video_validation.get("valid")), "Warnings": len(safe_list(video_validation.get("warnings"))), "Errors": len(safe_list(video_validation.get("errors")))}])])
        scores = safe_dict(video_validation.get("scores"))
        if scores:
            lines.extend(["", render_heading("Video Validation Scores", level=3), render_table([
                {"Metric": "Structure", "Value": safe_float(scores.get("structure"), 0.0)},
                {"Metric": "Pacing", "Value": safe_float(scores.get("pacing"), 0.0)},
                {"Metric": "Brand Fit", "Value": safe_float(scores.get("brand_fit"), 0.0)},
                {"Metric": "Platform Fit", "Value": safe_float(scores.get("platform_fit"), 0.0)},
                {"Metric": "Factual Safety", "Value": safe_float(scores.get("factual_safety"), 0.0)},
            ])])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_governance_section(data: dict[str, Any]) -> str:
    governance = safe_dict(data.get("governance_result"))
    creative_validation = safe_dict(data.get("creative_validation"))
    image_validation = safe_dict(data.get("image_prompt_validation"))
    video_validation = safe_dict(data.get("video_script_validation"))
    if not governance and not creative_validation and not image_validation and not video_validation:
        return ""
    rows = [
        {"Field": "Status", "Value": safe_text(governance.get("status") or data.get("approval_status") or data.get("workflow_status") or "", limit=80)},
        {"Field": "Approval", "Value": safe_text(governance.get("approved") if "approved" in governance else data.get("approval_status"), limit=80)},
        {"Field": "Overall Score", "Value": safe_float(governance.get("overall_score"), 0.0)},
        {"Field": "Quality Score", "Value": safe_float(governance.get("quality_score"), 0.0)},
        {"Field": "Brand Score", "Value": safe_float(governance.get("brand_score"), 0.0)},
        {"Field": "Platform Score", "Value": safe_float(governance.get("platform_score"), 0.0)},
        {"Field": "Factual Safety Score", "Value": safe_float(governance.get("factual_safety_score"), 0.0)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=120)]
    if not rows:
        return ""
    lines = [render_heading("Governance", level=2), render_table(rows)]
    warnings = unique_strings(governance.get("warnings", []) + creative_validation.get("warnings", []) + image_validation.get("warnings", []) + video_validation.get("warnings", []) + safe_list(data.get("warnings")))
    errors = unique_strings(governance.get("errors", []) + creative_validation.get("errors", []) + image_validation.get("errors", []) + video_validation.get("errors", []) + safe_list(data.get("errors")))
    if warnings:
        lines.extend(["", build_warnings_section({"warnings": warnings})])
    if errors:
        lines.extend(["", build_errors_section({"errors": errors})])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_token_usage_section(data: dict[str, Any]) -> str:
    token_usage = safe_dict(data.get("token_usage"))
    summary = safe_dict(data.get("token_summary") or data.get("execution_token_summary") or data.get("report_summary", {}).get("token_summary"))
    token_source = token_usage or summary
    if not token_source:
        return ""
    rows = [
        {"Metric": "Provider", "Value": safe_text(token_source.get("provider"), limit=80)},
        {"Metric": "Model", "Value": safe_text(token_source.get("model"), limit=80)},
        {"Metric": "Input Tokens", "Value": safe_int(token_source.get("input_tokens"), 0)},
        {"Metric": "Output Tokens", "Value": safe_int(token_source.get("output_tokens"), 0)},
        {"Metric": "Cached Tokens", "Value": safe_int(token_source.get("cached_input_tokens"), 0)},
        {"Metric": "Total Tokens", "Value": safe_int(token_source.get("total_tokens"), 0)},
        {"Metric": "Estimated", "Value": safe_bool(token_source.get("estimated"))},
        {"Metric": "Source", "Value": safe_text(token_source.get("source"), limit=80)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=120)]
    if not rows:
        return ""
    lines = [render_heading("Token Usage", level=2), render_table(rows)]
    breakdown_sources = {
        "Workflow Token Summary": safe_dict(data.get("workflow_token_summary")),
        "Module Breakdown": safe_dict(data.get("module_token_summary") or token_source.get("module_breakdown")),
        "Provider Breakdown": safe_dict(data.get("provider_token_summary") or token_source.get("provider_breakdown")),
        "Execution Breakdown": safe_dict(data.get("execution_token_summary") or token_source.get("execution_breakdown")),
    }
    for title, source in breakdown_sources.items():
        if not source:
            continue
        breakdown_rows = []
        for key, value in source.items():
            if isinstance(value, dict):
                breakdown_rows.append(
                    {
                        "Item": safe_text(key, limit=80),
                        "Tokens": safe_int(value.get("total_tokens") or value.get("input_tokens") or value.get("records_count"), 0),
                        "Estimated": safe_bool(value.get("estimated") or value.get("estimated_usage") or value.get("estimated_cost")),
                        "Details": compact_value(value, limit=180),
                    }
                )
            else:
                breakdown_rows.append({"Item": safe_text(key, limit=80), "Value": compact_value(value, limit=180)})
        if breakdown_rows:
            lines.extend(["", render_heading(title, level=3), render_table(breakdown_rows[:10])])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_cost_usage_section(data: dict[str, Any]) -> str:
    cost_usage = safe_dict(data.get("cost_usage"))
    summary = safe_dict(data.get("cost_summary") or data.get("execution_cost_summary") or data.get("report_summary", {}).get("cost_summary"))
    source = cost_usage or summary
    if not source:
        return ""
    rows = [
        {"Metric": "Provider", "Value": safe_text(source.get("provider"), limit=80)},
        {"Metric": "Model", "Value": safe_text(source.get("model"), limit=80)},
        {"Metric": "Currency", "Value": safe_text(source.get("currency"), limit=32)},
        {"Metric": "Input Cost", "Value": safe_float(source.get("input_cost"), 0.0)},
        {"Metric": "Output Cost", "Value": safe_float(source.get("output_cost"), 0.0)},
        {"Metric": "Cached Input Cost", "Value": safe_float(source.get("cached_input_cost"), 0.0)},
        {"Metric": "Generation Cost", "Value": safe_float(source.get("generation_cost"), safe_float(source.get("total_cost"), 0.0))},
        {"Metric": "Workflow Cost", "Value": safe_float(source.get("workflow_cost"), safe_float(source.get("total_cost"), 0.0))},
        {"Metric": "Total Cost", "Value": safe_float(source.get("total_cost"), 0.0)},
        {"Metric": "Estimated Cost", "Value": safe_bool(source.get("estimated_cost"))},
        {"Metric": "Pricing Found", "Value": safe_bool(source.get("pricing_found"))},
        {"Metric": "Pricing Version", "Value": safe_text(source.get("pricing_version"), limit=80)},
        {"Metric": "Pricing Source", "Value": safe_text(source.get("pricing_source"), limit=80)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=120)]
    if not rows:
        return ""
    lines = [render_heading("Cost Usage", level=2), render_table(rows)]
    breakdown_sources = {
        "Workflow Cost Summary": safe_dict(data.get("workflow_cost_summary")),
        "Execution Cost Summary": safe_dict(data.get("execution_cost_summary") or source.get("execution_breakdown")),
        "Module Breakdown": safe_dict(data.get("module_cost_summary") or source.get("module_breakdown")),
        "Provider Breakdown": safe_dict(data.get("provider_cost_summary") or source.get("provider_breakdown")),
        "Model Breakdown": safe_dict(data.get("model_cost_summary") or source.get("model_breakdown")),
    }
    for title, source_map in breakdown_sources.items():
        if not source_map:
            continue
        breakdown_rows = []
        for key, value in source_map.items():
            if isinstance(value, dict):
                breakdown_rows.append(
                    {
                        "Item": safe_text(key, limit=80),
                        "Total Cost": safe_float(value.get("total_cost"), 0.0),
                        "Records": safe_int(value.get("records_count"), 0),
                        "Estimated": safe_int(value.get("estimated_cost_records"), 0),
                        "Details": compact_value(value, limit=180),
                    }
                )
            else:
                breakdown_rows.append({"Item": safe_text(key, limit=80), "Value": compact_value(value, limit=180)})
        if breakdown_rows:
            lines.extend(["", render_heading(title, level=3), render_table(breakdown_rows[:10])])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_storage_section(data: dict[str, Any]) -> str:
    storage = safe_dict(data.get("storage_summary") or data.get("persistence_result"))
    if not storage:
        return ""
    rows = [
        {"Field": "Status", "Value": safe_text(storage.get("persistence_status") or storage.get("status"), limit=80)},
        {"Field": "Storage Location", "Value": safe_text(storage.get("storage_location") or storage.get("storage_root"), limit=260)},
        {"Field": "Records Saved", "Value": safe_int(storage.get("records_saved"), 0)},
        {"Field": "Markdown Saved", "Value": safe_bool(storage.get("markdown_saved"))},
        {"Field": "Stored Record IDs", "Value": ", ".join(safe_list(storage.get("stored_record_ids")))},
        {"Field": "Storage Paths", "Value": safe_text(storage.get("storage_paths"), limit=260)},
    ]
    rows = [row for row in rows if safe_text(row["Value"], limit=240)]
    if not rows:
        return ""
    lines = [render_heading("Storage", level=2), render_table(rows)]
    if safe_list(storage.get("generated_artifacts")):
        lines.extend(["", render_heading("Generated Artifacts", level=3), render_bullets([compact_value(item, limit=200) for item in safe_list(storage.get("generated_artifacts"))])])
    if safe_list(storage.get("report_exports")):
        lines.extend(["", render_heading("Report Exports", level=3), render_bullets([compact_value(item, limit=200) for item in safe_list(storage.get("report_exports"))])])
    if safe_list(storage.get("workflow_snapshots")):
        lines.extend(["", render_heading("Workflow Snapshots", level=3), render_bullets([compact_value(item, limit=200) for item in safe_list(storage.get("workflow_snapshots"))])])
    if safe_list(storage.get("execution_archives")):
        lines.extend(["", render_heading("Execution Archives", level=3), render_bullets([compact_value(item, limit=200) for item in safe_list(storage.get("execution_archives"))])])
    if safe_list(storage.get("warnings")):
        lines.extend(["", render_heading("Storage Warnings", level=3), render_bullets(unique_strings(storage.get("warnings")))])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_tracking_section(data: dict[str, Any]) -> str:
    token_section = build_token_usage_section(data)
    cost_section = build_cost_usage_section(data)
    if not token_section and not cost_section:
        return ""
    lines = [render_heading("Tracking", level=2)]
    if token_section:
        lines.append(token_section)
    if cost_section:
        lines.extend(["", cost_section])
    return "\n".join([line for line in lines if line.strip()]).strip()


def build_warnings_section(data: dict[str, Any]) -> str:
    warnings = unique_strings(data.get("warnings", []))
    if not warnings:
        return ""
    return "\n".join([render_heading("Warnings", level=2), render_bullets(warnings)]).strip()


def build_errors_section(data: dict[str, Any]) -> str:
    errors = unique_strings(data.get("errors", []))
    if not errors:
        return ""
    return "\n".join([render_heading("Errors", level=2), render_bullets(errors)]).strip()


def build_metadata_section(data: dict[str, Any]) -> str:
    metadata = safe_dict(data.get("metadata"))
    if not metadata:
        return ""
    rows = []
    for key, value in metadata.items():
        if key in {"raw_response", "provider_response", "openai_raw_response"}:
            continue
        text = compact_value(value, limit=240)
        if not text:
            continue
        rows.append({"Field": key.replace("_", " ").title(), "Value": text})
    if not rows:
        return ""
    return "\n".join([render_heading("Metadata", level=2), render_table(rows)]).strip()


def _resolve_context(data: dict[str, Any]) -> dict[str, Any]:
    context = safe_dict(data.get("context") or data.get("input_request"))
    metadata = safe_dict(data.get("metadata"))
    merged = {
        "brand": data.get("brand") or metadata.get("brand") or context.get("brand", ""),
        "platform": data.get("platform") or metadata.get("platform") or context.get("platform", ""),
        "campaign_type": data.get("campaign_type") or metadata.get("campaign_type") or context.get("campaign_type", ""),
        "content_type": data.get("content_type") or metadata.get("content_type") or context.get("content_type", ""),
        "objective": data.get("objective") or metadata.get("objective") or context.get("objective", ""),
        "audience": data.get("audience") or metadata.get("audience") or context.get("audience", ""),
        "location": data.get("location") or metadata.get("location") or context.get("location", ""),
        "property_type": data.get("property_type") or metadata.get("property_type") or context.get("property_type", ""),
        "visual_style": data.get("visual_style") or metadata.get("visual_style") or context.get("visual_style", ""),
        "creative_direction": data.get("creative_direction") or metadata.get("creative_direction") or context.get("creative_direction", ""),
    }
    return merged
