"""The four-tier image router.

This file is the strategy. Everything else is plumbing.

The rule is economic before it is aesthetic: each visual job goes to the cheapest
thing that can do it well. A recurring character needs consistency (expensive and
worth it). A cutout of a coffee cup needs an outline (cheap and fine). A photo of
a real person must not be invented at all.

Reference systems send everything to one premium model and pay 10x for no gain.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Tier(str, Enum):
    CHARACTER = "character"  # Magnific — consistency across scenes
    SCENE = "scene"          # Nano Banana — prompt adherence, complex composition
    CUTOUT = "cutout"        # Flux / Z-Image — green-screen stickers
    PHOTO = "photo"          # Apify — real things that exist in the world


@dataclass(frozen=True)
class Asset:
    """One visual the script asks for."""

    id: str
    description: str
    is_real_entity: bool = False   # a named person, a logo, a brand, a screenshot
    is_recurring_character: bool = False  # Alexander, Kiro
    needs_text_in_image: bool = False
    is_complex_composition: bool = False


# Which model serves each tier. Swap here, not in twenty call sites.
# Kie is deliberately absent as a default: it is a reseller with a documented
# ~94% success rate and no direct partnership with model owners. It stays
# available in providers/ as a fallback, not as the road we build on.
DEFAULT_MODELS: dict[Tier, str] = {
    Tier.CHARACTER: "magnific/character",
    Tier.SCENE: "wavespeed/nano-banana-2-fast",
    Tier.CUTOUT: "wavespeed/z-image",
    Tier.PHOTO: "apify/google-images",
}


def route(asset: Asset) -> Tier:
    """Decide which tier an asset belongs to. Order matters."""
    if asset.is_real_entity:
        return Tier.PHOTO
    if asset.is_recurring_character:
        return Tier.CHARACTER
    if asset.needs_text_in_image or asset.is_complex_composition:
        return Tier.SCENE
    return Tier.CUTOUT


def plan(assets: list[Asset]) -> dict[Tier, list[Asset]]:
    """Group a script's assets by tier. This is what gets priced before spending."""
    grouped: dict[Tier, list[Asset]] = {tier: [] for tier in Tier}
    for asset in assets:
        grouped[route(asset)].append(asset)
    return grouped


CUTOUT_PROMPT = (
    "{description}, cutout illustration style, bold outlines, high contrast, "
    "isolated on pure green screen background #00FF00, no shadow on background, "
    "centered, editorial documentary aesthetic"
)

SCENE_PROMPT = (
    "{description}. Editorial documentary motion-graphics still. "
    "High contrast, oversized type friendly composition, generous negative space. "
    "Isolated on pure green screen background #00FF00, no shadow on background."
)

CHARACTER_PROMPT = (
    "CRITICAL: keep the character 100% consistent with the reference image — "
    "same proportions, same face, same clothing style. {description}. "
    "Isolated on pure green screen background #00FF00, no shadow on background."
)


def build_prompt(asset: Asset, tier: Tier) -> str:
    templates = {
        Tier.CUTOUT: CUTOUT_PROMPT,
        Tier.SCENE: SCENE_PROMPT,
        Tier.CHARACTER: CHARACTER_PROMPT,
    }
    if tier not in templates:
        raise ValueError(f"Tier {tier} does not use generated prompts.")
    return templates[tier].format(description=asset.description)
