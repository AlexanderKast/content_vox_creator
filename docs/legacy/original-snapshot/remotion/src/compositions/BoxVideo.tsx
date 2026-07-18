import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Background } from "../components/Background";
import { Cutout } from "../components/Cutout";
import { KineticText } from "../components/KineticText";
import { Underline } from "../components/Underline";
import type { Manifest } from "../types";

/**
 * Mode VIDEO — 9:16, continuous narration, the edit sets the pace.
 *
 * Rules enforced here:
 *   - nothing static past ~1.2s (every beat carries a moving element)
 *   - no fades anywhere (springs only)
 *   - text lands with the voice
 */

// Deterministic scatter so cutouts never stack in the same spot.
const PLACEMENTS = [
  { x: 0, y: -12, scale: 1.0, rotate: -3 },
  { x: -18, y: -20, scale: 0.72, rotate: 5 },
  { x: 20, y: -6, scale: 0.66, rotate: -6 },
];

export const BoxVideo: React.FC<{ manifest: Manifest }> = ({ manifest }) => {
  const { tokens, fps, beats, voice } = manifest;
  let cursor = 0;

  return (
    <AbsoluteFill>
      <Background tokens={tokens} />

      {voice ? <Audio src={staticFile(voice)} /> : null}

      {beats.map((beat) => {
        const from = cursor;
        const durationInFrames = Math.round(beat.seconds * fps);
        cursor += durationInFrames;

        return (
          <Sequence
            key={beat.index}
            from={from}
            durationInFrames={durationInFrames}
            name={`beat-${beat.index}`}
          >
            {beat.assets.map((src, assetIndex) => {
              const place = PLACEMENTS[assetIndex % PLACEMENTS.length];
              return (
                <Cutout
                  key={src}
                  src={staticFile(src)}
                  delay={assetIndex * 4}
                  x={place.x}
                  y={place.y}
                  scale={place.scale}
                  rotate={place.rotate}
                />
              );
            })}
            <KineticText text={beat.text} tokens={tokens} delay={3} size={104} />
            <Underline tokens={tokens} delay={10} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
