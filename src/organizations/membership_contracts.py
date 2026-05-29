"""Membership contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MembershipContract:
    membership_id: str
    organization_id: str
    team_id: str
    user_id: str
    role: str
    status: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "membership_id": self.membership_id,
            "organization_id": self.organization_id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

