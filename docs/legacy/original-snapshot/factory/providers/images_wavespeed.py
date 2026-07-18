"""WaveSpeed image provider.

Default for cutouts and scenes. Same models as the alternatives, lower price on
Nano Banana 2, direct rather than resold.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE_URL = "https://api.wavespeed.ai/api/v3"
POLL_INTERVAL_SECONDS = 1.5
POLL_TIMEOUT_SECONDS = 120


class WaveSpeedImages:
    name = "wavespeed"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            f"{BASE_URL}/{path}",
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

    def generate(self, prompt: str, *, model: str, width: int, height: int,
                 reference: str | None = None) -> bytes:
        # model arrives as "wavespeed/z-image"; the API wants the bare slug.
        slug = model.split("/", 1)[1] if "/" in model else model
        payload: dict = {
            "prompt": prompt,
            "size": f"{width}*{height}",
            "output_format": "png",
        }
        if reference:
            payload["images"] = [reference]

        submitted = self._post(f"{slug}", payload)
        result_url = (
            submitted.get("data", {})
            .get("urls", {})
            .get("get")
        )
        if not result_url:
            raise RuntimeError(f"WaveSpeed did not return a poll URL: {submitted}")

        deadline = time.time() + POLL_TIMEOUT_SECONDS
        while time.time() < deadline:
            status_body = self._get(result_url)
            data = status_body.get("data", {})
            status = data.get("status")
            if status == "completed":
                outputs = data.get("outputs") or []
                if not outputs:
                    raise RuntimeError("WaveSpeed completed with no outputs.")
                with urllib.request.urlopen(outputs[0], timeout=60) as image:
                    return image.read()
            if status == "failed":
                raise RuntimeError(f"WaveSpeed generation failed: {data.get('error')}")
            time.sleep(POLL_INTERVAL_SECONDS)

        raise TimeoutError(f"WaveSpeed timed out after {POLL_TIMEOUT_SECONDS}s.")
