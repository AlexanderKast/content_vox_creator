---
name: content-vox-brief
description: >-
  Compuerta de aprobación para la fábrica de contenido (fabrica-box). Se dispara
  ante CUALQUIER pedido de contenido a la fábrica — "dame un carrusel sobre X",
  "hazme un reel de Y", "necesito contenido sobre Z", "un carrusel de las skills"
  — INCLUSO si suena a orden directa de construir. NUNCA construye en el primer
  turno: primero produce un brief (razonamiento en español) + el JSON ejecutable,
  corre `estimate` para validar y costear sin gastar en APIs, y PARA para que
  Alexander apruebe. Solo con aprobación explícita se ejecuta `build`.
---

# content-vox-brief — la compuerta brief → aprobar → construir

Pedir contenido y construirlo NO son el mismo paso. Esta skill mete una compuerta
entre los dos: **investigar → reportar → PARAR → aprobar → ejecutar.**

La etapa de brief **no llama ninguna API paga**. Revisar sale gratis; construir
cuesta. Por eso la compuerta va antes de `build`, nunca después.

## Cuándo se dispara

Cualquier pedido de contenido a la fábrica. Ejemplos:
- "dame un carrusel sobre X"
- "hazme un reel / video de Y"
- "necesito contenido sobre Z"
- "un carrusel de las skills"

**Aunque el pedido suene a orden directa de construir, la regla es la misma:
NUNCA construir en el primer turno.** El primer turno produce el brief y para.

No se dispara para: editar un guion ya aprobado, correr `build` de un JSON que
Alexander ya aprobó, o preguntas sobre la fábrica que no piden contenido nuevo.

## El flujo, paso por paso

### PASO 1 — Entender sin interrogar
Inferí del pedido:
- **modo**: "carrusel" → `carrusel`; "reel"/"video"/"tiktok"/"short" → `video`.
  Si no lo dice y el tema es tutorial denso, sugerí video en la nota de formato
  (ver abajo) pero respetá lo que pidió.
- **marca**: default `alexander`. Solo otra si la nombra (`mile`, `kreoon`).
- **tema y ángulo**: del enunciado.

Preguntá SOLO si algo es genuinamente bloqueante y no inferible. **Máximo 2
preguntas, nunca más.** Si dijo "carrusel", no le preguntes si quiere carrusel.
Si no hay nada bloqueante, no preguntes: seguí al PASO 2.

### PASO 2 — Producir DOS archivos

**a) `briefs/<slug>.brief.md`** — el razonamiento, en español, para que Alexander
lo lea. (La carpeta `briefs/` está en `.gitignore`: son efímeros y regenerables;
lo durable es el JSON en `examples/`.) Si no existe, `mkdir -p briefs`.

El brief DEBE contener, en este orden:
1. **Ángulo elegido y POR QUÉ ese y no otro.**
2. **Hook propuesto + 2 alternativas descartadas con la razón del descarte.** Un
   brief que solo muestra lo elegido es un resumen; lo útil es ver qué se
   descartó y por qué.
3. **Estructura slide por slide en TABLA**: `# | text (en pantalla) | subtitle |
   tease/nota`. Una fila por slide.
4. **CTA + gating**: la pregunta personalizada (nunca genérica).
5. **Lead magnet**: cuál haría falta si hay gating, y si **existe en disco** o
   hay que crearlo. (Chequealo: `assets/lead-magnets/`.)
6. **Costo estimado**: el número REAL de `estimate`, nunca inventado.
7. **"Lo que este contenido NO hace"**: el alcance que se deja fuera a propósito.
8. **Nota de honestidad de formato** cuando aplique (ver sección dedicada).

**b) `examples/<slug>.json`** — el guion ejecutable, input real de `build`.
Estructura (campos que `factory.cli.load_script` acepta):
```json
{
  "mode": "carrusel",
  "brand": "alexander",
  "topic": "...",
  "hook": "...",
  "cta": "...",
  "music_prompt": "...",
  "gating": {
    "gating_question": "comenta QUE VENDES",
    "lead_magnet_path": "assets/lead-magnets/<archivo>.md"
  },
  "beats": [
    { "index": 1, "text": "...", "subtitle": "...", "seconds": 6,
      "assets": [{ "id": "x", "description": "... editorial cutout" }] }
  ]
}
```
Notas:
- `seconds` por slide de carrusel: **4.0–12.0** (usá ~5–6).
- Cada beat necesita `text` no vacío (el carrusel se consume en mudo).
- `assets[].description` va en inglés (es prompt de imagen). Terminá en
  "editorial cutout" / estilo grabado para el look de la marca.
