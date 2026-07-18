# Catálogo de SFX — dónde suena cada efecto

Estos son los efectos de sonido reales que usa la fábrica de videos. Son una
**selección curada** del pack "Efectos de Sonido — Edwin Arenas" (993 audios,
613 MB en total). Aquí solo viajan los ~19 que el sistema realmente dispara,
para que el repositorio quede liviano.

## Cómo funciona (en una frase)

El pipeline busca cada sonido por su **nombre de archivo**. Si el archivo existe
en esta carpeta, lo usa tal cual (gratis, instantáneo). Si no existe, lo genera
con ElevenLabs y lo cobra. O sea: **poner un `.mp3` aquí con el nombre correcto
reemplaza automáticamente al sonido generado.**

Código que lo resuelve: `factory/pipeline.py` → función `_local_sfx()`.

---

## 1) Sonidos del sistema (automáticos)

La fábrica dispara estos 4 "familias" sola, según lo que pasa en cada escena
(ver `factory/script.py` → `Script.sfx_cues`). Cada familia tiene variantes
(a, b, c) que **rotan por escena** para que no suene siempre igual.

| Archivo | Familia | ¿Cuándo suena? | Origen en el pack |
|---|---|---|---|
| `pop-a.mp3` `pop-b.mp3` `pop-c.mp3` | **pop** | Cada vez que **entra un recorte/cutout** a la escena (una imagen que aparece) | `29-POP/pop-1..3.mp3` |
| `whoosh-a.mp3` `whoosh-b.mp3` `whoosh-c.mp3` | **whoosh** | En **cada corte entre escenas** (la transición) | `36-WHOOSH`, `32-SWOSH` |
| `impact-a.mp3` `impact-b.mp3` `impact-c.mp3` | **impact** | En el **golpe de apertura (hook)**, en el **cierre (remate)** y en cualquier escena con un **número** | `05-BOOM (IMPACTO)` |
| `marker-a.mp3` `marker-b.mp3` | **marker** | Cuando se **dibuja el subrayado** debajo del título | `28-PAPEL/Paper*.mp3` |

> Regla de rotación: escena 0 usa la variante `a`, escena 1 la `b`, escena 2 la
> `c`, y vuelve a empezar. Por eso hay 3 variantes de pop/whoosh/impact y 2 de
> marker (coincide con `SFX_FAMILY_VARIANTS` en `factory/script.py`).

---

## 2) Sonidos extra (a pedido)

Estos **no suenan solos**. Se disparan solo si en el guion una escena lo pide
explícitamente con el campo `sfx`. Ejemplo en el JSON de un guion:

```json
{ "text": "Gané $2.000 USD", "sfx": "money" }
```

Eso pone ese sonido una vez, al inicio de esa escena.

| Escribe `sfx: "..."` | Archivo | Sonido | Origen en el pack |
|---|---|---|---|
| `ding` | `ding.mp3` | Campanita / notificación | `14-DING/Ting.mp3` |
| `money` | `money.mp3` | Billetes / dinero | `13-DINERO/Money-1.mp3` |
| `coin` | `coin.wav` | Moneda | `27-MONEDA/sound2.wav` |
| `transition` | `transition.mp3` | Transición suave | `35-TRANSICION` |
| `error` | `error.wav` | Error / negación | `16-ERROR/sound1.wav` |
| `glitch` | `glitch.mp3` | Glitch digital | `22-GLITCH/SFX- Glitch1.mp3` |
| `explosion` | `explosion.mp3` | Explosión | `17-EXPLOSION/SFX- Explosion01.mp3` |
| `click` | `click.wav` | Click / tecla | `10-CLICK/click.wav` |

---

## ¿Quieres cambiar un sonido o agregar otro?

1. **Reemplazar uno existente:** copia tu `.mp3` encima del archivo con ese
   nombre (p. ej. reemplaza `whoosh-a.mp3` por otro que te guste más). Listo.
2. **Agregar un extra nuevo** (p. ej. `risa`):
   - Copia el audio aquí como `risa.mp3`.
   - Úsalo en el guion con `"sfx": "risa"`.
   - (Opcional) agrégalo a esta tabla para no olvidarlo.

No hace falta tocar código: el pipeline detecta el archivo por su nombre.

---

## Pack completo

La librería completa de 993 sonidos (36 categorías: agua, alarma, cinemática,
memes, terror, etc.) vive fuera del repo, en la carpeta original de Edwin
Arenas. Si necesitas un sonido que no está en esta selección, cópialo desde ahí
siguiendo el paso 2 de arriba.
