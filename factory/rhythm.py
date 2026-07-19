"""Rhythm validator — makes "nothing static past ~1.2s" measurable.

Until now that rule was a comment in BoxVideo.tsx. This walks the manifest
and checks it for real: a "visual event" is a beat's text landing, an asset
entering, or the underline drawing — the same three things BoxVideo.tsx
actually animates. If two consecutive events are more than 1.2s apart, that
stretch of the video is dead.

This is advisory only (criterion, not law — a formula's own duration bounds
can legitimately force a longer breath in a spot). `pipeline.build()` prints
the report but never fails the build over it.

Coupling note: UNDERLINE_DELAY_FRAMES and asset_entrance_frame() (factory.timing)
mirror the `delay` values BoxVideo.tsx actually uses for Underline/Cutout. If
those change in the TSX, update factory.timing too — there is no runtime
instrumentation tying this to the real render, this is static analysis of
the manifest.
"""

from __future__ import annotations

from .timing import UNDERLINE_DELAY_FRAMES, asset_entrance_frame

MAX_GAP_SECONDS = 1.2


def compute_visual_events(manifest: dict) -> list[int]:
    """Frame numbers (global) where something visual changes."""
    fps = manifest["fps"]
    events: list[int] = []
    for beat in manifest["beats"]:
        start = beat["sequenceFrom"]
        events.append(start)  # text change — every beat changes the caption
        beat_duration_frames = round(beat["seconds"] * fps)
        assets = beat["assets"]
        for i, _asset in enumerate(assets):
            events.append(start + asset_entrance_frame(i, len(assets), beat_duration_frames))
        events.append(start + UNDERLINE_DELAY_FRAMES)
    return sorted(set(events))


def find_dead_zones(
    manifest: dict, max_gap_seconds: float = MAX_GAP_SECONDS
) -> list[tuple[float, float]]:
    """Return (start_seconds, end_seconds) for every gap between consecutive
    visual events that exceeds max_gap_seconds. Carrusel is exempt — each
    slide is its own autonomous, independently-paced render, not a
    continuous edited timeline."""
    if manifest.get("mode") != "video" or not manifest.get("beats"):
        return []

    fps = manifest["fps"]
    total_frames = sum(round(beat["seconds"] * fps) for beat in manifest["beats"])
    events = [0, *compute_visual_events(manifest), total_frames]
    max_gap_frames = max_gap_seconds * fps

    dead_zones = []
    for start_frame, end_frame in zip(events, events[1:]):
        if end_frame - start_frame > max_gap_frames:
            dead_zones.append((start_frame / fps, end_frame / fps))
    return dead_zones


def report(manifest: dict, max_gap_seconds: float = MAX_GAP_SECONDS) -> str | None:
    """Human-readable warning, or None if the rhythm holds throughout."""
    zones = find_dead_zones(manifest, max_gap_seconds)
    if not zones:
        return None

    lines = [
        f"RITMO: {len(zones)} tramo(s) sin cambio visual por mas de {max_gap_seconds}s:"
    ]
    for start, end in zones:
        midpoint = (start + end) / 2
        lines.append(
            f"  - {start:.2f}s - {end:.2f}s ({end - start:.2f}s muerto). "
            f"Mete un asset, un subrayado, o corta el beat cerca de {midpoint:.2f}s."
        )
    return "\n".join(lines)
