# AUDIT — fabrica-box (content_vox_creator)

Raíz: `F:\Users\SICOMMER SAS\Documents\Proyectos\content_vox_creator`. Snapshot: 2026-07-17.
Nombre interno del proyecto: `fabrica-box` (package.json remotion `fabrica-box-remotion`; README "Fábrica de Contenido Box").

## 1. Árbol

Conteo de líneas al lado de cada archivo de código. `remotion/public/generated/` colapsado (110 archivos png/mp3 generados). node_modules, .cache, assets/generated, out, __pycache__, .git excluidos.

```
raíz/
  .env                         (secretos, gitignored)
  .env.example         42 líneas aprox
  .gitignore           18
  README.md            188   (markdown)
  SKILL.md             (gitignored, ~17KB)
  brand.json           72    (JSON, gitignored)
  brand.example.json   (JSON)
  requirements.txt     9
  factory.db           53248 bytes (SQLite, gitignored)
  files.zip / "files 2 .zip"   (zips de entrega, 50KB/46KB)
factory/
  __init__.py            6
  align.py             165
  cache.py              37
  caption.py           111
  chroma.py             56
  cli.py               290
  config.py             86
  cost.py              170
  db.py                160
  feedback.py          331
  formulas.py           99
  gating.py             86
  hooks.py             110
  pipeline.py          529
  rhythm.py             75
  router.py            125
  script.py            523
  timing.py             16
  providers/
    __init__.py         42
    character_magnific.py  99
    images_wavespeed.py   115
    photos_apify.py        52
    text_llm.py            67
    voice_elevenlabs.py   101
remotion/
  remotion.config.ts     7
  tsconfig.json         15
  package.json          22
  public/generated/    (110 archivos generados png/mp3 — colapsado)
  src/
    Root.tsx            92
    index.ts             4
    types.ts            77
    design.ts          150
    fonts.ts            33
    compositions/
      BoxVideo.tsx      126
      CarouselSlide.tsx 148
    components/
      Background.tsx     59
      Badge.tsx          61
      BeatStage.tsx      67
      Cutout.tsx         66
      DecorativeBorder.tsx 40
      KickerLabel.tsx    55   ← NO IMPORTADO POR NADIE (ver §8)
      KineticText.tsx   133
      SceneBackground.tsx 55
      SearchBar.tsx      78
      SeriesKicker.tsx   61
      Signature.tsx      45
      SlideCounter.tsx   35
      Stat.tsx           54
      Subtitle.tsx       62
      SwipeHint.tsx      54
      Underline.tsx      45
scripts/
  render_carousel.py   102
  render_hooks.py      141
tests/
  test_align.py        126
  test_character_magnific.py  77
  test_chroma.py        66
  test_feedback.py     182
  test_formulas.py     279
  test_llm_copy.py     126
  test_rhythm.py        68
  fixtures/lead-magnet.md
examples/   (9 JSON): carrusel-ia, comuna13, ia-empresas, lanzamiento-ia,
            mcp-carrusel, mcp-reel, musculos + mcp-carrusel/mcp-reel
assets/
  sfx/     19 archivos (mp3/wav) + CATALOGO.md
  lead-magnets/guia-automatizacion.md  (gitignored dir)
out/     13 manifests, 3 mp4 (ver §6), caption/hooks por job
```

## 2. Historia

**NO HAY HISTORIA GIT.** `.git/` contiene únicamente `info/exclude` (301 bytes). No existe `HEAD`, ni `objects/`, ni `refs/`, ni commits. `git log`, `git status`, `git rev-list` fallan con `fatal: not a git repository`. El repo fue `git init`-eado parcialmente (o el `.git` quedó vaciado) y nunca se hizo un solo commit.

Consecuencia directa sobre lo pedido en esta sección:
- `git log --oneline`: **no encontrado** (0 commits).
- `git diff --stat` primer commit→HEAD: **no computable** (no hay commits).
- Archivos agregados después del commit inicial: **no computable** (no hay commit inicial).
- Archivos del commit inicial ya inexistentes: **no computable**.

Único proxy de cronología = mtime de archivos (frágil, no es historia): los `.py`/`.tsx` van del 2026-07-16 (17:56 dir raíz) al 2026-07-17 (script.py 00:35, brand.json 17:38, out/ 21:34). `files.zip` (2026-07-16 18:52) y `files 2 .zip` (2026-07-17 00:02) parecen entregas empaquetadas sucesivas, no verificado su contenido.

## 3. brand.json

