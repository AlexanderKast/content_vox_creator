import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens, WordTiming } from "../types";
import { ELEVATION, MOTION, TYPE, roles } from "../design";

/**
 * Oversized display type that lands word by word — and doesn't land flat.
 * Every visual value (sizes, weights, tracking, emphasis, motion, color)
 * comes from the design system (design.ts), so it matches the rest of the
 * project instead of being tuned in isolation.
 *
 *   - SIZE VARIES per word: numbers and long/key words come in bigger and in
 *     the accent (TYPE.emphasisScale); short connectors step back
 *     (TYPE.deemphasisScale). Varied size reads as design, not caption.
 *   - each word POPS in (MOTION.spring.word) with a small hand-made tilt.
 *   - emphasized words keep a gentle size pulse so the line never freezes.
 *
 * Timing: `wordTimings` (factory.align) lands each word on its real spoken
 * frame; otherwise the estimated `delay + index*stagger`. `impact` (hook) makes
 * words SLAM down from oversized. `loopFrames` (carrusel) makes settled motion
 * periodic so the loop wrap stays seamless.
 */

const CONNECTORS = new Set([
  "de", "el", "la", "los", "las", "y", "o", "en", "un", "una", "a", "que",
  "con", "por", "su", "tu", "al", "del", "es", "no", "ni", "lo",
]);

function wordScale(word: string): number {
  const clean = word.replace(/[^\p{L}\p{N}]/gu, "");
  if (/\d/.test(clean)) return TYPE.emphasisScale; // a number — always emphasize
  if (clean.length >= 8) return TYPE.emphasisScale; // long, load-bearing word
  // Only real connector words step back — NOT short acronyms (MCP, IA, USB).
  if (CONNECTORS.has(clean.toLowerCase())) return TYPE.deemphasisScale;
  return 1;
}

export const KineticText: React.FC<{
  text: string;
  tokens: BrandTokens;
  delay?: number;
  size?: number;
  bottom?: number;
  weight?: number;
  wordTimings?: WordTiming[] | null;
  sequenceFrom?: number;
  loopFrames?: number;
  impact?: boolean;
  stagger?: number;
  // True when this text sits over a photographic backdrop (beat.scene) —
  // a flat brand-ink color reads fine over a flat surface color but loses
  // to a busy photo. Switches to near-white fill + a black outline/shadow,
  // which stays legible over ANY image tone (verified 2026-07-18: plain
  // dark ink on a dim office photo was unreadable).
  legibleOverPhoto?: boolean;
}> = ({
  text, tokens, delay = 0, size = TYPE.size.headline, bottom = 18,
  weight = TYPE.weight.black, wordTimings, sequenceFrom = 0, loopFrames,
  impact = false, stagger = 2, legibleOverPhoto = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  const { ink: brandInk, accent } = roles(tokens);
  const ink = legibleOverPhoto ? "#FFFFFF" : brandInk;
  const looping = !!loopFrames && loopFrames > 0;

  const useRealTimings = !!wordTimings && wordTimings.length === words.length;

  return (
    <div
      style={{
        position: "absolute",
        left: "8%",
        right: "8%",
        bottom: `${bottom}%`,
        display: "flex",
        flexWrap: "wrap",
        alignItems: "flex-end",
        // Generous WORD gap — Anton is very condensed, so a tight gap makes
        // words touch and read as one blob. Row gap keeps wrapped lines apart.
        gap: `${TYPE.rowGapEm}em 0.5em`,
        justifyContent: "center",
      }}
    >
      {words.map((word, index) => {
        const landingFrame = useRealTimings
          ? wordTimings![index].startFrame - sequenceFrom
          : delay + index * stagger;
        const enter = looping
          ? 1
          : spring({
              frame: frame - landingFrame,
              fps,
              config: impact ? MOTION.spring.wordImpact : MOTION.spring.word,
            });

        const emph = wordScale(word);
        const emphasized = emph >= TYPE.emphasisScale;

        const settled = frame - landingFrame;
        const angle = looping ? (frame / loopFrames!) * Math.PI * 2 : settled / fps;
        const alive = looping || enter > 0.98;
        const floatY = alive ? Math.sin(angle * 1.6 + index) * MOTION.ambient.textFloatPx : 0;
        // Tiny transient pulse only — kept small so it never grows a word into
        // its neighbour.
        const pulse = emphasized && alive ? 1 + Math.sin(angle * 1.2 + index) * 0.02 : 1;
        const tilt = ((index % 3) - 1) * 1.0; // gentle hand-made tilt

        // Emphasis is REAL fontSize (the layout box grows with it, so flexWrap
        // spaces neighbours correctly). Only the entrance/pulse use transform
        // scale — transient, small, can't cause a persistent overlap.
        const entryScale = impact ? 1 + (1 - enter) * 0.4 : 0.9 + enter * 0.1;
        const wordFontSize = Math.round(size * emph);

        return (
          <span
            key={`${word}-${index}`}
            style={{
              display: "inline-block",
              fontFamily: tokens.displayFont,
              fontWeight: emphasized ? TYPE.weight.black : weight,
              fontSize: wordFontSize,
              lineHeight: TYPE.lineHeight,
              textTransform: "uppercase",
              color: emphasized ? accent : ink,
              transform: `translateY(${(1 - enter) * 34 + floatY}px) scale(${entryScale * pulse}) rotate(${tilt * enter}deg)`,
              transformOrigin: "center bottom",
              opacity: enter > 0.02 ? 1 : 0,
              letterSpacing: TYPE.tracking,
              textShadow: legibleOverPhoto
                ? "0 3px 10px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.9)"
                : emphasized
                  ? ELEVATION.glowText(accent)
                  : "none",
              WebkitTextStroke: legibleOverPhoto ? "3px #000000" : undefined,
              paintOrder: legibleOverPhoto ? "stroke fill" : undefined,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
