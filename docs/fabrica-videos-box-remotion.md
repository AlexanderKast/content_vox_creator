---
title: Fábrica de Videos Box con Claude Code + Remotion
created: 2026-07-16
tags: [alexemprendee, vibe-coding, ia-aplicada, contenido]
status: activo
related: ["[[Marca Personal Alexander]]", "[[Editor de Video Remotion]]", "[[Kreoon]]"]
---

> [!summary] Resumen ejecutivo
> Se diseñó el skill `fabrica-videos-box`: un motor, dos productos. **Modo VIDEO** (reel/TikTok 9:16 estilo documental) y **modo CARRUSEL DE VIDEO** (slides en loop 4:5 para feed de IG). Claude Code dirige; Remotion edita; ElevenLabs, Magnific, Kie AI y Apify producen los recursos. Decisiones clave: modelo híbrido de imagen (Magnific solo personajes, Kie recortes), primer uso en [[Marca Personal Alexander]], y **los dos modos son contenido distinto, no el mismo reencuadrado**. Pendiente: decidir si se monta sobre el pipeline existente o en proyecto nuevo.

## Contexto

El origen es un video de referencia guardado en NotebookLM ("Despedí a mi editor y contraté a Claude Code", de Santiago), que documenta cómo automatizar la producción de videos estilo *box* con Claude Code como orquestador.

La diferencia frente al referente: Alexander **ya tiene la mitad construida**. El [[Editor de Video Remotion]] (FastAPI + Remotion) ya corre, ElevenLabs ya está en uso, Apify MCP ya está conectado y Magnific ya tiene librería de personajes. Lo que faltaba no era el proyecto — era la **receta**. Por eso el entregable es un skill portátil y no una carpeta.

## Arquitectura

| Pieza | Rol | Nota |
|---|---|---|
| **Claude Code** | Director — orquesta, escribe guion y código, no genera assets | Usar Opus para diseño de escenas: el video es código, mejor código = mejor video |
| **Remotion** | Editor / render | Open source, gratis, sin costo por video. Preview en `localhost` |
| **ElevenLabs** | Voz clonada + música | Settings SSML en [[Pipeline Video IA]] |
| **Magnific** | Personajes consistentes (Alexander, [[Kiro]]) | Caro — su valor es la consistencia, no la imagen |
| **Kie AI** | Recortes e ilustraciones desechables | Nano Banana 2 Lite, ~$5 / 1000 créditos |
| **Apify** | Fotos reales de internet | Actor: Automation Lab Google Images, ~$2.90 / 1000 imgs |

### Regla de decisión de imagen

```
¿Persona real, logo o marca?               → Apify
¿Personaje que se repite (Alexander/Kiro)? → Magnific con reference character
¿Cualquier otra cosa?                      → Kie AI
```

Esta regla es económica antes que estética. Objetivo: **menos de $1 USD de generación por video**. Si se dispara, casi siempre es Magnific haciendo trabajo de Kie.

## Los dos modos

> [!warning] El error que hay que evitar
> **Un carrusel de video no es un video cortado en pedazos.** Cambia la unidad narrativa: en un video el ritmo lo pone la edición; en un carrusel lo pone el dedo del usuario. Si le metes la narración corrida del formato box a un carrusel, se rompe — el usuario desliza cuando quiere y se pierde media frase.

| | **VIDEO** | **CARRUSEL** |
|---|---|---|
| Ritmo lo pone | La edición | El dedo del usuario |
| Unidad narrativa | El timeline | **La slide** |
| Formato | 9:16 — 1080×1920 | **4:5 — 1080×1350** |
| Sonido | Central | **Secundario: se ve en mudo** |
| Duración | 60–75 s corridos | 4–8 s por slide, en loop |
| Retención | Que no se salga | **Que deslice** |
| Destino | Reels, TikTok | Feed de Instagram |
| Render | 1 mp4 | N mp4 independientes |

