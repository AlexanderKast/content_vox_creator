"""Render the first 3 seconds of every hook variant for a job.

    python3 scripts/render_hooks.py out/<job>.manifest.json

Reads the sibling out/<job>.hooks.md (written by factory.hooks during build)
and renders one short clip per numbered variant, reusing the job's already-
cached assets and SFX — the whole point is testing the hook, the 80% of the
video that matters, for near-zero marginal cost.

Produces out/<job>.hook-01.mp4 .. hook-05.mp4, all matching the job's own
width/height, ~3s each. Respects RENDER_CONCURRENCY from .env for the same
reason scripts/render_carousel.py does: Chromium headless competes for CPU.
"""

from __future__ import annotations

import argparse
import json
import re
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
COMPOSITION_ID = "BoxVideo"
CLIP_SECONDS = 3.0

NPX = "npx.cmd" if sys.platform.startswith("win") else "npx"

_VARIANT_LINE = re.compile(r"^\s*\d+\.\s+(.*\S)\s*$")


def load_hook_variants(hooks_md_path: Path) -> list[str]:
    variants = []
    for line in hooks_md_path.read_text(encoding="utf-8").splitlines():
        match = _VARIANT_LINE.match(line)
        if match:
            variants.append(match.group(1))
    return variants


def _clip_props(manifest: dict, variant_text: str) -> dict:
    if not manifest["beats"]:
        raise ValueError("Manifest has no beats to build a hook clip from.")

    first_beat = manifest["beats"][0]
    clip_beat = {
        **first_beat,
        "text": variant_text,
        "seconds": CLIP_SECONDS,
        "sequenceFrom": 0,
        # The variant's wording won't match the original word-level timing —
        # force the estimated fallback rather than land words on stale frames.
        "wordTimings": None,
    }
    return {**manifest, "mode": "video", "beats": [clip_beat]}


def render_variant(manifest: dict, index: int, variant_text: str) -> Path:
    output = OUT_DIR / f"{manifest['jobId']}.hook-{index + 1:02d}.mp4"
    props = _clip_props(manifest, variant_text)

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


def probe_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="render_hooks")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    hooks_md_path = args.manifest.parent / f"{manifest['jobId']}.hooks.md"
    if not hooks_md_path.exists():
        print(f"No hooks file at {hooks_md_path} — did the build run factory.hooks?", file=sys.stderr)
        return 1

    variants = load_hook_variants(hooks_md_path)
    if not variants:
        print(f"No numbered variants found in {hooks_md_path}.", file=sys.stderr)
        return 1

    concurrency = max(1, load_config().render_concurrency)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Rendering {len(variants)} hook variants with concurrency={concurrency}...")
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        outputs = list(
            pool.map(lambda item: render_variant(manifest, item[0], item[1]), enumerate(variants))
        )

    print(f"\nRendered {len(outputs)} hook clips:")
    mismatches = 0
    for path, variant in zip(outputs, variants):
        duration = probe_duration_seconds(path)
        ok = abs(duration - CLIP_SECONDS) <= 0.5
        mismatches += not ok
        print(f"  {path.name}: {duration:.2f}s [{'OK' if ok else 'MISMATCH'}] — \"{variant}\"")

    if mismatches:
        print(f"\n{mismatches} clip(s) did not land near {CLIP_SECONDS}s.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
