# Fábrica de Contenido Box

Un motor, dos productos. Le pasas un tema y sale contenido listo para publicar.

- **VIDEO** — 9:16 (1080×1920), narración continua, estilo documental. Reels / TikTok.
- **CARRUSEL** — 4:5 (1080×1350), 6–10 slides en loop, se consume en mudo. Feed de Instagram.

No son la misma pieza reencuadrada. En un video el ritmo lo pone la edición; en un carrusel lo pone el dedo del usuario.

---

## Primeros pasos (para ti, si es tu primera vez)

Seguí estos pasos en orden. Uno por uno.

**Paso 1 — Configurá tu marca.** En la terminal, dentro de la carpeta del proyecto, escribí esto y apretá Enter:

```bash
python -m factory.cli setup
```

Te va a hacer preguntas (tu nombre, tu @, tus colores, tu voz de ElevenLabs, etc.). Respondé cada una y apretá Enter. Si una pregunta no la sabés o no aplica, dejá el renglón vacío y apretá Enter. Al final te crea dos archivos: `brand.json` (tu marca) y `.env` (para tus claves).

**Paso 2 — Pegá tus claves de API.** Una "clave de API" (API key) es como la contraseña que te da cada servicio (ElevenLabs, WaveSpeed, etc.) para que el programa pueda usarlos en tu nombre. Abrí el archivo `.env` con cualquier editor de texto y, en cada renglón, pegá la clave que corresponde después del `=`. Guardá el archivo.

> Dónde sacar cada clave: ElevenLabs → Profile → API Keys. WaveSpeed → wavespeed.ai/accesskey. Apify → Settings → Integrations. Guardalas como quien guarda una contraseña: nunca las compartas ni las subas a internet.

**Paso 3 — Probá sin gastar plata.** Esto te dice cuánto costaría, sin generar nada:

```bash
python -m factory.cli estimate examples/musculos.json
```

**Paso 4 — Generá de verdad** (esto sí gasta, poca cosa — centavos):

```bash
python -m factory.cli build examples/musculos.json
```

**Paso 5 — Convertilo en video.** La primera vez, instalá lo necesario (una sola vez):

```bash
cd remotion
npm install
```

Y después, cada vez que quieras ver o renderizar:

```bash
npx remotion studio                                       # ver un preview en tu navegador
npx remotion render BoxVideo out/video.mp4 --props=../out/<job>.manifest.json   # sacar el mp4 final
```

> Tus datos son tuyos: `.env` (tus claves) y `brand.json` (tu marca, tu voz) **nunca viajan** cuando compartís el repo — están en `.gitignore`. Lo que sí viaja son las plantillas vacías `.env.example` y `brand.example.json`, para que la próxima persona corra `setup` y ponga LO SUYO.

---

## Referencia rápida (usuarios avanzados)

```bash
python -m factory.cli setup                              # configurar/agregar una marca
python -m factory.cli estimate examples/musculos.json    # cuánto costaría
python -m factory.cli build    examples/musculos.json    # producir assets + manifest

cd remotion && npm install
npx remotion studio                                       # preview en localhost
npx remotion render BoxVideo out/video.mp4 --props=../out/<job>.manifest.json
```

Para carrusel se renderiza una slide por corrida, cambiando `slideIndex` en los props:

```bash
npx remotion render CarouselSlide out/slide-01.mp4 --props=../out/<job>.manifest.json
```

Salen N mp4 numerados, todos a 1080×1350. Se suben en orden al uploader de Instagram.

---

## Cómo está pensado

**El orden no es negociable:** planear → estimar → bloquear si excede → producir → renderizar.

Nada se genera antes de que pase el techo de gasto. El sistema de referencia genera primero y descubre la cuenta después; `factory/cost.py` existe para romper ese hábito.

