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

# Validated settings live in the pipeline-video-ia skill. Keep them in sync.
DEFAULT_SETTINGS = {
    "stability": 0.45,
    "similarity_boost": 0.85,
    "style": 0.35,
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
        payload = {"prompt": prompt, "music_length_ms": duration_ms}
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
