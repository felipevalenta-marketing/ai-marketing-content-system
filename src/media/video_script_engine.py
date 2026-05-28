"""High-level orchestration for deterministic video script generation."""

from __future__ import annotations

from typing import Any

from src.media.scene_templates import get_scene_template, resolve_scene_template
from src.media.storyboard_rules import resolve_storyboard_rules
from src.media.video_prompt_enhancer import VideoPromptEnhancer
from src.media.video_script_contracts import (
    build_video_script_request_contract,
    build_video_script_response_contract,
    get_supported_durations,
    get_supported_platforms,
    get_supported_video_types,
    normalize_duration,
    normalize_video_type,
)
from src.media.video_script_validator import VideoScriptValidator
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context, log_warning


DEFAULT_VOICEOVER = "A calm, premium, and grounded Mediterranean story."
DEFAULT_CTA = "Contact our team to learn more."


class VideoScriptEngine:
    """Create structured short-form video scripts and storyboard plans."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.enhancer = VideoPromptEnhancer()
        self.validator = VideoScriptValidator()

    def generate_video_script(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate a structured video script from a request."""

        valid, reason = self.validate_request(request)
        normalized = self._normalize_request(request)
        log_context(self.logger, f"Generating video script for {normalized['platform']}/{normalized['video_type']}")
        warnings: list[str] = []
        errors: list[str] = []

        template = self.select_scene_template(normalized)
        scenes = self.build_scene_sequence(normalized, template)
        storyboard = self.build_storyboard(normalized, scenes)
        voiceover = self.build_voiceover(normalized, scenes)
        camera_direction = self.build_camera_direction(normalized, scenes)
        music_mood = self.build_music_mood(normalized)
        cta = self.build_cta(normalized)
        hook = str(normalized.get("creative_direction") or normalized.get("extra_notes") or "").strip()
        if not hook:
            hook = self._build_hook(normalized, template)

        script = self._build_script_text(normalized, hook, scenes, voiceover, cta, music_mood)
        script = self.enhancer.enhance_script(script, normalized)
        validation_payload = {
            "brand": normalized["brand"],
            "platform": normalized["platform"],
            "content_type": "video_script",
            "video_type": normalized["video_type"],
            "duration": normalized["duration"],
            "hook": hook,
            "script": script,
            "voiceover": voiceover,
            "cta": cta,
            "music_mood": music_mood,
            "scene_sequence": scenes,
            "storyboard": storyboard,
            "camera_direction": camera_direction,
            "metadata": self._build_metadata(normalized, template),
        }
        validation_result = self.validator.validate(validation_payload)
        warnings.extend(validation_result.get("warnings", []))
        errors.extend(validation_result.get("errors", []))
        if not valid and reason:
            warnings.append(reason)
        elif reason:
            warnings.append(reason)
        if not script:
            errors.append("Video script generation produced an empty script.")

        result = self.build_result(
            success=not errors and validation_result.get("valid", False),
            video_type=normalized["video_type"],
            duration=normalized["duration"],
            platform=normalized["platform"],
            hook=hook,
            script=script,
            voiceover=voiceover,
            cta=cta,
            music_mood=music_mood,
            scene_sequence=scenes,
            storyboard=storyboard,
            camera_direction=camera_direction,
            metadata=self._build_metadata(normalized, template),
            warnings=warnings,
            errors=errors,
            validation_result=validation_result,
            request_contract=build_video_script_request_contract(),
            response_contract=build_video_script_response_contract(),
            scene_contract=self._scene_contract(),
            storyboard_contract=self._storyboard_contract(),
        )
        log_context(self.logger, f"Video script ready for {normalized['brand']}/{normalized['video_type']}")
        return result

    def validate_request(self, request: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate a video script request before generation."""

        if not isinstance(request, dict):
            return False, "Video script request must be a dictionary."
        brand = normalize_key(str(request.get("brand", "")))
        platform = normalize_key(str(request.get("platform", "")))
        video_type = normalize_video_type(str(request.get("video_type") or request.get("content_type") or ""))
        duration = normalize_duration(str(request.get("duration") or ""))
        creative_direction = str(request.get("creative_direction", "")).strip()
        if not brand:
            return False, "Missing brand."
        if not platform:
            return False, "Missing platform."
        if platform not in get_supported_platforms():
            return False, f"Unsupported platform: {platform}"
        warnings: list[str] = []
        if not video_type:
            warnings.append("Missing video_type; using a generic property launch structure.")
        elif video_type not in get_supported_video_types():
            warnings.append(f"Unsupported video_type: {video_type}; using a generic property launch structure.")
        if not duration:
            warnings.append("Missing duration; using the default duration.")
        elif duration not in get_supported_durations():
            warnings.append(f"Unsupported duration: {duration}; using the default duration.")
        if not creative_direction:
            warnings.append("Missing creative_direction; using contextual fallback guidance.")
        return True, "; ".join(warnings) if warnings else None

    def select_scene_template(self, request: dict[str, Any]) -> dict[str, Any]:
        """Select the best scene template for a request."""

        return resolve_scene_template(request)

    def build_scene_sequence(self, request: dict[str, Any], template: dict[str, Any]) -> list[dict[str, Any]]:
        """Build a structured sequence of scenes."""

        duration = normalize_duration(str(request.get("duration") or "30s"))
        target_count = self._scene_count_for_duration(duration, int(template.get("scene_count", 5)))
        purposes = list(template.get("scene_purposes", [])) or [f"Scene {index + 1}" for index in range(target_count)]
        distributions = list(template.get("recommended_duration_distribution", []))
        if len(distributions) != target_count:
            distributions = self._normalize_distribution(target_count)
        visuals = self._visual_roles(template, target_count)
        scenes: list[dict[str, Any]] = []
        for index in range(target_count):
            purpose = purposes[index] if index < len(purposes) else f"Scene {index + 1}"
            scene_seconds = self._scene_seconds(duration, distributions[index], target_count)
            visual = self._scene_visual(request, template, purpose, index)
            camera_motion = self._scene_camera_motion(request, template, index)
            voiceover = self._scene_voiceover(request, purpose, index, target_count)
            on_screen_text = self._scene_on_screen_text(request, purpose, index)
            scenes.append({
                "scene_number": index + 1,
                "duration": scene_seconds,
                "visual": visual,
                "camera_motion": camera_motion,
                "voiceover": voiceover,
                "on_screen_text": on_screen_text,
                "purpose": purpose,
                "visual_role": visuals[index] if index < len(visuals) else "scene",
            })
        return scenes

    def build_storyboard(self, request: dict[str, Any], scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build storyboard frames from scenes."""

        frames: list[dict[str, Any]] = []
        for index, scene in enumerate(scenes, start=1):
            frames.append({
                "frame_number": index,
                "scene_number": scene.get("scene_number", index),
                "shot_type": self._shot_type_for_scene(request, scene),
                "visual_description": scene.get("visual", ""),
                "camera_direction": scene.get("camera_motion", ""),
                "lighting": self._lighting_for_request(request),
                "motion": scene.get("camera_motion", ""),
                "on_screen_text": scene.get("on_screen_text", ""),
                "voiceover": scene.get("voiceover", ""),
            })
        return frames

    def build_voiceover(self, request: dict[str, Any], scenes: list[dict[str, Any]]) -> str:
        """Build a single voiceover narrative from scenes."""

        lines = [str(scene.get("voiceover", "")).strip() for scene in scenes if str(scene.get("voiceover", "")).strip()]
        if not lines:
            lines = [self._build_hook(request, self.select_scene_template(request))]
        script = " ".join(lines).strip()
        return self.enhancer.optimize_voiceover_length(script, str(request.get("duration") or "30s"))

    def build_camera_direction(self, request: dict[str, Any], scenes: list[dict[str, Any]]) -> dict[str, Any]:
        """Build a compact camera direction summary."""

        return {
            "platform": normalize_key(str(request.get("platform", ""))),
            "framing": "vertical-safe" if normalize_key(str(request.get("platform", ""))) in {"instagram", "tiktok"} else "balanced",
            "movement": [scene.get("camera_motion", "") for scene in scenes if scene.get("camera_motion")],
            "shot_types": [self._shot_type_for_scene(request, scene) for scene in scenes],
            "continuity_note": "Maintain cinematic continuity and avoid fake luxury exaggeration.",
        }

    def build_music_mood(self, request: dict[str, Any]) -> str:
        """Build a music mood recommendation."""

        platform = normalize_key(str(request.get("platform", "")))
        tone = str(request.get("tone") or "premium but approachable").strip().lower()
        if platform in {"instagram", "tiktok"}:
            return "warm, modern, rhythmic, and elegant"
        if platform == "linkedin":
            return "subtle, polished, and professional"
        if platform == "facebook":
            return "warm, clear, and inviting"
        if "luxury" in tone:
            return "cinematic, premium, and restrained"
        return "calm, premium, and grounded"

    def build_cta(self, request: dict[str, Any]) -> str:
        """Build a safe call to action."""

        platform = normalize_key(str(request.get("platform", "")))
        if platform == "linkedin":
            return "Request the full details from our team."
        if platform == "facebook":
            return "Message us to learn more."
        if platform in {"instagram", "tiktok", "youtube"}:
            return "Send us a message to learn more."
        if platform == "website":
            return "Request more information."
        return DEFAULT_CTA

    def build_result(
        self,
        *,
        success: bool,
        video_type: str,
        duration: str,
        platform: str,
        hook: str,
        script: str,
        voiceover: str,
        cta: str,
        music_mood: str,
        scene_sequence: list[dict[str, Any]],
        storyboard: list[dict[str, Any]],
        camera_direction: dict[str, Any],
        metadata: dict[str, Any],
        warnings: list[str],
        errors: list[str],
        validation_result: dict[str, Any],
        request_contract: dict[str, Any],
        response_contract: dict[str, Any],
        scene_contract: dict[str, Any],
        storyboard_contract: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a stable engine response."""

        return {
            "success": success,
            "video_type": video_type,
            "duration": duration,
            "platform": platform,
            "hook": hook,
            "script": script,
            "voiceover": voiceover,
            "cta": cta,
            "music_mood": music_mood,
            "scene_sequence": scene_sequence,
            "storyboard": storyboard,
            "camera_direction": camera_direction,
            "metadata": metadata,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "validation": validation_result,
            "request_contract": request_contract,
            "response_contract": response_contract,
            "scene_contract": scene_contract,
            "storyboard_contract": storyboard_contract,
        }

    def _normalize_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Normalize request values and apply safe defaults."""

        normalized = dict(request or {})
        normalized["brand"] = normalize_key(str(normalized.get("brand", "")))
        normalized["platform"] = normalize_key(str(normalized.get("platform", "")))
        normalized["content_type"] = normalize_key(str(normalized.get("content_type", "video_script")))
        normalized["campaign_type"] = normalize_key(str(normalized.get("campaign_type", "")))
        normalized["objective"] = str(normalized.get("objective", "")).strip()
        normalized["audience"] = str(normalized.get("audience", "")).strip()
        normalized["location"] = normalize_key(str(normalized.get("location", "")))
        normalized["property_type"] = normalize_key(str(normalized.get("property_type", "")))
        normalized["video_type"] = normalize_video_type(str(normalized.get("video_type") or normalized.get("content_type") or "instagram_reel"))
        if normalized["video_type"] not in get_supported_video_types():
            normalized["video_type"] = "instagram_reel"
        normalized["duration"] = normalize_duration(str(normalized.get("duration") or "30s"))
        if normalized["duration"] not in get_supported_durations():
            normalized["duration"] = "30s"
        normalized["creative_direction"] = str(normalized.get("creative_direction", "")).strip()
        normalized["visual_style"] = str(normalized.get("visual_style", "")).strip()
        normalized["tone"] = str(normalized.get("tone", "")).strip()
        normalized["extra_notes"] = str(normalized.get("extra_notes", "")).strip()
        normalized["enable_storyboard_generation"] = bool(normalized.get("enable_storyboard_generation", True))
        return normalized

    def _build_script_text(self, request: dict[str, Any], hook: str, scenes: list[dict[str, Any]], voiceover: str, cta: str, music_mood: str) -> str:
        """Build the core script text."""

        sections = [
            f"Hook: {hook}",
            f"Voiceover: {voiceover}",
            f"Music Mood: {music_mood}",
        ]
        for scene in scenes:
            sections.append(f"Scene {scene.get('scene_number')}: {scene.get('visual', '')} | {scene.get('voiceover', '')}")
        sections.append(f"CTA: {cta}")
        if request.get("creative_direction"):
            sections.append(f"Creative Direction: {request.get('creative_direction')}")
        if request.get("extra_notes"):
            sections.append(f"Notes: {request.get('extra_notes')}")
        return "\n".join(part for part in sections if part).strip()

    def _build_hook(self, request: dict[str, Any], template: dict[str, Any]) -> str:
        """Build the opening hook."""

        video_type = normalize_key(str(request.get("video_type", "")))
        if video_type in {"instagram_reel", "tiktok_video", "youtube_short"}:
            return "A quick look at why this Mallorca property stands out."
        if template.get("name") == "relocation_video":
            return "Thinking about relocating to Mallorca?"
        if template.get("name") == "neighborhood_spotlight":
            return "Here is what makes this neighborhood feel special."
        if template.get("name") == "reform_opportunity_video":
            return "This home has clear reform potential."
        return "A calm, premium look at a Mallorca property."

    def _scene_count_for_duration(self, duration: str, template_count: int) -> int:
        mapping = {"15s": 3, "30s": 5, "45s": 5, "60s": 6, "90s": 7}
        return max(3, mapping.get(duration, template_count or 5))

    def _normalize_distribution(self, scene_count: int) -> list[float]:
        if scene_count <= 0:
            return []
        return [round(1.0 / scene_count, 3) for _ in range(scene_count)]

    def _scene_seconds(self, duration: str, weight: float, scene_count: int) -> str:
        total_map = {"15s": 15, "30s": 30, "45s": 45, "60s": 60, "90s": 90}
        total = total_map.get(duration, 30)
        seconds = max(2, round(total * weight))
        if scene_count and seconds * scene_count < total:
            seconds += 1
        return f"{seconds}s"

    def _visual_roles(self, template: dict[str, Any], scene_count: int) -> list[str]:
        roles = list(template.get("visual_roles", []))
        if len(roles) < scene_count:
            roles.extend(["scene"] * (scene_count - len(roles)))
        return roles[:scene_count]

    def _scene_visual(self, request: dict[str, Any], template: dict[str, Any], purpose: str, index: int) -> str:
        direction = str(request.get("creative_direction") or request.get("extra_notes") or "").strip()
        location = str(request.get("location") or "").strip()
        property_type = str(request.get("property_type") or "").strip()
        parts = [purpose]
        if index == 0 and direction:
            parts.append(direction)
        if location:
            parts.append(f"Grounded in {location}")
        if property_type:
            parts.append(f"Reflect the {property_type}")
        parts.append("realistic Mediterranean lifestyle visuals")
        return ", ".join(part for part in parts if part)

    def _scene_camera_motion(self, request: dict[str, Any], template: dict[str, Any], index: int) -> str:
        platform = normalize_key(str(request.get("platform", "")))
        if platform in {"instagram", "tiktok"}:
            motions = ["slow reveal", "gentle push-in", "steady glide", "subtle pan", "clean closing frame"]
        else:
            motions = ["steady reveal", "slow move", "balanced framing", "controlled pan", "closing hold"]
        return motions[min(index, len(motions) - 1)]

    def _scene_voiceover(self, request: dict[str, Any], purpose: str, index: int, scene_count: int) -> str:
        location = str(request.get("location") or "").strip()
        property_type = str(request.get("property_type") or "").strip()
        objective = str(request.get("objective") or "").strip()
        if index == 0:
            return self._build_hook(request, self.select_scene_template(request))
        if "CTA" in purpose:
            return self.build_cta(request)
        segments = [purpose]
        if location:
            segments.append(f"in {location}")
        if property_type:
            segments.append(f"for {property_type.replace('_', ' ')} living")
        if objective:
            segments.append(f"aligned with {objective.replace('_', ' ')}")
        return " ".join(segments).strip()

    def _scene_on_screen_text(self, request: dict[str, Any], purpose: str, index: int) -> str:
        if index == 0:
            return "Discover more"
        if "CTA" in purpose:
            return self.build_cta(request)
        return purpose

    def _shot_type_for_scene(self, request: dict[str, Any], scene: dict[str, Any]) -> str:
        purpose = str(scene.get("purpose", "")).lower()
        if "hook" in purpose:
            return "hero"
        if "cta" in purpose:
            return "closing"
        if normalize_key(str(request.get("platform", ""))) in {"instagram", "tiktok"}:
            return "vertical detail"
        return "establishing"

    def _lighting_for_request(self, request: dict[str, Any]) -> str:
        style = str(request.get("visual_style") or "").lower()
        if "sunset" in style:
            return "golden hour"
        if "interior" in style:
            return "soft natural interior light"
        return "natural daylight"

    def _build_metadata(self, request: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
        """Build safe metadata for observability and reporting."""

        scene_count = int(template.get("scene_count", 5))
        return {
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": request.get("content_type", "video_script"),
            "campaign_type": request.get("campaign_type", ""),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "video_type": request.get("video_type", ""),
            "duration": request.get("duration", ""),
            "visual_style": request.get("visual_style", ""),
            "tone": request.get("tone", ""),
            "scene_count": scene_count,
            "template_name": template.get("name", ""),
            "storyboard_enabled": bool(request.get("enable_storyboard_generation", True)),
        }

    def _scene_contract(self) -> dict[str, Any]:
        return {
            "fields": ["scene_number", "duration", "visual", "camera_motion", "voiceover", "on_screen_text", "purpose"],
            "description": "Per-scene storyboard planning contract.",
        }

    def _storyboard_contract(self) -> dict[str, Any]:
        return {
            "fields": ["frame_number", "scene_number", "shot_type", "visual_description", "camera_direction", "lighting", "motion", "on_screen_text", "voiceover"],
            "description": "Storyboard frame planning contract.",
        }


if __name__ == "__main__":
    engine = VideoScriptEngine()
    sample = {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "video_script",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "video_type": "instagram_reel",
        "duration": "30s",
        "creative_direction": "Rustic exterior with modern comfort inside, close to Manacor and beaches.",
        "visual_style": "mediterranean_lifestyle",
        "tone": "premium but approachable",
        "extra_notes": "Do not invent property facts.",
    }
    print(engine.validate_request(sample))
    print(engine.select_scene_template(sample))
    result = engine.generate_video_script(sample)
    print(result)
