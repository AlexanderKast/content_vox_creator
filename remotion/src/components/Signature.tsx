import React from "react";
import type { BrandTokens } from "../types";
import { TYPE, roles } from "../design";

/**
 * The brand handle signature (@alexemprendee) — a small persistent watermark
 * on every slide and every video, so the piece is always attributable. A tiny
 * accent dot + the handle, bottom-left, subtle but readable. Handle comes from
 * brand.json (tokens.handle), never hardcoded.
 */
export const Signature: React.FC<{
  tokens: BrandTokens;
  // Pass exactly one of top/bottom — reference carousels (2026-07-18 batch)
  // put the handle in the top band with the rest of the account chrome
  // (SlideCounter, SeriesKicker), not bottom-left; CarouselSlide uses `top`
  // now. BoxVideo still passes `bottom` — video has no top UI band to match.
  top?: number;
  bottom?: number;
  left?: number;
}> = ({ tokens, top, bottom, left = 8 }) => {
  const { ink, accent } = roles(tokens);
  if (!tokens.handle) return null;

  return (
    <div
      style={{
        position: "absolute",
        ...(top !== undefined ? { top: `${top}%` } : { bottom: `${bottom ?? 8}%` }),
        left: `${left}%`,
        display: "flex",
        alignItems: "center",
        gap: 10,
        opacity: 0.72,
      }}
    >
      <span style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: accent, display: "inline-block" }} />
      <span
        style={{
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.bold,
          fontSize: 28,
          letterSpacing: "0.06em",
          color: ink,
        }}
      >
        {tokens.handle}
      </span>
    </div>
  );
};
