---
name: content-vox-news
description: >-
  Compuerta de aprobación para contenido de noticias/política (fabrica-box),
  con research obligatorio y capítulos. Se dispara ante pedidos de video/reel/
  carrusel sobre un evento actual, una figura pública, o un tema político —
  "hazme un video sobre X", "un carrusel de lo que pasó con Y", "un explicativo
  de 3 capítulos sobre Z" — INCLUSO si no dan tema (investigá y elegí uno vos).
  Comparte el patrón de compuerta de content-vox-brief (brief → estimate →
  PARAR → aprobar → build) pero es una categoría de contenido distinta: sin
  fórmula de marca personal, sin credenciales/prueba/gating, con investigación
  obligatoria y reglas de seguridad para figuras públicas reales.
---

# content-vox-news — noticias/política investigadas, con capítulos

Misma compuerta que `content-vox-brief` (**investigar → reportar → PARAR →
aprobar → ejecutar**), pero para una categoría de contenido distinta:
noticias, política, eventos actuales. No es contenido de marca personal de
Alexander — es objetivo, investigado, y toca personas reales con nombre. Por
eso es un skill separado, no una opción de `content-vox-brief`.

## Cuándo se dispara

Pedidos de contenido sobre un evento actual, una figura pública, o un tema
político. Ejemplos:
- "hazme un video sobre [evento actual]"
- "un explicativo de 3 capítulos sobre X"
- "qué está pasando con Y" (si de ahí sale un pedido de contenido)
- sin tema: "hazme una noticia" / "un video de algo que esté pasando" →
  investigá vos y elegí el ángulo.

No se dispara para contenido de marca personal de Alexander (KREOON, UGC
Colombia, tips de creación de contenido) — eso sigue siendo
`content-vox-brief`.

## El flujo, paso por paso

### PASO 0 — Investigar SIEMPRE (nuevo respecto a content-vox-brief)

Esta skill nunca escribe un guion sobre una afirmación sin verificar.

- **Si Alexander dio un tema**: investigalo (Perplexity/WebSearch) para
  verificar los hechos, fechas, y cifras concretas antes de guionar. Un dato
  mal verificado en un video de noticias no es un error de marca — es un
  error de hecho, publicado.
- **Si NO dio tema**: investigá eventos actuales (Perplexity/WebSearch,
  noticias de las últimas 48-72h) y elegí el que mejor sirva para un
  explicativo visual (tiene ángulo claro, no requiere contexto previo pesado,
  no es puramente especulativo). Decí en el brief POR QUÉ ese evento y no
  otro.
- Guardá 2-3 fuentes (URL o nombre del medio) en el brief — no hace falta
  citarlas en el video, pero si Alexander pregunta "de dónde salió esto"
  tiene que haber respuesta.

### PASO 1 — Entender sin interrogar

Igual que `content-vox-brief`: infiere modo (carrusel/video/reel), marca
(default `alexander`), y de la guidance prompt sacá:
- **tema**: si lo dio, o el que investigaste en el PASO 0.
- **capítulos**: número al final del pedido ("3 capítulos") → `chapters`.
  **Default 1, máximo 4.** Cada capítulo es ~30s (25-35s de slack) —
  ver `factory/script.py::validate()`. Si pide más de 4, avisale que el
  límite hoy es 4 y seguí con 4 (no rechaces el pedido entero por esto).

Máximo 2 preguntas si algo es genuinamente bloqueante — igual que
`content-vox-brief`.

### PASO 2 — Producir brief + JSON

Mismo par de archivos que `content-vox-brief` (`briefs/<slug>.brief.md` +
`examples/<slug>.json`), MISMO schema JSON (`factory.cli.load_script`), con
estas diferencias:

- **`chapters`**: en el JSON top-level cuando > 1. Ejemplo:
  `"chapters": 3` para un video de ~90s en 3 partes.
- **Marcador de capítulo en pantalla**: el primer beat de cada capítulo lleva
  `"kicker": "CAPÍTULO 2 DE 3"` (campo `Beat.kicker`, ya existe — no hace
  falta código nuevo).
- **`formula`**: nunca lo declares. Este contenido no pasa por F1-F5 (esas
  reglas son de marca personal — credenciales, prueba propia, CTA triple — no
  aplican a una noticia objetiva).
- **Template sugerido**: `vox-paper` (el look Vox real) — usalo salvo que
  Alexander pida otro. Igual respeta el default de `brand.json` si no dice
  nada.
