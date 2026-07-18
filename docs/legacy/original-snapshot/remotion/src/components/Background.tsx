import React from "react";
import { AbsoluteFill } from "remotion";
import type { BrandTokens } from "../types";

/**
 * Textured paper background. Never flat black — flat black reads as a slide
 * deck, not as a documentary.
 */
export const Background: React.FC<{ tokens: BrandTokens }> = ({ tokens }) => {
  const grainOpacity = tokens.grain;

  return (
    <AbsoluteFill style={{ backgroundColor: tokens.colors.paper }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 35%, ${tokens.colors.black}00 0%, ${tokens.colors.black} 85%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: grainOpacity,
          mixBlendMode: "overlay",
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)'/%3E%3C/svg%3E\")",
          backgroundRepeat: "repeat",
        }}
      />
    </AbsoluteFill>
  );
};
