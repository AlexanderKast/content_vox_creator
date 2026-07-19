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
import { Typewriter } from "../components/Typewriter";
import { SAFE, SUBTITLE_BOTTOM, TITLE_TOP, TYPE, fitTitleSize, hexToRgba, roles } from "../design";
import type { Manifest } from "../types";

/**
 * Mode CARRUSEL — 4:5, one looping slide, consumed MUTED. Full-bleed layout
 * (2026-07-18 — replaced header-over-image, which pushed the photo into a
 * boxed-in lower zone with paper margins and read as a template): the image
 * is the entire frame, text sits on top of it inside SceneBackground's
 * top/bottom gradient bands, cutouts float over the clear middle. Matches
 * the 7 reference carousels Alexander approved (samusdesign, CT Escola,
 * Rarison, ST Fitness, Guardian, Mirza).
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
  const hasKicker = !!beat.kicker;
  const titleSize = fitTitleSize(beat.text);
  const titleTop = hasKicker ? TITLE_TOP.withKicker : TITLE_TOP.plain;

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
        {/* Cutouts float over the clear middle band of the image (roughly
            28%-50%, where SceneBackground's gradient stays fully clear) —
            no topPercent means Cutout's own default (dead center, 50%).
            Over a scene the cutout is a smaller accent (70% scale), not the
            hero; without one it's the hero, bigger, on the flat dark
            surface fill. A public figure never gets the size-0.56 hero slot
            or centered rotation-free treatment — smallest scale, dead
            center, no rotation, regardless of index. */}
        {beat.assets.map((asset, assetIndex) => {
          const compact = !!beat.scene;
          const baseScale = asset.isPublicFigure ? 0.32 : assetIndex === 0 ? 0.56 : 0.4;
          return (
            <Cutout
              key={asset.src}
              src={staticFile(asset.src)}
              delay={assetIndex * 3}
              scale={compact ? baseScale * 0.7 : baseScale}
              x={asset.isPublicFigure ? 0 : assetIndex === 0 ? 0 : assetIndex % 2 === 1 ? 24 : -24}
              rotate={asset.isPublicFigure ? 0 : assetIndex === 0 ? -2 : assetIndex % 2 === 1 ? 6 : -7}
              index={assetIndex}
              loopFrames={durationInFrames}
              isPublicFigure={asset.isPublicFigure}
            />
          );
        })}

        {/* Kicker chip — top, over the top gradient band. Own semi-opaque
            surface backing, unchanged style, just lives over a photo now
            instead of paper. Typewriter reveal like the reference sheet's
            annotation labels. */}
        {beat.kicker ? (
          <div style={{ position: "absolute", left: 0, right: 0, top: "8%", display: "flex", justifyContent: "center" }}>
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
              <Typewriter text={beat.kicker} delay={4} />
            </span>
          </div>
        ) : null}

        {/* Title + subtitle always sit on top of the full-bleed image now —
            there is no flat-paper case anymore, so legibleOverPhoto is
            unconditional, not derived from beat.scene. The accent (gold)
            color for emphasized words stays as-is (KineticText) — it reads
            fine over the dark gradient. */}
        {hasStat ? (
          <Stat text={beat.stat} tokens={tokens} bottom={30} loopFrames={durationInFrames} />
        ) : (
          <KineticText
            text={beat.text}
            tokens={tokens}
            delay={2}
            size={titleSize}
            top={titleTop}
            loopFrames={durationInFrames}
            legibleOverPhoto
          />
        )}

        <Subtitle
          text={beat.subtitle}
          tokens={tokens}
          size={38}
          bottom={SUBTITLE_BOTTOM}
          loopFrames={durationInFrames}
          legibleOverPhoto
        />

        <Badge text={beat.badge} tokens={tokens} top={22} right={13} rotate={-7} loopFrames={durationInFrames} />

        {/* CTA search-bar mockup. */}
        <SearchBar word={beat.search} tokens={tokens} bottom={12} loopFrames={durationInFrames} />
      </AbsoluteFill>

      {/* Always sits inside SceneBackground's top dark-gradient band now —
          legible-white is unconditional, same reasoning as the title. */}
      <SlideCounter index={slideIndex + 1} total={beats.length} tokens={tokens} legibleOverPhoto />
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
