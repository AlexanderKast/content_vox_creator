import React from "react";
import { AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { Cutout } from "../components/Cutout";
import { KineticText } from "../components/KineticText";
import { SlideCounter } from "../components/SlideCounter";
import type { Manifest } from "../types";

/**
 * Mode CARRUSEL — 4:5, one autonomous looping slide.
 *
 * This is NOT the video cropped. Different rules apply:
 *   - the slide must loop seamlessly (first frame == last frame)
 *   - it must be readable with sound OFF (text is mandatory)
 *   - everything critical lives inside the 1000x1070 safe area
 */

// Instagram's UI: 80px top, 200px bottom, ~40px sides. Content stays inside.
const SAFE_INSET = { top: 90, bottom: 210, side: 50 };

export const CarouselSlide: React.FC<{
  manifest: Manifest;
  slideIndex: number;
}> = ({ manifest, slideIndex }) => {
  const { tokens, beats } = manifest;
  const beat = beats[slideIndex];
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Seamless loop: the last frame must match the first. A visible jump on the
  // wrap is what makes a carousel look cheap.
  const loopPhase = (frame / durationInFrames) * Math.PI * 2;
  const breathe = 1 + Math.sin(loopPhase) * 0.018;

  if (!beat) {
    return (
      <AbsoluteFill>
        <Background tokens={tokens} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill>
      <Background tokens={tokens} />

      <AbsoluteFill
        style={{
          paddingTop: SAFE_INSET.top,
          paddingBottom: SAFE_INSET.bottom,
          paddingLeft: SAFE_INSET.side,
          paddingRight: SAFE_INSET.side,
          transform: `scale(${breathe})`,
        }}
      >
        {beat.assets.map((src, assetIndex) => (
          <Cutout
            key={src}
            src={staticFile(src)}
            delay={assetIndex * 3}
            y={-16}
            scale={assetIndex === 0 ? 0.86 : 0.55}
            x={assetIndex === 0 ? 0 : 22}
            rotate={assetIndex === 0 ? -2 : 6}
          />
        ))}

        {/* Text is not optional here — the slide is consumed muted. */}
        <KineticText
          text={beat.text}
          tokens={tokens}
          delay={2}
          size={78}
          bottom={22}
        />
      </AbsoluteFill>

      <SlideCounter
        index={slideIndex + 1}
        total={beats.length}
        tokens={tokens}
      />
    </AbsoluteFill>
  );
};
