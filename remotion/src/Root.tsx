import React from "react";
import { Composition, getInputProps } from "remotion";
import { BoxVideo } from "./compositions/BoxVideo";
import { CarouselSlide } from "./compositions/CarouselSlide";
import { useDisplayFont } from "./fonts";
import type { Manifest } from "./types";

/**
 * Compositions are driven entirely by the manifest the Python side produces.
 * brand.json is the single source of visual truth — nothing is hardcoded here.
 *
 * Render:
 *   npx remotion render BoxVideo out/video.mp4 --props=../out/<job>.manifest.json
 *   npx remotion render CarouselSlide out/slide-01.mp4 --props=../out/<job>.manifest.json
 */

const FALLBACK: Manifest = {
  jobId: "preview",
  mode: "video",
  brand: "alexander",
  tokens: {
    handle: "@alexemprendee",
    displayFont: "Archivo",
    quoteFont: "Playfair Display",
    colors: {
      black: "#050505",
      gold: "#D4AF37",
      yellow: "#FFD400",
      paper: "#12100C",
      white: "#F5F1E8",
    },
    dominant: "gold",
    aesthetic: "dark luxury",
    grain: 0.14,
    voiceId: null,
    characterRef: null,
  },
  width: 1080,
  height: 1920,
  fps: 30,
  hook: "Preview",
  cta: "",
  voice: null,
  music: null,
  beats: [
    {
      index: 1, text: "SIN MANIFEST CARGADO", subtitle: "", kicker: "", badge: "", stat: "", search: "", scene: null,
      voice: null, seconds: 3, assets: [], sfx: [], sequenceFrom: 0, wordTimings: null,
    },
  ],
  loop: false,
  seriesKicker: "",
  spendUsd: 0,
};

export const RemotionRoot: React.FC = () => {
  const props = getInputProps() as Partial<Manifest> & { slideIndex?: number };
  const manifest: Manifest = { ...FALLBACK, ...props } as Manifest;
  useDisplayFont(manifest.tokens.displayFont);

  const totalFrames = Math.max(
    1,
    Math.round(manifest.beats.reduce((sum, b) => sum + b.seconds, 0) * manifest.fps)
  );

  const slideIndex = props.slideIndex ?? 0;
  const slideBeat = manifest.beats[slideIndex];
  const slideFrames = Math.max(1, Math.round((slideBeat?.seconds ?? 5) * manifest.fps));

  return (
    <>
      <Composition
        id="BoxVideo"
        component={BoxVideo}
        durationInFrames={totalFrames}
        fps={manifest.fps}
        width={1080}
        height={1920}
        defaultProps={{ manifest }}
      />
      <Composition
        id="CarouselSlide"
        component={CarouselSlide}
        durationInFrames={slideFrames}
        fps={manifest.fps}
        width={1080}
        height={1350}
        defaultProps={{ manifest, slideIndex }}
      />
    </>
  );
};
