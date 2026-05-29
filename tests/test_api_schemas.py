from __future__ import annotations

from src.api.schemas import ApiResponse, GenerateRequest, WorkflowRequest


def test_api_schema_list_fields_coerce_from_strings() -> None:
    request = GenerateRequest(platforms="instagram, facebook", assets="image_prompt, video_prompt")
    workflow = WorkflowRequest(platforms="instagram,linkedin", assets=["image_prompt", "social_post"])

    assert request.platforms == ["instagram", "facebook"]
    assert request.assets == ["image_prompt", "video_prompt"]
    assert workflow.platforms == ["instagram", "linkedin"]
    assert workflow.assets == ["image_prompt", "social_post"]


def test_api_response_model_has_safe_defaults() -> None:
    response = ApiResponse(success=True)

    assert response.success is True
    assert response.data is None
    assert response.warnings == []
    assert response.errors == []
