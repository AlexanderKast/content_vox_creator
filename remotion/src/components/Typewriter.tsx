import React from "react";
import { useCurrentFrame } from "remotion";

/**
 * Character-by-character reveal with a blinking cursor — the "annotation
 * label" typewriter treatment from the vox-paper reference sheet (Fig. 3 —
 * Trade Route style captions), requested 2026-07-18 for the carrusel kicker.
 *
 * Runs once per Sequence (each carrusel slide is its own Sequence, so this
 * naturally replays every time a slide is entered — including on the loop
 * wrap, which is what we want: frame 0 is always "nothing typed yet").
 */
export const Typewriter: React.FC<{
  text: string;
  delay?: number;
  charFrames?: number; // frames per character
  style?: React.CSSProperties;
}> = ({ text, delay = 0, charFrames = 1.4, style }) => {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - delay);
  const charsShown = Math.min(text.length, Math.floor(elapsed / charFrames));
  const done = charsShown >= text.length;
  // Cursor blinks while typing, then settles hidden once the line is complete
  // — a permanently blinking cursor on a static kicker reads as broken, not
  // stylistic.
  const cursorOn = !done && Math.floor(elapsed / 8) % 2 === 0;

  return (
    <span style={style}>
      {text.slice(0, charsShown)}
      <span style={{ opacity: cursorOn ? 1 : 0 }}>▌</span>
    </span>
  );
};
