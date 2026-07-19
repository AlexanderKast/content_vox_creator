import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { BrandTokens } from "../types";
import { Background } from "./Background";
import { roles } from "../design";

/**
 * The beat's "world": a full-bleed photo/illustration, edge to edge, no
 * margins (2026-07-18: replaced the header-over-image layout — a top paper
 * band pushing the photo down read as a template, not a full-frame image.
 * The 7 reference carousels Alexander approved — samusdesign, CT Escola,
 * Rarison, ST Fitness, Guardian, Mirza — all share one architecture: image
 * is the whole frame, text sits on top of it, a dark top+bottom gradient
 * (below) makes that legible without hiding the middle of the shot.
 *
 * Falls back to the flat brand-surface color when the beat has no scene —
 * never a light paper box, a real full-bleed fill either way. No gradient
 * on that fallback — a flat color doesn't need one, and CarouselSlide's
 * text is legible-white regardless (see its legibleOverPhoto usage).
 *
 * A slow push-in keeps it alive. `seamless` (carrusel) makes the push-in
 * periodic so the loop wrap is clean.
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
      {/* Dual-band legibility gradient — pure black, not brand-tinted (the
          reference carousels all do this the same way regardless of
          palette). Top: 55% black fading to clear by 28% height, for the
          kicker + title. Bottom: clear from 50% fading to 88% black by the
          bottom edge, for the subtitle/CTA. The 28%-50% band stays fully
          clear so the shot itself is still visible, not just a dark frame. */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 28%, " +
            "rgba(0,0,0,0) 50%, rgba(0,0,0,0.88) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
