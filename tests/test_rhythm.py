"""Unit tests for factory.rhythm. Pure manifest-dict logic, no rendering.

Run with:
    python -m unittest tests.test_rhythm
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory import rhythm  # noqa: E402

FPS = 30


def _beat(index: int, seconds: float, sequence_from: int, n_assets: int = 1) -> dict:
    return {
        "index": index,
        "text": f"BEAT {index}",
        "seconds": seconds,
        "assets": [f"a{i}" for i in range(n_assets)],
        "sequenceFrom": sequence_from,
    }


class RhythmTest(unittest.TestCase):
    def test_dense_video_has_no_dead_zones(self):
        # 1s beats: text-change-per-beat alone keeps every gap under 1.2s,
        # regardless of asset placement inside each beat.
        manifest = {
            "mode": "video",
            "fps": FPS,
            "beats": [_beat(1, 1, 0), _beat(2, 1, 30), _beat(3, 1, 60)],
        }
        self.assertEqual(rhythm.find_dead_zones(manifest), [])
        self.assertIsNone(rhythm.report(manifest))

    def test_long_static_beat_with_no_asset_is_flagged(self):
        manifest = {
            "mode": "video",
            "fps": FPS,
            "beats": [
                _beat(1, 3, 0),
                {"index": 2, "text": "STATIC", "seconds": 6, "assets": [], "sequenceFrom": 90},
                _beat(3, 3, 90 + 180),
            ],
        }
        zones = rhythm.find_dead_zones(manifest)
        self.assertTrue(len(zones) >= 1)
        report = rhythm.report(manifest)
        self.assertIsNotNone(report)
        self.assertIn("RITMO", report)

    def test_carrusel_mode_is_exempt(self):
        manifest = {
            "mode": "carrusel",
            "fps": FPS,
            "beats": [{"index": 1, "text": "X", "seconds": 20, "assets": [], "sequenceFrom": 0}],
        }
        self.assertEqual(rhythm.find_dead_zones(manifest), [])


if __name__ == "__main__":
    unittest.main()
