"""Forced word-level alignment of the on-screen caption to the actual voice.

Two-stage, both local, zero paid calls:

  1. AUDIO -> NARRATION WORDS. Local Whisper (faster-whisper, CPU) transcribes
     the ElevenLabs mp3 we already generated and already know the text of.
     Paying an API to re-transcribe audio we ourselves synthesized from a
     known script would be paying to read our own handwriting back to us —
     so this never calls a network endpoint. The ASR transcript is aligned
     back to the KNOWN narration text (difflib), because whisper's own
     tokenization/punctuation rarely matches the script verbatim even when
     it heard every word correctly.

  2. NARRATION WORDS -> ON-SCREEN CAPTION WORDS. `beat.text` (the kinetic
     caption) is usually a short excerpt of `beat.narration` (the spoken
     line), not the same string — e.g. text="NO CRECEN EN EL GIMNASIO" is a
     substring of narration="Tus musculos no crecen en el gimnasio...". A
     second difflib pass lines up the caption's words against that beat's own
     narration words to inherit their timestamps.

Any failure at any stage (no whisper model available, a beat's caption isn't
actually a subset of its narration, corrupt audio) degrades that BEAT to the
old estimated timing — never the whole build. This module never raises past
its own boundary in normal operation; pipeline.py still wraps the call in
try/except as a second layer of protection.
"""

from __future__ import annotations

import difflib
import unicodedata
from dataclasses import dataclass
from pathlib import Path

WHISPER_LANGUAGE = "es"

_models: dict[str, object] = {}  # lazy singletons keyed by model size — loading is the expensive part


@dataclass(frozen=True)
class WordTiming:
    word: str
    start_seconds: float
    end_seconds: float


def _get_model(model_size: str):
    if model_size not in _models:
        from faster_whisper import WhisperModel

        _models[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _models[model_size]


def transcribe_words(audio_path: Path, model_size: str = "medium") -> list[WordTiming]:
    model = _get_model(model_size)
    segments, _info = model.transcribe(
        str(audio_path), language=WHISPER_LANGUAGE, word_timestamps=True
    )
    words: list[WordTiming] = []
    for segment in segments:
        for w in (segment.words or []):
            token = (w.word or "").strip()
            if token:
                words.append(WordTiming(word=token, start_seconds=w.start, end_seconds=w.end))
    return words


def _normalize(word: str) -> str:
    """Lowercase, strip diacritics, keep only alnum. Without the diacritic
    strip, "musica" (an all-caps on-screen caption, often written without
    accents) would never match "música" (properly-accented narration prose)
    — a very plausible mismatch in Spanish, not an edge case."""
    decomposed = unicodedata.normalize("NFKD", word.lower())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return "".join(ch for ch in stripped if ch.isalnum())


def _align_words(
    source_words: list[str], timed_words: list[WordTiming]
) -> list[WordTiming | None]:
    """Map each word in `source_words` (in order) to a WordTiming from
    `timed_words`, via sequence alignment on normalized tokens. Unmatched
    positions are None."""
    a = [_normalize(w) for w in source_words]
    b = [_normalize(w.word) for w in timed_words]
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    result: list[WordTiming | None] = [None] * len(source_words)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("equal", "replace"):
            span = min(i2 - i1, j2 - j1)
            for k in range(span):
                result[i1 + k] = timed_words[j1 + k]
    return result


def compute_beat_word_timings(
    voice_path: Path, beats: list, fps: int, model_size: str = "medium"
) -> dict[int, list[dict]]:
    """Return {beat.index: [{"word", "startFrame", "endFrame"}, ...]} for
    every beat whose on-screen text could be fully aligned to real voice
    timing. A beat missing from the returned dict should fall back to
    estimated timing — this is a partial result by design, not an error."""
    narrated_beats = [b for b in beats if b.narration.strip()]
    if not narrated_beats:
        return {}

    whisper_words = transcribe_words(voice_path, model_size)
    if not whisper_words:
        return {}

    all_narration_words = [w for b in narrated_beats for w in b.narration.split()]
    narration_timings = _align_words(all_narration_words, whisper_words)

    result: dict[int, list[dict]] = {}
    cursor = 0
    for beat in narrated_beats:
        n_words = beat.narration.split()
        beat_narration_timings = narration_timings[cursor: cursor + len(n_words)]
        cursor += len(n_words)

        caption_words = beat.text.split()
        if not caption_words or any(t is None for t in beat_narration_timings):
            continue

        caption_timings = _align_narration_to_caption(caption_words, n_words, beat_narration_timings)

        if any(t is None for t in caption_timings):
            continue

        result[beat.index] = [
            {
                "word": word,
                "startFrame": round(t.start_seconds * fps),
                "endFrame": round(t.end_seconds * fps),
            }
            for word, t in zip(caption_words, caption_timings)
        ]

    return result


def _align_narration_to_caption(
    caption_words: list[str], narration_words: list[str], narration_timings: list[WordTiming | None]
) -> list[WordTiming | None]:
    """Stage 2: line up the short on-screen caption against this beat's own
    narration words (already timestamped in stage 1).

    Only "equal" opcodes count. Unlike stage 1 (ASR transcript vs. known
    text, where a "replace" is almost always the same word transcribed with
    minor noise), here the caption is a genuinely different, shorter string —
    a "replace" block means a caption word that isn't actually present in
    the narration, which is exactly the not-a-subset case that must fall
    back to estimated timing rather than inherit a wrong timestamp."""
    a = [_normalize(w) for w in caption_words]
    b = [_normalize(w) for w in narration_words]
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    result: list[WordTiming | None] = [None] * len(caption_words)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                timing = narration_timings[j1 + k]
                if timing is not None:
                    result[i1 + k] = timing
    return result
