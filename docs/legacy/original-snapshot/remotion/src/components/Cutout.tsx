import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A cutout sticker. Enters with a bounce, never a fade.
 *
 * The no-fade rule is the whole box aesthetic: fades read as "template",
 * bounces read as "edited".
 */
export const Cutout: React.FC<{
  src: string;
  delay?: number;
  x?: number;
  y?: number;
  scale?: number;
  rotate?: number;
}> = ({ src, delay = 0, x = 0, y = 0, scale = 1, rotate = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delay,
    fps,
    config: { damping: 11, mass: 0.6, stiffness: 180 },
  });

  const drift = interpolate(frame - delay, [0, 90], [0, -14], {
    extrapolateRight: "clamp",
  });

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
          `translate(${x}%, ${y + drift / 10}%)`,
          `scale(${entrance})`,
          `rotate(${rotate * entrance}deg)`,
        ].join(" "),
        filter: "drop-shadow(0 24px 48px rgba(0,0,0,0.55))",
      }}
    />
  );
};
