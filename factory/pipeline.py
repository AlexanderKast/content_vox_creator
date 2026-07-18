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
import shutil
import threading
from dataclasses import asdict
from pathlib import Path

from . import align, cache, caption, chroma, config, cost, db, gating, hooks, rhythm
from .providers.character_magnific import MagnificCharacter
from .providers.images_wavespeed import WaveSpeedImages
from .providers.photos_apify import ApifyPhotos
from .providers.text_llm import MistralText
from .providers.voice_elevenlabs import ElevenLabsVoice
from .router import DEFAULT_MODELS, SCENE_FULL_PROMPT, Asset, Tier, build_prompt, plan
from .script import DIMENSIONS, FPS, Mode, Script, assert_valid

VOICE_MODEL = "elevenlabs/multilingual-v2"
# Full-frame themed scene backgrounds. A mid model: good enough composition for
# a background that text sits over, without the premium per-image cost of the
# character/scene tier (these run once per beat that declares a scene).
SCENE_MODEL = "wavespeed/nano-banana-2-fast"
MUSIC_DEFAULT_DURATION_MS = 30_000


def _music_duration_ms(script: Script) -> int:
    """Music bed length.

    VIDEO: covers the whole timeline (the bed is the emotional floor — it can't
    stop halfway). CARRUSEL: a short, loopable clip (~ the longest slide), since
    each independent slide loops the bed rather than playing one long track —
    generating the full timeline there would just waste money. Floor 10s."""
    if script.mode is Mode.CARRUSEL:
        longest_slide = max((b.seconds for b in script.beats), default=10)
        return max(10_000, round(longest_slide * 1000))
    return max(10_000, round(script.duration_seconds * 1000))

# SFX names a Beat's cues can use (factory.script.Script.sfx_cues), mapped to
# the ElevenLabs sound-generation prompt and a fixed duration.
#
# Each entry type has SEVERAL variants (pop-a/pop-b/pop-c ...). sfx_cues rotates
# the variant by beat, so consecutive beats don't all trigger the identical
# sound — it stops feeling repetitive. Every unique variant is still generated
# once and cached, so more variety costs a few cents at most. Prompts are
# modern/punchy (not the old flat "documentary" ones). ElevenLabs rejects
# duration_seconds < 0.5, so 0.5 is the floor.
SFX_PROMPTS: dict[str, str] = {
    # cutout enters
    "pop-a": "a snappy modern UI pop, crisp digital click, clean, no reverb, isolated",
    "pop-b": "a soft bubble pop, bright and short, clean, isolated",
    "pop-c": "a plucky synth blip pop, tight and modern, isolated",
    # cut between beats
    "whoosh-a": "a fast clean cinematic swoosh transition, airy, modern",
    "whoosh-b": "a crisp digital swipe transition, sharp, futuristic",
    "whoosh-c": "a punchy reverse whoosh riser into a cut, tight",
    # remate / hook hit
    "impact-a": "a deep cinematic boom impact hit, punchy, tight, no music",
    "impact-b": "a hard trailer braaam impact, short and powerful",
    "impact-c": "a tight sub-bass drop hit, modern trap style, short",
    # underline draws
    "marker-a": "a quick crisp marker-pen swipe, minimal, no reverb",
    "marker-b": "a short sharp paper-swipe scribble, tight",
}
SFX_DURATIONS: dict[str, float] = {
    "pop-a": 0.5, "pop-b": 0.5, "pop-c": 0.5,
    "whoosh-a": 0.8, "whoosh-b": 0.7, "whoosh-c": 0.8,
    "impact-a": 0.6, "impact-b": 0.6, "impact-c": 0.7,
    "marker-a": 0.5, "marker-b": 0.5,
}

