"""Environment loading. Secrets live in .env, never in code. Non-negotiable."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "generated"
CACHE_DIR = ROOT / ".cache"
OUT_DIR = ROOT / "out"
DB_PATH = ROOT / "factory.db"
BRAND_PATH = ROOT / "brand.json"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader. No dependency, no surprises."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Config:
    wavespeed_key: str | None
    kie_key: str | None
    fal_key: str | None
    magnific_key: str | None
    apify_token: str | None
    apify_image_actor: str
    elevenlabs_key: str | None
    max_spend_per_run: float
    render_concurrency: int
    whisper_model_size: str
    mistral_key: str | None
    use_llm_copy: bool

    def require(self, name: str) -> str:
        value = getattr(self, name)
        if not value:
            raise RuntimeError(
                f"Missing credential: {name}. Add it to .env (see .env.example)."
            )
        return value


def load() -> Config:
    return Config(
        wavespeed_key=os.environ.get("WAVESPEED_API_KEY") or None,
        kie_key=os.environ.get("KIE_API_KEY") or None,
        fal_key=os.environ.get("FAL_API_KEY") or None,
        magnific_key=os.environ.get("MAGNIFIC_API_KEY") or None,
        apify_token=os.environ.get("APIFY_API_TOKEN") or None,
        apify_image_actor=os.environ.get(
            "APIFY_IMAGE_ACTOR", "hooli~google-images-scraper"
        ),
        elevenlabs_key=os.environ.get("ELEVENLABS_API_KEY") or None,
        max_spend_per_run=float(os.environ.get("MAX_SPEND_PER_RUN_USD", "1.50")),
        render_concurrency=int(os.environ.get("RENDER_CONCURRENCY", "1")),
        # Local Whisper, zero dollar cost either way — "medium" over "small"
        # is a straight accuracy win on Spanish, paid for in CPU time, not
        # money. Bump to "large-v3" for even better accuracy if the extra
        # render time is worth it; "tiny"/"base" only make sense on very
        # weak hardware.
        whisper_model_size=os.environ.get("WHISPER_MODEL_SIZE", "medium"),
        mistral_key=os.environ.get("MISTRAL_API_KEY") or None,
        # Opt-in, off by default: hooks/caption stay free mechanical templates
        # (factory.hooks/factory.caption) unless explicitly turned on — this
        # is a deliberate spend decision, not something a build should do
        # silently just because a key happens to be present.
        use_llm_copy=os.environ.get("ENABLE_LLM_COPY", "false").lower() in ("1", "true", "yes"),
    )


def ensure_dirs() -> None:
    for directory in (ASSETS_DIR, CACHE_DIR, OUT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
