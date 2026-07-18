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
#
# CUTOUT and SCENE bumped one notch above the cheapest option 2026-07-17, on
# request: quality matters here, not just cost. Still routed by tier — this
# is "spend a bit more per asset," not "always use the premium model."
#   CUTOUT: z-image ($0.005) -> flux-2-klein-4b ($0.008) — better prompt
#     adherence on cutouts, ~60% more per asset.
#   SCENE:  nano-banana-2-fast ($0.045) -> nano-banana-pro ($0.14) — a
#     genuinely different, higher-quality model line (Gemini 3.0 Pro Image),
#     not a flag on the fast one. ~3x per asset — this is the real cost
#     driver of the step-up, budget accordingly.
DEFAULT_MODELS: dict[Tier, str] = {
    Tier.CHARACTER: "magnific/character",
    Tier.SCENE: "wavespeed/nano-banana-pro",
    Tier.CUTOUT: "wavespeed/flux-2-klein-4b",
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


# Vintage-engraving editorial look (matches the reference reel): black ink
# line art + halftone shading + a few orange-red accents, cut out on green.
# After chroma it drops onto the cream paper and reads like a woodcut print.
CUTOUT_PROMPT = (
    "{description}, vintage engraving woodcut illustration, bold black ink line art, "
    "cross-hatching and halftone shading, minimal warm orange-red (#E8451F) accents, "
    "high contrast, retro editorial newspaper print aesthetic, "
    "isolated on pure green screen background #00FF00, no shadow on background, centered"
)

SCENE_PROMPT = (
    "{description}. Vintage engraving woodcut editorial still, black ink line art with "
    "halftone shading and minimal orange-red (#E8451F) accents, retro newspaper print, "
    "high contrast, generous negative space. "
    "Isolated on pure green screen background #00FF00, no shadow on background."
)

CHARACTER_PROMPT = (
    "CRITICAL: keep the character 100% consistent with the reference image — "
    "same proportions, same face, same clothing style. {description}. "
    "Isolated on pure green screen background #00FF00, no shadow on background."
)

# Full-frame themed background scene (NOT isolated on green — it fills the
# whole frame as the beat's "world": a bakery, a vintage map, a stadium).
# Cream/warm palette + engraving so it matches the editorial look, with a big
# clear area in the center-lower third for the title + subtitle to sit on.
SCENE_FULL_PROMPT = (
    "{description}. Full-frame vertical 9:16 illustrated scene, vintage engraving "
    "and woodcut style on an ELEGANT DARK near-black background, luminous GOLD and "
    "warm amber line work and highlights, fine halftone shading, subtle green accents, "
    "ornate gold decorative border framing the edges, premium dark AI-luxury poster "
    "aesthetic. Keep the LOWER THIRD dark and empty so large light text can sit over it. "
    "ABSOLUTELY NO TEXT: no words, no letters, no captions, no titles, no labels, "
    "no signage, no writing, no typography anywhere in the image — imagery only."
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