Gitignored (no viaja). Contenido COMPLETO en disco:

```json
{
  "alexander": {
    "handle": "@alexemprendee",
    "displayFont": "Anton",
    "quoteFont": "Playfair Display",
    "colors": { "black": "#050505", "gold": "#FFC61A", "yellow": "#FFD400",
      "paper": "#0F0E0C", "white": "#F5F1E8", "ink": "#F5F1E8", "green": "#46B36A" },
    "dominant": "gold",
    "aesthetic": "AI-first dark luxury: near-black background, bright gold accent, condensed bold caps, gold engraving illustrations, gold badges + kicker",
    "grain": 0.12,
    "voiceId": "oXj06RrfrpuZLbwMQGmL",
    "characterRef": "REPLACE_WITH_MAGNIFIC_CHARACTER_ID",
    "founderName": "Alexander",
    "credentials": ["8 años en negocios digitales", "6 años en pauta"],
    "proof": ["KREOON", "UGC Colombia", "LiveCake"],
    "hashtags": ["#emprendimiento", "#IA"],
    "signature": "Nos vemos en el proximo, con todo. — @alexemprendee"
  },
  "mile": {
    "handle": "@militougc", "displayFont": "Cormorant", "quoteFont": "Cormorant",
    "colors": { "black": "#2B2622", "gold": "#C9A961", "yellow": "#E8D5A3",
      "paper": "#F3EDE3", "white": "#FFFFFF", "lilac": "#B9A3C9" },
    "dominant": "paper",
    "aesthetic": "wellness, anti-aging, natural light, feminine elegant",
    "grain": 0.06, "voiceId": "VmejBeYhbrcTPwDniox7", "characterRef": null
  },
  "kreoon": {
    "handle": "@kreoon.latam", "displayFont": "Anton", "quoteFont": "Playfair Display",
    "colors": { "black": "#0A0714", "gold": "#D4AF37", "yellow": "#FFD400",
      "purple": "#7c3aed", "paper": "#140F24", "white": "#F5F1E8" },
    "dominant": "purple",
    "aesthetic": "dual system: yellow for creator-facing, purple for brand/AI",
    "grain": 0.1, "voiceId": null, "characterRef": "eRALiEwGnmo3g1ze76Y2"
  }
}
```

`git log -p --follow brand.json`: **no encontrado** — sin repo git, no hay historia por-archivo. No se puede determinar quién/cuándo/con-qué-mensaje se cambió, ni distinguir cambios "colados" en otro commit. mtime disco: 2026-07-17 17:38.

Notas de contenido (no de historia): `alexander.characterRef` = literal `"REPLACE_WITH_MAGNIFIC_CHARACTER_ID"` (placeholder sin resolver → tier CHARACTER de esa marca fallaría, ver pipeline.py:224). `kreoon.voiceId` = null. `mile.characterRef` = null.

## 4. Reglas activas

`script.validate(script)` (factory/script.py:473) — cada línea = una regla y su mensaje de rechazo (bloqueante):

- hook vacío → `"Missing hook. The first 3 seconds are the whole video."` (l.477)
- CARRUSEL con <6 o >10 beats → `"Carrusel has N slides. Use 6-10 — the technical limit is 20, but nobody finishes 20."` (l.481)
- CARRUSEL beat.text vacío → `"Slide {index} has no on-screen text..."` (l.487)
- CARRUSEL beat.seconds fuera de [4.0, 12.0] → `"Slide {index} is Xs. Use 4-12s per slide..."` (l.492)
- VIDEO duration_seconds fuera de [45, 90] → `"Video runs Xs. Target 60-75s."` (l.498) — NOTA: el rango del check es 45–90, el mensaje dice 60–75 (ver §9).
- VIDEO beat con seconds>1.2 y sin assets y sin scene → `"Beat {index} holds Xs with no visual. Nothing stays static past ~1.2s..."` (l.503)
- cta vacío → `"Missing CTA."` (l.509)
- luego agrega `validate_formula()` (siempre), `validate_transversal()` (solo si formula≠None), `validate_gating()` (siempre).

