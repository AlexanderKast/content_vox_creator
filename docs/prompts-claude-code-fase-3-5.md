# Prompts Claude Code — Fábrica Box · Fases 3 a 5

Continúan `prompts-claude-code.md` (fases 1 y 2).
**No arranques estas sin haber cerrado la fase 2** — sin chroma key ni SFX básicos no hay video, y optimizar viralidad sobre algo que no renderiza es pulir humo.

Orden deliberado: **fase 3 antes que fase 4.** La fase 3 es lógica pura, sin APIs pagas, y toca la palanca documentada más grande (gating, 40-100x en comentarios). La fase 4 es oficio de retención. Si solo tienes tiempo para una, es la 3.

---

## FASE 3 — Motor viral (lógica pura, cero APIs nuevas)

```
Estás en `fabrica-box`. Lee README.md, `factory/script.py` y `factory/router.py`.

CONTEXTO ESTRATÉGICO (no lo re-litigues, es investigación propia validada):
Existe una skill del usuario, `reels-formulas-virales-alexander`, con ingeniería
inversa real de 34 videos transcritos de los 5 referentes top de IA y métricas de
180 posts. Si tienes acceso a `/mnt/skills/user/reels-formulas-virales-alexander/`
o `.claude/skills/`, LÉELA COMPLETA antes de escribir código: es la fuente de
verdad de este trabajo. Si no la encuentras, dímelo y te la paso — no inventes las
fórmulas.

TAREA: convertir esa investigación en reglas que el código haga cumplir. Hoy
`script.py` valida estructura genérica; debe validar la estructura de la fórmula
específica que declara cada guion.

--- 1. factory/formulas.py ---
Un enum/registro con las 5 fórmulas y su estructura obligatoria:

  F1 TUTORIAL_DENSO      75-100s · 6 fases · autoridad + captación
  F2 KILL_SHOT           33-60s  · promesa de INGRESO, no de ahorro
  F3 OPINION_CRUDA       20-40s  · selfie sin editar
  F4 EXPERIMENTO         30-60s  · prompts reales en pantalla
  F5 SERIE               parte N de M · usa F1 o F2 por dentro

Cada fórmula declara: rango de duración, fases requeridas en orden, y sus reglas
propias.

IMPORTANTE — F3 ES UN CASO ESPECIAL: es "sin edición pulida, selfie, energía
real". Esta fábrica NO puede producirla y no debe intentarlo. Si un guion declara
F3, `validate()` debe rechazarlo con un mensaje claro: "F3 se graba a cámara, no
se fabrica. Este es el formato que más alcance genera — grábalo tú."
No es un bug. Es el límite del sistema, explícito.

--- 2. Validadores de estructura por fórmula ---
Extiende `script.validate()`. Cada guion declara `formula` y se valida contra ella:

- F1 debe tener: hook inclusivo-pérdida (0-4s), agitación con escena vívida LATAM
  (4-15s), promesa minimizada, cuerpo con lista numerada de 3-6 ítems,
  PRUEBA PROPIA (referencia a KREOON / UGC Colombia / LiveCake / cliente real),
  y CTA triple.
- F2 debe contener promesa de ingreso ("se lo puedes cobrar a un cliente por $X"),
  no de ahorro. Rechaza si solo promete ahorrar.
- F4 debe incluir los prompts literales en `text` de algún beat.
- F5 debe declarar parte N de M y la fórmula interna.

--- 3. Validadores transversales (aplican a todas) ---
- NÚMEROS HIPERESPECÍFICOS: al menos un número concreto en el guion.
  "ahorra 63%" pasa; "ahorra mucho" no. La especificidad ES la credibilidad.
- AUTO-DIÁLOGO: F1 debe incluir al menos una objeción del avatar respondida
  ("Pero Alexander, ¿y si no sé nada de código?" → respuesta).
- SIN PROMESAS DE GANANCIA GARANTIZADA: rechaza "vas a ganar", "garantizado",
  "seguro ganas". Permite "se lo puedes cobrar", "puedes llegar a". Esto no es
  cosmético: es riesgo legal y de marca.
- UNA IDEA POR VIDEO: si el guion declara dos tesis, sugiere partirlo en serie F5.
- CREDENCIALES EXACTAS: si el guion menciona experiencia, debe decir 8 años en
  negocios digitales o 6 años en pauta. Rechaza "10+ años" o similar. Innegociable.

--- 4. factory/gating.py ---
La palanca más grande del research: el gating multiplica comentarios 40-100x
(caso documentado: 10-30 → 1,335).

- Todo guion con CTA de gating declara: `gating_question` (pregunta PERSONALIZADA,
  no palabra genérica — "comenta QUÉ VENDES", no "comenta INFO"),
  `lead_magnet_path` y `botcake_flow` (spec del flujo).
- `validate()` rechaza el build si hay gating y `lead_magnet_path` no existe en
  disco. Regla: prometer un entregable que no existe rompe la confianza, que es el
  activo más caro de la marca. El build falla, no advierte.
- El CTA debe seguir el orden validado: (1) seguir como condición no como favor,
  (2) compartir, (3) comentario personalizado.
- Genera el spec de Botcake como .md junto al manifest: trigger, DM 1 con link +
  pregunta de calificación, tags de segmentación, DM 2 de re-engagement a 24h.

--- 5. factory/caption.py ---
Genera el caption completo con la fórmula SEO validada:
  1. CTA de gating
  2. Resumen del guion en 2-4 líneas (valor legible sin audio)
  3. 3 preguntas TAL COMO la gente las buscaría en Instagram/Google
  4. 4-5 hashtags (mezcla ES + EN)
  5. Firma emocional consistente
Sale como `out/<job>.caption.txt`.

--- 6. factory/hooks.py ---
Dado un guion, produce 5 variantes de hook siguiendo el patrón de su fórmula.
No las renderiza todavía — solo las escribe a `out/<job>.hooks.md` para que yo
elija. El hook es el 80% del video; probarlo debe ser barato.

RESTRICCIONES DURAS:
- Esta fase NO llama ninguna API paga. Es lógica pura. Si crees que necesitas una,
  para y pregúntame.
- No toques `brand.json`, `router.py` ni el orden del pipeline.
- No rompas los ejemplos existentes: actualiza `examples/*.json` con su campo
  `formula` para que sigan pasando.
- Código en inglés, comunicación en español.

CRITERIO DE ÉXITO (pega la salida real, no la describas):
  python3 -m factory.cli estimate examples/musculos.json
  python3 -m factory.cli estimate examples/carrusel-ia.json
Más tests que demuestren que las reglas MUERDEN:
  - guion F3 → rechazado con el mensaje de "grábalo tú"
  - guion F1 sin prueba propia → rechazado
  - guion sin números específicos → rechazado
  - guion con "vas a ganar garantizado" → rechazado
  - gating sin lead magnet en disco → rechazado
  - guion con "10+ años" → rechazado
Una regla que no bloquea es decoración.

REPORTA: qué reglas quedaron activas, cuáles no pudiste implementar y por qué.
```

---

## FASE 4 — Motor de retención

```
Contexto: `fabrica-box`, fase 3 cerrada. Ahora el oficio: que el video se sienta
vivo. Trabaja en orden; no pases al siguiente hasta que el anterior corra.

--- 1. ALINEACIÓN FORZADA DE SUBTÍTULOS ---
Hoy el texto entra con timing estimado. Debe entrar en el golpe exacto de la voz.
- Usa Whisper local (NO la API — es audio propio y ya generado, no hay razón para
  pagar por transcribir lo que nosotros mismos sintetizamos) para sacar timestamps
  por palabra del mp3 de ElevenLabs.
- Guarda los word timings en el manifest, por beat.
- En Remotion, `KineticText` recibe los timings reales y cada palabra aterriza en
  su frame. Mantén el fallback estimado si no hay timings: degradación elegante.
- Criterio: el manifest contiene word timings y el preview muestra el texto
  sincronizado con la voz.

--- 2. VALIDADOR DE RITMO ---
La regla "nada estático más de 1.2s" hoy es un comentario. Hazla medible.
- `factory/rhythm.py`: recorre el manifest y verifica que exista un cambio visual
  (entrada de asset, cambio de texto, subrayado) al menos cada 1.2s de timeline.
- Si un tramo está muerto, reporta el rango exacto en segundos y sugiere dónde
  meter un elemento.
- Corre automáticamente en `build` y advierte fuerte (no bloquea: el ritmo es
  criterio, no ley).

--- 3. SFX POR TIPO DE ENTRADA ---
Si la fase 2 ya montó SFX, extiéndelo. Si no, móntalo aquí.
- Mapa: entrada de cutout → "pop"; corte entre beats → "whoosh"; remate/número
  clave → "impact"; subrayado → "marker".
- Genera cada SFX ÚNICO una sola vez y reúsalo. El mismo "pop" va en los 11 beats;
  generarlo 11 veces es pagar 11 veces por el mismo archivo.
- Posición: el frame EXACTO de la entrada, no aproximado. Un SFX 3 frames tarde se
  siente peor que no ponerlo.
- El estimate debe contar SFX únicos, no beats.

--- 4. LOOP EN MODO VIDEO ---
El carrusel ya loopea. El video no.
- Que el último segundo del video pueda encadenar con el primero sin salto visible.
- El loop dispara replays, y el algoritmo lee replays como retención >100%.
- Hazlo opcional por guion (`loop: true`), no forzado: no todo remate admite loop.

--- 5. VARIANTES DE HOOK RENDERIZADAS ---
La fase 3 escribió 5 hooks. Ahora renderízalos.
- `scripts/render_hooks.py`: renderiza solo los primeros 3 segundos de cada
  variante, mismo job, mismos assets cacheados.
- Salen 5 mp4 de 3s para elegir/testear.
- Costo casi cero: los assets ya están en caché. Ese es el punto — probar el 80%
  del video por el 5% del costo.

RESTRICCIONES DURAS:
- Respeta RENDER_CONCURRENCY (default 1). Chromium headless compite por CPU con
  Whisper y FFmpeg; sin semáforo se cae el equipo. Esto ya nos pasó.
- Whisper local, no API.
- Cero credenciales en código.
- Si agregas dependencia, pregunta antes.
- Nunca reintentes a ciegas una llamada que cobra.

CRITERIO DE ÉXITO: build completo de `examples/musculos.json` que produzca
manifest con word timings + SFX posicionados por frame, reporte de ritmo sin
tramos muertos, y 5 hooks de 3s renderizados. Pega la salida real.

REPORTA breve: qué funciona, qué dependencias agregaste, costo real de un video.
```

---

## FASE 5 — El bucle de aprendizaje (el superpoder de verdad)

> Esta es la que ningún sistema de referencia tiene. Una fábrica que produce es
> una fábrica. Una que **mide lo que produjo y ajusta** es un activo compuesto.

```
Contexto: `fabrica-box`, fases 3 y 4 cerradas. El sistema ya produce. Ahora tiene
que aprender de lo que publica.

El usuario tiene Metricool conectado por MCP (cuentas de Instagram y TikTok).

--- 1. factory/feedback.py ---
- Ingesta: por cada pieza publicada, trae sus métricas de Metricool (alcance,
  retención, comentarios, guardados, compartidos, ratio comentarios/likes).
- Vincula la pieza publicada con su job_id en SQLite. Necesitarás un campo nuevo:
  `published_url` / `published_at` en la tabla jobs.
- Guarda un histórico. La tabla `assets` ya existe; crea `performance`.

--- 2. Detección de ganadores ---
Regla validada del research: si una pieza supera 3x el promedio de la cuenta,
se republica con hook variante a las 3-4 semanas.
- `factory/cli.py winners`: lista las piezas que cruzaron el umbral y para cuáles
  ya pasaron 3-4 semanas.
- Por cada ganador, propone el re-render: mismo guion, hook variante (ya tenemos
  las 5 de la fase 3), assets desde caché → costo ~cero.

--- 3. Señales que importan ---
- El ratio comentarios/likes alto es la huella de un funnel sano. Repórtalo, no
  solo los likes.
- Verifica la mezcla 70/30 (tutorial-valor / personalidad-opinión) de lo publicado
  en los últimos 30 días y advierte si se desbalanceó. Dato del research: los
  mayores virales de TODOS los referentes fueron de emoción/opinión. Si la mezcla
  se va al 100% tutorial, el alcance cae aunque la conversión se vea bien.
- Correlaciona fórmula (F1-F5) vs. rendimiento. Después de ~20 piezas, reporta qué
  fórmula funciona mejor EN ESTA CUENTA — no en la cuenta de los referentes.

--- 4. factory/cli.py report ---
Un reporte legible en markdown: qué se publicó, qué rindió, qué fórmula gana, qué
regrabar, si la mezcla está sana.

RESTRICCIONES DURAS:
- SOLO LECTURA en Metricool. No publiques, no programes, no borres nada. La
  publicación la decide Alexander, siempre.
- No inventes métricas. Si Metricool no devuelve un dato, di que no está — un
  reporte con números inventados es peor que no tener reporte.
- Cero credenciales en código.
- Con menos de ~20 piezas publicadas, cualquier correlación fórmula-rendimiento es
  ruido. Dilo explícitamente en el reporte en lugar de fingir señal.

CRITERIO DE ÉXITO: `python3 -m factory.cli report` corre contra datos reales de
Metricool y produce el markdown. Pega la salida real.

REPORTA: qué métricas trae Metricool de verdad y cuáles no, y qué tan confiable es
la vinculación pieza-publicada con job_id.
```

---

## Lo que NO se automatiza

Decidido, no delegable al agente:

- **F3 (opinión cruda)** — el formato de mayor alcance. Selfie, sin edición. Lo grabas tú.
- **Publicar** — la fábrica produce y mide; la decisión de publicar es humana.
- **Las decisiones de postura** en newsjacking — eso pasa por `guiones-picantes-alexander` primero.
- **Llenar `brand.json`** y rotar el PAT.

Y el recordatorio incómodo, para que no se pierda entre tanto código: **la palanca más grande de todo tu research no es la animación.** Es el gating (40-100x) y la mezcla 70/30. La fase 3 vale más que la 4, aunque la 4 se vea más bonita.
