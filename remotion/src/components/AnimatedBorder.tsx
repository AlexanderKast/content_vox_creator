import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { roles } from "../design";

/**
 * BoxVideo's frame — DecorativeBorder's double-line ink frame (unchanged),
 * plus accent-colored corner ticks that breathe continuously (opacity +
 * scale, sine over real time, not tied to a loop) so the frame reads as
 * alive for the whole video, not a static overlay pasted on top
 * (2026-07-18, "marco animado" — explicit request; the carrusel's
 * DecorativeBorder stays static on purpose, one slide at a time, but a
 * 100s continuous video benefits from a frame that visibly lives with it).
 */
export const AnimatedBorder: React.FC<{ tokens: BrandTokens; inset?: number }> = ({
  tokens,
  inset = 28,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { ink, accent } = roles(tokens);

  const t = frame / fps;
  const pulse = 0.55 + Math.sin(t * 1.4) * 0.45; // 0.1 - 1.0, ~4.5s period
  const tickScale = 1 + Math.sin(t * 1.4) * 0.12;

  const tick = (style: React.CSSProperties) => (
    <div
      style={{
        position: "absolute",
        width: 30,
        height: 30,
        opacity: pulse,
        transform: `scale(${tickScale})`,
        ...style,
      }}
    />
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Static ink double-line — same as DecorativeBorder, frames without
          fighting the art. */}
      <div style={{ position: "absolute", inset, border: `2px solid ${ink}`, opacity: 0.85 }} />
      <div style={{ position: "absolute", inset: inset + 8, border: `5px solid ${ink}`, opacity: 0.9 }} />
      {/* Accent corner ticks — these breathe. */}
      {tick({ top: inset + 4, left: inset + 4, borderTop: `4px solid ${accent}`, borderLeft: `4px solid ${accent}` })}
      {tick({ top: inset + 4, right: inset + 4, borderTop: `4px solid ${accent}`, borderRight: `4px solid ${accent}` })}
      {tick({ bottom: inset + 4, left: inset + 4, borderBottom: `4px solid ${accent}`, borderLeft: `4px solid ${accent}` })}
      {tick({ bottom: inset + 4, right: inset + 4, borderBottom: `4px solid ${accent}`, borderRight: `4px solid ${accent}` })}
    </AbsoluteFill>
  );
};
