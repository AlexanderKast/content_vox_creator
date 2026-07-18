"""Unit tests for factory.providers.character_magnific. All HTTP calls are
mocked — no network, no real Magnific credits spent.

Run with:
    python -m unittest tests.test_character_magnific
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory.providers.character_magnific import (  # noqa: E402
    MagnificCharacter,
    _aspect_ratio,
)


class AspectRatioTest(unittest.TestCase):
    def test_known_video_and_carrusel_dimensions(self):
        self.assertEqual(_aspect_ratio(1080, 1920), "social_story_9_16")
        self.assertEqual(_aspect_ratio(1080, 1350), "traditional_3_4")

    def test_unknown_dimensions_fall_back_by_orientation(self):
        self.assertEqual(_aspect_ratio(2000, 1000), "widescreen_16_9")
        self.assertEqual(_aspect_ratio(1000, 2000), "traditional_3_4")


class MagnificCharacterGenerateTest(unittest.TestCase):
    def test_happy_path_posts_then_polls_then_downloads(self):
        provider = MagnificCharacter("fake-key")
        with patch.object(provider, "_post", return_value={"data": {"task_id": "abc123"}}) as post, \
             patch.object(provider, "_get", return_value={
                 "data": {"task_id": "abc123", "status": "COMPLETED",
                          "generated": ["https://example.com/img.png"]}
             }) as get, \
             patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b"PNGDATA"
            result = provider.generate(
                "a character cutout", character_id="char-42", width=1080, height=1920
            )

        self.assertEqual(result, b"PNGDATA")
        post_payload = post.call_args[0][0]
        self.assertEqual(post_payload["styling"]["characters"], [{"id": "char-42", "strength": 100}])
        self.assertEqual(post_payload["aspect_ratio"], "social_story_9_16")
        get.assert_called_with("https://api.magnific.com/v1/ai/mystic/abc123")

    def test_missing_task_id_raises(self):
        provider = MagnificCharacter("fake-key")
        with patch.object(provider, "_post", return_value={"data": {}}):
            with self.assertRaises(RuntimeError):
                provider.generate("x", character_id="c", width=1080, height=1920)

    def test_failed_status_raises(self):
        provider = MagnificCharacter("fake-key")
        with patch.object(provider, "_post", return_value={"data": {"task_id": "abc"}}), \
             patch.object(provider, "_get", return_value={"data": {"status": "FAILED"}}):
            with self.assertRaises(RuntimeError):
                provider.generate("x", character_id="c", width=1080, height=1920)

    def test_completed_with_no_outputs_raises(self):
        provider = MagnificCharacter("fake-key")
        with patch.object(provider, "_post", return_value={"data": {"task_id": "abc"}}), \
             patch.object(provider, "_get", return_value={
                 "data": {"status": "COMPLETED", "generated": []}
             }):
            with self.assertRaises(RuntimeError):
                provider.generate("x", character_id="c", width=1080, height=1920)


if __name__ == "__main__":
    unittest.main()
