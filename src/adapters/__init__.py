"""Multi-platform content adaptation layer."""

from src.adapters.adaptation_result import AdaptationResult, build_adaptation_failure, build_adaptation_success
from src.adapters.platform_adapter import PlatformAdapter
from src.adapters.platform_constraints import get_platform_constraints, list_supported_platforms
from src.adapters.platform_contracts import get_platform_contract

__all__ = [
    "AdaptationResult",
    "PlatformAdapter",
    "build_adaptation_failure",
    "build_adaptation_success",
    "get_platform_constraints",
    "get_platform_contract",
    "list_supported_platforms",
]