- **Figura pública real (persona nombrada, con cargo)**: el asset lleva
  ```json
  { "id": "...", "description": "a government official speaking at a podium",
    "is_real_entity": true, "is_public_figure": true }
  ```
  Reglas, sin excepción:
  - `is_real_entity` y `is_public_figure` van SIEMPRE juntos — una figura
    pública es SIEMPRE una foto real (`Tier.PHOTO`, Apify), **nunca
    generada**. `script.validate()` rechaza el build si falta
    `is_real_entity` — no es opcional, es un check de código.
  - **El nombre de la persona NUNCA va en `description`.** Describí por
    cargo/rol/contexto visual ("a head of state at a press conference"), no
    por nombre. Esto no lo valida el código — es disciplina de quien escribe
    el JSON (vos). Un nombre propio en el prompt de imagen es el error a no
    cometer.
  - El pipeline ya tapa los ojos automáticamente (`factory/redact.py`, local,
    sin costo) y Remotion ya la ubica en el placement más chico/alejado
    (`DISTANT_PLACEMENT` en `design.ts`) — no hace falta pedir nada de eso en
    el prompt, es automático una vez que las dos banderas están puestas.
  - **Apify (`Tier.PHOTO`) puede igual devolver 0 resultados** para una query
    muy específica o rara (normal en cualquier scraper — el actor
    `hooli~google-images-scraper`, en uso desde 2026-07-18, ya funciona bien
    en general). Si pasa, el beat construye igual pero sin esa imagen
    (degradación silenciosa, `factory/pipeline.py::_produce_photo` devuelve
    `None`). Después de un `build`, **revisá el manifest** —
    `out/<job-id>.manifest.json`, campo `beats[i].assets` — y si un beat con
    figura pública salió con `assets: []`, avisale a Alexander que esa foto
    no se pudo scrapear (nunca la reemplaces con una imagen generada: sin
    foto real, ese beat va solo con el fondo/kicker, no con un rostro
    inventado).

### PASO 3 — Validar ANTES de mostrar

Igual que `content-vox-brief`:
```bash
python -m factory.cli estimate examples/<slug>.json
```
Si `chapters > 1` y `estimate` rechaza por duración, el rango exacto que
pide es `25*chapters` a `35*chapters` segundos — ajustá `seconds` por beat
hasta caer en rango.

### PASO 4 — PARAR

Igual que `content-vox-brief`: presentá brief + costo + fuentes investigadas,
y **pará**. Nunca construyas en el mismo turno.

### PASO 5 — Solo con aprobación explícita: `build`

Igual que `content-vox-brief`.
```bash
python -m factory.cli build examples/<slug>.json
```
Después del build, si hubo algún asset `is_public_figure`, revisá el
manifest (ver nota de Apify arriba) antes de dar el trabajo por terminado.

## Reglas de contenido

A diferencia de `content-vox-brief`, **ninguna** regla de `validate_formula`/
`validate_transversal` aplica (esas viven bajo `script.formula`, que acá
siempre es `None`). Las que SÍ aplican, siempre:

- **Hook no vacío**, CTA no vacío (regla genérica de `validate()`).
- **Carrusel**: 6-10 slides, cada uno con `text` no vacío.
- **Figura pública → `is_real_entity` + `is_public_figure` juntos**, siempre
  (código, ver PASO 2).
- **Nunca el nombre de una figura pública en `description`** (disciplina, no
  código — ver PASO 2).
- **Sin cifra sin verificar**: igual que `content-vox-brief`, si no lo
  verificaste en el PASO 0, el brief dice "dato por verificar", nunca lo
  inventa.
- **Objetividad**: esto no es contenido de opinión de Alexander — no le
  metas la voz/postura de él a menos que lo pida explícitamente.

## El brief lo escribís VOS, no un LLM automático

Igual que `content-vox-brief`: el guion final lo escribís vos, en sesión, con
la investigación del PASO 0 como base. No hay un paso de "generar guion
automáticamente sin supervisión" — la compuerta (PARAR antes de `build`) es
justamente el punto de control humano.

## Restricciones

- **NUNCA construir en el primer turno.**
- No toques `script.py`, `router.py`, `pipeline.py`, `redact.py`, `cost.py`.
- Español en el brief; inglés en cualquier prompt de imagen.
- El costo que muestres sale de `estimate`, real, nunca inventado.
- Ante cualquier duda sobre si algo cruza una línea de difamación/semejanza
  con una persona real, PARÁ y preguntale a Alexander en vez de decidir solo.
