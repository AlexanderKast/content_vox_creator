"""ElevenLabs voice provider.

Deliberately not cost-optimized, and that is the decision, not an oversight.

A 60-75s script is ~1,000 characters — about $0.12. The cheapest TTS on the
market would save eleven cents per video. The cloned voice is the one asset in
this pipeline that cannot be re-derived: it is the brand. We optimize images
aggressively and we do not touch this.
"""

from __future__ import annotations

import json
import urllib.request

BASE_URL = "https://api.elevenlabs.io/v1"

# Voice settings tuned for a NATURAL, non-robotic conversational read (Spanish
# VO). The trade-off, per ElevenLabs' own guidance:
#   - stability LOW-ish (0.38) → emotional range and human inflection. Too high
#     (>0.6) is where it starts to sound flat/robotic; too low (<0.3) drifts.
#   - similarity_boost 0.80 → stays clearly the cloned voice without over-
#     clamping the expressiveness.
#   - style 0.55 → brings the speaker's own cadence/energy (this is the biggest
#     lever against a monotone, "AI-reading-a-paper" delivery).
#   - use_speaker_boost True → tighter resemblance on longer reads.
# Delivery ALSO comes from the text: write it with real punctuation, commas and
# ellipses for breath and dramatic pauses, and short conversational sentences —
# ElevenLabs reads punctuation as pacing. See the reel narration for the pattern.
DEFAULT_SETTINGS = {
    "stability": 0.38,
    "similarity_boost": 0.80,
    "style": 0.55,
    "use_speaker_boost": True,
}


class ElevenLabsVoice:
    name = "elevenlabs"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def speak(self, text: str, *, voice_id: str, model: str = "eleven_multilingual_v2") -> bytes:
        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": DEFAULT_SETTINGS,
        }
        request = urllib.request.Request(
            f"{BASE_URL}/text-to-speech/{voice_id}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.read()

    def music(self, prompt: str, *, duration_ms: int = 30000) -> bytes:
        payload = {
            "prompt": prompt,
            "music_length_ms": duration_ms,
            # Every endpoint defaults to the legacy music_v1 for backwards
            # compatibility. We always want v2 unless someone deliberately
            # downgrades this call.
            "model_id": "music_v2",
        }
        request = urllib.request.Request(
            f"{BASE_URL}/music",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.read()

    def sound_effect(self, text: str, *, duration_seconds: float | None = None,
                      loop: bool = False, output_format: str = "mp3_44100_128") -> bytes:
        payload: dict = {"text": text, "loop": loop}
        if duration_seconds is not None:
            payload["duration_seconds"] = duration_seconds
        request = urllib.request.Request(
            f"{BASE_URL}/sound-generation?output_format={output_format}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
