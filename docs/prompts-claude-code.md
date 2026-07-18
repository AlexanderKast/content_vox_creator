# Prompts para Claude Code — Fábrica Box

Dos fases. **No pegues la fase 2 hasta haber leído el reporte de la fase 1.**
El agente ejecuta; las decisiones de diseño ya están tomadas.

Antes de empezar:

```bash
cd fabrica-box
cp .env.example .env    # llenar credenciales
claude
# shift+tab para modo auto. NO uses --dangerously-skip-permissions:
# este proyecto llama APIs pagas.
```

---

## FASE 1 — Descubrimiento (no construir nada)

> Copiar tal cual:

```
Estás en el proyecto `fabrica-box`: una fábrica de contenido en video que orquesta
APIs pagas desde Python (`factory/`) y renderiza con Remotion (`remotion/`).

Lee primero el README.md y luego `factory/router.py`, `factory/cost.py` y
`factory/providers/`. Ese es el contexto.

TAREA: FASE DE DESCUBRIMIENTO ÚNICAMENTE. No escribas ni modifiques código.
No instales dependencias. Solo investiga y reporta.

Los adaptadores en `factory/providers/` fueron escritos parcialmente de memoria y
necesitan verificarse contra documentación real antes de gastar un peso. Verifica:

1. WAVESPEED (`providers/images_wavespeed.py`)
   - ¿Cuál es el slug real del modelo Z-Image? Lo puse como "z-image" y puede
     estar mal.
   - ¿Cuál es el slug de Nano Banana 2 Fast?
   - ¿El endpoint es POST /api/v3/{slug} con polling a data.urls.get? Verifica el
     shape real de request y response.
   - ¿El parámetro de tamaño es "size": "1080*1920" o algo distinto?
   - ¿Precios actuales por imagen de ambos modelos? Compáralos con la tabla en
     `factory/cost.py` y reporta cualquier diferencia.

2. ELEVENLABS (`providers/voice_elevenlabs.py`)
   - Verifica el endpoint y el body de text-to-speech.
   - ¿Existe `/v1/sound-generation` para SFX? ¿Cuál es su contrato y su precio?
   - ¿Cuál es el contrato real del endpoint de música? Lo puse como `/v1/music`.

3. APIFY (`providers/photos_apify.py`)
   - ¿El actor `automation_lab~google-images-scraper` existe con ese ID exacto?
     Si no, encuentra el mejor scraper de Google Images por precio y confiabilidad,
     y reporta su ID real.
   - Verifica el shape del input y de los items del dataset.

4. CHROMA KEY
   - Investiga la mejor forma de quitar fondo verde puro (#00FF00) de un PNG en
     Python, manejando el halo verde en los bordes (green spill).
   - Reporta qué dependencia haría falta y su tamaño.

RESTRICCIONES DURAS:
- No modifiques `brand.json`. Es la única fuente de verdad visual.
- No escribas código en esta fase.
- No inventes: si no encuentras algo en la documentación, dilo explícitamente en
  lugar de suponer.

REPORTA AL TERMINAR, en español:
- Una tabla: lo que asumí en el código vs. lo que dice la doc real vs. veredicto
  (correcto / incorrecto / no encontrado).
- Los precios reales contra `factory/cost.py`.
- Qué está roto y qué hay que cambiar, en orden de gravedad.
- NADA de código todavía.
```

---

## FASE 2 — Construcción

> **Solo después de leer el reporte de la fase 1 y aprobar los cambios.**
> Ajusta lo que esté entre `<<<>>>` con los hallazgos reales.