**Regla de decisión de modo:** ¿mecanismo que se explica en secuencia? → VIDEO. ¿N puntos independientes? → CARRUSEL. ¿Necesita sonido? → VIDEO. ¿Se entiende mejor pausando? → CARRUSEL.

## Specs de carrusel (verificadas 16 jul 2026)

| Spec | Valor |
|---|---|
| Formato | **4:5 — 1080×1350** (1:1 solo si se reusa en pauta) |
| Slides máx. | 20 técnicamente — **usar 6–10** |
| Duración por slide | **4–8 s** (límite técnico 60 s) |
| Peso máx. por slide | 250 MB |
| Zona segura | **1000×1070 centrada** |
| Margen superior / inferior | 80 px / 200 px |

Hallazgos que cambian el diseño:
- **La primera slide bloquea el ratio de todo el carrusel.** Construir slide 1, duplicar el frame, diseñar todo adentro.
- **Subir 9:16 a un carrusel → IG lo recorta a 3:4.** Para formato alto, exportar 1080×1440 y usar modo "Original".
- **El preview del grid renderiza a 3:4** aunque el post sea 4:5. El texto de los bordes es lo primero que sufre.
- El límite de slides subió de 10 a **20** (no significa usarlas).

### Reglas de construcción de carrusel
1. Cada slide loopea sin costura: primer frame = último frame.
2. **Todo texto, siempre** — se ve en mudo. Si necesita audio para entenderse, está mal.
3. La slide 1 es el 80%: funciona sola, sin contexto y sin sonido.
4. **Precipicio de deslizamiento**: cada slide abre algo que solo cierra la siguiente. El swipe es el corte y hay que ganárselo.
5. Ancla visual constante (mismo fondo, tipografía, posición del contador).
6. Contador visible (1/8) — la gente termina lo que sabe que tiene final.
7. Última slide = CTA.

**Audio en carrusel**: cama musical idéntica en todas las slides (así el audio se siente continuo aunque cada slide sea independiente). Alternativa: micro-VO de 3–5 s autoconclusivo por slide. **Nunca cortar una frase entre dos slides.**

**Estructura de 8 slides**: 1 hook · 2 el costo de no saberlo · 3–6 un punto por slide · 7 síntesis · 8 CTA.

## El estilo box (modo VIDEO)

Motion graphics de documental: cortes rápidos y bruscos, recortes tipo sticker sobre fondo texturizado, subrayados que se dibujan solos, efecto revista.

Reglas duras:
- **Cero fades.** Todo entra con rebote, slide, pop o escala.
- Nada estático más de ~1.2 s.
- Un elemento visual nuevo cada 2–3 s de narración.
- Subtítulos sincronizados al golpe de voz, no como accesorio.
- 9:16 vertical, 1080×1920, 30 fps por defecto.

Los recortes se generan **sobre fondo verde puro** (`#00FF00`) y se recortan por chroma — de ahí el look de sticker flotante.

## Brand tokens — @alexemprendee

| Token | Valor |
|---|---|
| Display font | Anton (Playfair solo para quote cards) |
| Negro | `#050505` |
| Dorado | `#D4AF37` |
| Dominante | Amarillo |
| Estética | Dark luxury, contraste alto, tipografía enorme |

[[Kiro]] es **opcional** en marca personal — se prefiere la imagen del propio Alexander por cercanía.

## Estructura de guion (60–75 s, ~150–190 palabras)

1. **Hook (0–3 s)** — afirmación que rompe. Contraintuitiva o con cifra. Nunca "hoy les voy a hablar de".
2. **Giro (3–15 s)** — por qué lo que creías está mal.
3. **Cuerpo (15–55 s)** — el mecanismo real. Una idea por escena, frases de menos de 12 palabras.
4. **Remate (55–70 s)** — consecuencia práctica para el emprendedor.
5. **CTA (5 s)** — pregunta polarizante + seguir. Nunca "link en bio" dentro del video.

Para newsjacking: la postura se define primero en `guiones-picantes-alexander`, y ese guion entra acá solo para producción.

