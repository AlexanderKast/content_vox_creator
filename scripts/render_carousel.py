"""Render every slide of a carrusel manifest to a numbered mp4.

    python3 scripts/render_carousel.py out/<job>.manifest.json

Produces out/slide-01.mp4 .. slide-NN.mp4, all 1080x1350, respecting
RENDER_CONCURRENCY from .env — Chromium headless competes for CPU, and an
unbounded fan-out here is what takes the machine down.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from factory.config import load as load_config  # noqa: E402

REMOTION_DIR = ROOT / "remotion"
OUT_DIR = ROOT / "out"
COMPOSITION_ID = "CarouselSlide"
EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1350

NPX = "npx.cmd" if sys.platform.startswith("win") else "npx"


def render_slide(manifest: dict, index: int) -> Path:
    output = OUT_DIR / f"slide-{index + 1:02d}.mp4"
    props = {**manifest, "slideIndex": index}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=OUT_DIR, encoding="utf-8"
    ) as handle:
        json.dump(props, handle, ensure_ascii=False)
        props_path = Path(handle.name)

    try:
        subprocess.run(
            [NPX, "remotion", "render", COMPOSITION_ID, str(output), f"--props={props_path}"],
            cwd=REMOTION_DIR,
            check=True,
        )
    finally:
        props_path.unlink(missing_ok=True)

    return output


def probe_dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    stream = json.loads(result.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="render_carousel")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest["mode"] != "carrusel":
        print(f"Manifest mode is '{manifest['mode']}', not 'carrusel'. Nothing to render.", file=sys.stderr)
        return 1

    total = len(manifest["beats"])
    concurrency = max(1, load_config().render_concurrency)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Rendering {total} slides with concurrency={concurrency}...")
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        outputs = list(pool.map(lambda i: render_slide(manifest, i), range(total)))

    print(f"\nRendered {len(outputs)} slides:")
    mismatches = 0
    for path in outputs:
        width, height = probe_dimensions(path)
        ok = (width, height) == (EXPECTED_WIDTH, EXPECTED_HEIGHT)
        mismatches += not ok
        print(f"  {path.name}: {width}x{height} [{'OK' if ok else 'MISMATCH'}]")

    if mismatches:
        print(f"\n{mismatches} slide(s) did not match {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