`validate_formula()` (l.422), solo VIDEO salvo F3:
- VIDEO y duration fuera de [spec.min_seconds, spec.max_seconds] → `"{F} ({name}) dura Xs; rango valido A-Bs."` (rangos: F1 75–100, F2 33–60, F3 20–40, F4 30–60, F5 sin límite)
- F1 (`_validate_f1`, l.323): hook sin patrón pérdida+inclusivo → rechazo; sin beat con narración+asset en ventana 4–15s → rechazo; beats numerados fuera de [3,6] → rechazo; falta prueba propia (si hay `proof` o frase genérica y no matchea) → rechazo; `gating is None` → rechazo; si `founder_name` set y no hay auto-diálogo `"Pero <name>, ...?"` → rechazo.
- F2 (`_validate_f2`, l.373): sin patrón de INGRESO (`cobrar/ingreso/factura/pagan/$`) → `"F2: falta promesa de INGRESO..."`.
- F3 (`_validate_f3`, l.382): SIEMPRE rechaza con `"F3 se graba a camara, no se fabrica..."` (buildable=False; el rechazo también se agrega fuera de VIDEO, l.444).
- F4 (`_validate_f4`, l.386): ningún beat.text con len>40 → `"F4: falta el prompt literal en pantalla..."`.
- F5 (`_validate_f5`, l.395): falta series_part/series_total; series_part fuera de [1,total]; series_formula ∉ {F1,F2}; y corre F1 o F2 anidada.

`validate_transversal()` (l.258, solo si formula≠None):
- sin ningún dígito en full_text → `"Sin numero hiperespecifico..."`.
- patrón `vas a ganar|garantizad[oa]|seguro ganas` → `"Promesa de ganancia garantizada detectada..."`.
- si `credentials` declaradas y hay claim `\d+ años` que no matchea exacto → `"Credencial de anos no exacta..."` (comparación con tildes plegadas).

`validate_gating()` (l.452, solo si gating≠None):
- pregunta no personalizada (`is_personalized` false: <3 palabras o última palabra en GENERIC_GATING_WORDS) → `"Gating question ... no esta personalizada..."`.
- `lead_magnet_path` no existe en disco → `"Gating promete un lead magnet que no existe en disco..."` (build FALLA, no advierte).

Otros puntos que bloquean/advierten fuera de validate:
- `cost.enforce_budget` (cost.py:162) → `BudgetExceeded` si estimate.total > `MAX_SPEND_PER_RUN_USD` (default 1.50). BLOQUEA antes de gastar.
- `pipeline.build` (l.350/356): brand.json ausente → RuntimeError; `script.brand` no está en brand.json → RuntimeError.
- `pipeline._produce_image` (l.224): tier CHARACTER sin `reference` → RuntimeError.
- `config.Config.require` (config.py:47): credencial faltante → RuntimeError.
- `rhythm.report` (rhythm.py:60): tramos muertos >1.2s → imprime advertencia, **NO** bloquea.
- `suggest_split` (script.py:301): advisory; **nadie lo llama** (ver §8).

## 5. Router y costos

`DEFAULT_MODELS` (router.py:52):
```python
DEFAULT_MODELS = {
    Tier.CHARACTER: "magnific/character",
    Tier.SCENE:     "wavespeed/nano-banana-pro",
    Tier.CUTOUT:    "wavespeed/flux-2-klein-4b",
    Tier.PHOTO:     "apify/google-images",
}
```
Ruteo (`route`, l.60): is_real_entity→PHOTO; is_recurring_character→CHARACTER; needs_text_in_image o is_complex_composition→SCENE; resto→CUTOUT.

`IMAGE_PRICES` (cost.py:25, USD/imagen):
```
wavespeed/z-image           0.005
wavespeed/flux-2-klein-4b   0.008
runware/flux-1-schnell      0.0013
wavespeed/nano-banana-2-fast 0.045
wavespeed/nano-banana-pro   0.140
kie/nano-banana-pro         0.090
fal/seedream-v4.5           0.030
magnific/character          0.080   (UNVERIFIED — placeholder; Magnific cobra por créditos)
```
Apify (Pay-Per-Event): RUN_STARTED 0.005 + IMAGE_SCRAPED 0.0023 + SERP_PAGE 0.05; RESULTS_PER_QUERY=3. `photo_price()` = 0.005 + 0.0023*3 + 0.05*1 = **0.0619** por búsqueda.

`VOICE_PRICES` (cost.py:58, USD/1M chars):
```
elevenlabs/multilingual-v2  100.0
elevenlabs/flash-v2.5        50.0
```
Extra: `MUSIC_PRICE_PER_MINUTE=0.15`, `SFX_PRICE_PER_MINUTE=0.12`, `TEXT_LLM_PRICES` mistral-small (0.10, 0.30).