# Real SFX shipped in the repo (curated from the "Edwin Arenas" pack) under
# assets/sfx/. When a cue's name has a real file here, we use THAT instead of
# paying ElevenLabs to synthesize one — it's free, instant, and identical every
# render. Generation (SFX_PROMPTS) stays as the fallback for any name without a
# local file. File name == cue name: the 11 system variants (pop-a..marker-b)
# plus extras a Beat can trigger via an explicit ``sfx=`` override (ding, money,
# coin, transition, error, glitch, explosion, click). See assets/sfx/CATALOGO.md
# for the full map of which sound fires where.
SFX_LIBRARY_DIR = config.ROOT / "assets" / "sfx"


def _local_sfx(name: str) -> Path | None:
    """Path to the real SFX file for ``name`` if one ships in the repo, else
    None (caller falls back to ElevenLabs generation)."""
    for ext in ("mp3", "wav"):
        candidate = SFX_LIBRARY_DIR / f"{name}.{ext}"
        if candidate.exists():
            return candidate
    return None


def _publish_for_remotion(path: Path) -> str:
    """Copy a generated asset into Remotion's public directory.

    Remotion's ``staticFile()`` resolves paths relative to ``public/``; cache
    paths are intentionally outside that directory so they remain provider
    cache artifacts. The manifest therefore stores a public-relative path.
    """
    public_dir = config.ROOT / "remotion" / "public" / "generated"
    public_dir.mkdir(parents=True, exist_ok=True)
    destination = public_dir / path.name
    if not destination.exists() or destination.stat().st_size != path.stat().st_size:
        shutil.copy2(path, destination)
    return f"generated/{path.name}"


TEXT_LLM_MODEL = "mistral/mistral-small-latest"


def estimate(script: Script, cfg: config.Config | None = None) -> cost.Estimate:
    """Price the whole run before a single cent is spent."""
    grouped = plan(script.all_assets)
    est = cost.Estimate()

    for tier, assets in grouped.items():
        if not assets:
            continue
        model = DEFAULT_MODELS[tier]
        if tier is Tier.PHOTO:
            # One Apify run per asset (run fee + per-image fee + page fee),
            # not a flat per-photo rate. See cost.photo_price.
            est.add(f"{tier.value} ({model})", cost.photo_price(), len(assets))
        else:
            est.add(f"{tier.value} ({model})", cost.image_price(model), len(assets))

    # Full-frame themed scene backgrounds — one per beat that declares a scene.
    n_scenes = sum(1 for b in script.beats if b.scene.strip())
    if n_scenes:
        est.add(f"scene ({SCENE_MODEL})", cost.image_price(SCENE_MODEL), n_scenes)

    if script.character_count:
        est.add(
            f"voice ({VOICE_MODEL})",
            cost.VOICE_PRICES[VOICE_MODEL] / 1_000_000,
            script.character_count,
        )

    # Music bed — now produced for BOTH modes (each carrusel slide plays the
    # same bed at low volume). One generation, priced once.
    if script.music_prompt:
        est.add("music (elevenlabs)", cost.music_price(_music_duration_ms(script)), 1)

    # SFX are priced once per unique sound, not once per cue that plays it —
    # the same "pop" reused across every cutout entrance is one generation,
    # one charge, however many beats or cues use it.
    for name in sorted(script.all_sfx_names()):
        # A real file shipped in assets/sfx/ costs nothing to use — only names
        # without one still get generated (and charged) by ElevenLabs.
        if _local_sfx(name) is not None:
            continue
        duration = SFX_DURATIONS.get(name)
        if duration is not None:
            est.add(f"sfx:{name} (elevenlabs)", cost.sfx_price(duration), 1)

    # Opt-in LLM copy (factory.config.use_llm_copy) — off by default, so this
    # line only appears when Alexander turned it on.
    if cfg is not None and cfg.use_llm_copy and cfg.mistral_key:
        hooks_in, hooks_out = cost.HOOKS_LLM_ESTIMATED_TOKENS
        caption_in, caption_out = cost.CAPTION_LLM_ESTIMATED_TOKENS
        llm_cost = cost.text_llm_price(
            TEXT_LLM_MODEL, hooks_in + caption_in, hooks_out + caption_out
        )
        est.add(f"copy ({TEXT_LLM_MODEL})", llm_cost, 1)

    return est


