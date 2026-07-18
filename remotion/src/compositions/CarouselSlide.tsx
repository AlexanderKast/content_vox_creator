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
import { SAFE, TYPE, hexToRgba, roles } from "../design";
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
        {/* Only float a cutout when there's no full scene behind. */}
        {!beat.scene &&
          beat.assets.map((src, assetIndex) => (
            <Cutout
              key={src}
              src={staticFile(src)}
              delay={assetIndex * 3}
              y={-32}
              scale={assetIndex === 0 ? 0.56 : 0.4}
              x={assetIndex === 0 ? 0 : assetIndex % 2 === 1 ? 24 : -24}
              rotate={assetIndex === 0 ? -2 : assetIndex % 2 === 1 ? 6 : -7}
              index={assetIndex}
              loopFrames={durationInFrames}
            />
          ))}

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

        {/* HERO: a giant stat, or the title. */}
        {hasStat ? (
          <Stat text={beat.stat} tokens={tokens} bottom={heroBottom} loopFrames={durationInFrames} />
        ) : (
          <KineticText
            text={beat.text}
            tokens={tokens}
            delay={2}
            size={TYPE.size.slide}
            bottom={heroBottom}
            loopFrames={durationInFrames}
          />
        )}

        <Subtitle text={beat.subtitle} tokens={tokens} size={38} bottom={hasStat ? 20 : 24} loopFrames={durationInFrames} />

        <Badge text={beat.badge} tokens={tokens} top={22} right={13} rotate={-7} loopFrames={durationInFrames} />

        {/* CTA search-bar mockup. */}
        <SearchBar word={beat.search} tokens={tokens} bottom={12} loopFrames={durationInFrames} />
      </AbsoluteFill>

      <SlideCounter index={slideIndex + 1} total={beats.length} tokens={tokens} />
      <Signature tokens={tokens} bottom={8} left={8} />
      {!isLast ? <SwipeHint tokens={tokens} /> : null}

      {manifest.music ? <Audio src={staticFile(manifest.music)} volume={0.22} loop /> : null}
      {beat.sfx.map((cue, i) => (
        <Sequence key={`${cue.src}-${i}`} from={cue.frame} name={`sfx-${cue.src}`}>
          <Audio src={staticFile(cue.src)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
