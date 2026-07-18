import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ELEVATION, MOTION } from "../design";

/**
 * A cutout sticker. Enters with a bounce (MOTION.spring.sticker), never a
 * fade, then keeps living: a slow drift plus a gentle float/tilt so it never
 * freezes. A still cutout on a moving background is the tell of a rigid
 * template — something is always in motion.
 *
 * The exit is handled by BeatStage (the whole beat clears together), so this
 * only owns entrance + continuous life. All amounts come from MOTION.ambient.
 *
 * `loopFrames` (carrusel) makes the motion periodic (whole cycles) and drops
 * the net drift + one-shot entrance, so the seamless loop stays intact.
 */
export const Cutout: React.FC<{
  src: string;
  delay?: number;
  x?: number;
  y?: number;
  scale?: number;
  rotate?: number;
  index?: number;
  loopFrames?: number;
}> = ({ src, delay = 0, x = 0, y = 0, scale = 1, rotate = 0, index = 0, loopFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - delay;
  const looping = !!loopFrames && loopFrames > 0;

  const entrance = looping ? 1 : spring({ frame: local, fps, config: MOTION.spring.sticker });

  const phase = index * 1.7;
  const loopAngle = looping ? (frame / loopFrames!) * Math.PI * 2 : 0;

  const drift = looping
    ? 0
    : interpolate(local, [0, 200], [0, MOTION.ambient.driftPct], { extrapolateRight: "clamp" });

  const floatY = looping
    ? Math.sin(loopAngle + phase) * MOTION.ambient.floatPx
    : Math.sin(local / fps + phase) * MOTION.ambient.floatPx;
  const sway = looping
    ? Math.sin(loopAngle * 2 + phase) * MOTION.ambient.swayDeg
    : Math.sin((local / fps) * 0.8 + phase) * MOTION.ambient.swayDeg;

  return (
    <Img
      src={src}
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        width: `${60 * scale}%`,
        transform: [
          `translate(-50%, -50%)`,
          `translate(${x}%, ${y + drift / 10 + floatY / 10}%)`,
          `scale(${entrance})`,
          `rotate(${rotate * entrance + sway}deg)`,
        ].join(" "),
        filter: ELEVATION.sticker,
      }}
    />
  );
};
