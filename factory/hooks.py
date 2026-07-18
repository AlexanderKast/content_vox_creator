"""Five hook variants per script.

The hook is 80% of the video, so testing it should be almost free. This
module writes drafts to `out/<job>.hooks.md` for Alexander to pick from — it
does not render anything. `scripts/render_hooks.py` (phase 4) renders
whichever variants get chosen, from cached assets, at near zero marginal cost.

Free mechanical rephrasings by default (phase 3's original "zero paid APIs"
rule) — pass `llm` (factory.providers.text_llm.TextLLM) to have 4 of the 5
variants actually written instead of templated. Opt-in, see
factory.config.use_llm_copy. The original hook (variant 1) is never
LLM-rewritten: it already passed the formula's loss-framing validators
(factory.script._validate_f1's hook check), and a rewrite could silently
break that. Any LLM failure falls back to the templates for all 5.
"""

from __future__ import annotations

import re

from .formulas import Formula
from .providers.text_llm import TextLLM
from .script import Script


def _first_number(text: str) -> str | None:
    match = re.search(r"\d+[.,]?\d*%?", text)
    return match.group(0) if match else None


_LEADING_HOW_PATTERN = re.compile(r"^c[oó]mo\s+", re.IGNORECASE)


def _lowered(text: str) -> str:
    text = text.strip().rstrip(".")
    return text[0].lower() + text[1:] if text else text


def _declarative(text: str) -> str:
    """Strip a leading "cómo/como" so a how-to topic reads as a clause
    ("automatizar tu primer proceso...") instead of a dangling question
    fragment ("cómo automatizar...") inside another question."""
    return _LEADING_HOW_PATTERN.sub("", _lowered(text))


def _template_variants(script: Script) -> list[str]:
    hook = script.hook.strip()
    topic = script.topic.strip().rstrip(".")
    number = _first_number(hook) or _first_number(script.full_text)

    variants = [
        hook,  # original — already the loss-framed version for F1/F2
        f"¿Sabías que puedes {_declarative(topic)}?",
        (f"{number}: la razón por la que {_declarative(topic)}." if number
         else f"La razón real detrás de {_declarative(topic)}."),
        f"Todo el mundo cree que sabe {_declarative(topic)}. Se equivocan.",
        f"Para. Si esto te suena, esto es sobre {_declarative(topic)} — sigue leyendo.",
    ]

    if script.formula is Formula.F2:
        variants[3] = f"Nadie te dice esto sobre {_declarative(topic)} porque no les conviene."

    return variants


def _llm_variants(script: Script, llm: TextLLM) -> list[str] | None:
    formula_note = f" La formula declarada es {script.formula.value}." if script.formula else ""
    prompt = (
        f"Escribe exactamente 4 variantes de hook (primeras 1-2 lineas de un video), en "
        f"espanol, para un video sobre: \"{script.topic}\".\n"
        f"El hook original, ya validado, es: \"{script.hook}\".{formula_note}\n"
        f"Cada variante debe ser una forma DISTINTA de enganchar con la misma idea "
        f"(pregunta, numero/dato, contradiccion, llamado directo) — no parafrasees el "
        f"original, escribe algo que un humano realmente diria. Una variante por linea, "
        f"sin numerar, sin comillas, sin texto extra."
    )
    text = llm.generate(prompt, max_tokens=300)
    variants = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
    return variants[:4] if len(variants) >= 4 else None


def generate_hooks(script: Script, llm: TextLLM | None = None) -> list[str]:
    variants = None
    if llm is not None:
        try:
            llm_variants = _llm_variants(script, llm)
            if llm_variants:
                variants = [script.hook.strip(), *llm_variants]
        except Exception:  # noqa: BLE001 - degrade to templates, never block the build
            pass

    if variants is None:
        variants = _template_variants(script)

    # de-dupe while preserving order — a short topic can make templates collide
    seen: list[str] = []
    for v in variants:
        if v not in seen:
            seen.append(v)
    return seen


def render_hooks_md(job_id: str, script: Script, llm: TextLLM | None = None) -> str:
    variants = generate_hooks(script, llm)
    lines = [f"# Hook variants — {job_id}", ""]
    for i, variant in enumerate(variants, start=1):
        lines.append(f"{i}. {variant}")
    lines.append("")
    lines.append("Elige una (o pide una re-escritura) antes de correr `scripts/render_hooks.py`.")
    return "\n".join(lines) + "\n"
