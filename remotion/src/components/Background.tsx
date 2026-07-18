import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { hexToRgba, roles } from "../design";

/**
 * Editorial paper background — cream newsprint, the base of the "breaking
 * news" reference look. Warm off-white (from brand.json `paper`) with a fine
 * paper grain (multiply, so it darkens like real fibre), the faintest accent
 * warmth, and soft aged edges. Almost still — paper doesn't move — with only a
 * barely-there grain breath so it isn't a frozen frame.
 *
 * `seamless` (carrusel): motion is a single sine over the clip so the loop
 * wrap is invisible.
 */
export const Background: React.FC<{ tokens: BrandTokens; seamless?: boolean }> = ({
  tokens,
  seamless = false,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const { surface, accent } = roles(tokens);

  const angle = (frame / Math.max(1, durationInFrames)) * Math.PI * 2;
  const t = frame / fps;
  const grainBreath = 1 + (seamless ? Math.sin(angle) : Math.sin(t * 0.5)) * 0.04;

  return (
    <AbsoluteFill style={{ backgroundColor: surface, overflow: "hidden" }}>
      {/* Faint warm wash so the cream isn't flat — a whisper of accent at the
          corners, like ink warmth on newsprint. */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 40%, ${hexToRgba(accent, 0.05)} 0%, ${hexToRgba(
            accent,
            0
          )} 55%)`,
        }}
      />

      {/* Paper grain — multiply so it reads as fibre/texture, not a glow. */}
      <AbsoluteFill
        style={{
          opacity: 0.5 + tokens.grain,
          mixBlendMode: "multiply",
          transform: `scale(${grainBreath})`,
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E\")",
          backgroundRepeat: "repeat",
        }}
      />

      {/* Soft aged edges — subtle, warm, not a black hole. */}
      <AbsoluteFill
        style={{ boxShadow: `inset 0 0 260px 60px ${hexToRgba("#000000", 0.06)}` }}
      />
    </AbsoluteFill>
  );
};
