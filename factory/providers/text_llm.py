"""Text-LLM provider — powers the optional LLM-written hooks/caption path.

Off by default (see factory.config.use_llm_copy). factory.hooks and
factory.caption ship with free mechanical templates that need zero paid
calls; this is the opt-in upgrade to real copywriting, on request.

Provider-agnostic by design via the TextLLM protocol. MistralText is the
only verified implementation today (endpoint, request/response shape, and
pricing confirmed 2026-07-17 against https://docs.mistral.ai/api/endpoint/chat
and https://mistral.ai/pricing/) because that's the key on hand. Gemini,
OpenAI, and Anthropic all speak a similar (mostly OpenAI-compatible) chat
shape — add a class here implementing TextLLM, wire its key into
factory.config, and hooks.py/caption.py need zero changes to use it. Do not
add an unverified provider class "just in case" — verify the real endpoint
and price first, the same discipline this whole factory holds paid image
providers to.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Protocol


class TextLLM(Protocol):
    name: str

    def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 400) -> str:
        ...


class MistralText:
    name = "mistral"
    BASE_URL = "https://api.mistral.ai/v1/chat/completions"
    # Cheap tier — $0.10 / $0.30 per 1M input/output tokens. Hooks and
    # captions are short; a call costs a fraction of a cent. See
    # factory/cost.py TEXT_LLM_PRICES for the estimator entry.
    MODEL = "mistral-small-latest"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 400) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.8,
        }
        request = urllib.request.Request(
            self.BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read())
        return body["choices"][0]["message"]["content"].strip()
