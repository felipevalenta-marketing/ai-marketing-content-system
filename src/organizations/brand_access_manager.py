"""Brand access management for organizations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

from src.brands.brand_manager import BrandManager
from src.reporting.report_metrics import safe_dict, safe_text, utc_now_iso

from .organization_storage import ensure_organizations_root, load_json, save_json


ALLOWED_ACCESS_LEVELS = ("owner", "manage", "use", "view")


class BrandAccessManager:
    def __init__(self, storage_root: str = "data/organizations", brand_manager: BrandManager | None = None, organization_manager: Any | None = None, logger: Any | None = None) -> None:
        self.storage_root = ensure_organizations_root(storage_root)
        self.file_path = self.storage_root / "brand_access.json"
        self.brand_manager = brand_manager or BrandManager()
        self.organization_manager = organization_manager
        self.logger = logger

    def grant_brand_access(self, organization_id: str, brand_id: str, access_level: str = "use", actor: dict[str, Any] | None = None) -> dict[str, Any]:
        if access_level not in ALLOWED_ACCESS_LEVELS:
            return {"success": False, "data": {}, "warnings": [], "errors": ["Invalid brand access level."], "metadata": {}}
        if not self._organization_exists(organization_id):
            return {"success": False, "data": {}, "warnings": [], "errors": ["Organization not found."], "metadata": {}}
        if not self.brand_manager.is_brand_available(brand_id):
            return {"success": False, "data": {}, "warnings": [], "errors": ["Brand not found."], "metadata": {}}
        store = self._load()
        access_list = store.setdefault("brand_access", [])
        existing = self._find(access_list, organization_id, brand_id)
        now = utc_now_iso()
        if existing:
            existing.update({"access_level": access_level, "updated_at": now, "metadata": {**safe_dict(existing.get("metadata")), "updated_by": safe_text((actor or {}).get("user_id"), limit=120)}})
        else:
            access_list.append({"brand_access_id": f"bra_{uuid.uuid4().hex}", "organization_id": safe_text(organization_id, limit=120), "brand_id": safe_text(brand_id, limit=120), "access_level": access_level, "created_at": now, "updated_at": now, "metadata": {"created_by": safe_text((actor or {}).get("user_id"), limit=120)}})
        save_json(self.file_path, store)
        return {"success": True, "data": self._find(access_list, organization_id, brand_id) or {}, "warnings": [], "errors": [], "metadata": {"organization_id": organization_id, "brand_id": brand_id}}

    def revoke_brand_access(self, organization_id: str, brand_id: str, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        store = self._load()
        access_list = store.setdefault("brand_access", [])
        before = len(access_list)
        access_list[:] = [item for item in access_list if not self._match(item, organization_id, brand_id)]
        save_json(self.file_path, store)
        return {"success": True, "data": {"removed": before - len(access_list)}, "warnings": [], "errors": [], "metadata": {"organization_id": organization_id, "brand_id": brand_id}}

    def list_organization_brands(self, organization_id: str) -> dict[str, Any]:
        store = self._load()
        brands = [dict(item) for item in store.get("brand_access", []) if str(item.get("organization_id", "")).strip() == str(organization_id).strip()]
        return {"success": True, "data": {"brand_access": brands, "count": len(brands)}, "warnings": [], "errors": [], "metadata": {"organization_id": organization_id}}

    def list_brand_organizations(self, brand_id: str) -> dict[str, Any]:
        store = self._load()
        orgs = [dict(item) for item in store.get("brand_access", []) if str(item.get("brand_id", "")).strip() == str(brand_id).strip()]
        return {"success": True, "data": {"brand_access": orgs, "count": len(orgs)}, "warnings": [], "errors": [], "metadata": {"brand_id": brand_id}}

    def can_access_brand(self, organization_id: str, brand_id: str, access_level: str = "use") -> bool:
        if not self._organization_exists(organization_id) or not self.brand_manager.is_brand_available(brand_id):
            return False
        store = self._load()
        order = {level: index for index, level in enumerate(ALLOWED_ACCESS_LEVELS)}
        target = order.get(access_level, order["use"])
        for item in store.get("brand_access", []):
            if self._match(item, organization_id, brand_id) and order.get(str(item.get("access_level", "view")), -1) <= target:
                return True
        return False

    def _load(self) -> dict[str, Any]:
        return load_json(self.file_path, {"brand_access": []})

    def _find(self, items: list[dict[str, Any]], organization_id: str, brand_id: str) -> dict[str, Any] | None:
        for item in items:
            if self._match(item, organization_id, brand_id):
                return item
        return None

    def _match(self, item: dict[str, Any], organization_id: str, brand_id: str) -> bool:
        return str(item.get("organization_id", "")).strip() == str(organization_id).strip() and str(item.get("brand_id", "")).strip() == str(brand_id).strip()

    def _organization_exists(self, organization_id: str) -> bool:
        if self.organization_manager is None:
            return True
        getter = getattr(self.organization_manager, "get_organization", None)
        if callable(getter):
            return bool(getter(organization_id))
        return True
