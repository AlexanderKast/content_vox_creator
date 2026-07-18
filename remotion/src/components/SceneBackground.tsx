import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { Background } from "./Background";
import { hexToRgba, roles } from "../design";

/**
 * The beat's "world": a full-frame themed scene illustration (bakery, map,
 * stadium) behind the content. Falls back to the cream paper Background when
 * the beat has no scene.
 *
 * A slow push-in keeps it alive, and a soft cream scrim over the lower third
 * guarantees the title + subtitle stay legible no matter what the scene shows.
 * `seamless` (carrusel) makes the push-in periodic so the loop wrap is clean.
 */
export const SceneBackground: React.FC<{
  tokens: BrandTokens;
  scene: string | null;
  seamless?: boolean;
}> = ({ tokens, scene, seamless = false }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const { surface } = roles(tokens);

  if (!scene) return <Background tokens={tokens} seamless={seamless} />;

  const angle = (frame / Math.max(1, durationInFrames)) * Math.PI * 2;
  const zoom = seamless
    ? 1.05 + ((1 - Math.cos(angle)) / 2) * 0.04
    : interpolate(frame, [0, durationInFrames], [1.04, 1.12], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: surface, overflow: "hidden" }}>
      <Img
        src={staticFile(scene)}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${zoom})`,
        }}
      />
      {/* Cream scrim over the lower third so text stays readable over any art. */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(to bottom, ${hexToRgba(surface, 0)} 40%, ${hexToRgba(
            surface,
            0.78
          )} 82%, ${hexToRgba(surface, 0.9)} 100%)`,
        }}
      />
    </AbsoluteFill>
  );
};
