"""Eye redaction + style treatment for real photos of public figures.

A public-figure asset (factory.router.Asset.is_public_figure) is always a
REAL scraped photo (factory.providers.photos_apify — never invented). Before
that photo is cached or rendered, this module:
  1. blacks out (in Hot Red) the eyes so the video never carries a clean,
     identifiable close-up, and
  2. converts the whole photo to the same black-and-white halftone duotone
     treatment as every generated `vox-paper` cutout (factory.router), so a
     real photo doesn't read as "a photo with a censor bar" sitting next to
     illustrated cutouts — it reads as the same design system. A raw black
     rectangle on an unmodified color photo looked like a moderation
     artifact, not a deliberate choice (verified 2026-07-18, Alexander:
     "las fotos no se ven bien").

Local only: OpenCV's bundled Haar cascades, no network call, no per-run cost.
If no face/eyes are found (bad angle, sunglasses, low resolution — Apify
results are not curated), this degrades to blacking out the image's upper
band rather than shipping an unredacted photo. Over-covering is the safe
failure; under-covering is not.
"""

from __future__ import annotations

import cv2
import numpy as np

# Bump when the treatment changes — factory.pipeline._produce_photo folds
# this into the cache key, so a version bump forces every public-figure
# photo to be reprocessed instead of quietly serving the old look from
# cache. v1 was a raw black rectangle on the unmodified color photo; v2 is
# the duotone + Hot Red bar below. v3 (2026-07-18, Alexander explicit
# request, confirmed after being told this reverses the earlier
# "sin excepcion" eye-bar rule): the eye bar becomes optional
# (redact_eyes=False), and the function now accepts an already
# background-removed RGBA source (person isolated, transparent elsewhere)
# and preserves that alpha channel through the duotone.
REDACT_VERSION = "redact-v3"

# Bundled with opencv-python-headless — no download, no external asset.
_FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_EYE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_eye.xml"

# Fallback when detection finds nothing: black out this fraction of the
# image's height from the top. A headshot's eyes sit well within this band;
# it over-covers non-headshot framing on purpose.
_FALLBACK_BAND_FRACTION = 0.4

# vox-paper palette (factory.router — keep these two in sync). OpenCV is
# BGR, not RGB.
_INK_BLACK_BGR = (26, 26, 26)       # #1A1A1A
_ARCHIVAL_TAN_BGR = (156, 187, 201)  # #C9BB9C
_HOT_RED_BGR = (31, 46, 182)         # #B62E1F — reserved for strokes/marks,
                                      # same rule the style sheet applies to
                                      # every other accent use in this project.

_face_cascade: cv2.CascadeClassifier | None = None
_eye_cascade: cv2.CascadeClassifier | None = None


def _cascades() -> tuple[cv2.CascadeClassifier, cv2.CascadeClassifier]:
    global _face_cascade, _eye_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(_FACE_CASCADE_PATH)
    if _eye_cascade is None:
        _eye_cascade = cv2.CascadeClassifier(_EYE_CASCADE_PATH)
    return _face_cascade, _eye_cascade


def has_face(image_bytes: bytes) -> bool:
    """True if at least one face is detected. Used as a sanity gate for
    is_public_figure assets: Apify's search can return a wrong or non-photo
    result (a screenshot of an unrelated page, an infographic, ...) for an
    otherwise normal query — verified 2026-07-18, a "president speaking
    press conference" search returned a chat-UI screenshot with unrelated
    text, and the eye cascade false-positived on that text. A minSize tied to
    the image's own dimensions (not a fixed pixel count) keeps the bar
    consistent across Apify's wildly varying result resolutions, and a higher
    minNeighbors than black_bar_eyes trades a few missed real faces (odd
    angles, low light) for fewer false positives on non-photo content — the
    right side to err on for a discard gate, the opposite of the redaction
    itself (which must never under-cover)."""
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        return False
    height, width = image.shape[:2]
    min_dim = round(min(height, width) * 0.08)
    face_cascade, _ = _cascades()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=8, minSize=(min_dim, min_dim)
    )
    return len(faces) > 0


def _eye_bars(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """(x, y, w, h) boxes, in full-image coords, generously padded over each
    detected eye — or, failing detection, one box over the image's upper
    band. Padded because a tight box over just the pupils still leaves the
    eye shape/expression visible, which is enough to identify someone. This
    is a redaction, not a decoration."""
    height, width = image.shape[:2]
    face_cascade, eye_cascade = _cascades()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    bars: list[tuple[int, int, int, int]] = []
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    for (fx, fy, fw, fh) in faces:
        face_gray = gray[fy:fy + fh, fx:fx + fw]
        eyes = eye_cascade.detectMultiScale(face_gray, scaleFactor=1.1, minNeighbors=6, minSize=(15, 15))
        for (ex, ey, ew, eh) in eyes:
            pad_x, pad_y = round(ew * 0.5), round(eh * 0.8)
            bars.append((
                max(0, fx + ex - pad_x),
                max(0, fy + ey - pad_y),
                ew + pad_x * 2,
                eh + pad_y * 2,
            ))

    if not bars:
        bars = [(0, 0, width, round(height * _FALLBACK_BAND_FRACTION))]
    return bars


def _duotone(image: np.ndarray) -> np.ndarray:
    """Map grayscale intensity to a gradient between Ink Black (shadows) and
    Archival Tan (highlights) — a 256-entry LUT, not a hard 2-level
    threshold, so real tonal gradation (a face, folds of a suit) survives
    instead of flattening into a silhouette. Matches the halftone
    black-and-white cutout treatment every other `vox-paper` asset gets
    (factory.router.CUTOUT_PROMPTS["vox-paper"])."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    lut = np.zeros((256, 3), dtype=np.uint8)
    for channel in range(3):
        dark = _INK_BLACK_BGR[channel]
        light = _ARCHIVAL_TAN_BGR[channel]
        lut[:, channel] = np.linspace(dark, light, 256)
    indices = (gray * 255).astype(np.uint8)
    return lut[indices]


def stylize_public_figure(image_bytes: bytes, *, redact_eyes: bool = True) -> bytes:
    """Return `image_bytes` (any format OpenCV can decode, RGBA or not) re-
    encoded as PNG: duotone black-and-white (matches the rest of the
    vox-paper look). `redact_eyes=True` (default) adds the Hot Red bar over
    the eyes (or, failing detection, the upper band) — `redact_eyes=False`
    skips it, full identifiable face. If the source already has an alpha
    channel (e.g. background-removed — Magnific remove-background, person
    isolated on transparent), that alpha survives the duotone untouched, so
    the result is a proper cutout, not a rectangular photo."""
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("redact.stylize_public_figure: could not decode image bytes")

    has_alpha = image.ndim == 3 and image.shape[2] == 4
    bgr = image[:, :, :3] if has_alpha else image

    bars = _eye_bars(bgr) if redact_eyes else []  # detected on the ORIGINAL — duotone flattens contrast
    styled = _duotone(bgr)

    for (bx, by, bw, bh) in bars:
        cv2.rectangle(styled, (bx, by), (bx + bw, by + bh), _HOT_RED_BGR, thickness=-1)

    if has_alpha:
        styled = cv2.merge([styled[:, :, 0], styled[:, :, 1], styled[:, :, 2], image[:, :, 3]])

    ok, encoded = cv2.imencode(".png", styled)
    if not ok:
        raise RuntimeError("redact.stylize_public_figure: PNG re-encode failed")
    return encoded.tobytes()