**¿SFX y música en la estimación? SÍ.** `pipeline.estimate()` (pipeline.py:123):
- Música: l.153-154, siempre que `music_prompt` no vacío, priced 1 vez con `music_price(_music_duration_ms)`.
- SFX: l.159-166, por cada nombre único de `all_sfx_names()`; **PERO** salta los que tienen archivo local en `assets/sfx/` (l.162). Como los 11 nombres del sistema (pop-a..c, whoosh-a..c, impact-a..c, marker-a..b) TODOS existen como mp3 locales, el SFX vía ElevenLabs prácticamente nunca se estima ni se genera (ver §8). Voz solo si `character_count>0` (l.144).

## 6. Duración de las composiciones

Fragmento EXACTO donde se calcula `durationInFrames` — `remotion/src/Root.tsx:61-68`:
```tsx
const totalFrames = Math.max(
  1,
  Math.round(manifest.beats.reduce((sum, b) => sum + b.seconds, 0) * manifest.fps)
);

const slideIndex = props.slideIndex ?? 0;
const slideBeat = manifest.beats[slideIndex];
const slideFrames = Math.max(1, Math.round((slideBeat?.seconds ?? 5) * manifest.fps));
```
- `BoxVideo`: `durationInFrames={totalFrames}` = suma de `beat.seconds` × fps (l.63-64, 76).
- `CarouselSlide`: `durationInFrames={slideFrames}` = `beats[slideIndex].seconds` × fps (l.68, 84).

Dentro de BoxVideo cada beat dura `Math.round(beat.seconds * fps)` (BoxVideo.tsx:60).

**De dónde sale el número y por qué NO es un 8s fijo:** en el código actual el número SÍ sale de `beat.seconds`. La premisa "los mp4 salen a 8s fijos" **NO se reproduce con los outputs presentes**. Medición real (ffprobe) de los 3 mp4 en `out/` contra la suma de su manifest:
```
ia-empresas-preview  mp4=51.05s  manifest_sum=51.0  (video, 8 beats [7,6,6,6,6,6,7,7])
musculos-primera-vez mp4=61.06s  manifest_sum=61.0  (video, 11 beats)
mcp-reel             mp4=70.06s  manifest_sum=70.0  (video, 8 beats [8,9,9,9,9,9,7,10])
```
Los tres coinciden con la suma de `beat.seconds`. El path VIDEO respeta la duración. No hay ningún `8`/`240` hardcodeado en Root.tsx/BoxVideo/CarouselSlide/remotion.config.ts. (Coincidencia parcial: el primer beat de `mcp-reel` es 8s, pero es dato del manifest, no un tope.) No existen `slide-*.mp4` en `out/` para medir el path CARRUSEL. Ver §11 — no puedo confirmar de dónde salió el "8s fijo" que reporta el diseño; el código y los mp4 existentes lo contradicen.

**Cómo llega `slideIndex`:** por PROPS vía CLI `--props`. `scripts/render_carousel.py:36` construye `props = {**manifest, "slideIndex": index}`, lo vuelca a un JSON temporal y lo pasa `--props=<tmp>` a `npx remotion render CarouselSlide` (una corrida por slide). Root.tsx:66 lo lee `props.slideIndex ?? 0`. No está hardcodeado ni en el manifest de `build` (pipeline.py no escribe slideIndex). GOTCHA: el comando manual del README (`render CarouselSlide ... --props=<job>.manifest.json`, sin slideIndex) cae en `?? 0` → SIEMPRE renderiza la slide 0.

## 7. Los agregados

