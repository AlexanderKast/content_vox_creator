/**
 * Actually loads the brand's display font before any frame renders.
 *
 * Previously `tokens.displayFont` was only ever used as a CSS font-family
 * string — nothing ever called Remotion's `loadFont()`, so headless
 * Chromium had no guarantee Anton/Playfair Display were ready before a
 * frame got captured; it could silently fall back to a default sans the
 * whole render. `useDisplayFont()` fixes this with the documented
 * delayRender/continueRender pattern — Remotion won't capture a frame
 * until the font is confirmed loaded.
 */

import { useEffect, useState } from "react";
import { continueRender, delayRender } from "remotion";
import { loadFont } from "@remotion/google-fonts/Anton";

// Anton — the condensed heavy grotesque behind the "breaking news / editorial"
// look of the reference reel. Single weight (400) that already reads black.
export const DISPLAY_FONT_FAMILY = "Anton";

export function useDisplayFont(): void {
  const [handle] = useState(() => delayRender("Loading Anton"));

  useEffect(() => {
    const { waitUntilDone } = loadFont("normal", { weights: ["400"] });
    waitUntilDone()
      .then(() => continueRender(handle))
      .catch((err) => {
        console.error("Font load failed, continuing with fallback font:", err);
        continueRender(handle);
      });
  }, [handle]);
}
