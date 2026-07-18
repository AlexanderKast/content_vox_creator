# Legacy — snapshot del diseño original

`original-snapshot/` es el estado ORIGINAL del proyecto, recuperado de
`fabrica-box.zip` (anidado dentro de `files.zip` / `files 2 .zip`, entregas
empaquetadas que existían en la raíz antes de que el repo tuviera git).

Sirve como **línea base**: es lo más cercano a un "commit inicial" que existía
antes de que el proyecto entrara a control de versiones (2026-07-17). Contra esto
se pueden leer los deltas que la auditoría (`../../AUDIT.md`) no pudo derivar por
falta de historia git.

## Qué tiene el original que ya cambió

El snapshot es notablemente más chico que el estado actual. NO estaban aún:

- **factory/**: `formulas.py`, `gating.py`, `feedback.py`, `hooks.py`,
  `caption.py`, `align.py`, `rhythm.py`, `chroma.py`, `timing.py`
- **providers/**: `character_magnific.py`, `text_llm.py`
- **remotion/src/**: `design.ts` y 12 de los 17 componentes actuales (el original
  solo tenía Background, Cutout, KineticText, SlideCounter, Underline)

Todo eso se agregó después (motor de fórmulas, gating, feedback, retención,
chroma key, design system, tier CHARACTER real, etc.).

## Qué se excluyó al versionarlo

Por política de secretos (igual que el repo vivo): se omitieron
`fabrica-box/brand.json` y `fabrica-box/SKILL.md` del snapshot. El resto
(código, examples, `.env.example`) se conservó tal cual.

## Docs sueltos (carpeta padre `docs/`)

- `fabrica-videos-box-remotion.md` — doc de diseño de la parte Remotion.
- `prompts-claude-code.md` / `prompts-claude-code-fase-3-5.md` — prompts de las
  fases de construcción, recuperados de los mismos zips.
