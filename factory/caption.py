"""Instagram/TikTok caption generator.

Zero paid calls by default. The SEO questions here are templated from the
topic, not pulled from real search-volume data — this factory doesn't call a
keyword-research API, and pretending otherwise would be inventing data.
Treat the template output as a strong first draft, not a finished caption.

Pass `llm` (factory.providers.text_llm.TextLLM) to have the summary and SEO
questions actually written instead of templated — opt-in, see
factory.config.use_llm_copy. Any LLM failure (network, bad response) falls
back to the template silently; a caption is never blocked on a text-gen call.
"""

from __future__ import annotations

import re

from .providers.text_llm import TextLLM
from .script import Script

# Generic fallbacks used only when a brand didn't declare its own in
# brand.json (script.hashtags / script.signature). Nothing here is tied to one
# person — a brand's own hashtags and sign-off come from its profile.
DEFAULT_HASHTAGS = ["#contenido", "#reels", "#tips"]
DEFAULT_SIGNATURE = "— gracias por llegar hasta aqui."


def _summary(script: Script) -> str:
    """2-4 lines of value legible without audio — the caption has to work for
    someone who never presses play."""
    lines = [script.hook.strip()]
    body_beats = [b for b in script.beats if b.text.strip()][:3]
    lines.extend(f"→ {b.text.strip().capitalize()}" for b in body_beats)
    return "\n".join(lines[:4])


_LEADING_HOW_PATTERN = re.compile(r"^c[oó]mo\s+", re.IGNORECASE)


def _seo_questions(script: Script) -> list[str]:
    """Templated the way people actually type into IG/Google search, not
    natural prose. Three variants: how-to, why, what-if."""
    topic = script.topic.strip().rstrip(".")
    topic_lower = topic[0].lower() + topic[1:] if topic else topic
    declarative = _LEADING_HOW_PATTERN.sub("", topic_lower)
    return [
        f"¿Cómo {declarative}?",
        f"¿Por qué {declarative}?",
        f"¿Qué pasa si no sabes esto sobre {declarative}?",
    ]


def _llm_summary(script: Script, llm: TextLLM) -> str | None:
    prompt = (
        f"Escribe un resumen de 2 a 4 lineas cortas para un caption de Instagram/TikTok, "
        f"en espanol, tono directo y sin relleno, para un video sobre: \"{script.topic}\".\n"
        f"El hook del video es: \"{script.hook}\".\n"
        f"Tiene que dar valor legible SIN ver el video (mucha gente no le da play). "
        f"No repitas el hook literal. No uses hashtags ni emojis. Solo las lineas del resumen."
    )
    text = llm.generate(prompt, max_tokens=200)
    return text.strip() or None


def _llm_seo_questions(script: Script, llm: TextLLM) -> list[str] | None:
    prompt = (
        f"Escribe exactamente 3 preguntas cortas, en espanol, tal como la gente las "
        f"buscaria de verdad en Instagram o Google, sobre este tema: \"{script.topic}\".\n"
        f"Una pregunta por linea, sin numerar, sin comillas, sin texto extra antes o despues."
    )
    text = llm.generate(prompt, max_tokens=150)
    questions = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
    return questions[:3] if len(questions) >= 3 else None


def _hashtags(script: Script) -> list[str]:
    # Brand's own hashtags (brand.json) first, generic fallbacks after.
    tags = list(script.hashtags) + DEFAULT_HASHTAGS
    seen: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.append(tag)
    return seen[:5] if len(seen) >= 4 else seen


def generate_caption(script: Script, llm: TextLLM | None = None) -> str:
    parts: list[str] = []

    if script.gating is not None:
        parts.append(f"👉 {script.gating.gating_question}")
        parts.append("")

    summary = None
    questions = None
    if llm is not None:
        try:
            summary = _llm_summary(script, llm)
            questions = _llm_seo_questions(script, llm)
        except Exception:  # noqa: BLE001 - degrade to template, never block the caption
            pass

    parts.append(summary or _summary(script))
    parts.append("")
    parts.extend(f"❓ {q}" for q in (questions or _seo_questions(script)))
    parts.append("")
    parts.append(" ".join(_hashtags(script)))
    parts.append("")
    parts.append(script.signature or DEFAULT_SIGNATURE)

    text = "\n".join(parts)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
