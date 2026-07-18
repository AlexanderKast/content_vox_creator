"""The five viral formulas.

Reverse-engineered from 34 transcribed videos of the top 5 AI/business referents
and metrics from 180 posts (skill `reels-formulas-virales-alexander`). This file
turns that research into a registry the rest of the codebase enforces against,
instead of leaving it as a comment nobody checks.

F3 is not a bug: it is the documented limit of this factory. It is the format
with the highest reach of all five, and it cannot be fabricated — a selfie with
real, unedited energy is precisely what a rendering pipeline cannot produce.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Formula(str, Enum):
    F1 = "F1"  # TUTORIAL_DENSO
    F2 = "F2"  # KILL_SHOT
    F3 = "F3"  # OPINION_CRUDA
    F4 = "F4"  # EXPERIMENTO
    F5 = "F5"  # SERIE


@dataclass(frozen=True)
class FormulaSpec:
    code: Formula
    name: str
    min_seconds: float | None
    max_seconds: float | None
    phases: tuple[str, ...]
    description: str
    buildable: bool = True
    rejection_message: str | None = None


FORMULAS: dict[Formula, FormulaSpec] = {
    Formula.F1: FormulaSpec(
        code=Formula.F1,
        name="TUTORIAL_DENSO",
        min_seconds=75,
        max_seconds=100,
        phases=(
            "hook_perdida",          # 0-4s, inclusive-loss framing
            "agitacion_latam",       # 4-15s, vivid LATAM scene
            "promesa_minimizada",
            "cuerpo_lista",          # numbered list, 3-6 items
            "prueba_propia",         # KREOON / UGC Colombia / LiveCake / real client
            "cta_triple",            # follow -> share -> personalized comment (gating)
        ),
        description="Densidad + autoridad. El formato de captación por excelencia.",
    ),
    Formula.F2: FormulaSpec(
        code=Formula.F2,
        name="KILL_SHOT",
        min_seconds=33,
        max_seconds=60,
        phases=("hook", "promesa_ingreso", "mecanismo", "cta"),
        description=(
            "Promesa de INGRESO, no de ahorro. \"Se lo puedes cobrar a un "
            "cliente por $X\", nunca \"ahorras X\"."
        ),
    ),
    Formula.F3: FormulaSpec(
        code=Formula.F3,
        name="OPINION_CRUDA",
        min_seconds=20,
        max_seconds=40,
        phases=(),
        description="Selfie sin editar, energia real. El formato de mayor alcance.",
        buildable=False,
        rejection_message=(
            "F3 se graba a camara, no se fabrica. Este es el formato que mas "
            "alcance genera — grabalo tu."
        ),
    ),
    Formula.F4: FormulaSpec(
        code=Formula.F4,
        name="EXPERIMENTO",
        min_seconds=30,
        max_seconds=60,
        phases=("hook", "setup", "prompts_en_pantalla", "resultado", "cta"),
        description="Prompts reales, literales, en pantalla — no descritos, mostrados.",
    ),
    Formula.F5: FormulaSpec(
        code=Formula.F5,
        name="SERIE",
        min_seconds=None,
        max_seconds=None,
        phases=(),
        description="Parte N de M. Usa F1 o F2 por dentro; declara ambas cosas.",
    ),
}


def spec(formula: Formula) -> FormulaSpec:
    return FORMULAS[formula]