```
factory/
  cost.py        Tabla de precios + estimador + freno de presupuesto
  router.py      LA ESTRATEGIA — router de 4 pisos. Todo lo demás es plomería
  cache.py       Caché por content hash. Nunca se paga dos veces por el mismo asset
  db.py          Estado en SQLite. Reiniciar no debe costar plata
  script.py      Modelo de guion + validación de las reglas de cada modo
  pipeline.py    Orquestación
  providers/     Capa de adaptadores — cambiar de proveedor es un env var, no un rewrite
remotion/
  src/Root.tsx           Compositions dirigidas por el manifest
  src/compositions/      BoxVideo (9:16) · CarouselSlide (4:5)
  src/components/        Background · BeatStage · Cutout · KineticText · Underline · SlideCounter
  src/fonts.ts           Carga la fuente display de verdad (delayRender) antes de capturar
brand.json       Única fuente de verdad visual. Nunca hardcodear colores
```

### Estilo de movimiento (fluidez, no rigidez)

El look no es una secuencia de slides — es un edit que fluye. Cuatro capas de movimiento, todas sutiles:

- **`Background.tsx`** — atmósfera viva: una luz cálida que se desplaza, un tinte de marca que respira, y un push-in continuo del ambiente. Modo `seamless` para carrusel (todo el movimiento cierra sobre el loop).
- **`BeatStage.tsx`** — la cámara de cada beat: push-in tipo Ken Burns + entrada que asienta + **salida en movimiento** (el beat se va mientras el siguiente entra). Esto convierte el corte seco en un relevo — la fluidez principal.
- **`Cutout.tsx`** — los recortes flotan y derivan; nunca se congelan. En carrusel el movimiento es periódico para no romper el loop.
- **`KineticText.tsx`** — subtítulos con **cambios de tamaño por palabra** (números y palabras clave entran más grandes y en dorado), pop de entrada, tilt hecho a mano, y flotación viva.

Regla de fades matizada: se prohíbe el fade-**in** (entra con spring, se siente editado). La **salida** de un beat sí lleva un poco de opacidad, pero pegada a movimiento real — se lee como "sale de cuadro", no como disolvencia.

### El router de 4 pisos

```
¿Persona real, logo o marca?                → Apify              $0.0029
¿Personaje que se repite (Alexander/Kiro)?  → Magnific           $0.08
¿Texto en imagen o composición compleja?    → Nano Banana PRO    $0.14
¿Cualquier otra cosa?                       → Flux Klein 4B      $0.008
```

Es una regla **económica** antes que estética — pero económica no es "el más barato siempre": es el modelo más barato que da la calidad que este tier necesita. Subido un escalón el 2026-07-17, a pedido: cutouts de Z-Image ($0.005) a Flux Klein 4B ($0.008, mejor adherencia al prompt), y escenas de Nano Banana 2 Fast ($0.045) a Nano Banana PRO ($0.14 — modelo distinto, Gemini 3.0 Pro Image, no una bandera "pro" sobre el mismo). Precios y slugs reales verificados contra `wavespeed.ai/docs` esa fecha — el "flux-klein" y "nano-banana-pro" que había antes en `cost.py` no correspondían a ningún endpoint real.

Verificado en `factory/cost.py`: 22 recortes en modelo premium = **$1.98**. Los mismos 22 bien ruteados = **$0.18** (con el escalón de calidad de arriba; $0.11 con el tier más barato de antes).

### La asimetría voz/imagen

El estimador la deja a la vista en cada corrida:

```
cutout (wavespeed/flux-2-klein-4b)      11 x $0.0080 = $0.0880
voice (elevenlabs/multilingual-v2)     799 x $0.0001 = $0.0799
music (elevenlabs)                       1 x $0.0750 = $0.0750
sfx:...                                                $0.0044
TOTAL                                                  $0.2473
```

**En imágenes se pelea el precio — pero no a cualquier costo de calidad. En voz no se pelea en absoluto.** Un guion son ~1.000 caracteres: $0.08-0.12. El TTS más barato del mercado ahorraría centavos por video y a cambio arriesga lo único irreemplazable — que la voz suene a Alexander.

