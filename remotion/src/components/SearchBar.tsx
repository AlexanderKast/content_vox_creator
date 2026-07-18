import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { ELEVATION, TYPE, roles } from "../design";

/**
 * A comment/search-bar mockup for the CTA — "escribe la palabra … y te mando
 * la info" from the reference. A rounded input with the word being typed out
 * letter by letter (a blinking caret), and a round accent send button.
 * Great as the final slide's call to action.
 */
export const SearchBar: React.FC<{
  word: string;
  tokens: BrandTokens;
  bottom?: number;
  loopFrames?: number;
}> = ({ word, tokens, bottom = 20, loopFrames }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const { surface, ink, accent } = roles(tokens);
  if (!word) return null;

  // Type the word out over the first ~1.5s, then hold. Loops cleanly.
  const total = loopFrames ?? durationInFrames;
  const typeDur = Math.min(total * 0.5, fps * 1.5);
  const shown = Math.max(0, Math.min(word.length, Math.floor((frame / typeDur) * word.length)));
  const caretOn = Math.floor(frame / (fps / 3)) % 2 === 0;

  return (
    <div
      style={{
        position: "absolute",
        left: "10%",
        right: "10%",
        bottom: `${bottom}%`,
        display: "flex",
        alignItems: "center",
        gap: 14,
        backgroundColor: surface,
        border: `4px solid ${ink}`,
        borderRadius: 999,
        padding: "16px 16px 16px 30px",
        boxShadow: ELEVATION.sticker,
      }}
    >
      <span
        style={{
          flex: 1,
          fontFamily: tokens.displayFont,
          fontWeight: TYPE.weight.bold,
          fontSize: 46,
          letterSpacing: "0.02em",
          color: ink,
          textTransform: "uppercase",
        }}
      >
        {word.slice(0, shown)}
        <span style={{ opacity: caretOn ? 1 : 0, color: accent }}>|</span>
      </span>
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: "50%",
          backgroundColor: accent,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flex: "0 0 auto",
        }}
      >
        <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
          <path d="M5 15 H23 M16 8 L23 15 L16 22" stroke={surface} strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
};
