"""Eye redaction for real photos of public figures.

A public-figure asset (factory.router.Asset.is_public_figure) is always a
REAL scraped photo (factory.providers.photos_apify — never invented). Before
that photo is cached or rendered, this module blacks out the eyes so the
video never carries a clean, identifiable close-up.

Local only: OpenCV's bundled Haar cascades, no network call, no per-run cost.
If no face/eyes are found (bad angle, sunglasses, low resolution — Apify
results are not curated), this degrades to blacking out the image's upper
band rather than shipping an unredacted photo. Over-covering is the safe
failure; under-covering is not.
"""

from __future__ import annotations

import cv2
import numpy as np

# Bundled with opencv-python-headless — no download, no external asset.
_FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_EYE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_eye.xml"

# Fallback when detection finds nothing: black out this fraction of the
# image's height from the top. A headshot's eyes sit well within this band;
# it over-covers non-headshot framing on purpose.
_FALLBACK_BAND_FRACTION = 0.4

_face_cascade: cv2.CascadeClassifier | None = None
_eye_cascade: cv2.CascadeClassifier | None = None


def _cascades() -> tuple[cv2.CascadeClassifier, cv2.CascadeClassifier]:
    global _face_cascade, _eye_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(_FACE_CASCADE_PATH)
    if _eye_cascade is None:
        _eye_cascade = cv2.CascadeClassifier(_EYE_CASCADE_PATH)
    return _face_cascade, _eye_cascade


def black_bar_eyes(image_bytes: bytes) -> bytes:
    """Return `image_bytes` (any format OpenCV can decode) re-encoded as PNG
    with the eyes (or, failing detection, the upper band) blacked out."""
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("redact.black_bar_eyes: could not decode image bytes")

    height, width = image.shape[:2]
    face_cascade, eye_cascade = _cascades()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    bars: list[tuple[int, int, int, int]] = []  # (x, y, w, h) in full-image coords
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    for (fx, fy, fw, fh) in faces:
        face_gray = gray[fy:fy + fh, fx:fx + fw]
        eyes = eye_cascade.detectMultiScale(face_gray, scaleFactor=1.1, minNeighbors=6, minSize=(15, 15))
        for (ex, ey, ew, eh) in eyes:
            # Pad generously — a tight box over just the pupils still leaves
            # the eye shape/expression visible, which is enough to identify
            # someone. This is a redaction, not a decoration.
            pad_x, pad_y = round(ew * 0.5), round(eh * 0.8)
            bars.append((
                max(0, fx + ex - pad_x),
                max(0, fy + ey - pad_y),
                ew + pad_x * 2,
                eh + pad_y * 2,
            ))

    if not bars:
        band_height = round(height * _FALLBACK_BAND_FRACTION)
        bars = [(0, 0, width, band_height)]

    for (bx, by, bw, bh) in bars:
        cv2.rectangle(image, (bx, by), (bx + bw, by + bh), (0, 0, 0), thickness=-1)

    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("redact.black_bar_eyes: PNG re-encode failed")
    return encoded.tobytes()
