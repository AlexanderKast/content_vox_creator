"""Shared animation-timing constants.

These mirror the `delay` values BoxVideo.tsx actually uses for Cutout and
Underline entrances. factory.rhythm (dead-zone detection) and factory.script
(SFX cue placement) both need to agree with the real render on where things
land — this is the one place that number lives, instead of three.

Coupling note: if BoxVideo.tsx's delays change, update this file too. There
is no runtime instrumentation tying this to the actual render; it is static
analysis and cue generation done in Python against a manifest.
"""

from __future__ import annotations

UNDERLINE_DELAY_FRAMES = 10  # BoxVideo.tsx: <Underline delay={10} />

# BoxVideo.tsx (2026-07-18, "mas dinamico... mas imagenes de apoyo"): a
# beat's cutout entrances spread across this fraction of the beat's OWN
# duration instead of clustering in the first few frames — asset 0 lands
# with the cut, later ones land partway through. Replaced the old flat
# ASSET_STAGGER_FRAMES=4 (which both this and BoxVideo.tsx used) because a
# fixed frame gap is invisible on a multi-second beat; a duration-relative
# spread keeps producing new visual events as the beat plays.
ASSET_SPREAD_FRACTION = 0.65


def asset_entrance_frame(index: int, count: int, beat_duration_frames: int) -> int:
    """Mirrors BoxVideo.tsx's per-asset Cutout `delay` exactly — same formula,
    same rounding — so factory.rhythm (dead-zone detection) and
    factory.script (SFX cue placement) both agree with what the real render
    actually does. `count` must be the SAME beat.assets length used on the
    TSX side (i.e. call this once per asset in that beat, not globally)."""
    if count <= 0:
        return 0
    return round((index / count) * beat_duration_frames * ASSET_SPREAD_FRACTION)
