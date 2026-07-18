"""Green-screen removal with spill suppression.

Runs on the Python side, before an asset reaches the cache — a cutout cached
with its green background baked in stays broken forever, since the cache
never regenerates something it already has. See CHROMA_VERSION below: it is
folded into the cache key, so bumping the algorithm invalidates stale cutouts
instead of leaving them un-recut.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

CHROMA_VERSION = "chroma-v1"

# Below LOW_THRESHOLD a pixel is treated as fully opaque foreground; above
# HIGH_THRESHOLD it is fully transparent background. Between them alpha ramps
# linearly — a hard cutoff is what makes an edge look like a paper sticker.
LOW_THRESHOLD = 15.0
HIGH_THRESHOLD = 70.0


def remove_green_screen(png_bytes: bytes) -> bytes:
    """Take a PNG with a pure green (#00FF00) background, return one with it
    cut to a transparent RGBA PNG.

    Callers should catch any exception from this and fall back to the
    original bytes — a failed chroma pass must never block the build.
    """
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    rgb = np.asarray(image, dtype=np.float32)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    # How much greener a pixel is than its red/blue ceiling. Pure background
    # scores highest; a red foreground scores negative or near zero.
    diff = green - np.maximum(red, blue)

    alpha = 1.0 - np.clip((diff - LOW_THRESHOLD) / (HIGH_THRESHOLD - LOW_THRESHOLD), 0.0, 1.0)

    # Spill suppression: clamp the excess green back to the red/blue ceiling
    # on every pixel touched by the screen, including ones that stay opaque
    # or partially opaque. This is what removes the halo, not just the flat
    # background color — a plain alpha cutout still shows a green fringe.
    spill = np.clip(diff, 0.0, None)
    green_clean = green - spill

    out_rgb = np.clip(np.stack([red, green_clean, blue], axis=-1), 0, 255).astype(np.uint8)
    out_alpha = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    rgba = np.dstack([out_rgb, out_alpha])

    buffer = io.BytesIO()
    Image.fromarray(rgba).save(buffer, format="PNG")
    return buffer.getvalue()
