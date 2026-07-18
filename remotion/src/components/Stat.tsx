import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { TYPE, roles } from "../design";

/**
 * A giant colored stat number — "7 PAÍSES", "18,078 KM", "×2" from the
 * reference. Huge condensed caps in the green secondary accent (or orange),
 * dropped in with an overshoot. This is a hero element, not a caption.
 */
export const Stat: React.FC<{
  text: string;
  tokens: BrandTokens;
  bottom?: number;
  color?: "accent" | "accent2";
  delay?: number;
  loopFrames?: number;
}> = ({ text, tokens, bottom = 44, color = "accent2", delay = 2, loopFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const r = roles(tokens);
  const looping = !!loopFrames && loopFrames > 0;
  const pop = looping ? 1 : spring({ frame: frame - delay, fps, config: { damping: 10, mass: 0.5, stiffness: 240 } });
  if (!text) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: "6%",
        right: "6%",
        bottom: `${bottom}%`,
        textAlign: "center",
        transform: `translateY(${(1 - pop) * 30}px) scale(${0.7 + pop * 0.3})`,
        opacity: pop > 0.02 ? 1 : 0,
      }}
    >
      <span
        style={{
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.black,
          fontSize: 168,
          lineHeight: 0.9,
          letterSpacing: "-0.01em",
          color: color === "accent2" ? r.accent2 : r.accent,
          textTransform: "uppercase",
          textShadow: `0 6px 0 ${roles(tokens).ink}22`,
        }}
      >
        {text}
      </span>
    </div>
  );
};
