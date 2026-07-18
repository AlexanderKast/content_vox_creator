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

ASSET_STAGGER_FRAMES = 4     # BoxVideo.tsx: delay={assetIndex * 4}
UNDERLINE_DELAY_FRAMES = 10  # BoxVideo.tsx: <Underline delay={10} />
