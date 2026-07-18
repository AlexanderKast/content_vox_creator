"""Smoke test for factory.chroma. No network calls, no API keys required.

Run with:
    python3 -m unittest tests.test_chroma
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory.chroma import remove_green_screen  # noqa: E402


def _synthetic_green_screen_with_red_circle(size: int = 512, radius: int = 120) -> bytes:
    pixels = np.zeros((size, size, 3), dtype=np.uint8)
    pixels[..., 1] = 255  # pure green, #00FF00

    center = size // 2
    yy, xx = np.ogrid[:size, :size]
    circle = (xx - center) ** 2 + (yy - center) ** 2 <= radius ** 2
    pixels[circle] = (220, 20, 20)  # red foreground

    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return buffer.getvalue()


class ChromaKeyTest(unittest.TestCase):
    def test_corners_transparent_center_red_no_green_dominant_border(self):
        source = _synthetic_green_screen_with_red_circle()
        result = remove_green_screen(source)

        image = Image.open(io.BytesIO(result))
        self.assertEqual(image.mode, "RGBA")
        rgba = np.asarray(image)

        corner = rgba[5, 5]
        self.assertEqual(int(corner[3]), 0, "corner should be fully transparent")

        center = rgba[256, 256]
        self.assertEqual(int(center[3]), 255, "center should stay fully opaque")
        self.assertGreater(int(center[0]), int(center[1]), "center should stay red-dominant")

        red = rgba[..., 0].astype(int)
        green = rgba[..., 1].astype(int)
        blue = rgba[..., 2].astype(int)
        alpha = rgba[..., 3].astype(int)

        visible = alpha > 0
        green_dominant = green > np.maximum(red, blue)
        self.assertFalse(
            bool(np.any(visible & green_dominant)),
            "no visible pixel (including the ramped edge) should have a dominant green channel",
        )


if __name__ == "__main__":
    unittest.main()
