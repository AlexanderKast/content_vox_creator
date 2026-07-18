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

export type Beat = {
  index: number;
  text: string;
  narration: string;
  seconds: number;
  assets: string[];
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
  beats: Beat[];
  spendUsd: number;
};