- **chroma key**: `factory/chroma.py:26` `remove_green_screen()`. Quita fondo verde #00FF00 con rampa de alpha (LOW 15 / HIGH 70) + spill suppression; corre en `_produce_image` (pipeline.py:238) antes de cachear; `CHROMA_VERSION="chroma-v1"` va en la cache key. Falla→degrada (mantiene frame crudo).
- **generación de SFX**: `pipeline.py:269` `_produce_sfx()` + `SFX_PROMPTS`/`SFX_DURATIONS` (l.60-82). Prefiere archivo local de `assets/sfx/`; si no existe, sintetiza con ElevenLabs `sound_effect`. Cues definidos en `script.py:151` `sfx_cues()`.
- **generación de música**: `pipeline.py:322` `_produce_music()` + `_music_duration_ms` (l.39). ElevenLabs `music()`. VIDEO cubre toda la timeline; CARRUSEL clip corto loopable (~slide más larga, piso 10s). Ahora para AMBOS modos.
- **campos nuevos del beat** (definidos en `script.py:56` Beat; leídos en `CarouselSlide.tsx` salvo donde se diga): `subtitle` (Subtitle.tsx), `kicker` (chip inline CarouselSlide.tsx:85), `badge` (Badge.tsx), `stat` (Stat.tsx, número gigante hero), `search` (SearchBar.tsx, mockup buscador), `scene` (full-frame background — BoxVideo.tsx:73 y CarouselSlide.tsx:53 vía SceneBackground; se genera en `pipeline._produce_scene` con `SCENE_FULL_PROMPT` y modelo `SCENE_MODEL=nano-banana-2-fast`, distinto del Tier.SCENE del router).
- **otros módulos fuera del diseño original**:
  - `factory/align.py` — word-timings reales con faster-whisper local (WhisperModel importado lazy, l.49).
  - `factory/rhythm.py` — detector de tramos muertos >1.2s (advisory).
  - `factory/feedback.py` (331 l) — tabla `performance`, `detect_winners`/`build_report`/`ingest_performance`; comandos CLI `ingest|winners|report`; correlación fórmula-rendimiento.
  - `factory/gating.py` — GatingSpec + `build_botcake_spec_md`.
  - `factory/hooks.py`, `factory/caption.py` — generación de hooks/caption (template o Mistral opt-in).
  - `factory/providers/character_magnific.py`, `text_llm.py` (Mistral) — providers nuevos.
  - `factory/cli.py setup` — wizard interactivo de brand.json/.env.
  - Componentes Remotion nuevos: Badge, DecorativeBorder, KickerLabel, SceneBackground, SearchBar, SeriesKicker, Stat, Subtitle, SwipeHint, SlideCounter.

## 8. Código muerto

- **`beat.voice`**: el manifest lo escribe (pipeline.py:474 `beat_voice.get(beat.index)`), pero `beat_voice` NUNCA se popula (queda `{}`, l.412) → siempre `null`. Ningún componente Remotion lo lee (solo aparece en types.ts). Voz per-slide de carrusel = feature muerta de punta a punta. (CarouselSlide no reproduce voz; pipeline comenta que carrusel va sin voz.)
- **`beat.narration`**: el manifest lo escribe (l.465) pero NINGÚN componente Remotion lo lee (uso server-side para voz/align únicamente). Muerto en el lado Remotion.
- **`KickerLabel.tsx`** (55 l): no lo importa ningún archivo. El kicker de carrusel se dibuja inline en CarouselSlide.tsx:85. Componente muerto.
- **`suggest_split()`** (script.py:301): sin ningún llamador vivo (solo aparece en el .pyc). Función muerta.
- **Exports de design.ts sin uso**: `SPACE` (grilla 8px) y `SAFE.videoTextBottomPct` no se referencian en ningún componente.
- **Path de generación SFX ElevenLabs**: `SFX_PROMPTS`/`SFX_DURATIONS` (11 nombres) son fallback para nombres sin archivo local; como los 11 tienen mp3 en `assets/sfx/`, ese path (y su costo) nunca se ejerce para los cues automáticos. Efectivamente inerte salvo un `sfx=` override a un nombre inexistente en disco.
- **Flag `loop`**: declarada en Script (script.py:105), leída por BoxVideo.tsx:40 (fade de extremos). PERO ningún ejemplo ni manifest la pone en `true` (los 13 manifests: `"loop": false`; en `lanzamiento-ia.json` "loop" es un id de asset, no la flag). Además aunque fuera true, el render de Remotion produce una sola pasada — `loop` solo hace fade en los bordes, no genera un loop real. Flag respetada por el código pero nunca activada y de efecto limitado.
- Campos que Remotion espera y el manifest NO escribe: **ninguno** — pipeline.py:457-475 escribe las 15 claves que `types.ts Beat` declara (index, text, subtitle, kicker, badge, stat, search, narration, seconds, assets, scene, sfx, sequenceFrom, wordTimings, voice). Coincidencia completa de forma (aunque voice/narration queden sin lector, arriba).

## 9. Contradicciones

