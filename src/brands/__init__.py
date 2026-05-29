"""Multi-brand management layer."""

from .brand_manager import BrandManager
from .brand_health import build_brand_health
from .brand_registry import build_brand_registry, discover_brands, is_valid_brand_id, normalize_brand_id
from .brand_defaults import get_brand_defaults, list_brand_defaults

__all__ = [
    "BrandManager",
    "build_brand_registry",
    "discover_brands",
    "build_brand_health",
    "get_brand_defaults",
    "is_valid_brand_id",
    "list_brand_defaults",
    "normalize_brand_id",
]
