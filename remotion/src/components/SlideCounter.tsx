import React from "react";
import type { BrandTokens } from "../types";
import { TYPE, roles } from "../design";

/**
 * Slide counter for carousels.
 *
 * Not decoration: people finish what they know has an end. It measurably lifts
 * swipe-through, which is the only retention metric a carousel has. Size, weight
 * and color come from the design system.
 */
export const SlideCounter: React.FC<{
  index: number;
  total: number;
  tokens: BrandTokens;
  // See KineticText's prop of the same name — a dark brand ink at 0.65
  // opacity nearly disappears against a busy photo backdrop (2026-07-18).
  legibleOverPhoto?: boolean;
}> = ({ index, total, tokens, legibleOverPhoto = false }) => {
  const { ink: brandInk } = roles(tokens);
  const ink = legibleOverPhoto ? "#FFFFFF" : brandInk;
  return (
    <div
      style={{
        position: "absolute",
        top: 110, // clears Instagram's 80px top UI band
        right: 60,
        fontFamily: tokens.displayFont,
        fontWeight: TYPE.weight.medium,
        fontSize: TYPE.size.counter,
        color: ink,
        opacity: legibleOverPhoto ? 0.95 : 0.65,
        letterSpacing: "0.05em",
        textShadow: legibleOverPhoto ? "0 2px 6px rgba(0,0,0,0.85)" : "none",
        WebkitTextStroke: legibleOverPhoto ? "1px #000000" : undefined,
        paintOrder: legibleOverPhoto ? "stroke fill" : undefined,
      }}
    >
      {index}/{total}
    </div>
  );
};
