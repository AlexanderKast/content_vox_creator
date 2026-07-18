import React from "react";
import type { BrandTokens } from "../types";

/**
 * Slide counter for carousels.
 *
 * Not decoration: people finish what they know has an end. It measurably lifts
 * swipe-through, which is the only retention metric a carousel has.
 */
export const SlideCounter: React.FC<{
  index: number;
  total: number;
  tokens: BrandTokens;
}> = ({ index, total, tokens }) => (
  <div
    style={{
      position: "absolute",
      top: 110, // clears Instagram's 80px top UI band
      right: 60,
      fontFamily: tokens.displayFont,
      fontSize: 40,
      color: tokens.colors.white,
      opacity: 0.65,
      letterSpacing: "0.05em",
    }}
  >
    {index}/{total}
  </div>
);
