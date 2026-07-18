"""Provider adapter layer.

The lesson that shaped this package: providers are fungible and some are
fragile. Kie is a reseller with no direct partnership with model owners — it had
to drop Midjourney when Midjourney demanded it. Any pipeline welded to one
vendor breaks on a Tuesday for reasons outside its control.

So: one interface, swappable backends. Changing provider is an env var and a
line in router.DEFAULT_MODELS, not a rewrite.
"""

from __future__ import annotations

from typing import Protocol


class ImageProvider(Protocol):
    """Anything that turns a prompt into image bytes."""

    name: str

    def generate(self, prompt: str, *, model: str, width: int, height: int,
                 reference: str | None = None) -> bytes:
        ...


class PhotoProvider(Protocol):
    """Anything that finds real photos that already exist in the world."""

    name: str

    def search(self, query: str, *, limit: int = 3) -> list[str]:
        ...


class VoiceProvider(Protocol):
    """Anything that turns a script into speech bytes."""

    name: str

    def speak(self, text: str, *, voice_id: str, model: str) -> bytes:
        ...
