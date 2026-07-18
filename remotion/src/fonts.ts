/**
 * Actually loads a brand's display font before any frame renders.
 *
 * Previously this loaded ONLY Anton, hardcoded, regardless of what a brand's
 * `tokens.displayFont` said — `mile` (Cormorant) or a future brand would
 * silently fall back to a default sans on every render, since nothing ever
 * called Remotion's `loadFont()` for their actual font. `useDisplayFont(name)`
 * now takes the brand's font name and loads the matching Google Font, with
 * the documented delayRender/continueRender pattern so Remotion won't
 * capture a frame until it's confirmed loaded. Unknown names fall back to
 * Anton rather than failing the build.
 */

import { useEffect, useState } from "react";
import { continueRender, delayRender } from "remotion";
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadCormorant } from "@remotion/google-fonts/Cormorant";
import { loadFont as loadMontserrat } from "@remotion/google-fonts/Montserrat";
import { loadFont as loadPlayfairDisplay } from "@remotion/google-fonts/PlayfairDisplay";

type FontLoader = () => { waitUntilDone: () => Promise<unknown> };

// One entry per font name actually used in brand.json. Montserrat loads
// several weights — it's a real weight family (unlike Anton, single-weight
// display-only), which is the point: TYPE.weight.medium/bold/black in
// design.ts need real 600/700/900 files to land on screen, not a browser
// faux-bold synthesized from one weight.
const FONT_LOADERS: Record<string, FontLoader> = {
  Anton: () => loadAnton("normal", { weights: ["400"] }),
  Montserrat: () => loadMontserrat("normal", { weights: ["600", "700", "800", "900"] }),
  Cormorant: () => loadCormorant("normal", { weights: ["400", "600", "700"] }),
  "Playfair Display": () => loadPlayfairDisplay("normal", { weights: ["400", "700", "900"] }),
};

export function useDisplayFont(fontName: string): void {
  const [handle] = useState(() => delayRender(`Loading ${fontName}`));

  useEffect(() => {
    const loader = FONT_LOADERS[fontName] ?? FONT_LOADERS.Anton;
    const { waitUntilDone } = loader();
    waitUntilDone()
      .then(() => continueRender(handle))
      .catch((err) => {
        console.error(`Font load failed for "${fontName}", continuing with fallback font:`, err);
        continueRender(handle);
      });
    // fontName is fixed for the lifetime of a single render (one manifest,
    // one brand) — this effect intentionally runs once, not on every prop
    // change, matching the original delayRender-once contract.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handle]);
}