```
Contexto: mismo proyecto `fabrica-box`. La fase de descubrimiento ya se ejecutó
y estos son los hallazgos aprobados: <<<pegar aquí las correcciones de la fase 1>>>

TAREA: implementar los tres pendientes que impiden que salga un video real.
Trabaja en este orden; no pases al siguiente hasta que el anterior corra.

--- 1. CORREGIR LOS ADAPTADORES ---
Aplica las correcciones de la fase 1 a `factory/providers/` y actualiza las tablas
de precios en `factory/cost.py` con los valores reales.
Criterio de éxito: `python3 -m factory.cli estimate examples/musculos.json`
imprime la estimación con precios reales sin errores.

--- 2. CHROMA KEY ---
Decisión ya tomada, no la re-litigues: el recorte se hace del lado de Python al
generar el asset, NO en Remotion. Razón: así entra al caché por content hash y se
paga una sola vez, en vez de gastar CPU en cada render.

Crea `factory/chroma.py`:
- Función que recibe bytes de PNG con fondo verde puro y devuelve PNG RGBA con
  fondo transparente.
- Debe manejar green spill (el halo verde en los bordes), no solo tumbar el color
  exacto. Un recorte con halo se ve barato y es el error #1 de este estilo.
- Intégralo en `pipeline.py::_produce_image`: el chroma corre ANTES de guardar en
  caché, de modo que lo cacheado sea el PNG ya transparente.
- El hash de caché debe incluir la versión del algoritmo de chroma, para que
  mejorarlo invalide lo viejo.
- Degradación elegante: si el chroma falla, guarda el original y sigue. Nunca
  bloquees el build.

Criterio de éxito: un test que genere un PNG sintético 512x512 con un círculo rojo
sobre #00FF00, lo pase por el chroma, y verifique que (a) las esquinas quedan con
alpha=0, (b) el centro conserva el rojo, (c) ningún píxel del borde tiene el canal
verde dominante. El test debe correr sin llamar a ninguna API.

--- 3. SFX ---
Decisión ya tomada: los SFX se GENERAN con ElevenLabs sound-generation, no se
descargan de una librería. Razón: entran al mismo caché por hash y quedan
trazables como todo lo demás.

- Añade el método de SFX al provider de ElevenLabs usando el contrato real
  verificado en la fase 1.
- En `factory/script.py`, cada Beat debe poder declarar su SFX (ej. "pop",
  "whoosh", "impact"). Dale un default sensato por tipo de entrada.
- En `pipeline.py`, produce y cachea cada SFX único una sola vez — el mismo "pop"
  se reusa en los 11 beats, no se genera 11 veces.
- El manifest debe llevar, por beat, la ruta del SFX y el frame exacto en el que
  dispara.
- En Remotion, reprodúcelos en ese frame exacto.

Los SFX no son cosmética: sin ellos el video se siente muerto aunque la animación
esté correcta.

Criterio de éxito: el manifest generado contiene sfx con su frame, y
`estimate` incluye el costo de los SFX únicos (no del total de beats).

--- 4. RENDER DE CARRUSEL ---
Crea `scripts/render_carousel.py`: dado un manifest de modo carrusel, renderiza N
mp4 numerados (slide-01.mp4 ... slide-08.mp4), todos a 1080x1350, pasando el
slideIndex correcto a Remotion en cada corrida.
- Respeta RENDER_CONCURRENCY del .env (default 1). Chromium headless compite por
  CPU; sin semáforo se cae el equipo.
- Criterio de éxito: corre contra `examples/carrusel-ia.json` y produce 8 archivos
  de 1080x1350. Verifica las dimensiones reales con ffprobe, no asumas.

RESTRICCIONES DURAS:
- Cero credenciales en código. Todo por .env. `.gitignore` ya está configurado.
- No hardcodees colores ni fuentes en ningún lado: `brand.json` es la única fuente
  de verdad.
- No rompas la firma de `router.route()` ni las reglas de `script.validate()`:
  son la estrategia del proyecto, no detalles de implementación.
- No cambies el orden del pipeline: planear → estimar → bloquear → producir.
  Nada se genera antes de que pase el freno de presupuesto.
- Nunca reintentes a ciegas una llamada que cobra.
- Código en inglés (nombres y comentarios). Comunicación conmigo en español.
- Código completo y ejecutable. Nada de fragmentos con "...".
- Si necesitas agregar una dependencia, dime cuál y por qué ANTES de instalarla.

VERIFICACIÓN FINAL:
Corre estas dos y pega la salida real (no la describas):
  python3 -m factory.cli estimate examples/musculos.json
  python3 -m factory.cli estimate examples/carrusel-ia.json
Más el test de chroma.

No hagas auto-revisiones intermedias largas: ejecuta y avísame cuando esté listo.

REPORTA AL TERMINAR, en español y breve:
- Qué quedó funcionando y qué no.
- Qué dependencias agregaste.
- Costo estimado real de un video y de un carrusel con los precios verificados.
- Qué falta para que salga el primer video de verdad.
```

---

## Después de la fase 2

El primer build real:

```bash
python3 -m factory.cli estimate examples/musculos.json   # mira el número primero
python3 -m factory.cli build    examples/musculos.json
cd remotion && npm install && npx remotion studio
```

Lo que va a reventar y está bien que reviente: los `REPLACE_WITH_*` de
`brand.json`. Solo tú tienes el `voiceId` de ElevenLabs y el `characterRef` de
Magnific — y ese ID hay que confirmarlo con `library_list`, porque el `1995665`
del historial está compartido con otro proyecto.

**No delegues al agente:** llenar `brand.json`, rotar el PAT de GitHub, y decidir
si esto se fusiona con el editor de video existente. Eso último decídelo con un
video ya renderizado en la mano, no antes.
