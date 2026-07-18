import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";

/**
 * Oversized display type that lands word by word.
 *
 * Subtitles are part of the animation, not an accessory bolted on at the end.
 */
export const KineticText: React.FC<{
  text: string;
  tokens: BrandTokens;
  delay?: number;
  accent?: string;
  size?: number;
  bottom?: number;
}> = ({ text, tokens, delay = 0, accent, size = 96, bottom = 18 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  const accentColor = accent ?? tokens.colors[tokens.dominant] ?? tokens.colors.gold;

  return (
    <div
      style={{
        position: "absolute",
        left: "6%",
        right: "6%",
        bottom: `${bottom}%`,
        display: "flex",
        flexWrap: "wrap",
        gap: "0.18em",
        justifyContent: "center",
      }}
    >
      {words.map((word, index) => {
        const enter = spring({
          frame: frame - delay - index * 2,
          fps,
          config: { damping: 12, mass: 0.4, stiffness: 220 },
        });
        return (
          <span
            key={`${word}-${index}`}
            style={{
              fontFamily: tokens.displayFont,
              fontSize: size,
              lineHeight: 0.95,
              textTransform: "uppercase",
              color: index % 3 === 1 ? accentColor : tokens.colors.white,
              transform: `translateY(${(1 - enter) * 40}px) scale(${0.85 + enter * 0.15})`,
              opacity: enter > 0.02 ? 1 : 0,
              letterSpacing: "-0.02em",
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
