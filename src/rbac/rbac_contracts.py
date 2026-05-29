"""RBAC contracts."""

from __future__ import annotations

from typing import Any


ROLE_CONTRACT: dict[str, Any] = {"role": "", "label": "", "description": "", "permissions": [], "level": 0}
PERMISSION_CONTRACT: dict[str, Any] = {"permission": "", "domain": "", "label": "", "description": ""}
ACCESS_SUMMARY_CONTRACT: dict[str, Any] = {"role": "", "permissions": [], "access": {}}
PERMISSION_CHECK_CONTRACT: dict[str, Any] = {"allowed": False, "permission": "", "role": "", "reason": "", "warnings": [], "errors": []}
ROLE_ASSIGNMENT_CONTRACT: dict[str, Any] = {"success": False, "user": {}, "warnings": [], "errors": [], "metadata": {}}
API_RESPONSE_CONTRACT: dict[str, Any] = {"success": True, "data": {}, "warnings": [], "errors": [], "metadata": {}}