- `gating` es opcional; si lo ponés, `lead_magnet_path` **debe existir en disco**
  o `validate()` rechaza el build.

### PASO 3 — Validar ANTES de mostrar
Corré (usá `python` en Windows, `python3` en mac/linux):
```bash
python -m factory.cli estimate examples/<slug>.json
```
`estimate` corre `validate()` internamente. Si rechaza el guion, **arreglá el
JSON y volvé a correr** hasta que pase. NUNCA le presentes a Alexander un brief
cuyo JSON el pipeline rechazaría — sería hacerle aprobar humo. El brief que le
llega es, por construcción, construible. Pegá la salida real de `estimate` en el
brief (paso 6) y en tu respuesta.

### PASO 4 — PARAR
Presentá el brief y el costo. **Y pará.** No construyas. No digas "¿procedo?" y
sigas de largo. Esperá respuesta real de Alexander.

### PASO 5 — Solo con aprobación explícita: `build`
- "Dale", "hagámosle", "apruebo", "constrúyelo", "listo" = adelante (`python` en
  Windows, `python3` en mac/linux):
  ```bash
  python -m factory.cli build examples/<slug>.json
  ```
- Cualquier corrección = actualizá brief + JSON, **re-validá (PASO 3)**, y volvé
  al PASO 4.
- Silencio o ambigüedad = **preguntá, no asumas.**

## Reglas de contenido que la skill hace cumplir

Ya viven en `script.validate()` — la skill NO las reimplementa ni re-valida por
su cuenta; **genera guiones que las cumplen de entrada** para no perder ciclos:

- **CARRUSEL**: slide 1 = hook disruptivo que **NO enseña** (sin "CÓMO", sin
  "1.", sin entregar el valor). Slides intermedias = valor autónomo + tease. Slide
  final = CTA sin tease. **6–10 slides.**
- **Número hiperespecífico**: al menos uno real. **Si no lo podés verificar, no
  lo inventes** — el brief escribe "dato por verificar" en vez de fabricar una
  cifra. Un número inventado en un brief se vuelve un número inventado publicado.
- **Credenciales exactas**: `8 años en negocios digitales` / `6 años en pauta`.
  Nunca "10+ años" ni redondeos.
- **Cero promesas de ganancia garantizada** ("vas a ganar", "garantizado").
- **Prueba propia** cuando aplique: KREOON, UGC Colombia, LiveCake.

## La sección que hace la diferencia: honestidad de formato

Data real del nicho (investigación Apify, 167 posts, 6 cuentas, julio 2026):
**solo el 3.6% de los posts del nicho son carruseles**, y los que funcionan son
**personales/emocionales, no tutoriales**. Los tutoriales rinden en **video**.

Entonces: si Alexander pide un **carrusel de un tema tutorial**, el brief lo
construye igual (es su decisión, ya la tomó — **no la re-litigues**) PERO incluye
UNA línea honesta, tipo:

> "Este tema es tutorial; la data del nicho (3.6% de posts son carruseles, y
> rinden mejor con temas personales) sugiere que la versión **video** tendría más
> respaldo. Si querés, la armo. Igual acá va el carrusel que pediste."

Una línea. No un sermón. **Alexander decide.**

## El brief lo escribís VOS, no Mistral

El repo tiene `providers/text_llm.py` (Mistral small). **No lo uses para el
brief.** El guion es el 80% del resultado; la regla del router es "usá lo más
barato que haga BIEN el trabajo", y el guion es de los caros: lo escribe el
modelo bueno — vos, en sesión, sin costo extra de API.

## Restricciones

- **NUNCA construir en el primer turno.** La compuerta es el punto entero.
- No toques `script.py`, `router.py`, `cost.py`, `pipeline.py`.
- No reimplementes validaciones existentes — la skill genera guiones que pasan.
- Español en el brief; inglés en cualquier código o prompt de imagen.
- El costo que muestres sale de `estimate`, real, nunca inventado.
