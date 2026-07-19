import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { TYPE } from "../design";

/**
 * "DESLIZA →" swipe affordance for carousel slides. Nudges horizontally to
 * pull the eye toward the next slide — the swipe is the cut, and you have to
 * earn it every time. Shown on every slide except the last.
 *
 * The nudge is periodic over the slide's full duration, so it stays seamless
 * on a looping slide (last frame == first).
 */
export const SwipeHint: React.FC<{ tokens: BrandTokens }> = ({ tokens }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  // White again (2026-07-18, full-bleed rewrite) — the earlier black call
  // was made for the flat light-paper background that architecture had at
  // the bottom of every slide. That background is gone: the bottom of the
  // frame is now always inside SceneBackground's dark gradient band, where
  // black text is invisible. White is the only choice that reads there.
  const color = "#FFFFFF";

  const angle = (frame / Math.max(1, durationInFrames)) * Math.PI * 2;
  const nudge = Math.sin(angle * 3) * 10; // horizontal beckon
  const glow = 0.55 + Math.sin(angle * 3) * 0.25;

  return (
    <div
      style={{
        position: "absolute",
        bottom: "9%",
        right: "8%",
        display: "flex",
        alignItems: "center",
        gap: 14,
        transform: `translateX(${nudge}px)`,
        opacity: glow,
      }}
    >
      <span
        style={{
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.bold,
          fontSize: 30,
          letterSpacing: "0.22em",
          color,
        }}
      >
        DESLIZA
      </span>
      <svg width="58" height="40" viewBox="0 0 58 40" fill="none">
        {/* double chevron pointing right */}
        <path d="M6 8 L22 20 L6 32" stroke={color} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" opacity="0.55" />
        <path d="M26 8 L42 20 L26 32" stroke={color} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};
