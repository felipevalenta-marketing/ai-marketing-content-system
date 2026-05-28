"""Descriptive color palette guidance for creative direction."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


COLOR_PALETTES: dict[str, dict[str, Any]] = {
    "mediterranean_neutrals": {
        "name": "mediterranean_neutrals",
        "primary_colors": ["warm white", "sand", "stone"],
        "secondary_colors": ["soft beige", "muted taupe", "light clay"],
        "accent_colors": ["olive", "terracotta"],
        "avoid_colors": ["neon", "over-saturated blue", "harsh magenta"],
        "usage_notes": "Best for premium but approachable Mallorca real estate visuals.",
    },
    "warm_stone_and_sand": {
        "name": "warm_stone_and_sand",
        "primary_colors": ["stone", "sand", "warm ivory"],
        "secondary_colors": ["soft caramel", "light oak"],
        "accent_colors": ["sage", "soft rust"],
        "avoid_colors": ["cold cyan", "electric tones"],
        "usage_notes": "Great for relocation warmth and grounded luxury.",
    },
    "coastal_blue_and_white": {
        "name": "coastal_blue_and_white",
        "primary_colors": ["white", "sea mist", "pale blue"],
        "secondary_colors": ["sand", "soft grey"],
        "accent_colors": ["navy", "coastal teal"],
        "avoid_colors": ["dark muddy brown", "over-saturated turquoise"],
        "usage_notes": "Use for coastal and lifestyle-led creative direction.",
    },
    "palma_editorial": {
        "name": "palma_editorial",
        "primary_colors": ["cool white", "soft grey", "graphite"],
        "secondary_colors": ["stone", "smoke blue"],
        "accent_colors": ["black", "brass"],
        "avoid_colors": ["bright candy colors"],
        "usage_notes": "Use for urban, editorial, and architecture-forward content.",
    },
    "rustic_earth_tones": {
        "name": "rustic_earth_tones",
        "primary_colors": ["earth brown", "warm beige", "olive"],
        "secondary_colors": ["stone", "oak", "soft clay"],
        "accent_colors": ["rust", "sage"],
        "avoid_colors": ["plastic white", "high-contrast neon"],
        "usage_notes": "Best for reform and rustic-modern balance.",
    },
    "premium_soft_contrast": {
        "name": "premium_soft_contrast",
        "primary_colors": ["soft ivory", "light grey", "warm taupe"],
        "secondary_colors": ["champagne", "stone", "smoke"],
        "accent_colors": ["bronze", "deep olive"],
        "avoid_colors": ["hard black-white contrast", "over-bright highlights"],
        "usage_notes": "Balanced premium tones without overstatement.",
    },
    "natural_light_palette": {
        "name": "natural_light_palette",
        "primary_colors": ["sunlit white", "sand", "pale stone"],
        "secondary_colors": ["soft green", "light timber"],
        "accent_colors": ["terracotta", "coastal grey"],
        "avoid_colors": ["harsh saturation", "fake HDR"],
        "usage_notes": "Use for natural light, relaxed lifestyle visuals.",
    },
}


def get_color_palette(name: str) -> dict[str, Any]:
    """Return a color palette profile."""

    key = str(name or "").strip().lower().replace(" ", "_")
    return deepcopy(COLOR_PALETTES.get(key, COLOR_PALETTES["mediterranean_neutrals"]))


def list_color_palettes() -> list[str]:
    """Return palette names."""

    return sorted(COLOR_PALETTES.keys())
