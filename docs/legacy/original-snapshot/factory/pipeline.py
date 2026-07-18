"""Orchestration.

Order is deliberate:
  1. plan    — route every asset to its tier
  2. price   — estimate the whole run
  3. gate    — refuse to start if it exceeds the ceiling
  4. produce — generate, caching every paid call by content hash
  5. render  — hand a manifest to Remotion

Nothing is generated before step 3 passes. The reference system generates first
and discovers the bill afterwards; that is the habit this file exists to break.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path

from . import cache, config, cost, db
from .providers.images_wavespeed import WaveSpeedImages
from .providers.photos_apify import ApifyPhotos
from .providers.voice_elevenlabs import ElevenLabsVoice
from .router import DEFAULT_MODELS, Asset, Tier, build_prompt, plan
from .script import DIMENSIONS, FPS, Mode, Script, assert_valid

VOICE_MODEL = "elevenlabs/multilingual-v2"


def estimate(script: Script) -> cost.Estimate:
    """Price the whole run before a single cent is spent."""
    grouped = plan(script.all_assets)
    est = cost.Estimate()

    for tier, assets in grouped.items():
        if not assets:
            continue
        model = DEFAULT_MODELS[tier]
        if tier is Tier.PHOTO:
            est.add(f"{tier.value} ({model})", cost.PHOTO_PRICE_PER_IMAGE, len(assets))
        else:
            est.add(f"{tier.value} ({model})", cost.image_price(model), len(assets))

    if script.character_count:
        est.add(
            f"voice ({VOICE_MODEL})",
            cost.VOICE_PRICES[VOICE_MODEL] / 1_000_000,
            script.character_count,
        )

    if script.music_prompt:
        est.add("music (elevenlabs)", cost.MUSIC_PRICE, 1)

    return est


class Factory:
    def __init__(self, cfg: config.Config | None = None) -> None:
        self.cfg = cfg or config.load()
        self.conn = db.connect()
        self._render_lock = threading.Semaphore(self.cfg.render_concurrency)

    # -- asset production -------------------------------------------------

    def _produce_image(self, job_id: str, asset: Asset, tier: Tier,
                       width: int, height: int, reference: str | None) -> Path:
        model = DEFAULT_MODELS[tier]
        prompt = build_prompt(asset, tier)
        key = cache.content_hash(
            model=model, prompt=prompt, width=width, height=height, reference=reference
        )

        hit = cache.get(key, "png")
        if hit:
            return hit  # already paid for. Never pay twice.

        provider = WaveSpeedImages(self.cfg.require("wavespeed_key"))
        data = provider.generate(
            prompt, model=model, width=width, height=height, reference=reference
        )
        path = cache.put(key, "png", data)
        db.record_asset(
            self.conn, key, job_id, tier.value, model, str(path), cost.image_price(model)
        )
        return path

    def _produce_photo(self, job_id: str, asset: Asset) -> Path | None:
        key = cache.content_hash(source="apify", query=asset.description)
        hit = cache.get(key, "jpg")
        if hit:
            return hit

        provider = ApifyPhotos(
            self.cfg.require("apify_token"), self.cfg.apify_image_actor
        )
        urls = provider.search(asset.description, limit=3)
        if not urls:
            return None  # graceful degradation: the build continues without it

        data = provider.download(urls[0])
        path = cache.put(key, "jpg", data)
        db.record_asset(
            self.conn, key, job_id, Tier.PHOTO.value, "apify/google-images",
            str(path), cost.PHOTO_PRICE_PER_IMAGE,
        )
        return path

    def _produce_voice(self, job_id: str, script: Script, voice_id: str) -> Path | None:
        text = script.narration_text
        if not text:
            return None

        key = cache.content_hash(model=VOICE_MODEL, voice=voice_id, text=text)
        hit = cache.get(key, "mp3")
        if hit:
            return hit

        provider = ElevenLabsVoice(self.cfg.require("elevenlabs_key"))
        data = provider.speak(text, voice_id=voice_id, model="eleven_multilingual_v2")
        path = cache.put(key, "mp3", data)
        db.record_asset(
            self.conn, key, job_id, "voice", VOICE_MODEL, str(path),
            cost.voice_price(VOICE_MODEL, len(text)),
        )
        return path

    # -- public api -------------------------------------------------------

    def build(self, job_id: str, script: Script, *, dry_run: bool = False) -> dict:
        assert_valid(script)
        config.ensure_dirs()

        brand_tokens = json.loads(config.BRAND_PATH.read_text(encoding="utf-8"))
        tokens = brand_tokens[script.brand]

        est = estimate(script)
        print(est.render())
        cost.enforce_budget(est, self.cfg.max_spend_per_run)

        if dry_run:
            return {"estimate": est.total, "lines": [asdict(line) for line in est.lines]}

        db.create_job(self.conn, job_id, script.mode.value, script.brand, script.topic)
        db.set_status(self.conn, job_id, "producing")

        width, height = DIMENSIONS[script.mode]
        grouped = plan(script.all_assets)
        produced: dict[str, str] = {}

        for tier, assets in grouped.items():
            for asset in assets:
                if tier is Tier.PHOTO:
                    path = self._produce_photo(job_id, asset)
                else:
                    reference = tokens.get("characterRef") if tier is Tier.CHARACTER else None
                    path = self._produce_image(job_id, asset, tier, width, height, reference)
                if path:
                    produced[asset.id] = str(path)

        voice_path = self._produce_voice(job_id, script, tokens["voiceId"])

        manifest = {
            "jobId": job_id,
            "mode": script.mode.value,
            "brand": script.brand,
            "tokens": tokens,
            "width": width,
            "height": height,
            "fps": FPS,
            "hook": script.hook,
            "cta": script.cta,
            "voice": str(voice_path) if voice_path else None,
            "beats": [
                {
                    "index": beat.index,
                    "text": beat.text,
                    "narration": beat.narration,
                    "seconds": beat.seconds,
                    "assets": [produced.get(a.id) for a in beat.assets if produced.get(a.id)],
                }
                for beat in script.beats
            ],
            "spendUsd": db.job_spend(self.conn, job_id),
        }

        manifest_path = config.OUT_DIR / f"{job_id}.manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        db.set_status(self.conn, job_id, "produced", {"manifest": str(manifest_path)})

        print(f"\nManifest: {manifest_path}")
        print(f"Actual spend: ${manifest['spendUsd']:.4f}")
        return manifest
