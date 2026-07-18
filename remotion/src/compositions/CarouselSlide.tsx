import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Badge } from "../components/Badge";
import { Cutout } from "../components/Cutout";
import { DecorativeBorder } from "../components/DecorativeBorder";
import { KineticText } from "../components/KineticText";
import { SceneBackground } from "../components/SceneBackground";
import { SearchBar } from "../components/SearchBar";
import { SeriesKicker } from "../components/SeriesKicker";
import { Signature } from "../components/Signature";
import { SlideCounter } from "../components/SlideCounter";
import { Stat } from "../components/Stat";
import { Subtitle } from "../components/Subtitle";
import { SwipeHint } from "../components/SwipeHint";
import { SAFE, TYPE, fitTitleSize, hexToRgba, roles } from "../design";
import type { Manifest } from "../types";

/**
 * Mode CARRUSEL — 4:5, one looping slide, consumed MUTED. Editorial
 * "breaking-news" layout over a themed scene (or cream paper): persistent
 * series tag, section kicker, giant stat OR title, subtitle, badge, decorative
 * frame, swipe arrow, signature. A CTA slide can show a search-bar mockup.
 */
const SAFE_INSET = SAFE.carousel;

export const CarouselSlide: React.FC<{ manifest: Manifest; slideIndex: number }> = ({
  manifest,
  slideIndex,
}) => {
  const { tokens, beats, seriesKicker } = manifest;
  const beat = beats[slideIndex];
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const { accent, surface } = roles(tokens);

  // Seam-closer: every carousel animation is periodic over durationInFrames so
  // the last frame lands back on the first — the loop is REAL and obligatory,
  // not a flag. This breathe (sin over the full slide length: sin(0)=sin(2π)=0)
  // is the outermost example; Cutout/Stat/Subtitle/etc. all get loopFrames=
  // durationInFrames for the same reason. Do NOT tie any of these to a fixed
  // frame count or the wrap-around will jump. Measured seam (8 slides of
  // examples/comuna13-style carousel, frame0 vs last frame): mean abs diff
  // 1.72/255 (0.68%) — one frame of motion, no hard cut.
  const loopPhase = (frame / durationInFrames) * Math.PI * 2;
  const breathe = 1 + Math.sin(loopPhase) * 0.012;
  const isLast = slideIndex === beats.length - 1;

  if (!beat) {
    return (
      <AbsoluteFill>
        <SceneBackground tokens={tokens} scene={null} seamless />
      </AbsoluteFill>
    );
  }

  const hasStat = !!beat.stat;
  const heroBottom = hasStat ? 30 : beat.subtitle ? 38 : 26;
  const titleSize = fitTitleSize(beat.text);

  return (
    <AbsoluteFill>
      <SceneBackground tokens={tokens} scene={beat.scene} seamless />
      <DecorativeBorder tokens={tokens} />

      <SeriesKicker text={seriesKicker} tokens={tokens} top={4} />

      <AbsoluteFill
        style={{
          paddingTop: SAFE_INSET.top,
          paddingBottom: SAFE_INSET.bottom,
          paddingLeft: SAFE_INSET.side,
          paddingRight: SAFE_INSET.side,
          transform: `scale(${breathe})`,
        }}
      >
        {/* Cutouts now render on TOP of a scene backdrop too, not only when
            there's no scene — real Vox layout is background + layered
            cutout props together (verified 2026-07-18: "aun le falta mas
            recortes... que aparezcan otras imagenes como recortes" — a
            scene-only slide with zero cutout reads flat next to the ones
            that have both). Over a scene the cutout is a smaller accent
            (70% scale), not the hero. y=-58 clears the title/subtitle block
            at the bottom regardless — a public figure never gets the
            size-0.56 hero slot or centered rotation-free treatment —
            smallest scale, dead center, no rotation, regardless of index. */}
        {beat.assets.map((asset, assetIndex) => {
          const compact = !!beat.scene;
          const baseScale = asset.isPublicFigure ? 0.32 : assetIndex === 0 ? 0.56 : 0.4;
          return (
            <Cutout
              key={asset.src}
              src={staticFile(asset.src)}
              delay={assetIndex * 3}
              y={-58}
              scale={compact ? baseScale * 0.7 : baseScale}
              x={asset.isPublicFigure ? 0 : assetIndex === 0 ? 0 : assetIndex % 2 === 1 ? 24 : -24}
              rotate={asset.isPublicFigure ? 0 : assetIndex === 0 ? -2 : assetIndex % 2 === 1 ? 6 : -7}
              index={assetIndex}
              loopFrames={durationInFrames}
            />
          );
        })}

        {/* Section kicker — small accent label above the hero, on a subtle
            surface chip so it stays legible over any part of the scene. */}
        {beat.kicker ? (
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: `${hasStat ? 46 : 54}%`,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <span
              style={{
                fontFamily: tokens.displayFont,
                fontWeight: TYPE.weight.bold,
                fontSize: 30,
                letterSpacing: "0.14em",
                color: accent,
                textTransform: "uppercase",
                backgroundColor: hexToRgba(surface, 0.66),
                padding: "6px 16px",
                borderRadius: 6,
              }}
            >
              {beat.kicker}
            </span>
          </div>
        ) : null}

        {/* HERO: a giant stat, or the title. legibleOverPhoto: a flat
            surface-color slide already has good ink/background contrast by
            brand design; a photo backdrop (beat.scene) doesn't guarantee
            that against ANY image tone, so it gets the white+outline
            treatment instead (verified 2026-07-18, dark ink unreadable over
            a dim office photo). */}
        {hasStat ? (
          <Stat text={beat.stat} tokens={tokens} bottom={heroBottom} loopFrames={durationInFrames} />
        ) : (
          <KineticText
            text={beat.text}
            tokens={tokens}
            delay={2}
            size={titleSize}
            bottom={heroBottom}
            loopFrames={durationInFrames}
            legibleOverPhoto={!!beat.scene}
          />
        )}

        <Subtitle
          text={beat.subtitle}
          tokens={tokens}
          size={38}
          bottom={hasStat ? 20 : 24}
          loopFrames={durationInFrames}
          legibleOverPhoto={!!beat.scene}
        />

        <Badge text={beat.badge} tokens={tokens} top={22} right={13} rotate={-7} loopFrames={durationInFrames} />

        {/* CTA search-bar mockup. */}
        <SearchBar word={beat.search} tokens={tokens} bottom={12} loopFrames={durationInFrames} />
      </AbsoluteFill>

      <SlideCounter index={slideIndex + 1} total={beats.length} tokens={tokens} />
      {/* Top band, left of SlideCounter — reference carousels put the
          account handle with the rest of the top chrome, not bottom-left
          (verified 2026-07-18, 7-image structural reference batch). */}
      <Signature tokens={tokens} top={8} left={8} />
      {!isLast ? <SwipeHint tokens={tokens} /> : null}

      {/* Music ducks under a slide's own narration (content-vox-news) the
          same way BoxVideo ducks it under the video's continuous voice —
          the voice leads, the bed is a floor under it, not competing. */}
      {manifest.music ? (
        <Audio src={staticFile(manifest.music)} volume={beat.voice ? 0.12 : 0.22} loop />
      ) : null}
      {/* Per-slide narration (content-vox-news). Not looped — one read per
          slide view, unlike the visual loop around it. If the narration
          runs longer than beat.seconds it's cut by this Sequence's own
          bound; the skill sizes `seconds` to the narration for this reason. */}
      {beat.voice ? <Audio src={staticFile(beat.voice)} /> : null}
      {beat.sfx.map((cue, i) => (
        <Sequence key={`${cue.src}-${i}`} from={cue.frame} name={`sfx-${cue.src}`}>
          <Audio src={staticFile(cue.src)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
