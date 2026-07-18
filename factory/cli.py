"""Entry point.

    python -m factory.cli setup                        # configura tu marca (1ra vez)
    python -m factory.cli estimate examples/musculos.json
    python -m factory.cli build    examples/musculos.json
    python -m factory.cli ingest   --published-url <url> --published-at <iso> --metrics <file.json> [--job-id <id>] [--formula F1]
    python -m factory.cli winners
    python -m factory.cli report
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config, db, feedback
from .formulas import Formula
from .gating import GatingSpec
from .pipeline import Factory
from .router import Asset
from .script import Beat, Mode, Script


def _all_brands() -> dict:
    try:
        return json.loads(config.BRAND_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _default_brand() -> str:
    """First brand in brand.json — so a portable example (one without an
    explicit "brand") works for whoever ran `setup`, not just the original
    owner. Falls back to 'alexander' only if brand.json is missing/empty."""
    brands = _all_brands()
    return next(iter(brands), "alexander")


def _brand_profile(brand: str) -> dict:
    """Pull one brand's profile fields (credentials/proof/founder/hashtags/
    signature) from brand.json. Missing file or brand → empty profile, so a
    fresh clone that hasn't run `setup` yet still loads scripts (the formula
    rules that depend on these just don't bite). Never raises here."""
    return _all_brands().get(brand, {})


