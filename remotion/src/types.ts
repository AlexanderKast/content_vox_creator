export type BrandTokens = {
  handle: string;
  displayFont: string;
  quoteFont: string;
  colors: Record<string, string>;
  dominant: string;
  aesthetic: string;
  grain: number;
  voiceId: string | null;
  characterRef: string | null;
};

export type BeatSfx = {
  src: string;
  frame: number;
};

export type WordTiming = {
  word: string;
  startFrame: number;
  endFrame: number;
};

export type Beat = {
  index: number;
  text: string;
  // Carrusel: short subtitle under the title, a small black top kicker label,
  // and an optional orange sticker badge callout. Empty on video beats.
  subtitle: string;
  kicker: string;
  badge: string;
  // Giant colored stat number ("7 PAÍSES", "18,078 KM"). Empty = none.
  stat: string;
  // CTA search-bar mockup: the word to type out. Empty = no search bar.
  search: string;
  // Full-frame themed scene background for this beat, or null → cream paper.
  scene: string | null;
  narration: string;
  seconds: number;
  assets: string[];
  // One entry per SFX cue this beat triggers (cutout entrance -> pop, beat
  // cut -> whoosh, underline draw -> marker, remate/key-number -> impact).
  sfx: BeatSfx[];
  // Global (whole-timeline) frame this beat's Sequence starts at — lets a
  // component inside the Sequence convert wordTimings (also global frames)
  // back to its own local useCurrentFrame() space.
  sequenceFrom: number;
  // Real per-word landing frames from factory.align, or null when alignment
  // didn't produce a full match for this beat's caption — components must
  // fall back to the estimated word-by-word reveal in that case.
  wordTimings: WordTiming[] | null;
  // CARRUSEL only: this slide's own voice clip. VIDEO uses Manifest.voice
  // (one continuous track) instead.
  voice: string | null;
};

export type Manifest = {
  jobId: string;
  mode: "video" | "carrusel";
  brand: string;
  tokens: BrandTokens;
  width: number;
  height: number;
  fps: number;
  hook: string;
  cta: string;
  voice: string | null;
  // Background music bed (video mode). Played under the voice at low volume.
  music: string | null;
  beats: Beat[];
  // Mode VIDEO only. When true, BoxVideo fades its foreground to bare
  // Background at both ends so the wrap-around cut is invisible.
  loop: boolean;
  // Persistent series tag shown at the top of every frame ("100% AUTOMATIZADO").
  seriesKicker: string;
  spendUsd: number;
};