Por eso `providers/voice_elevenlabs.py` no está optimizado por costo, y eso es una decisión, no un descuido.

### Por qué hay capa de proveedores

Kie es revendedor, no socio directo de los dueños de los modelos. Tuvo que sacar Midjourney cuando Midjourney lo exigió, y su tasa de éxito documentada ronda el 94%. Cualquier pipeline soldado a un proveedor se rompe un martes por razones ajenas.

Por eso: una interfaz, backends intercambiables. Kie sigue disponible como fallback en `providers/`, no como el camino sobre el que se construye.

---

## Reglas que el código hace cumplir

Las pruebas de humo verifican que muerden de verdad:

| Regla | Dónde vive |
|---|---|
| Slide de carrusel sin texto → rechazada | `script.validate` |
| Carrusel de 20 slides → rechazado (6–10) | `script.validate` |
| Video fuera de 60–75s → rechazado | `script.validate` |
| Beat estático >1.2s sin visual → rechazado | `script.validate` |
| Presupuesto excedido → no arranca | `cost.enforce_budget` |
| Persona real generada con IA → imposible | `router.route` |

---

## Pendientes

- [x] Confirmar el slug real del modelo Z-Image (y Nano Banana 2 Fast) en WaveSpeed contra su doc — corregido en `providers/images_wavespeed.py`
- [x] Chroma key de los recortes verdes con supresión de spill — `factory/chroma.py`, corre antes de cachear
- [x] SFX posicionados por frame — `factory/pipeline.py` los genera, cachea una vez por sonido único, y el manifest lleva src + frame por beat
- [x] Motor viral (fase 3) — `factory/formulas.py`, `script.validate_formula/validate_transversal/validate_gating`, `factory/gating.py`, `factory/caption.py`, `factory/hooks.py`. F3 rechazado por diseño; gating con lead magnet ausente rompe el build.
- [x] Motor de retención (fase 4) — `factory/align.py` (Whisper local, word timings reales por beat), `factory/rhythm.py` (tramos muertos >1.2s, advierte no bloquea), SFX multi-cue por tipo de entrada (`Script.sfx_cues`), loop opcional (`BoxVideo.tsx`, fade a Background en los extremos), `scripts/render_hooks.py`. Verificado con tests unitarios y `tsc --noEmit`; **no** con un build real (sin credenciales en `.env` no se puede correr `factory.cli build` de punta a punta — pendiente de que Alexander cargue las keys).
- [x] Bucle de aprendizaje (fase 5) — `factory/feedback.py` (tabla `performance`, ganadores 3x leave-one-out, mezcla 70/30, correlación fórmula-rendimiento con piso de 20 piezas), `factory.cli winners|report|ingest`. Solo lectura: `ingest` nunca llama a Metricool directamente, recibe metricas ya obtenidas (hoy, por MCP) como JSON. Campos verificados en vivo contra la cuenta real de Metricool (brand "Alexander Kast", id 6450128): `reach`, `retention` (solo en Reels), `comments`, `saved` (no `saves`), `shares`, `likes`. Sin piezas publicadas todavia — `report`/`winners` corren limpio contra la base vacia, pero no hay datos reales que correlacionar aún.
- [x] Auto-revisión post-QA (2026-07-17) — el agente `qa-reviewer` delegado no devolvió resultados (canal de mensajería atascado); revisión manual encontró y corrigió 3 bugs reales: `align.py` no toleraba tildes al comparar narración vs. caption on-screen, el check de credenciales exactas en `script.py` tampoco toleraba tildes (rechazaba guiones válidos escritos sin acentos, como los propios ejemplos del proyecto), y `factory.db` local quedó con un esquema viejo de mis propias pruebas (reseteado, sin jobs reales).
- [x] Costo + calidad (2026-07-17, a pedido) — router subido un escalón: cutouts a Flux Klein 4B ($0.008), escenas a Nano Banana PRO ($0.14, modelo distinto a Nano Banana 2). Slugs/precios verificados contra `wavespeed.ai/docs` en vivo. Whisper subido de "small" a "medium" (gratis, configurable por `WHISPER_MODEL_SIZE`). Hooks/caption ahora pueden usar un LLM real (Mistral, endpoint/precio verificados) en vez de templates — apagado por default, prende con `MISTRAL_API_KEY` + `ENABLE_LLM_COPY=true` en `.env`. Interfaz (`factory/providers/text_llm.py`) preparada para sumar Gemini/OpenAI/Anthropic después sin tocar `hooks.py`/`caption.py`, pero solo se construyó la de Mistral — las otras no están verificadas, no se inventaron.
- [x] Provider real de Magnific para el tier CHARACTER (2026-07-17) — nunca existió: `_produce_image` le pegaba a WaveSpeed con el modelo "magnific/character", que no es un endpoint real, así que cualquier asset con `is_recurring_character: true` habría fallado. Encontrado al cargar la key real de Magnific. `factory/providers/character_magnific.py` — endpoint (`POST/GET https://api.magnific.com/v1/ai/mystic`), auth y forma de respuesta verificados en vivo contra `docs.magnific.com`. **El precio NO está verificado** — Magnific cobra por créditos de plan (Premium/Premium+/Pro), no hay tarifa fija en USD publicada; el `$0.080` en `cost.py` es el placeholder de antes, sin confirmar. Revisa tu saldo de créditos después del primer lote real. `MAGNIFIC_WEBHOOK_KEY` no se usa — el provider usa polling, no webhook.
- [x] Credenciales reales cargadas en `.env` (2026-07-17): WaveSpeed, Magnific (+ webhook key sin uso), ElevenLabs, Mistral. Faltan: `KIE_API_KEY` (opcional, fallback), `FAL_API_KEY` (opcional), `APIFY_API_TOKEN` (necesaria para el tier PHOTO).
- [x] Sistema de diseño en el video (2026-07-17) — `remotion/src/design.ts`: motion (springs con nombre), escala tipográfica por rol, grilla de 8px, roles de color, elevación, layout. Los 8 componentes de Remotion beben de ahí. Fondo cálido vivo (sin negro), hook épico (slam+shake), música energética, subtítulos con efectos.
- [x] Repo compartible sin filtrar tus datos (2026-07-17) — `brand.json` y `.env` ahora son PERSONALES (gitignored); se agregaron plantillas `brand.example.json` y `.env.example`. Los validadores específicos de marca (credenciales exactas, prueba propia, nombre en auto-diálogo) pasaron de constantes hardcodeadas a config por marca en `brand.json` — sin esto, el sistema rechazaba los guiones de cualquier otra persona. Nuevo comando `python -m factory.cli setup` (wizard interactivo) genera el `brand.json` + `.env` del nuevo usuario. Si una marca no declara credenciales/prueba/nombre, esas reglas se omiten en vez de rechazar.
- [ ] Llenar `voiceId` y `characterRef` en `brand.json` (verificar el ID de Magnific con `library_list` — el `1995665` del historial está compartido con otro proyecto)
- [ ] `APIFY_API_TOKEN` sigue vacío — el tier PHOTO (personas/logos/marcas reales) no puede correr hasta que se cargue
- [ ] Decidir si esto se fusiona con el editor de video existente o queda aparte — con un video ya renderizado en la mano, no antes
- [ ] Rotar el PAT de GitHub expuesto en preferencias

## Seguridad

`.env` está en `.gitignore` desde antes del primer archivo. Cero credenciales en código. Límites de gasto configurados en cada proveedor donde exista la opción, y `MAX_SPEND_PER_RUN_USD` como segunda red.
