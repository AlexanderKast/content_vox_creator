import React from "react";
import type { BrandTokens } from "../types";
import { TYPE, roles } from "../design";

/**
 * The persistent series tag at the top of EVERY frame — "100% AUTOMATIZADO"
 * in the reference. A black pill with a small orange burst icon and the label.
 * Static (doesn't animate) so it reads as a fixed brand/series stamp.
 */
export const SeriesKicker: React.FC<{ text: string; tokens: BrandTokens; top?: number }> = ({
  text,
  tokens,
  top = 4,
}) => {
  const { surface, accent } = roles(tokens);
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
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          backgroundColor: accent,
          borderRadius: 999,
          padding: "9px 20px 9px 12px",
        }}
      >
        {/* burst icon in the surface color so it reads inside the gold pill */}
        <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
          <path
            d="M13 1 l2.4 6.2 6.2-2.4-2.4 6.2 6.2 2.4-6.2 2.4 2.4 6.2-6.2-2.4L13 25l-2.4-6.2-6.2 2.4 2.4-6.2L.6 13l6.2-2.4L4.4 4.4l6.2 2.4z"
            fill={surface}
          />
        </svg>
        <span
          style={{
            fontFamily: tokens.displayFont,
            fontWeight: TYPE.weight.bold,
            fontSize: 26,
            letterSpacing: "0.14em",
            color: surface,
            textTransform: "uppercase",
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};
