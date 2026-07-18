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
  bottom?: number;
  left?: number;
}> = ({ tokens, bottom = 8, left = 8 }) => {
  const { ink, accent } = roles(tokens);
  if (!tokens.handle) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: `${bottom}%`,
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