- **Rango de duración VIDEO**: `script.py:498` rechaza fuera de **[45, 90]s** pero el mensaje dice `"Target 60-75s"`, y README l.159/tabla dice `"Video fuera de 60–75s → rechazado"`. Tres números distintos (45–90 real vs 60–75 dicho). El código no rechaza a los 60–75.
- **F1 vs regla genérica**: `formulas.py` F1 `min_seconds=75, max_seconds=100`; `script.py:498` regla genérica exige ≤90. Un F1 válido de 91–100s pasa `validate_formula` pero lo rechaza la regla genérica → ventana efectiva real de F1 = 75–90s, contradiciendo su propio spec 75–100.
- **Dos "scene" distintos con el mismo nombre**: router `Tier.SCENE` → `wavespeed/nano-banana-pro` ($0.14, para needs_text/composición compleja); pero el campo `beat.scene` full-frame usa `pipeline.SCENE_MODEL = wavespeed/nano-banana-2-fast` ($0.045). El README (l.117-120) solo documenta el primero como "Nano Banana PRO $0.14"; el segundo (el que más se usa, 1 por beat con scene) no aparece en la tabla del router.
- **README "se consume en mudo"** (l.6) vs pipeline: el carrusel ahora lleva bed de música (`CarouselSlide.tsx:140` `<Audio ... loop />`, manifest carrusel-67e13205 tiene `music`). "Mudo" es cierto solo para autoplay de Instagram, no para el render.
- **README componentes desactualizados** (l.98): lista 6 componentes (`Background · BeatStage · Cutout · KineticText · Underline · SlideCounter`); existen 17 (KickerLabel entre ellos, y muerto).
- **README l.172** afirma "loop opcional (BoxVideo.tsx, fade)" como feature entregada; en la práctica nunca se activa (ver §8).
- **requirements.txt l.1-2** dice "Everything else in factory/ is deliberately stdlib-only" — verificado correcto: providers usan solo stdlib (urllib, etc.), numpy/Pillow solo en chroma.py, faster-whisper solo en align.py. Sin contradicción (se anota como confirmación).

## 10. Dependencias

`pip freeze` (solo lo que usa este proyecto; requirements.txt declara numpy, Pillow, faster-whisper):
```
numpy==2.4.3
pillow==11.3.0
faster-whisper==1.2.1
  # deps transitivas de faster-whisper, presentes:
  av==17.0.1
  ctranslate2==4.7.1
  onnxruntime==1.20.1
  tokenizers==0.23.1
  huggingface_hub==1.12.2
```
El resto de `factory/` (config, db, cache, cli, cost, router, script, gating, feedback, hooks, caption, rhythm, timing, providers) es stdlib puro (urllib, json, sqlite3, hashlib, argparse, dataclasses…).

`remotion/package.json` bloque `dependencies`:
```json
"dependencies": {
  "@remotion/cli": "^4.0.0",
  "@remotion/google-fonts": "^4.0.0",
  "@remotion/media-utils": "^4.0.0",
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "remotion": "^4.0.0"
}
```
devDependencies: `@types/react ^18.3.1`, `typescript ^5.5.0`. Versión remotion instalada: **4.0.490**. `zod` está en node_modules pero es transitiva (no está en package.json).

"Cuáles se agregaron después del commit inicial": **no computable** — sin historia git no hay línea base contra la cual medir deltas de dependencias (ver §2).

## 11. Lo que NO sé

- **El "8s fijo" del punto 6**: no pude reproducirlo ni ubicar su origen. El código deriva la duración de `beat.seconds` y los 3 mp4 de video existentes coinciden con la suma del manifest (51/61/70s). No hay `slide-*.mp4` en disco para medir el path carrusel. Puede ser: (a) comportamiento ya corregido antes de este snapshot, (b) específico del render de carrusel/hooks bajo condiciones no presentes, o (c) un getInputProps() que en cierta versión/modo no propaga a `durationInFrames`. No lo afirmo — no hay evidencia en el estado actual.
- **Historia / autoría / deltas**: sin repo git funcional no puedo decir qué cambió, quién, cuándo, ni qué archivos son nuevos vs originales. Todo el análisis de "lo que cambió" se apoya en lectura del código actual, no en diffs.
- **Contenido de `files.zip` / `files 2 .zip` / `factory.db`**: no los abrí/inspeccioné en profundidad; no sé si `files*.zip` son el estado "diseño original" (serviría como línea base) ni cuántos jobs reales tiene la db (README afirma que se reseteó, sin verificar aquí).
- **Si el path CARRUSEL o `render_hooks.py` producen la duración correcta en la práctica**: no hay outputs para medirlos; solo verifiqué el path VIDEO.
- **Precio real de `magnific/character`** ($0.080): marcado UNVERIFIED por el propio código (créditos de plan, sin tarifa USD publicada). No lo confirmé.
- **Si `beat_voice` (voz per-slide carrusel) estuvo alguna vez conectado**: hoy está muerto; sin historia git no sé si fue removido o nunca se terminó.
```
