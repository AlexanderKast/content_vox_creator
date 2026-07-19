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

# Friendly slug (the part of factory.router.DEFAULT_MODELS after "wavespeed/")
# to the real WaveSpeed API path. Verified against https://wavespeed.ai/docs/
# 2026-07-16 — the bare "z-image" and "nano-banana-2-fast" slugs used before
# this table don't exist on the real API.
#
# flux-2-klein-4b and nano-banana-pro verified 2026-07-17. Two corrections
# from what was assumed before: (1) WaveSpeed's plain "Flux Klein" models are
# edit-only (image-in, image-out) — the text-to-image variant is specifically
# the 4B/9B/base-9B line; (2) Nano Banana PRO is a different model line from
# Nano Banana 2 (Gemini 3.0 Pro Image vs. 2.5 Flash Image), not a "pro" flag
# on the fast one, and it's priced like it — see factory/cost.py.
API_PATHS: dict[str, str] = {
    "z-image": "wavespeed-ai/z-image/turbo",
    "nano-banana-2-fast": "google/nano-banana-2/text-to-image-fast",
    "flux-2-klein-4b": "wavespeed-ai/flux-2-klein-4b/text-to-image",
    "nano-banana-pro": "google/nano-banana-pro/text-to-image",
}

# These models take "aspect_ratio" + "resolution" instead of a pixel "size"
# string. Sending "size" to them is rejected.
ASPECT_RATIO_MODELS = {"nano-banana-2-fast", "nano-banana-pro"}

# The API only accepts a FIXED enum of aspect_ratio strings — NOT an
# arbitrary ratio computed from width/height. Verified 2026-07-18 (real 400
# response): ["1:1","3:2","2:3","3:4","4:3","4:5","5:4","9:16", + 6 more].
# gcd-reducing an arbitrary width/height pair can also land on a string
# that's mathematically equivalent but not the literal accepted spelling —
# "21:9" does NOT reduce to itself via gcd (21 and 9 share factor 3, gcd
# lands on "7:3", which the API rejects) even though "21:9" itself IS a
# valid enum value. So this list is hand-verified-valid literals, not
# computed — pick from here, don't derive.
VALID_ASPECT_RATIOS = {"1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}


def _aspect_ratio(width: int, height: int) -> str:
    from math import gcd

    divisor = gcd(width, height)
    ratio = f"{width // divisor}:{height // divisor}"
    if ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(
            f"width={width}, height={height} reduces to aspect_ratio \"{ratio}\", which "
            f"WaveSpeed doesn't accept. Valid: {sorted(VALID_ASPECT_RATIOS)}. Pass an "
            "explicit `aspect_ratio=` to WaveSpeedImages.generate() instead of relying on "
            "this gcd derivation when you need a specific one (e.g. \"21:9\", which never "
            "survives gcd reduction)."
        )
    return ratio


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
                 reference: str | None = None, aspect_ratio: str | None = None) -> bytes:
        # model arrives as "wavespeed/z-image"; map the friendly slug to the
        # real API path (see API_PATHS above).
        friendly = model.split("/", 1)[1] if "/" in model else model
        api_path = API_PATHS.get(friendly, friendly)

        payload: dict = {"prompt": prompt, "output_format": "png"}
        if friendly in ASPECT_RATIO_MODELS:
            # Explicit aspect_ratio wins — needed for values like "21:9" that
            # don't survive gcd reduction from a pixel width/height (see
            # VALID_ASPECT_RATIOS above). Falls back to deriving one from
            # width/height for every existing caller that doesn't pass it.
            if aspect_ratio is not None:
                if aspect_ratio not in VALID_ASPECT_RATIOS:
                    raise ValueError(f"aspect_ratio \"{aspect_ratio}\" not in {sorted(VALID_ASPECT_RATIOS)}.")
                payload["aspect_ratio"] = aspect_ratio
            else:
                payload["aspect_ratio"] = _aspect_ratio(width, height)
            payload["resolution"] = "2k"
        else:
            payload["size"] = f"{width}*{height}"
        if reference:
            payload["images"] = [reference]

        submitted = self._post(api_path, payload)
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
