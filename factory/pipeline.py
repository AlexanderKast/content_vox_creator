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

import io
import json
import shutil
import threading
from dataclasses import asdict
from pathlib import Path

from PIL import Image

from . import align, cache, caption, chroma, config, cost, db, gating, hooks, redact, rhythm
from .providers.character_magnific import MagnificCharacter
from .providers.images_wavespeed import WaveSpeedImages
from .providers.photos_apify import ApifyPhotos
from .providers.text_llm import MistralText
from .providers.voice_elevenlabs import ElevenLabsVoice
from .router import (
    DEFAULT_MODELS,
    DEFAULT_TEMPLATE,
    TEMPLATE_NAMES,
    Asset,
    Tier,
    backdrop_prompt,
    build_prompt,
    plan,
)
from .script import DIMENSIONS, FPS, Mode, PanoramaGroup, Script, assert_valid

VOICE_MODEL = "elevenlabs/multilingual-v2"
# Full-frame themed BACKDROP (the beat's `scene` field). A mid model: good enough
# composition for a background that text sits over, without the premium per-image
# cost of the character/Tier.SCENE tier (these run once per beat that declares a
# backdrop). Distinct from router.Tier.SCENE ($0.14, isolated composition) — see
# router.BACKDROP_PROMPT for the two-concept note.
BACKDROP_MODEL = "wavespeed/nano-banana-2-fast"
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

    # Full-frame themed backdrops — one per beat that declares a `scene`.
    n_backdrops = sum(1 for b in script.beats if b.scene.strip())
    if n_backdrops:
        est.add(f"backdrop ({BACKDROP_MODEL})", cost.image_price(BACKDROP_MODEL), n_backdrops)

    # Panorama groups (2-4 beats sharing one wide backdrop, sliced per-beat —
    # factory.script.PanoramaGroup): ONE backdrop-priced generation per
    # group, never per beat it spans — that's the whole point of the
    # feature. Slicing itself is free (local PIL crop, no API call).
    if script.panoramas:
        est.add(f"panorama ({BACKDROP_MODEL})", cost.image_price(BACKDROP_MODEL), len(script.panoramas))

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

    def _produce_backdrop(
        self, job_id: str, description: str, width: int, height: int, template: str
    ) -> Path | None:
        """A full-frame themed backdrop (the beat's 'world', from beat.scene).
        Unlike a cutout it is NOT chroma-keyed — it fills the frame and text sits
        over it. Distinct from Tier.SCENE. Cached by (model, prompt, size) — the
        template is baked into the prompt text, so switching templates never
        serves a stale cached image under a new look."""
        prompt = backdrop_prompt(description, template)
        key = cache.content_hash(model=BACKDROP_MODEL, prompt=prompt, width=width, height=height, kind="backdrop")
        hit = cache.get(key, "png")
        if hit:
            return hit

        provider = WaveSpeedImages(self.cfg.require("wavespeed_key"))
        data = provider.generate(prompt, model=BACKDROP_MODEL, width=width, height=height)
        path = cache.put(key, "png", data)
        db.record_asset(
            self.conn, key, job_id, "backdrop", BACKDROP_MODEL, str(path), cost.image_price(BACKDROP_MODEL)
        )
        return path

    def _produce_panorama(
        self, job_id: str, group: PanoramaGroup, width: int, height: int, template: str
    ) -> dict[int, Path]:
        """One wide backdrop (width * len(group.beats)) sliced into
        len(group.beats) per-beat strips — a group of consecutive carrusel
        slides that shares one continuous background instead of each paying
        for (and getting) an independent one. Returns {beat_index: slice
        Path}, or None if generation failed (degrades to no backdrop for
        those beats, same as a failed _produce_backdrop).

        The panorama itself is cached once (so a rebuild never re-pays for
        it); each slice is ALSO cached under its own deterministic key (not
        content-hashed from the crop bytes — from the group + index, same
        style as every other cache key here) so re-slicing on a rebuild is
        just a cheap local crop, never a re-fetch."""
        prompt = backdrop_prompt(group.description, template)
        n = len(group.beats)
        # nano-banana-2-fast only accepts a FIXED enum of aspect ratios (see
        # images_wavespeed.VALID_ASPECT_RATIOS) — width*n/height rarely lands
        # on one, so pick the closest valid wide ratio explicitly instead of
        # letting generate() derive (and reject) one. n is validated to 2-3
        # (script._validate_panoramas) specifically because these are the
        # two ratios that exist and fit reasonably.
        aspect_ratio = {2: "16:9", 3: "21:9"}[n]
        pano_key = cache.content_hash(
            model=BACKDROP_MODEL, prompt=prompt, aspect_ratio=aspect_ratio, kind="panorama",
        )
        pano_path = cache.get(pano_key, "png")
        if not pano_path:
            provider = WaveSpeedImages(self.cfg.require("wavespeed_key"))
            data = provider.generate(
                prompt, model=BACKDROP_MODEL, width=width * n, height=height, aspect_ratio=aspect_ratio,
            )
            pano_path = cache.put(pano_key, "png", data)
            db.record_asset(
                self.conn, pano_key, job_id, "panorama", BACKDROP_MODEL,
                str(pano_path), cost.image_price(BACKDROP_MODEL),
            )

        panorama: Image.Image | None = None  # lazy-loaded only if a slice is missing from cache

        slices: dict[int, Path] = {}
        for i, beat_index in enumerate(group.beats):
            slice_key = cache.content_hash(
                model=BACKDROP_MODEL, prompt=prompt, width=width, height=height,
                kind="panorama-slice", beats=group.beats, slice_index=i,
            )
            slice_path = cache.get(slice_key, "png")
            if slice_path is None:
                if panorama is None:
                    panorama = Image.open(pano_path).convert("RGB")
                # The generated image rarely lands on the EXACT pixel width
                # asked (aspect-ratio + fixed-resolution providers, see
                # images_wavespeed.ASPECT_RATIO_MODELS) — slice by FRACTION
                # of whatever width actually came back, not width * n.
                actual_width, actual_height = panorama.size
                slice_width = actual_width / n
                left = round(i * slice_width)
                right = round((i + 1) * slice_width)
                crop = panorama.crop((left, 0, right, actual_height)).resize((width, height))
                buf = io.BytesIO()
                crop.save(buf, "PNG")
                slice_path = cache.put(slice_key, "png", buf.getvalue())
            slices[beat_index] = slice_path
        return slices

    def _produce_image(self, job_id: str, asset: Asset, tier: Tier,
                       width: int, height: int, reference: str | None, template: str) -> Path:
        model = DEFAULT_MODELS[tier]
        prompt = build_prompt(asset, tier, template)
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
        # is_public_figure is part of the key: the SAME query must never
        # serve a cached un-redacted photo once an asset asks for redaction
        # (or vice versa) — the two are different artifacts, not a cache hit.
        # redact.REDACT_VERSION is part of it too, same reason as
        # chroma.CHROMA_VERSION elsewhere: a treatment change (e.g. the
        # 2026-07-18 switch from a raw black bar to duotone + red) must
        # reprocess, never quietly serve the old look from cache.
        key = cache.content_hash(
            source="apify", query=asset.description, public_figure=asset.is_public_figure,
            redact=redact.REDACT_VERSION if asset.is_public_figure else None,
        )
        hit = cache.get(key, "png" if asset.is_public_figure else "jpg")
        if hit:
            return hit

        provider = ApifyPhotos(
            self.cfg.require("apify_token"), self.cfg.apify_image_actor
        )
        urls = provider.search(asset.description, limit=cost.APIFY_RESULTS_PER_QUERY)
        if not urls:
            return None  # graceful degradation: the build continues without it

        # Try each candidate URL in order rather than betting everything on
        # the first one. Two independent failure modes showed up in the same
        # afternoon (2026-07-18): a URL that 404s on download (dead link,
        # hotlink-blocked), and — for a public figure — a URL that downloads
        # fine but isn't even a photo of a person (has_face rejects it, see
        # below). Either one on url[0] alone used to take the whole beat's
        # asset down with it; now it just moves to the next candidate.
        data: bytes | None = None
        for url in urls:
            try:
                candidate = provider.download(url)
            except Exception as exc:  # noqa: BLE001 - a single bad URL must not sink the build
                print(f"Photo download failed for '{asset.description}' ({url}): {exc}")
                continue
            if asset.is_public_figure and not redact.has_face(candidate):
                # Apify's search can return the wrong thing entirely for an
                # otherwise normal query — a screenshot of an unrelated page,
                # an infographic, not a photo of anyone, or even a real photo
                # of the WRONG person (verified 2026-07-18). Shipping any of
                # those as a redacted "figure" defeats the entire point —
                # try the next candidate instead of accepting it.
                continue
            data = candidate
            break

        if data is None:
            return None  # every candidate failed or (public figure) had no usable face

        ext = "jpg"
        if asset.is_public_figure:
            # A real, named public figure — never shipped as a clean,
            # identifiable close-up, and never as a raw color photo with a
            # black box (reads as moderation, not design). See
            # factory.redact for the duotone + eye-bar treatment.
            data = redact.stylize_public_figure(data)
            ext = "png"
        path = cache.put(key, ext, data)
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

        # Template resolution order: script override -> brand default -> global
        # default. Validated NOW, before estimate/spend, so a typo'd template
        # name fails the brief instead of failing mid-build after real assets
        # were already paid for.
        template = script.template or tokens.get("template") or DEFAULT_TEMPLATE
        if template not in TEMPLATE_NAMES:
            raise RuntimeError(
                f"Plantilla '{template}' no existe.\n"
                f"Disponibles: {', '.join(TEMPLATE_NAMES)}"
            )

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
                    path = self._produce_image(job_id, asset, tier, width, height, reference, template)
                if path:
                    produced[asset.id] = _publish_for_remotion(path)

        # Panorama groups first (2-4 beats sharing one wide backdrop, sliced
        # per-beat — factory.script.PanoramaGroup). validate() already
        # guarantees a grouped beat's own `beat.scene` is empty, so the
        # per-beat loop below naturally leaves these entries alone — no
        # explicit skip needed. Degrade gracefully per group, same as a
        # single backdrop failure: that group's beats fall back to no scene.
        scene_by_beat: dict[int, str] = {}
        for group in script.panoramas:
            try:
                slices = self._produce_panorama(job_id, group, width, height, template)
                for beat_index, p in slices.items():
                    scene_by_beat[beat_index] = _publish_for_remotion(p)
            except Exception as exc:  # noqa: BLE001 - degrade, never block
                print(f"Panorama generation failed for beats {list(group.beats)}, using paper bg: {exc}")

        # Full-frame themed backdrops, one per beat that declares one (beat.scene).
        # Degrade gracefully: a backdrop failure just falls back to the cream
        # paper Background for that beat, never blocks the build.
        for beat in script.beats:
            if beat.scene.strip():
                try:
                    p = self._produce_backdrop(job_id, beat.scene, width, height, template)
                    if p:
                        scene_by_beat[beat.index] = _publish_for_remotion(p)
                except Exception as exc:  # noqa: BLE001 - degrade, never block
                    print(f"Backdrop generation failed for beat {beat.index}, using paper bg: {exc}")

        voice_id = tokens.get("voiceId")

        # VIDEO carries one continuous voice track. CARRUSEL is muted by
        # default (content-vox-brief: it tells its story through on-screen
        # title + subtitle text) — UNLESS a beat declares its own
        # `narration`, in which case that slide gets its own voice clip
        # (content-vox-news: narrated explainer carousels). No narration on
        # any beat -> voice_by_beat stays empty -> identical to the old
        # always-muted behavior, so this is backward compatible.
        voice_path = None
        if voice_id and script.mode is Mode.VIDEO:
            voice_path = self._produce_voice(job_id, script, voice_id)

        voice_by_beat: dict[int, str] = {}
        if voice_id and script.mode is Mode.CARRUSEL:
            for beat in script.beats:
                if not beat.narration.strip():
                    continue
                try:
                    p = self._produce_voice_text(job_id, beat.narration, voice_id)
                    if p:
                        voice_by_beat[beat.index] = _publish_for_remotion(p)
                except Exception as exc:  # noqa: BLE001 - degrade, never block
                    print(f"Voice generation failed for beat {beat.index}, slide stays silent: {exc}")

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
                "seconds": beat.seconds,
                "assets": [
                    {"src": produced[a.id], "isPublicFigure": a.is_public_figure}
                    for a in beat.assets if produced.get(a.id)
                ],
                "scene": scene_by_beat.get(beat.index),
                "voice": voice_by_beat.get(beat.index),
                "sfx": sfx_entries,
                "sequenceFrom": cursor_frames,
                "wordTimings": word_timings_by_beat.get(beat.index),
            })
            cursor_frames += round(beat.seconds * FPS)

        manifest = {
            "jobId": job_id,
            "mode": script.mode.value,
            "brand": script.brand,
            "template": template,
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
