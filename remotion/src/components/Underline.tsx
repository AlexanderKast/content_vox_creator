import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import type { BrandTokens } from "../types";
import { MOTION, roles } from "../design";

/** A marker underline that draws itself. Pure box-style signature. Accent
 * color and draw duration come from the design system. */
export const Underline: React.FC<{
  tokens: BrandTokens;
  delay?: number;
  width?: number;
  bottom?: number;
}> = ({ tokens, delay = 0, width = 52, bottom = 15 }) => {
  const frame = useCurrentFrame();
  const { accent } = roles(tokens);
  const progress = interpolate(frame - delay, [0, MOTION.frames.underline], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <svg
      viewBox="0 0 100 6"
      preserveAspectRatio="none"
      style={{
        position: "absolute",
        left: `${(100 - width) / 2}%`,
        bottom: `${bottom}%`,
        width: `${width}%`,
        height: 22,
      }}
    >
      <path
        d="M1,4 C22,1 48,6 72,2.5 C84,1 92,3.5 99,2"
        fill="none"
        stroke={accent}
        strokeWidth={3.5}
        strokeLinecap="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - progress}
      />
    </svg>
  );
};
