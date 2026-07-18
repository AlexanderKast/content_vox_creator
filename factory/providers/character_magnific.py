"""Magnific (Mystic) character-consistent image provider.

Endpoint, auth, and request/response shape verified 2026-07-17 against
https://docs.magnific.com/api-reference/mystic/post-mystic and
.../get-mystic-task. Character consistency goes through the `styling.
characters` parameter, not an inline reference image — `character_id` is a
Magnific Library character asset id. brand.json's `characterRef` IS that id;
per SKILL.md, verify it with the Magnific MCP `library_list` tool before
trusting a value copied from history (an old id can be shared with another
project).

PRICING IS NOT VERIFIED THE WAY EVERY OTHER PROVIDER IN THIS FACTORY IS.
Magnific's API is credit-based against a subscription plan (Premium/
Premium+/Pro; 20K-300K credits/month), and the credits-per-image cost scales
with resolution and model — there is no single published flat USD/image
figure to check `factory/cost.py`'s `magnific/character` price against.
Check your actual credit balance after a real batch (`account_balance` via
the Magnific MCP, or the dashboard) before trusting the estimator here for
this one tier specifically.
"""

from __future__ import annotations

import json
import time
import urllib.request

BASE_URL = "https://api.magnific.com/v1/ai/mystic"
POLL_INTERVAL_SECONDS = 2.0
POLL_TIMEOUT_SECONDS = 180

# Magnific takes a named aspect-ratio enum, not raw pixel width/height.
# Exact matches for this factory's two formats; anything else falls back to
# the closest documented option.
_ASPECT_RATIO_MAP: dict[tuple[int, int], str] = {
    (1080, 1920): "social_story_9_16",  # VIDEO — exact match
    (1080, 1350): "traditional_3_4",    # CARRUSEL (4:5) — closest enum is 3:4, not exact
}


def _aspect_ratio(width: int, height: int) -> str:
    if (width, height) in _ASPECT_RATIO_MAP:
        return _ASPECT_RATIO_MAP[(width, height)]
    return "traditional_3_4" if height > width else "widescreen_16_9"


class MagnificCharacter:
    name = "magnific"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"x-magnific-api-key": self._api_key, "Content-Type": "application/json"}

    def _post(self, payload: dict) -> dict:
        request = urllib.request.Request(
            BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())

    def _get(self, url: str) -> dict:
        request = urllib.request.Request(url, headers=self._headers(), method="GET")
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())

    def generate(self, prompt: str, *, character_id: str, width: int, height: int,
                 strength: int = 100) -> bytes:
        payload = {
            "prompt": prompt,
            "aspect_ratio": _aspect_ratio(width, height),
            "resolution": "2k",
            "styling": {"characters": [{"id": character_id, "strength": strength}]},
        }
        submitted = self._post(payload)
        task_id = submitted.get("data", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"Magnific did not return a task_id: {submitted}")

        deadline = time.time() + POLL_TIMEOUT_SECONDS
        while time.time() < deadline:
            status_body = self._get(f"{BASE_URL}/{task_id}")
            data = status_body.get("data", {})
            status = data.get("status")
            if status == "COMPLETED":
                generated = data.get("generated") or []
                if not generated:
                    raise RuntimeError("Magnific completed with no outputs.")
                with urllib.request.urlopen(generated[0], timeout=60) as image:
                    return image.read()
            if status == "FAILED":
                raise RuntimeError(f"Magnific generation failed: {data}")
            time.sleep(POLL_INTERVAL_SECONDS)

        raise TimeoutError(f"Magnific timed out after {POLL_TIMEOUT_SECONDS}s.")
