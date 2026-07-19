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
    SCENE = "scene"          # Nano Banana PRO — isolated-on-green complex
                             # composition / text-in-image asset (NOT the
                             # full-frame beat backdrop; that's BACKDROP_MODEL).
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
    # A named, real public figure (politician, official, ...) appearing in the
    # asset. Requires is_real_entity=True (validated in script.assert_valid) —
    # a public figure is ALWAYS a real scraped photo, never generated. Once
    # set, the pipeline black-bars the eyes (factory.redact) before caching
    # and Remotion places the cutout at its smallest, most distant scale
    # (never a close-up). description must never contain the person's name —
    # describe by role/context instead; see content-vox-news SKILL.md.
    is_public_figure: bool = False


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


# ---------------------------------------------------------------------------
# Visual templates. A template is a full look — cutout, scene, character AND
# backdrop all pull from the SAME template so a carrusel never mixes two
# unrelated palettes (that was the 2026-07-18 bug: cutouts were orange-on-green,
# backdrops were hardcoded gold-on-black, with no shared name between them and
# no way to pick one on purpose).
#
# Selected per script via the JSON brief's "template" field, falling back to
# the brand's own default (brand.json "template"), falling back to
# DEFAULT_TEMPLATE. See factory.pipeline.Factory.build for the resolution order.
DEFAULT_TEMPLATE = "engraving-orange"

# Vintage-engraving editorial look (matches the reference reel): black ink
# line art + halftone shading + a few orange-red accents, cut out on green.
# After chroma it drops onto the cream paper and reads like a woodcut print.
CUTOUT_PROMPTS: dict[str, str] = {
    "engraving-orange": (
        "{description}, vintage engraving woodcut illustration, bold black ink line art, "
        "cross-hatching and halftone shading, minimal warm orange-red (#E8451F) accents, "
        "high contrast, retro editorial newspaper print aesthetic, "
        "isolated on pure green screen background #00FF00, no shadow on background, centered"
    ),
    "dark-luxury-gold": (
        "{description}, vintage engraving illustration, bold black ink line art, "
        "cross-hatching and halftone shading, luminous gold (#FFC61A) accents, "
        "high-contrast premium AI-luxury editorial aesthetic, "
        "isolated on pure green screen background #00FF00, no shadow on background, centered"
    ),
    "minimal-flat": (
        "{description}, minimal flat vector illustration, clean geometric shapes, thick "
        "outlines, two-tone limited palette, modern editorial icon style, no gradients, "
        "no texture, isolated on pure green screen background #00FF00, "
        "no shadow on background, centered"
    ),
    "vox-paper": (
        "{description}, highly detailed intricate illustration, sharp crisp linework, "
        "black-and-white halftone cutout in a documentary-collage explainer style, "
        "rich fine cross-hatching and stippling for depth and texture, rough white paper "
        "keyline around the silhouette, offset Hot Red (#B62E1F) accent stroke behind it, "
        "print grain and halftone dot texture, no color in the subject itself, no "
        "gradients, no glossy 3D, no photorealistic color, no blurry or low-detail areas, "
        "isolated on pure green screen background #00FF00, no shadow on background, centered"
    ),
}

SCENE_PROMPTS: dict[str, str] = {
    "engraving-orange": (
        "{description}. Vintage engraving woodcut editorial still, black ink line art with "
        "halftone shading and minimal orange-red (#E8451F) accents, retro newspaper print, "
        "high contrast, generous negative space. "
        "Isolated on pure green screen background #00FF00, no shadow on background."
    ),
    "dark-luxury-gold": (
        "{description}. Vintage engraving editorial still, black ink line art with halftone "
        "shading and luminous gold (#FFC61A) accents, premium AI-luxury high-contrast look, "
        "generous negative space. "
        "Isolated on pure green screen background #00FF00, no shadow on background."
    ),
    "minimal-flat": (
        "{description}. Minimal flat vector illustration, clean geometric composition, thick "
        "outlines, two-tone limited palette, generous negative space, no gradients, no texture. "
        "Isolated on pure green screen background #00FF00, no shadow on background."
    ),
    "vox-paper": (
        "{description}. Black-and-white halftone cutout in a documentary-collage explainer "
        "style, rough white paper keyline, offset Hot Red (#B62E1F) accent stroke behind it, "
        "print grain and halftone dot texture, generous negative space, no color in the "
        "subject itself, no gradients, no glossy 3D. "
        "Isolated on pure green screen background #00FF00, no shadow on background."
    ),
}

