"""Gating CTA — the single biggest lever in the research.

Documented case: gating turns 10-30 comments into 1,335 (40-100x). The mechanic
is not "ask people to comment" — it is: promise a real deliverable, require a
personalized comment to unlock it, and route the unlock through a bot flow.

Three rules make this work instead of reading as spam:
  1. The question is personalized ("comenta QUE VENDES"), never a generic
     token ("comenta INFO") — a generic token reads as engagement bait and
     the algorithm plus the audience both know it.
  2. The CTA order is fixed: follow first (framed as the condition to unlock,
     not a favor), then share, then the personalized comment.
  3. The lead magnet must exist before the video does. Promising a deliverable
     that isn't on disk breaks the one asset this brand can't buy back: trust.
     `script.validate()` makes this a hard build failure, not a warning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CTA_ORDER: tuple[str, ...] = ("seguir", "compartir", "comentario_personalizado")

# A gating question that collapses to one of these generic tokens (after
# stripping a leading imperative verb) is not personalized. This is a floor,
# not a substitute for judgment — a two-word question can still be generic.
GENERIC_GATING_WORDS = {"info", "informacion", "listo", "yo", "presente", "aqui", "mas"}

MIN_QUESTION_WORDS = 3


@dataclass(frozen=True)
class GatingSpec:
    gating_question: str          # e.g. "comenta QUE VENDES"
    lead_magnet_path: str         # path on disk, checked by script.validate()
    botcake_flow: dict = field(default_factory=dict)


def is_personalized(gating_question: str) -> bool:
    """A generic single-token ask ("comenta INFO") fails this check; a real
    question ("comenta QUE VENDES") passes."""
    words = gating_question.strip().split()
    if len(words) < MIN_QUESTION_WORDS:
        return False
    tail = words[-1].strip("?.,!").lower()
    return tail not in GENERIC_GATING_WORDS


def build_botcake_spec_md(job_id: str, gating: GatingSpec) -> str:
    """Render the Botcake flow spec as markdown, saved next to the manifest so
    it can be handed to whoever wires the actual bot — this factory does not
    call Botcake, it only specifies what to build there."""
    flow = gating.botcake_flow
    trigger = flow.get("trigger", gating.gating_question)
    dm1_link = flow.get("dm1_link", gating.lead_magnet_path)
    dm1_question = flow.get("dm1_qualifying_question", gating.gating_question)
    tags = flow.get("tags", [])
    dm2_hours = flow.get("dm2_at_hours", 24)
    dm2_message = flow.get(
        "dm2_message",
        "Vi que no habias abierto el link — sigue disponible. Si tienes dudas, respondeme aqui.",
    )

    tags_md = "\n".join(f"  - {tag}" for tag in tags) or "  - (sin tags declarados)"

    return f"""# Botcake flow — {job_id}

## Trigger
Comentario que contiene: `{trigger}`

## CTA order (no reordenar)
1. Seguir (condicion para desbloquear, no favor)
2. Compartir
3. Comentario personalizado: "{gating.gating_question}"

## DM 1 — inmediato
- Link: {dm1_link}
- Pregunta de calificacion: {dm1_question}

## Tags de segmentacion
{tags_md}

## DM 2 — re-engagement
- Dispara a las {dm2_hours}h si no hubo apertura del link.
- Mensaje: {dm2_message}
"""