## Decisiones tomadas

> [!important] No re-litigar
> - **Imagen híbrida**: Magnific solo para personajes con consistencia; Kie AI para todo recorte desechable; Apify para lo que existe en el mundo real. No intercambiar.
> - **Un motor, dos productos**: video (9:16) y carrusel de video (4:5) viven en el mismo skill, pero son **contenido distinto** — no se reencuadra uno para sacar el otro.
> - **Carrusel = 4:5 (1080×1350)**, 6–10 slides, 4–8 s por slide. No 9:16, no 20 slides.
> - **En carrusel el texto es obligatorio en toda slide** — se consume en mudo.
> - **Primer uso**: [[Marca Personal Alexander]] (@alexemprendee), no clientes ni producto vendible. Esos vienen después, sobre el mismo sistema.
> - **El entregable es el skill, no el proyecto** — así el "dónde montarlo" no bloquea el arranque.
> - **Remotion sobre Hyperframes**: validado por el referente para este estilo específico.
> - **Apify: Automation Lab Google Images** sobre el actor default — más barato y mejor.

> [!warning] Seguridad
> Las API keys (ElevenLabs, Kie, Apify, Magnific) van en `.env`, con `.gitignore` configurado **antes** del primer archivo. Nunca en código, nunca en commit, nunca pegadas en chat.
> Pendiente aparte: el PAT de GitHub sigue expuesto en texto plano en las preferencias — rotarlo.

## Pendientes

- [ ] Decidir dónde montarlo: sobre el [[Editor de Video Remotion]] existente vs. proyecto nuevo limpio
- [ ] Confirmar el ID de personaje de Magnific con `library_list` (el `1995665` del historial está compartido con otro proyecto)
- [ ] Registrar el personaje "Alexander" en la librería de Magnific si aún no existe
- [ ] Instalar el skill y correr el primer video de prueba (modo VIDEO)
- [ ] Correr el primer carrusel de prueba y validar loop + zona segura en un teléfono real
- [ ] Definir la voz de ElevenLabs a usar por defecto y fijarla en el skill
- [ ] Después del primer video: evaluar expansión a [[Kreoon]] / clientes de agencia
- [ ] Rotar el PAT de GitHub

> [!tip] Aprendizajes reutilizables
> - **Claude dirige, no crea.** Cuando el video sale mal, el problema está en la dirección (prompt de escena, timing), no en la herramienta.
> - **El video es código** → mejor modelo = mejor video, porque el modelo toma todas las decisiones de diseño.
> - **Los SFX son lo que hace que el video se sienta vivo.** Un video sin SFX se siente plano aunque la animación sea correcta. No es un detalle final: es estructural.
> - **Decirle a Claude "no revises mucho, ejecuta y avísame"** evita que queme tokens en auto-revisiones intermedias.
> - El paso donde más tiempo hay que invertir es el 4 (estilo de generación). La primera versión nunca es la mejor — se refina viendo el preview y corrigiendo.

## Errores conocidos

| Síntoma | Causa real |
|---|---|
| Magnific no devuelve nada, sin error | Sin créditos — revisar `account_balance` |
| Recortes con halo verde | Chroma mal aplicado; pedir verde puro sin sombra proyectada |
| El video se siente plano | Faltan SFX en las entradas |
| Personaje cambia entre escenas | No se pasó `references: character` |
| Costo disparado | Magnific haciendo recortes desechables |
| El video se ve "de IA" | Faltan fotos reales — meter Apify |
| Carrusel recortado al subir | Se exportó 9:16 → IG lo lleva a 3:4. Exportar 4:5 |
| Slides con encuadres distintos | La slide 1 fijó otro ratio |
| Texto cortado en el perfil | No se revisó el preview de grid a 3:4 |
| El carrusel se siente desarmado | Falta ancla visual constante o cama musical común |
| Nadie desliza más de 2 slides | Falta precipicio: las slides cierran en vez de abrir |