def load_script(path: Path) -> Script:
    raw = json.loads(path.read_text(encoding="utf-8"))
    beats = [
        Beat(
            index=item["index"],
            text=item["text"],
            subtitle=item.get("subtitle", ""),
            kicker=item.get("kicker", ""),
            badge=item.get("badge", ""),
            scene=item.get("scene", ""),
            stat=item.get("stat", ""),
            search=item.get("search", ""),
            narration=item.get("narration", ""),
            seconds=float(item.get("seconds", 3.0)),
            sfx=item.get("sfx"),
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

    gating_raw = raw.get("gating")
    gating = (
        GatingSpec(
            gating_question=gating_raw["gating_question"],
            lead_magnet_path=gating_raw["lead_magnet_path"],
            botcake_flow=gating_raw.get("botcake_flow", {}),
        )
        if gating_raw
        else None
    )

    brand = raw.get("brand") or _default_brand()
    profile = _brand_profile(brand)

    return Script(
        mode=Mode(raw["mode"]),
        brand=brand,
        topic=raw["topic"],
        hook=raw["hook"],
        beats=beats,
        cta=raw["cta"],
        music_prompt=raw.get("music_prompt", ""),
        formula=Formula(raw["formula"]) if raw.get("formula") else None,
        series_part=raw.get("series_part"),
        series_total=raw.get("series_total"),
        series_formula=Formula(raw["series_formula"]) if raw.get("series_formula") else None,
        gating=gating,
        loop=raw.get("loop", False),
        series_kicker=raw.get("series_kicker", ""),
        # Brand profile (per-brand, from brand.json) — makes the validators
        # brand-agnostic. A script may also override any of these inline.
        credentials=tuple(raw.get("credentials", profile.get("credentials", []))),
        proof=tuple(raw.get("proof", profile.get("proof", []))),
        founder_name=raw.get("founder_name", profile.get("founderName")),
        hashtags=tuple(raw.get("hashtags", profile.get("hashtags", []))),
        signature=raw.get("signature", profile.get("signature")),
    )


def _cmd_estimate_or_build(args: argparse.Namespace) -> int:
    script = load_script(args.script)
    job_id = args.job_id or f"{script.mode.value}-{uuid.uuid4().hex[:8]}"
    factory = Factory()
    factory.build(job_id, script, dry_run=args.command == "estimate")
    return 0


# --- setup wizard ----------------------------------------------------------

def _ask(prompt: str, default: str = "") -> str:
    """One friendly prompt. Enter keeps the default (shown in brackets)."""
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def _ask_list(prompt: str) -> list[str]:
    raw = input(f"{prompt} (separa con comas, o Enter para saltar): ").strip()
    return [item.strip() for item in raw.split(",") if item.strip()]


def _cmd_setup(args: argparse.Namespace) -> int:
    """Interactive first-run setup. Asks a new user for THEIR branding and
    writes their own brand.json entry + a blank .env — so the shared repo
    carries none of the previous owner's voice, keys, or brand."""
    print("\n=== Configuracion de tu marca ===")
    print("Te voy a hacer unas preguntas. En las que tengan [algo] entre")
    print("corchetes, podes apretar Enter para dejar ese valor por defecto.\n")

    slug = _ask("Nombre corto de tu marca (sin espacios, ej. mimarca)", "mimarca")
    handle = _ask("Tu @ de Instagram/TikTok (ej. @mimarca)", f"@{slug}")
    founder = _ask("Tu nombre (el que dirias en un video, ej. Ana)")

    print("\nColores (en formato #RRGGBB, como en Photoshop):")
    accent = _ask("  Color principal de tu marca", "#D4AF37")
    paper = _ask("  Color de fondo (algo oscuro y calido va bien)", "#2e2318")
    white = _ask("  Color del texto principal", "#F5F1E8")
    font = _ask("\nTipografia para los titulos", "Archivo")

    print("\nVoz e imagen (opcional — Enter para saltar si aun no las tenes):")
    voice_id = _ask("  Voice ID de ElevenLabs")
    character_ref = _ask("  Character ID de Magnific (si usas personaje fijo)")

    print("\nReglas de tus guiones (opcional, se pueden dejar vacias):")
    credentials = _ask_list("  Tu experiencia EXACTA (ej. 5 años en marketing)")
    proof = _ask_list("  Tus marcas/clientes que sirven de prueba")
    hashtags = _ask_list("  Hashtags de tu marca (ej. #minicho, #tips)")
    signature = _ask("  Firma para el final del caption")

    entry = {
        "handle": handle,
        "displayFont": font,
        "quoteFont": "Playfair Display",
        "colors": {"black": "#050505", "gold": accent, "paper": paper, "white": white},
        "dominant": "gold",
        "aesthetic": "custom",
        "grain": 0.12,
        "voiceId": voice_id or None,
        "characterRef": character_ref or None,
        "founderName": founder or None,
        "credentials": credentials,
        "proof": proof,
        "hashtags": hashtags,
        "signature": signature or None,
    }

    # Merge into brand.json (create it if this is a fresh clone).
    try:
        brands = json.loads(config.BRAND_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        brands = {}
    brands[slug] = entry
    config.BRAND_PATH.write_text(
        json.dumps(brands, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nOK: guarde tu marca '{slug}' en brand.json")

    # Create a blank .env from the template if there isn't one yet — never
    # overwrite an existing .env (it may already hold real keys).
    env_path = config.ROOT / ".env"
    example_path = config.ROOT / ".env.example"
    if not env_path.exists() and example_path.exists():
        env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        print("OK: cree un archivo .env en blanco (copia de .env.example)")

    print("\n=== Falta un ultimo paso, a mano ===")
    print("1. Abri el archivo .env y pega TUS claves de API")
    print("   (WaveSpeed, ElevenLabs, etc. — cada una tiene su renglon).")
    print(f"2. En tus guiones, poné  \"brand\": \"{slug}\"")
    print("3. Probá sin gastar:  python -m factory.cli estimate examples/musculos.json")
    print("\nListo. Tu marca quedo configurada.\n")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    """Store one Metricool pull for a published piece. This command never
    talks to Metricool itself — SOLO LECTURA means whoever fetched the
    numbers (a Claude Code session with the Metricool MCP connector, today;
    a standalone API-key provider, later) hands them here as JSON. Missing
    keys in that JSON stay NULL in the database, never a guess."""
    metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    published_at = datetime.fromisoformat(args.published_at).timestamp()

    conn = db.connect()
    feedback.ingest_performance(
        conn,
        published_url=args.published_url,
        published_at=published_at,
        metrics=metrics,
        job_id=args.job_id,
        formula=args.formula,
    )
    print(f"Ingested metrics for {args.published_url}.")
    return 0


def _cmd_winners(args: argparse.Namespace) -> int:
    conn = db.connect()
    winners = feedback.detect_winners(conn)
    if not winners:
        print("Sin ganadores todavia (o datos insuficientes para un promedio).")
        return 0
    for w in winners:
        status = "LISTO PARA RE-RENDER" if w["ready_to_rerender"] else f"esperar (semana {w['weeks_since_published']})"
        print(f"{w['published_url']} — {w['multiplier']}x el promedio — {status}")
        if w["hooks_file"]:
            print(f"  hooks: {w['hooks_file']}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    conn = db.connect()
    report = feedback.build_report(conn)
    print(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="factory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("estimate", "build"):
        sub = subparsers.add_parser(name)
        sub.add_argument("script", type=Path)
        sub.add_argument("--job-id", default=None)
        sub.set_defaults(func=_cmd_estimate_or_build, command=name)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--published-url", required=True)
    ingest.add_argument("--published-at", required=True, help="ISO 8601, e.g. 2026-07-01T00:00:00")
    ingest.add_argument("--metrics", required=True, type=Path, help="JSON file with reach/retention/comments/saved/shares/likes (Metricool's own field names)")
    ingest.add_argument("--job-id", default=None)
    ingest.add_argument("--formula", default=None, choices=[f.value for f in Formula])
    ingest.set_defaults(func=_cmd_ingest)

    winners = subparsers.add_parser("winners")
    winners.set_defaults(func=_cmd_winners)

    report = subparsers.add_parser("report")
    report.set_defaults(func=_cmd_report)

    setup = subparsers.add_parser("setup", help="Configura tu marca (interactivo)")
    setup.set_defaults(func=_cmd_setup)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
