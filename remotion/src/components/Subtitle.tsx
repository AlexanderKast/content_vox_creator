import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { TYPE, roles } from "../design";

/**
 * The body / subtitle under a carousel title. This is where the slide actually
 * develops its part of the story in readable prose — not oversized display
 * type, but a clean, legible block that a muted viewer reads.
 *
 * `loopFrames` (carrusel) keeps it fully shown with a tiny float so the loop
 * stays seamless; otherwise it eases up into place.
 */
export const Subtitle: React.FC<{
  text: string;
  tokens: BrandTokens;
  delay?: number;
  size?: number;
  bottom?: number;
  loopFrames?: number;
}> = ({ text, tokens, delay = 6, size = 40, bottom = 26, loopFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { ink } = roles(tokens);
  const looping = !!loopFrames && loopFrames > 0;

  const enter = looping
    ? 1
    : spring({ frame: frame - delay, fps, config: { damping: 18, mass: 0.6, stiffness: 120 } });
  const angle = looping ? (frame / loopFrames!) * Math.PI * 2 : 0;
  const floatY = looping ? Math.sin(angle * 1.3) * 2 : 0;

  if (!text) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: "10%",
        right: "10%",
        bottom: `${bottom}%`,
        textAlign: "center",
        transform: `translateY(${(1 - enter) * 22 + floatY}px)`,
        opacity: enter,
      }}
    >
      <span
        style={{
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.bold,
          fontSize: size,
          lineHeight: 1.18,
          color: ink,
          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        {text}
      </span>
    </div>
  );
};
