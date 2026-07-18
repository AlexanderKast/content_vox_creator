import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { ELEVATION, TYPE, roles } from "../design";

/**
 * An orange sticker callout — the "$$$", "-50%", "RÉCORD", "MAX" tags from the
 * reference reel. Tilted, punchy, drops in with an overshoot. Positioned by
 * top/right/left percentages so a slide can place one near its illustration.
 */
export const Badge: React.FC<{
  text: string;
  tokens: BrandTokens;
  top?: number;
  right?: number;
  left?: number;
  rotate?: number;
  delay?: number;
  loopFrames?: number;
}> = ({ text, tokens, top = 18, right, left, rotate = -6, delay = 6, loopFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { surface, accent } = roles(tokens);
  const looping = !!loopFrames && loopFrames > 0;
  const pop = looping ? 1 : spring({ frame: frame - delay, fps, config: { damping: 9, mass: 0.5, stiffness: 240 } });

  if (!text) return null;

  const pos: React.CSSProperties = { top: `${top}%` };
  if (right !== undefined) pos.right = `${right}%`;
  if (left !== undefined) pos.left = `${left}%`;

  return (
    <div
      style={{
        position: "absolute",
        ...pos,
        transform: `scale(${pop}) rotate(${rotate}deg)`,
        transformOrigin: "center",
      }}
    >
      <span
        style={{
          display: "inline-block",
          backgroundColor: accent,
          color: surface,
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.black,
          fontSize: 40,
          letterSpacing: "0.02em",
          padding: "10px 20px 6px",
          borderRadius: 8,
          textTransform: "uppercase",
          boxShadow: ELEVATION.sticker,
        }}
      >
        {text}
      </span>
    </div>
  );
};
