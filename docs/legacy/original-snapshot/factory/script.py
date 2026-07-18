"""Script model and validation.

The script is 80% of the result. A beautiful video with a weak script is
useless; a strong script with mediocre animation still works. So the structure
is enforced in code, not left to vibes.

Two shapes, because the two modes are genuinely different products:
  VIDEO    — the edit sets the pace. Continuous narration, one timeline.
  CARRUSEL — the user's thumb sets the pace. Each slide is autonomous.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .router import Asset


class Mode(str, Enum):
    VIDEO = "video"
    CARRUSEL = "carrusel"


# Format per mode. These are not preferences — 9:16 uploaded to a carousel gets
# cropped to 3:4 by Instagram, which eats the frame.
DIMENSIONS: dict[Mode, tuple[int, int]] = {
    Mode.VIDEO: (1080, 1920),   # 9:16 — Reels, TikTok
    Mode.CARRUSEL: (1080, 1350),  # 4:5 — Instagram feed
}

FPS = 30

# Carousel safe area, centered. Instagram's UI covers 80px top / 200px bottom.
CAROUSEL_SAFE_AREA = (1000, 1070)


@dataclass
class Beat:
    """One scene (VIDEO) or one slide (CARRUSEL)."""

    index: int
    text: str                  # on-screen text — mandatory in carrusel, sound is off
    narration: str = ""        # spoken line; empty means silent beat
    seconds: float = 3.0
    assets: list[Asset] = field(default_factory=list)


@dataclass
class Script:
    mode: Mode
    brand: str
    topic: str
    hook: str
    beats: list[Beat]
    cta: str
    music_prompt: str = "understated documentary underscore, tense, minimal percussion"

    @property
    def narration_text(self) -> str:
        return " ".join(beat.narration.strip() for beat in self.beats if beat.narration).strip()

    @property
    def character_count(self) -> int:
        return len(self.narration_text)

    @property
    def all_assets(self) -> list[Asset]:
        return [asset for beat in self.beats for asset in beat.assets]

    @property
    def duration_seconds(self) -> float:
        return round(sum(beat.seconds for beat in self.beats), 2)


class ScriptError(ValueError):
    """Raised when a script violates a rule we already know breaks the output."""


def validate(script: Script) -> list[str]:
    """Return blocking errors. Empty list means the script may proceed."""
    errors: list[str] = []

    if not script.hook.strip():
        errors.append("Missing hook. The first 3 seconds are the whole video.")

    if script.mode is Mode.CARRUSEL:
        if not 6 <= len(script.beats) <= 10:
            errors.append(
                f"Carrusel has {len(script.beats)} slides. Use 6-10 — the technical "
                "limit is 20, but nobody finishes 20."
            )
        for beat in script.beats:
            if not beat.text.strip():
                errors.append(
                    f"Slide {beat.index} has no on-screen text. Carousels are consumed "
                    "muted; a slide that needs audio to be understood is a broken slide."
                )
            if not 4.0 <= beat.seconds <= 8.0:
                errors.append(
                    f"Slide {beat.index} is {beat.seconds}s. Use 4-8s per slide."
                )
    else:
        if not 45 <= script.duration_seconds <= 90:
            errors.append(
                f"Video runs {script.duration_seconds}s. Target 60-75s."
            )
        for beat in script.beats:
            if beat.seconds > 1.2 and not beat.assets:
                errors.append(
                    f"Beat {beat.index} holds {beat.seconds}s with no visual. "
                    "Nothing stays static past ~1.2s."
                )

    if not script.cta.strip():
        errors.append("Missing CTA.")

    return errors


def assert_valid(script: Script) -> None:
    errors = validate(script)
    if errors:
        raise ScriptError("Script rejected:\n  - " + "\n  - ".join(errors))
