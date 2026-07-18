"""Entry point.

    python -m factory.cli estimate examples/musculos.json
    python -m factory.cli build    examples/musculos.json
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .pipeline import Factory
from .router import Asset
from .script import Beat, Mode, Script


def load_script(path: Path) -> Script:
    raw = json.loads(path.read_text(encoding="utf-8"))
    beats = [
        Beat(
            index=item["index"],
            text=item["text"],
            narration=item.get("narration", ""),
            seconds=float(item.get("seconds", 3.0)),
            assets=[
                Asset(
                    id=asset["id"],
                    description=asset["description"],
                    is_real_entity=asset.get("is_real_entity", False),
                    is_recurring_character=asset.get("is_recurring_character", False),
                    needs_text_in_image=asset.get("needs_text_in_image", False),
                    is_complex_composition=asset.get("is_complex_composition", False),
                )
                for asset in item.get("assets", [])
            ],
        )
        for item in raw["beats"]
    ]
    return Script(
        mode=Mode(raw["mode"]),
        brand=raw.get("brand", "alexander"),
        topic=raw["topic"],
        hook=raw["hook"],
        beats=beats,
        cta=raw["cta"],
        music_prompt=raw.get("music_prompt", ""),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="factory")
    parser.add_argument("command", choices=["estimate", "build"])
    parser.add_argument("script", type=Path)
    parser.add_argument("--job-id", default=None)
    args = parser.parse_args(argv)

    script = load_script(args.script)
    job_id = args.job_id or f"{script.mode.value}-{uuid.uuid4().hex[:8]}"

    factory = Factory()
    factory.build(job_id, script, dry_run=args.command == "estimate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
