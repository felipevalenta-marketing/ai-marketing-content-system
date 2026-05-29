"""Team contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TeamContract:
    team_id: str
    organization_id: str
    name: str
    slug: str
    status: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "team_id": self.team_id,
            "organization_id": self.organization_id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

