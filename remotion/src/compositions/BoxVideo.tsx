import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { BeatStage } from "../components/BeatStage";
import { Cutout } from "../components/Cutout";
import { KineticText } from "../components/KineticText";
import { SceneBackground } from "../components/SceneBackground";
import { SeriesKicker } from "../components/SeriesKicker";
import { Signature } from "../components/Signature";
import { Underline } from "../components/Underline";
import { DISTANT_PLACEMENT, MOTION, PLACEMENTS, TYPE } from "../design";
import type { Manifest } from "../types";

/**
 * Mode VIDEO — 9:16, continuous narration, the edit sets the pace.
 *
 * Rules enforced here:
 *   - nothing static past ~1.2s (every beat carries a moving element)
 *   - text lands with the voice
 *   - no fade-INS (entrances are springs) — but beats hand off with a moving
 *     exit (BeatStage), and the whole frame drifts (Background + Ken Burns),
 *     so the edit flows instead of cutting between frozen slides
 *
 * Every layout/motion/type value comes from the design system (design.ts).
 */

const MUSIC_VOLUME = 0.12; // low bed — the voiceover clearly leads

export const BoxVideo: React.FC<{ manifest: Manifest }> = ({ manifest }) => {
  const { tokens, fps, beats, voice, music, loop } = manifest;
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const loopFade = MOTION.frames.loopFade;
  let cursor = 0;

  // manifest.loop: fade the foreground (not the Background, which is
  // frame-identical everywhere) to nothing at both ends so the wrap-around
  // cut is a brief breath, not a jump.
  let foregroundOpacity = 1;
  if (loop) {
    if (frame < loopFade) {
      foregroundOpacity = frame / loopFade;
    } else if (frame > durationInFrames - loopFade) {
      foregroundOpacity = Math.max(0, (durationInFrames - frame) / loopFade);
    }
  }

  return (
    <AbsoluteFill>
      <Background tokens={tokens} />

      {/* Music sits under the voice — a bed, but a driving one. Loud enough
          to feel the beat, not so loud it fights the narration. */}
      {music ? <Audio src={staticFile(music)} volume={MUSIC_VOLUME} /> : null}
      {voice ? <Audio src={staticFile(voice)} /> : null}

      <AbsoluteFill style={{ opacity: foregroundOpacity }}>
        {beats.map((beat, beatIndex) => {
          const from = cursor;
          const durationInFramesForBeat = Math.round(beat.seconds * fps);
          cursor += durationInFramesForBeat;

          return (
            <Sequence
              key={beat.index}
              from={from}
              durationInFrames={durationInFramesForBeat}
              name={`beat-${beat.index}`}
            >
              {/* This beat's themed scene fills the frame behind the content
                  during its window (falls back to the base Background when the
                  beat has no scene). It does NOT ride the beat camera. */}
              {beat.scene ? <SceneBackground tokens={tokens} scene={beat.scene} /> : null}
              {/* Visuals ride the camera (BeatStage: push-in + moving hand-off).
                  Audio stays outside it so the exit-opacity never touches sound. */}
              <BeatStage
                durationInFrames={durationInFramesForBeat}
                index={beatIndex}
                opener={beatIndex === 0}
              >
                {beat.assets.map((asset, assetIndex) => {
                  // Rotate the placement slot by the beat too, so the same
                  // asset count lands in different spots from beat to beat —
                  // never the same layout twice in a row. A public figure
                  // skips that rotation entirely — always DISTANT_PLACEMENT,
                  // never a close-up.
                  const place = asset.isPublicFigure
                    ? DISTANT_PLACEMENT
                    : PLACEMENTS[(assetIndex + beatIndex) % PLACEMENTS.length];
                  return (
                    <Cutout
                      key={asset.src}
                      src={staticFile(asset.src)}
                      delay={assetIndex * MOTION.frames.assetStagger}
                      x={place.x}
                      y={place.y}
                      scale={place.scale}
                      rotate={place.rotate}
                      index={assetIndex}
                    />
                  );
                })}
                <KineticText
                  text={beat.text}
                  tokens={tokens}
                  delay={beatIndex === 0 ? 1 : 3}
                  size={beatIndex === 0 ? TYPE.size.hook : TYPE.size.headline}
                  impact={beatIndex === 0}
                  stagger={beatIndex === 0 ? 1 : 2}
                  wordTimings={beatIndex === 0 ? null : beat.wordTimings}
                  sequenceFrom={beat.sequenceFrom}
                />
                <Underline tokens={tokens} delay={MOTION.frames.underline} />
              </BeatStage>
              {beat.sfx.map((cue, i) => (
                <Sequence key={`${cue.src}-${i}`} from={cue.frame} name={`sfx-${cue.src}`}>
                  <Audio src={staticFile(cue.src)} />
                </Sequence>
              ))}
            </Sequence>
          );
        })}
      </AbsoluteFill>

      {/* Persistent series tag + brand signature — always on. */}
      <SeriesKicker text={manifest.seriesKicker} tokens={tokens} top={3} />
      <Signature tokens={tokens} bottom={7} left={7} />
    </AbsoluteFill>
  );
};
