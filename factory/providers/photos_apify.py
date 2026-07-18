"""Apify photo provider.

For anything that exists in the real world: named people, logos, brands, news
screenshots. The rule is absolute — a real person is never invented by an image
model. That is how content starts looking (and being) fake.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

BASE_URL = "https://api.apify.com/v2"


class ApifyPhotos:
    name = "apify"

    def __init__(self, token: str, actor: str) -> None:
        self._token = token
        self._actor = actor

    def search(self, query: str, *, limit: int = 3) -> list[str]:
        """Return direct image URLs. Keep limit small — cost scales with volume."""
        endpoint = (
            f"{BASE_URL}/acts/{urllib.parse.quote(self._actor, safe='~')}"
            f"/run-sync-get-dataset-items?token={self._token}"
        )
        payload = {"queries": [query], "maxResultsPerQuery": limit}
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            items = json.loads(response.read())

        urls: list[str] = []
        for item in items:
            for key in ("imageUrl", "url", "originalImageUrl", "src"):
                value = item.get(key)
                if isinstance(value, str) and value.startswith("http"):
                    urls.append(value)
                    break
        return urls[:limit]

    @staticmethod
    def download(url: str) -> bytes:
        # Some hosts 403 a request with no/default User-Agent (basic
        # anti-hotlinking) — a real, if minimal, browser UA is enough to pass.
        request = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; fabrica-box/1.0)"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
