import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { KEN_BURNS, MOTION } from "../design";

/**
 * The camera for one beat. Turns a row of hard cuts into a flowing edit.
 *
 *   - KEN BURNS: a slow push-in plus a directional pan (design.KEN_BURNS),
 *     deterministic per beat, so the eye is never on a frozen frame.
 *   - ENTRANCE: content snaps into place (MOTION.spring.snap) — a punchy move,
 *     never a fade.
 *   - EXIT: over the last frames (MOTION.frames.exit) content lifts and clears
 *     while the next beat arrives — the cut reads as a hand-off, not a jump.
 *   - OPENER: the first beat hits like a drop (MOTION.spring.slam) plus a quick
 *     decaying screen shake. The intro should punch, not ease in.
 */
export const BeatStage: React.FC<{
  durationInFrames: number;
  index: number;
  opener?: boolean;
  children: React.ReactNode;
}> = ({ durationInFrames, index, opener = false, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const dir = KEN_BURNS[index % KEN_BURNS.length];
  const panX = interpolate(progress, [0, 1], [0, dir.x]);
  const panY = interpolate(progress, [0, 1], [0, dir.y]);
  const kenBurnsZoom = 1 + progress * MOTION.ambient.kenBurnsZoom;

  const enter = spring({ frame, fps, config: MOTION.spring.snap });
  const exit = spring({
    frame: frame - (durationInFrames - MOTION.frames.exit),
    fps,
    config: MOTION.spring.settle,
  });

  // Opener slam + decaying screen shake so the hook lands like a beat drop.
  const slam = opener ? spring({ frame, fps, config: MOTION.spring.slam }) : 1;
  const openerZoom = opener ? interpolate(slam, [0, 1], [1.16, 1]) : 1;
  const shakeAmt = opener ? Math.max(0, 1 - frame / MOTION.frames.shake) : 0;
  const shakeX = shakeAmt * Math.sin(frame * 3.1) * 14;
  const shakeY = shakeAmt * Math.cos(frame * 2.7) * 10;

  const enterY = opener ? 0 : (1 - enter) * 18;
  const exitY = exit * -30;
  const settleScale = 0.985 + enter * 0.015;
  const opacity = 1 - exit * 0.85;

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${panX + shakeX}px, ${panY + enterY + exitY + shakeY}px) scale(${
          kenBurnsZoom * settleScale * openerZoom
        })`,
        opacity,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
