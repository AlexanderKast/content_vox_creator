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
  // Same treatment as every other text component (2026-07-18, "todos
  // absolutamente todos los textos") — white + shadow/outline instead of
  // the flat brand ink, for whatever unpredictable photo/dark background
  // sits behind it at this point in the video.
  legibleOverPhoto?: boolean;
}> = ({ tokens, top, bottom, left = 8, legibleOverPhoto = false }) => {
  const { ink: brandInk, accent } = roles(tokens);
  const ink = legibleOverPhoto ? "#FFFFFF" : brandInk;
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
      <span
        style={{
          width: 12,
          height: 12,
          borderRadius: "50%",
          backgroundColor: accent,
          display: "inline-block",
          boxShadow: legibleOverPhoto ? "0 1px 4px rgba(0,0,0,0.85)" : "none",
        }}
      />
      <span
        style={{
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.bold,
          fontSize: 28,
          letterSpacing: "0.06em",
          color: ink,
          textShadow: legibleOverPhoto ? "0 2px 6px rgba(0,0,0,0.85), 0 0 3px rgba(0,0,0,0.9)" : "none",
          WebkitTextStroke: legibleOverPhoto ? "1px #000000" : undefined,
          paintOrder: legibleOverPhoto ? "stroke fill" : undefined,
        }}
      >
        {tokens.handle}
      </span>
    </div>
  );
};
