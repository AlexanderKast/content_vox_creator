/**
 * THE DESIGN SYSTEM. One locked set of tokens every component reads from, so
 * the whole video reads as one studio's work instead of per-file guesses.
 *
 * brand.json still owns the palette (per-brand colors). This file owns
 * everything else — the type scale, the spacing grid, the motion language,
 * elevation, and the color ROLES derived from the palette. Nothing visual
 * should be a magic number in a component; it should be a token here.
 */

import type { BrandTokens } from "./types";

// ---------------------------------------------------------------------------
// Color: hex helper + semantic roles derived from the brand palette.
// ---------------------------------------------------------------------------

export function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export type ColorRoles = {
  surface: string; // the background base
  ink: string; // primary text
  accent: string; // primary highlight (numbers, key words, underline)
  accent2: string; // secondary highlight (some stats/remates — green in this brand)
  accentSoft: (a: number) => string; // accent at an alpha, for glows/washes
};

export function roles(tokens: BrandTokens): ColorRoles {
  const accent = tokens.colors[tokens.dominant] ?? tokens.colors.gold ?? "#D4AF37";
  return {
    surface: tokens.colors.paper ?? "#2e2318",
    // Primary text. On a light (cream) surface this is a dark ink; on a dark
    // surface it's near-white. Brands set `ink` explicitly; fall back to white
    // for older dark-only brands.
    ink: tokens.colors.ink ?? tokens.colors.white ?? "#F5F1E8",
    accent,
    accent2: tokens.colors.green ?? accent,
    accentSoft: (a: number) => hexToRgba(accent, a),
  };
}

// ---------------------------------------------------------------------------
// Motion language. Named spring presets + standard frame counts. Every
// animation in the project picks a NAMED motion, never an ad-hoc spring.
// ---------------------------------------------------------------------------

export const MOTION = {
  spring: {
    slam: { damping: 9, mass: 0.5, stiffness: 240 }, // hook drop / opener
    snap: { damping: 14, mass: 0.4, stiffness: 210 }, // standard entrance
    word: { damping: 12, mass: 0.4, stiffness: 220 }, // a word landing
    wordImpact: { damping: 10, mass: 0.5, stiffness: 260 }, // hook word slam
    settle: { damping: 16, mass: 0.5, stiffness: 130 }, // exit / soft hand-off
    sticker: { damping: 11, mass: 0.6, stiffness: 180 }, // cutout bounce-in
  },
  frames: {
    exit: 10, // beat hand-off window
    shake: 9, // opener screen-shake decay
    underline: 12, // underline draw
    loopFade: 6, // seamless-loop foreground breath
    assetStagger: 4, // cutouts entering one after another
  },
  // Ambient continuous motion (drift/float), in scene units.
  ambient: {
    driftPct: -20, // cutout slow upward drift over a beat
    floatPx: 6, // cutout bob amplitude
    swayDeg: 1.2, // cutout tilt amplitude
    kenBurnsZoom: 0.05, // per-beat push-in
    textFloatPx: 2.5, // settled subtitle float
  },
} as const;

// ---------------------------------------------------------------------------
// Type scale. Roles, not raw pixels, at the call sites.
// ---------------------------------------------------------------------------

export const TYPE = {
  weight: { black: 900, bold: 700, medium: 600 },
  tracking: "-0.02em",
  lineHeight: 1.0, // per-word box height (real fontSize does the sizing)
  rowGapEm: 0.26, // vertical gap between wrapped lines — stops line collisions
  emphasisScale: 1.18, // numbers + long/key words come in bigger (real fontSize)
  deemphasisScale: 0.9, // connectors step back — subtle, not a size jump
  // On-screen display sizes by role (px at 1080-wide comp).
  size: {
    hook: 120, // the opener — biggest
    headline: 104, // standard video beat text
    slide: 78, // carrusel slide text
    counter: 40, // slide counter
  },
} as const;

// ---------------------------------------------------------------------------
// Spacing grid (8px base) + safe areas.
// ---------------------------------------------------------------------------

const UNIT = 8;
export const SPACE = {
  unit: UNIT,
  s: UNIT, // 8
  m: UNIT * 2, // 16
  l: UNIT * 3, // 24
  xl: UNIT * 5, // 40
} as const;

export const SAFE = {
  // Carrusel: Instagram covers ~80px top / 200px bottom / ~40px sides.
  carousel: { top: 90, bottom: 210, side: 50 },
  // Video text sits above TikTok/Reels bottom UI.
  videoTextBottomPct: 18,
} as const;

// ---------------------------------------------------------------------------
// Elevation — one shadow vocabulary.
// ---------------------------------------------------------------------------

export const ELEVATION = {
  sticker: "drop-shadow(0 24px 48px rgba(0,0,0,0.45))",
  glowText: (accent: string) => `0 4px 22px ${hexToRgba(accent, 0.33)}`,
} as const;

// ---------------------------------------------------------------------------
// Layout: deterministic cutout scatter. More slots + spread so a beat can
// carry several images without stacking, and never the same layout twice.
// ---------------------------------------------------------------------------

export const PLACEMENTS = [
  { x: 0, y: -14, scale: 1.0, rotate: -3 },
  { x: -22, y: -24, scale: 0.66, rotate: 6 },
  { x: 24, y: -6, scale: 0.6, rotate: -7 },
  { x: -18, y: 16, scale: 0.54, rotate: 4 },
  { x: 26, y: 20, scale: 0.5, rotate: -5 },
  { x: 4, y: 24, scale: 0.58, rotate: 8 },
] as const;

// Ken Burns pan directions (px), one per beat, cycled.
export const KEN_BURNS = [
  { x: -26, y: 10 },
  { x: 22, y: -12 },
  { x: -18, y: -16 },
  { x: 24, y: 14 },
  { x: 12, y: 20 },
  { x: -22, y: -8 },
] as const;