CHARACTER_PROMPTS: dict[str, str] = {
    name: (
        "CRITICAL: keep the character 100% consistent with the reference image — "
        "same proportions, same face, same clothing style. {description}. "
        "Isolated on pure green screen background #00FF00, no shadow on background."
    )
    for name in ("engraving-orange", "dark-luxury-gold", "minimal-flat", "vox-paper")
}

# BACKDROP — full-frame themed background (NOT isolated on green — it fills the
# whole frame as the beat's "world": a bakery, a vintage map, a stadium). This
# is a DIFFERENT concept from Tier.SCENE above:
#   Tier.SCENE  = an isolated-on-green complex composition/text asset, routed
#                 to nano-banana-pro ($0.14), keyed and composited like a cutout.
#   BACKDROP    = a full-bleed background image, NOT keyed, text sits over it,
#                 produced by pipeline.BACKDROP_MODEL (nano-banana-2-fast $0.045).
# The manifest field `beat.scene` feeds the BACKDROP path, not Tier.SCENE.
# Each entry below matches its CUTOUT/SCENE counterpart above by name, so a
# carrusel built on one template is visually consistent front to back.
BACKDROP_PROMPTS: dict[str, str] = {
    "engraving-orange": (
        "{description}. Full-frame vertical 9:16 illustrated scene, vintage engraving and "
        "woodcut style on a WARM CREAM paper background, black ink line work with warm "
        "orange-red (#E8451F) accents, fine halftone shading, retro editorial newspaper "
        "poster aesthetic, filling the entire frame edge to edge with no blank margins. "
        "Pure imagery, no typography."
    ),
    "dark-luxury-gold": (
        "{description}. Full-frame vertical 9:16 illustrated scene, vintage engraving "
        "and woodcut style on an ELEGANT DARK near-black background, luminous GOLD and "
        "warm amber line work and highlights, fine halftone shading, subtle green accents, "
        "ornate gold decorative border framing the edges, premium dark AI-luxury poster "
        "aesthetic, filling the entire frame edge to edge with no blank margins. Pure "
        "imagery, no typography."
    ),
    "minimal-flat": (
        "{description}. Full-frame vertical 9:16 illustrated scene, minimal flat vector "
        "illustration, clean geometric shapes, thick outlines, two-tone limited palette, "
        "generous negative space, no gradients, no texture, modern editorial poster "
        "aesthetic, filling the entire frame edge to edge with no blank margins. Pure "
        "imagery, no typography."
    ),
    "vox-paper": (
        "{description}. Full-frame vertical 9:16 'the stage' — a muted archival tan "
        "(#C9BB9C) map/paper-texture field, evenly toned, pre-lit, print grain and subtle "
        "halftone dot texture, matte finish, no gloss, no lens flares, desaturated "
        "documentary-collage explainer aesthetic with at most one Hot Red (#B62E1F) accent "
        "stroke or underline, filling the entire frame edge to edge with no blank margins. "
        "Pure imagery, no typography."
    ),
}

TEMPLATE_NAMES: tuple[str, ...] = tuple(CUTOUT_PROMPTS)


def build_prompt(asset: Asset, tier: Tier, template: str = DEFAULT_TEMPLATE) -> str:
    families = {
        Tier.CUTOUT: CUTOUT_PROMPTS,
        Tier.SCENE: SCENE_PROMPTS,
        Tier.CHARACTER: CHARACTER_PROMPTS,
    }
    if tier not in families:
        raise ValueError(f"Tier {tier} does not use generated prompts.")
    family = families[tier]
    if template not in family:
        raise ValueError(f"Plantilla '{template}' no existe. Disponibles: {', '.join(TEMPLATE_NAMES)}")
    return family[template].format(description=asset.description)


def backdrop_prompt(description: str, template: str = DEFAULT_TEMPLATE) -> str:
    if template not in BACKDROP_PROMPTS:
        raise ValueError(f"Plantilla '{template}' no existe. Disponibles: {', '.join(TEMPLATE_NAMES)}")
    return BACKDROP_PROMPTS[template].format(description=description)