class Factory:
    def __init__(self, cfg: config.Config | None = None) -> None:
        self.cfg = cfg or config.load()
        self.conn = db.connect()
        self._render_lock = threading.Semaphore(self.cfg.render_concurrency)

    # -- asset production -------------------------------------------------

    def _produce_scene(self, job_id: str, description: str, width: int, height: int) -> Path | None:
        """A full-frame themed background scene (the beat's 'world'). Unlike a
        cutout it is NOT chroma-keyed — it fills the frame and text sits over
        it. Cached by (model, prompt, size)."""
        prompt = SCENE_FULL_PROMPT.format(description=description)
        key = cache.content_hash(model=SCENE_MODEL, prompt=prompt, width=width, height=height, kind="scene")
        hit = cache.get(key, "png")
        if hit:
            return hit

        provider = WaveSpeedImages(self.cfg.require("wavespeed_key"))
        data = provider.generate(prompt, model=SCENE_MODEL, width=width, height=height)
        path = cache.put(key, "png", data)
        db.record_asset(
            self.conn, key, job_id, "scene", SCENE_MODEL, str(path), cost.image_price(SCENE_MODEL)
        )
        return path

    def _produce_image(self, job_id: str, asset: Asset, tier: Tier,
                       width: int, height: int, reference: str | None) -> Path:
        model = DEFAULT_MODELS[tier]
        prompt = build_prompt(asset, tier)
        # chroma.CHROMA_VERSION is part of the key so improving the chroma
        # algorithm invalidates old cutouts instead of leaving them stale.
        key = cache.content_hash(
            model=model, prompt=prompt, width=width, height=height,
            reference=reference, chroma=chroma.CHROMA_VERSION,
        )

        hit = cache.get(key, "png")
        if hit:
            return hit  # already paid for. Never pay twice.

        if tier is Tier.CHARACTER:
            if not reference:
                raise RuntimeError(
                    "Tier.CHARACTER asset with no characterRef — fill brand.json "
                    "before generating a recurring character."
                )
            character_provider = MagnificCharacter(self.cfg.require("magnific_key"))
            data = character_provider.generate(
                prompt, character_id=reference, width=width, height=height
            )
        else:
            provider = WaveSpeedImages(self.cfg.require("wavespeed_key"))
            data = provider.generate(
                prompt, model=model, width=width, height=height, reference=reference
            )
        try:
            data = chroma.remove_green_screen(data)
        except Exception:
            pass  # degrade gracefully: keep the raw green-screen frame rather than block the build

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
        urls = provider.search(asset.description, limit=cost.APIFY_RESULTS_PER_QUERY)
        if not urls:
            return None  # graceful degradation: the build continues without it

        data = provider.download(urls[0])
        path = cache.put(key, "jpg", data)
        db.record_asset(
            self.conn, key, job_id, Tier.PHOTO.value, "apify/google-images",
            str(path), cost.photo_price(),
        )
        return path

    def _produce_sfx(self, job_id: str, name: str) -> Path | None:
        # Prefer the real, repo-shipped sound (assets/sfx/) — free, no API call.
        local = _local_sfx(name)
        if local is not None:
            db.record_asset(
                self.conn, cache.content_hash(source="local-sfx", name=name),
                job_id, "sfx", f"local/edwin-arenas:{name}", str(local), 0.0,
            )
            return local

        prompt = SFX_PROMPTS.get(name)
        duration = SFX_DURATIONS.get(name)
        if prompt is None or duration is None:
            return None

        key = cache.content_hash(source="elevenlabs-sfx", name=name, prompt=prompt, duration=duration)
        hit = cache.get(key, "mp3")
        if hit:
            return hit

        provider = ElevenLabsVoice(self.cfg.require("elevenlabs_key"))
        data = provider.sound_effect(prompt, duration_seconds=duration)
        path = cache.put(key, "mp3", data)
        db.record_asset(
            self.conn, key, job_id, "sfx", f"elevenlabs/sound-generation:{name}",
            str(path), cost.sfx_price(duration),
        )
        return path

    def _produce_voice_text(self, job_id: str, text: str, voice_id: str) -> Path | None:
        """Synthesize one voice clip for a given text (a whole video's
        narration, or a single carrusel slide's line). Cached by voice+text."""
        text = text.strip()
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

    def _produce_voice(self, job_id: str, script: Script, voice_id: str) -> Path | None:
        return self._produce_voice_text(job_id, script.narration_text, voice_id)

    def _produce_music(self, job_id: str, script: Script) -> Path | None:
        """The music bed — the emotional floor that makes the edit feel like
        storytelling instead of a slideshow. Cached by prompt + duration, so
        it's generated once per (prompt, length) and reused across rebuilds."""
        if not script.music_prompt:
            return None

        duration_ms = _music_duration_ms(script)
        key = cache.content_hash(source="elevenlabs-music", prompt=script.music_prompt, duration_ms=duration_ms)
        hit = cache.get(key, "mp3")
        if hit:
            return hit

        provider = ElevenLabsVoice(self.cfg.require("elevenlabs_key"))
        data = provider.music(script.music_prompt, duration_ms=duration_ms)
        path = cache.put(key, "mp3", data)
        db.record_asset(
            self.conn, key, job_id, "music", "elevenlabs/music-v2",
            str(path), cost.music_price(duration_ms),
        )
        return path

    # -- public api -------------------------------------------------------

    def build(self, job_id: str, script: Script, *, dry_run: bool = False) -> dict:
        assert_valid(script)
        config.ensure_dirs()

        if not config.BRAND_PATH.exists():
            raise RuntimeError(
                "No hay brand.json. Configura tu marca primero:\n"
                "  python -m factory.cli setup"
            )
        brand_tokens = json.loads(config.BRAND_PATH.read_text(encoding="utf-8"))
        if script.brand not in brand_tokens:
            available = ", ".join(brand_tokens.keys()) or "(ninguna)"
            raise RuntimeError(
                f"La marca '{script.brand}' no esta en tu brand.json.\n"
                f"Marcas disponibles: {available}\n"
                f"Corré  python -m factory.cli setup  para crear la tuya, o cambiá "
                f"el campo \"brand\" de tu guion."
            )
        tokens = brand_tokens[script.brand]

        est = estimate(script, self.cfg)
        print(est.render())
        cost.enforce_budget(est, self.cfg.max_spend_per_run)

        if dry_run:
            return {"estimate": est.total, "lines": [asdict(line) for line in est.lines]}

        db.create_job(
            self.conn, job_id, script.mode.value, script.brand, script.topic,
            formula=script.formula.value if script.formula else None,
        )
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
                    produced[asset.id] = _publish_for_remotion(path)

        # Full-frame themed scene backgrounds, one per beat that declares one.
        # Degrade gracefully: a scene failure just falls back to the cream
        # paper Background for that beat, never blocks the build.
        scene_by_beat: dict[int, str] = {}
        for beat in script.beats:
            if beat.scene.strip():
                try:
                    p = self._produce_scene(job_id, beat.scene, width, height)
                    if p:
                        scene_by_beat[beat.index] = _publish_for_remotion(p)
                except Exception as exc:  # noqa: BLE001 - degrade, never block
                    print(f"Scene generation failed for beat {beat.index}, using paper bg: {exc}")

        voice_id = tokens.get("voiceId")

        # VIDEO carries a continuous voice track. CARRUSEL is consumed muted —
        # it tells its whole story through on-screen title + subtitle text, so
        # it gets NO voice (just a music bed). See CarouselSlide.
        voice_path = None
        beat_voice: dict[int, str] = {}
        if voice_id and script.mode is Mode.VIDEO:
            voice_path = self._produce_voice(job_id, script, voice_id)

        # Music bed for BOTH modes now (each carrusel slide plays it low under
        # the voice). Degrade gracefully: a music failure never blocks a build.
        music_path = None
        try:
            music_path = self._produce_music(job_id, script)
        except Exception as exc:  # noqa: BLE001 - never block the build on the bed
            print(f"Music generation failed, continuing without a bed: {exc}")

        # Real per-word timing (VIDEO only — carrusel text is a short headline
        # that just animates in). Degrades to estimated timing on any failure.
        word_timings_by_beat: dict[int, list[dict]] = {}
        if voice_path is not None:
            try:
                word_timings_by_beat = align.compute_beat_word_timings(
                    voice_path, script.beats, FPS, self.cfg.whisper_model_size
                )
            except Exception as exc:  # noqa: BLE001 - degrade, never block the build
                print(f"Word alignment failed, falling back to estimated timing: {exc}")

        # Produce each unique SFX once — the same "pop" reused across every
        # cutout entrance in the whole script is one generation, cached and
        # reused, not one per occurrence.
        sfx_paths: dict[str, str] = {
            name: _publish_for_remotion(path)
            for name in script.all_sfx_names()
            if (path := self._produce_sfx(job_id, name)) is not None
        }

        beats_manifest = []
        cursor_frames = 0
        for beat in script.beats:
            # Local offset within the beat's own Sequence — Remotion's
            # <Audio from={...}> is relative to its parent Sequence, so this
            # is NOT the global timeline frame (contrast with wordTimings,
            # which the KineticText component consumes across Sequence
            # boundaries and therefore does need in global frames).
            sfx_entries = [
                {"src": sfx_paths[cue.name], "frame": cue.frame_offset}
                for cue in script.sfx_cues(beat)
                if cue.name in sfx_paths
            ]
            beats_manifest.append({
                "index": beat.index,
                "text": beat.text,
                "subtitle": beat.subtitle,
                "kicker": beat.kicker,
                "badge": beat.badge,
                "stat": beat.stat,
                "search": beat.search,
                "narration": beat.narration,
                "seconds": beat.seconds,
                "assets": [produced.get(a.id) for a in beat.assets if produced.get(a.id)],
                "scene": scene_by_beat.get(beat.index),
                "sfx": sfx_entries,
                "sequenceFrom": cursor_frames,
                "wordTimings": word_timings_by_beat.get(beat.index),
                # CARRUSEL: this slide's own voice clip (VIDEO uses the
                # top-level continuous track instead).
                "voice": beat_voice.get(beat.index),
            })
            cursor_frames += round(beat.seconds * FPS)

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
            "voice": _publish_for_remotion(voice_path) if voice_path else None,
            "music": _publish_for_remotion(music_path) if music_path else None,
            "beats": beats_manifest,
            "loop": script.loop,
            "seriesKicker": script.series_kicker,
            "spendUsd": db.job_spend(self.conn, job_id),
        }

        manifest_path = config.OUT_DIR / f"{job_id}.manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        db.set_status(self.conn, job_id, "produced", {"manifest": str(manifest_path)})

        rhythm_warning = rhythm.report(manifest)
        if rhythm_warning:
            print(f"\n{rhythm_warning}")

        # Free by default (template-only). Opt-in LLM copy (priced above,
        # in `estimate`) only activates when both the flag and the key are
        # set — see factory.config.use_llm_copy.
        llm = (
            MistralText(self.cfg.mistral_key)
            if self.cfg.use_llm_copy and self.cfg.mistral_key
            else None
        )

        caption_path = config.OUT_DIR / f"{job_id}.caption.txt"
        caption_path.write_text(caption.generate_caption(script, llm), encoding="utf-8")

        hooks_path = config.OUT_DIR / f"{job_id}.hooks.md"
        hooks_path.write_text(hooks.render_hooks_md(job_id, script, llm), encoding="utf-8")

        if script.gating is not None:
            botcake_path = config.OUT_DIR / f"{job_id}.botcake.md"
            botcake_path.write_text(
                gating.build_botcake_spec_md(job_id, script.gating), encoding="utf-8"
            )

        print(f"\nManifest: {manifest_path}")
        print(f"Actual spend: ${manifest['spendUsd']:.4f}")
        return manifest
