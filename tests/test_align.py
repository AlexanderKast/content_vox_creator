"""Unit tests for word-alignment logic. No whisper model load, no audio, no
network — transcribe_words is monkeypatched with canned timings so this runs
fast and deterministically.

Run with:
    python -m unittest tests.test_align
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory import align  # noqa: E402
from factory.script import Beat  # noqa: E402


def _wt(word: str, start: float, end: float) -> align.WordTiming:
    return align.WordTiming(word=word, start_seconds=start, end_seconds=end)


class AlignWordsTest(unittest.TestCase):
    def test_exact_sequence_maps_one_to_one(self):
        source = ["tus", "musculos", "no", "crecen"]
        timed = [_wt("Tus", 0.0, 0.3), _wt("músculos", 0.3, 0.8), _wt("no", 0.8, 1.0), _wt("crecen", 1.0, 1.4)]
        result = align._align_words(source, timed)
        self.assertEqual(len(result), 4)
        self.assertTrue(all(r is not None for r in result))
        self.assertEqual(result[0].start_seconds, 0.0)
        self.assertEqual(result[3].end_seconds, 1.4)

    def test_extra_words_in_timed_are_skipped(self):
        source = ["no", "crecen"]
        timed = [_wt("Tus", 0.0, 0.3), _wt("no", 0.3, 0.5), _wt("crecen", 0.5, 0.9)]
        result = align._align_words(source, timed)
        self.assertEqual(result[0].start_seconds, 0.3)
        self.assertEqual(result[1].start_seconds, 0.5)


class NormalizeTest(unittest.TestCase):
    def test_strips_diacritics(self):
        self.assertEqual(align._normalize("MÚSICA"), align._normalize("musica"))
        self.assertEqual(align._normalize("señal"), align._normalize("SENAL"))


class AccentInsensitiveCaptionMatchTest(unittest.TestCase):
    def test_all_caps_caption_without_accents_matches_accented_narration(self):
        # A very plausible real case: the on-screen caption is written in
        # plain, unaccented caps while the spoken narration is properly
        # accented Spanish prose.
        narration_words = ["Y", "eso", "no", "es", "un", "accidente", "Ese", "dano", "es", "la", "señal"]
        timings = [_wt(w, i * 0.3, i * 0.3 + 0.3) for i, w in enumerate(narration_words)]
        caption_words = ["ES", "LA", "SENAL"]
        result = align._align_narration_to_caption(caption_words, narration_words, timings)
        self.assertTrue(all(r is not None for r in result), f"expected accent-insensitive match, got: {result}")
        self.assertEqual(result[-1].start_seconds, timings[-1].start_seconds)


class AlignNarrationToCaptionTest(unittest.TestCase):
    def test_caption_substring_of_narration_inherits_timestamps(self):
        narration_words = ["Tus", "musculos", "no", "crecen", "en", "el", "gimnasio"]
        timings = [
            _wt(w, i * 0.3, i * 0.3 + 0.3) for i, w in enumerate(narration_words)
        ]
        caption_words = ["NO", "CRECEN", "EN", "EL", "GIMNASIO"]
        result = align._align_narration_to_caption(caption_words, narration_words, timings)
        self.assertTrue(all(r is not None for r in result))
        self.assertEqual(result[0].start_seconds, timings[2].start_seconds)  # "no"
        self.assertEqual(result[-1].start_seconds, timings[6].start_seconds)  # "gimnasio"

    def test_caption_not_a_subset_falls_back_to_none(self):
        narration_words = ["Tus", "musculos", "no", "crecen"]
        timings = [_wt(w, i * 0.3, i * 0.3 + 0.3) for i, w in enumerate(narration_words)]
        caption_words = ["ESTO", "ES", "OTRA", "COSA", "TOTALMENTE", "DISTINTA"]
        result = align._align_narration_to_caption(caption_words, narration_words, timings)
        self.assertTrue(any(r is None for r in result))


class ComputeBeatWordTimingsTest(unittest.TestCase):
    def test_beat_with_matching_caption_gets_timings_beat_without_falls_back(self):
        beats = [
            Beat(
                index=1,
                text="NO CRECEN EN EL GIMNASIO",
                narration="Tus musculos no crecen en el gimnasio",
                seconds=6,
            ),
            Beat(
                index=2,
                text="TOTALMENTE DISTINTO AL AUDIO",
                narration="Cada repeticion crea microdesgarros",
                seconds=5,
            ),
            Beat(index=3, text="SIN NARRACION", narration="", seconds=3),
        ]

        canned_words = []
        t = 0.0
        for w in "Tus musculos no crecen en el gimnasio Cada repeticion crea microdesgarros".split():
            canned_words.append(_wt(w, t, t + 0.3))
            t += 0.3

        with patch.object(align, "transcribe_words", return_value=canned_words):
            result = align.compute_beat_word_timings(Path("fake.mp3"), beats, fps=30)

        self.assertIn(1, result)
        self.assertNotIn(2, result)  # caption text isn't a subset of its narration
        self.assertNotIn(3, result)  # no narration at all

        words_beat1 = result[1]
        self.assertEqual([w["word"] for w in words_beat1], ["NO", "CRECEN", "EN", "EL", "GIMNASIO"])
        self.assertEqual(words_beat1[0]["startFrame"], round(0.6 * 30))  # "no" is the 3rd word, t=0.6s

    def test_empty_transcription_returns_empty_dict(self):
        beats = [Beat(index=1, text="X", narration="Algo", seconds=3)]
        with patch.object(align, "transcribe_words", return_value=[]):
            result = align.compute_beat_word_timings(Path("fake.mp3"), beats, fps=30)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
