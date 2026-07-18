import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { TYPE, roles } from "../design";

/**
 * The little black "kicker" tag at the top of a slide — the "ÚLTIMA HORA" /
 * section label from the reference reel. Black pill, cream text, letter-spaced
 * caps. Pops in with a small spring; static in loop mode.
 */
export const KickerLabel: React.FC<{
  text: string;
  tokens: BrandTokens;
  top?: number;
  loopFrames?: number;
}> = ({ text, tokens, top = 8, loopFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { surface, ink } = roles(tokens);
  const looping = !!loopFrames && loopFrames > 0;
  const enter = looping ? 1 : spring({ frame, fps, config: { damping: 14, mass: 0.4, stiffness: 200 } });

  if (!text) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: `${top}%`,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        transform: `translateY(${(1 - enter) * -16}px)`,
        opacity: enter,
      }}
    >
      <span
        style={{
          backgroundColor: ink,
          color: surface,
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.bold,
          fontSize: 30,
          letterSpacing: "0.22em",
          padding: "10px 22px 6px",
          borderRadius: 6,
          textTransform: "uppercase",
        }}
      >
        {text}
      </span>
    </div>
  );
};
