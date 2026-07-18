# Fábrica de Contenido Box — @alexemprendee

Un motor, dos productos. Le pasas un tema y sale contenido listo para publicar.

- **VIDEO** — 9:16 (1080×1920), narración continua, estilo documental. Reels / TikTok.
- **CARRUSEL** — 4:5 (1080×1350), 6–10 slides en loop, se consume en mudo. Feed de Instagram.

No son la misma pieza reencuadrada. En un video el ritmo lo pone la edición; en un carrusel lo pone el dedo del usuario.

---

## Arranque

```bash
cp .env.example .env          # llenar credenciales (nunca commitear)
python3 -m factory.cli estimate examples/musculos.json   # cuánto costaría
python3 -m factory.cli build    examples/musculos.json   # producir assets + manifest

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
  src/components/        Background · Cutout · KineticText · Underline · SlideCounter
brand.json       Única fuente de verdad visual. Nunca hardcodear colores
```

### El router de 4 pisos

```
¿Persona real, logo o marca?                → Apify        $0.0029
¿Personaje que se repite (Alexander/Kiro)?  → Magnific     $0.08
¿Texto en imagen o composición compleja?    → Nano Banana  $0.045
¿Cualquier otra cosa?                       → Z-Image      $0.005
```

Es una regla **económica** antes que estética. Un recorte tipo sticker sobre verde es un dibujo con borde grueso, no una fotografía. Mandarlo al modelo insignia es pagar 18x por el mismo resultado.

Verificado en `factory/cost.py`: 22 recortes en modelo premium = **$1.98**. Los mismos 22 bien ruteados = **$0.11**.

### La asimetría voz/imagen

El estimador la deja a la vista en cada corrida:

```
cutout (wavespeed/z-image)              11 x $0.0050 = $0.0550
voice (elevenlabs/multilingual-v2)     799 x $0.0001 = $0.0959   <-- más caro que TODAS las imágenes
music (elevenlabs)                       1 x $0.0200 = $0.0200
TOTAL                                                  $0.1709
```

**En imágenes se pelea el precio hasta el último centavo. En voz no se pelea.** Un guion son ~1.000 caracteres: $0.12. El TTS más barato del mercado ahorraría once centavos por video y a cambio arriesga lo único irreemplazable — que la voz suene a Alexander.

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

- [ ] Llenar `voiceId` y `characterRef` en `brand.json` (verificar el ID de Magnific con `library_list` — el `1995665` del historial está compartido con otro proyecto)
- [ ] Confirmar el slug real del modelo Z-Image en WaveSpeed contra su doc
- [ ] Chroma key de los recortes verdes (hoy el PNG llega con fondo; falta el paso de recorte)
- [ ] SFX posicionados por frame — el video se siente plano sin ellos
- [ ] Decidir si esto se fusiona con el editor de video existente o queda aparte
- [ ] Rotar el PAT de GitHub expuesto en preferencias

## Seguridad

`.env` está en `.gitignore` desde antes del primer archivo. Cero credenciales en código. Límites de gasto configurados en cada proveedor donde exista la opción, y `MAX_SPEND_PER_RUN_USD` como segunda red.
