import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { AnimatedBorder } from "../components/AnimatedBorder";
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
 * Mode LANDSCAPE — 16:9 (1920×1080), narración continua.
 * Mismo flujo que BoxVideo pero orientado horizontal: YouTube, Facebook, stories horizontales.
 */

const MUSIC_VOLUME = 0.12;

export const LandscapeVideo: React.FC<{ manifest: Manifest }> = ({ manifest }) => {
  const { tokens, fps, beats, voice, music, loop } = manifest;
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const loopFade = MOTION.frames.loopFade;
  let cursor = 0;

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
              {beat.scene ? <SceneBackground tokens={tokens} scene={beat.scene} /> : null}
              <BeatStage
                durationInFrames={durationInFramesForBeat}
                index={beatIndex}
                opener={beatIndex === 0}
              >
                {beat.assets.map((asset, assetIndex) => {
                  const place = asset.isPublicFigure
                    ? DISTANT_PLACEMENT
                    : PLACEMENTS[(assetIndex + beatIndex) % PLACEMENTS.length];
                  const delay = Math.round(
                    (assetIndex / beat.assets.length) * durationInFramesForBeat * MOTION.frames.assetSpreadFraction
                  );
                  return (
                    <Cutout
                      key={asset.src}
                      src={staticFile(asset.src)}
                      delay={delay}
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
                  legibleOverPhoto
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

      <AnimatedBorder tokens={tokens} />
      <SeriesKicker text={manifest.seriesKicker} tokens={tokens} top={3} />
      <Signature tokens={tokens} bottom={7} left={7} legibleOverPhoto />
    </AbsoluteFill>
  );
};
