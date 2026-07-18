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
    // Lower damping than the old 11 -> a visibly bouncier overshoot on entry
    // (2026-07-18: "mas efectos a los objetos que aparecen" — the pop-in
    // read as too flat/quick to register as a deliberate spring).
    sticker: { damping: 8, mass: 0.6, stiffness: 180 }, // cutout bounce-in
  },
  frames: {
    exit: 10, // beat hand-off window
    shake: 9, // opener screen-shake decay
    underline: 12, // underline draw
    loopFade: 6, // seamless-loop foreground breath
    assetStagger: 4, // cutouts entering one after another
  },
  // Ambient continuous motion (drift/float), in scene units. floatPx/swayDeg
  // bumped 2026-07-18 (6->10, 1.2->2.5) — the cutout bob/tilt read as nearly
  // static at the old amplitude. scalePulse is new: a slow breathing scale
  // so a cutout never looks like a frozen sticker even mid-beat, only on
  // objects (Cutout — a public figure does NOT get this, see Cutout.tsx).
  ambient: {
    driftPct: -20, // cutout slow upward drift over a beat
    floatPx: 10, // cutout bob amplitude
    swayDeg: 2.5, // cutout tilt amplitude
    scalePulse: 0.05, // cutout slow breathing scale amplitude
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
  // Vertical gap between wrapped lines. 0.26 wasn't enough once a row holds
  // an emphasisScale (1.18x) word — the next row's box starts from the
  // container's base line-height, not the taller row's actual rendered
  // height, so a wrapped title with an emphasized word on one line would
  // collide with the line below it (verified 2026-07-18, "POSESION DEL 7" /
  // "DE AGOSTO"). 0.55 clears that case with real fontSize headroom.
  rowGapEm: 0.55,
  emphasisScale: 1.18, // numbers + long/key words come in bigger (real fontSize)
  deemphasisScale: 0.9, // connectors step back — subtle, not a size jump
  // On-screen display sizes by role (px at 1080-wide comp).
  size: {
    hook: 120, // the opener — biggest
    headline: 104, // standard video beat text
    slide: 78, // carrusel slide text, SHORT titles only — see fitTitleSize
    counter: 40, // slide counter
  },
} as const;

// Carrusel titles are now ALWAYS a full sentence (2026-07-18 — the AIDA
// rewrite: `text` is the hook itself, not a 2-5 word label). TYPE.size.slide
// (78) was tuned for a short label; a full sentence at that size wraps to
// 3-4 lines and either collides with the subtitle/cutout below it or runs
// off frame. Scale the title DOWN as the sentence gets longer instead of
// hardcoding one size for every length. Bucketed on word count (a proxy for
// line count at ~4-5 words/line at this weight), not character count — two
// short words wrap differently than one long compound word, but word count
// tracks perceived length well enough for a scale bucket, not pixel-perfect
// layout.
export function fitTitleSize(text: string, base: number = TYPE.size.slide): number {
  const words = text.trim().split(/\s+/).length;
  if (words <= 4) return base;
  if (words <= 7) return Math.round(base * 0.78);
  if (words <= 10) return Math.round(base * 0.62);
  return Math.round(base * 0.52);
}

// Carrusel header stack (2026-07-18 — title moved from "hero over the image"
// to "header above it"): kicker, title, subtitle all top-anchored now, in
// that order. subtitleTop has to clear however many lines the title wraps
// to — same word-count buckets as fitTitleSize (smaller font at higher word
// counts still wraps to more lines, so the buckets track independently, not
// proportionally). Single source of truth so CarouselSlide never hand-picks
// a top offset that goes stale the next time a title gets longer.
export function headerLayout(text: string, hasKicker: boolean): {
  size: number;
  titleTop: number;
  subtitleTop: number;
} {
  const words = text.trim().split(/\s+/).length;
  const titleTop = hasKicker ? 20 : 13;
  const estLines = words <= 4 ? 1 : words <= 10 ? 2 : 3;
  return {
    size: fitTitleSize(text),
    titleTop,
    subtitleTop: titleTop + estLines * 10 + 6,
  };
}

// ---------------------------------------------------------------------------
// Safe areas.
// ---------------------------------------------------------------------------

export const SAFE = {
  // Carrusel: Instagram covers ~80px top / 200px bottom / ~40px sides.
  carousel: { top: 90, bottom: 210, side: 50 },
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

// A real public figure (content-vox-news, BeatAsset.isPublicFigure) never
// gets a close-up — smallest scale of the set, centered, no PLACEMENTS
// rotation. The eyes are already black-barred by factory.redact before the
// image ever reaches Remotion; this keeps the figure small on top of that,
// never the dominant element of the frame.
export const DISTANT_PLACEMENT = { x: 0, y: 10, scale: 0.4, rotate: 0 } as const;

// Ken Burns pan directions (px), one per beat, cycled.
export const KEN_BURNS = [
  { x: -26, y: 10 },
  { x: 22, y: -12 },
  { x: -18, y: -16 },
  { x: 24, y: 14 },
  { x: 12, y: 20 },
  { x: -22, y: -8 },
] as const;
