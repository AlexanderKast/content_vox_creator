"""Cost model and dry-run estimator.

The reference system generates first and finds out the bill later. We refuse to
spend before we know the number. Every paid call is priced here.

Prices verified 2026-07-16 against each provider's public pricing docs. They
move, and some (voice) vary by subscription tier — re-check before trusting a
big batch.

wavespeed/flux-2-klein-4b and wavespeed/nano-banana-pro re-verified
2026-07-17 (live WaveSpeed docs, see factory/providers/images_wavespeed.py
API_PATHS comment): the earlier "wavespeed/flux-klein" slug at $0.010 didn't
correspond to a real text-to-image endpoint (Flux Klein's plain "klein"
variants are edit-only; the real cheap-tier model is the 4B text-to-image
variant at $0.008), and "wavespeed/nano-banana-pro" was priced at $0.070 when
the real price is $0.14 — a different model line from Nano Banana 2 (Gemini
3.0 Pro Image vs. 2.5 Flash Image), not just a "pro" flag on the same model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# USD per single image, by provider/model slug.
IMAGE_PRICES: dict[str, float] = {
    # Cheap tier — cutouts. A green-screen sticker is a drawing, not a photograph.
    "wavespeed/z-image": 0.005,
    "wavespeed/flux-2-klein-4b": 0.008,
    "runware/flux-1-schnell": 0.0013,
    # Mid tier — complex scenes where prompt adherence actually matters.
    "wavespeed/nano-banana-2-fast": 0.045,
    "wavespeed/nano-banana-pro": 0.140,
    "kie/nano-banana-pro": 0.090,
    "fal/seedream-v4.5": 0.030,
    # Character tier — we pay for consistency, not for pixels.
    # UNVERIFIED, unlike every other line in this table: Magnific's real API
    # (see factory/providers/character_magnific.py) is credit-based against a
    # subscription plan (Premium/Premium+/Pro), and the credits-per-image
    # cost scales with resolution/model — there's no published flat USD/image
    # figure to check this $0.080 against. It's the pre-existing placeholder
    # from before this tier had a real provider. Check your actual credit
    # balance after a real batch before trusting this number.
    "magnific/character": 0.080,
}

# Apify's google-images-scraper is billed Pay-Per-Event, not a flat rate per
# photo: a run-started fee, a per-image fee (tiered by Apify account tier —
# this is the FREE-tier rate), and a per-SERP-page fee that stays flat across
# every tier. A single asset search is one run, so all three fire together.
APIFY_RUN_STARTED_PRICE: float = 0.005
APIFY_IMAGE_SCRAPED_PRICE: float = 0.0023
APIFY_SERP_PAGE_PRICE: float = 0.05
APIFY_RESULTS_PER_QUERY: int = 3  # keep in sync with providers/photos_apify.py limit

# USD per 1M characters of synthesized speech (official list price; the
# account's actual per-character rate depends on its subscription tier —
# confirm on the ElevenLabs dashboard before trusting a large batch).
VOICE_PRICES: dict[str, float] = {
    "elevenlabs/multilingual-v2": 100.0,
    "elevenlabs/flash-v2.5": 50.0,
}

# USD per minute of generated audio.
MUSIC_PRICE_PER_MINUTE: float = 0.15
SFX_PRICE_PER_MINUTE: float = 0.12

# USD per 1M tokens (input, output), by text-LLM model slug. Opt-in only —
# see factory.config.use_llm_copy and factory/providers/text_llm.py. Verified
# 2026-07-17 against https://mistral.ai/pricing/.
TEXT_LLM_PRICES: dict[str, tuple[float, float]] = {
    "mistral/mistral-small-latest": (0.10, 0.30),
}

# Hooks/caption calls are short; token counts aren't known before the call,
# so — same pattern as SFX/music fixed durations — use a conservative fixed
# budget that keeps the estimate and the actual charge in agreement.
HOOKS_LLM_ESTIMATED_TOKENS = (300, 300)      # (input, output)
CAPTION_LLM_ESTIMATED_TOKENS = (250, 250)    # (input, output)


def text_llm_price(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in TEXT_LLM_PRICES:
        raise KeyError(f"Unpriced text-LLM model: {model}. Add it to TEXT_LLM_PRICES first.")
    input_price, output_price = TEXT_LLM_PRICES[model]
    return round(input_price * input_tokens / 1_000_000 + output_price * output_tokens / 1_000_000, 6)


@dataclass
class CostLine:
    label: str
    unit_price: float
    quantity: float
    subtotal: float


@dataclass
class Estimate:
    lines: list[CostLine] = field(default_factory=list)

    def add(self, label: str, unit_price: float, quantity: float) -> None:
        self.lines.append(
            CostLine(
                label=label,
                unit_price=unit_price,
                quantity=quantity,
                subtotal=round(unit_price * quantity, 4),
            )
        )

    @property
    def total(self) -> float:
        return round(sum(line.subtotal for line in self.lines), 4)

    def render(self) -> str:
        if not self.lines:
            return "No paid calls planned."
        width = max(len(line.label) for line in self.lines)
        rows = [
            f"  {line.label.ljust(width)}  {line.quantity:>6.0f} x ${line.unit_price:<8.4f} = ${line.subtotal:.4f}"
            for line in self.lines
        ]
        rows.append(f"  {'TOTAL'.ljust(width)}  {'':>6}   {'':<9}   ${self.total:.4f}")
        return "\n".join(rows)


def image_price(model: str) -> float:
    if model not in IMAGE_PRICES:
        raise KeyError(f"Unpriced image model: {model}. Add it to IMAGE_PRICES first.")
    return IMAGE_PRICES[model]


def photo_price(results_per_query: int = APIFY_RESULTS_PER_QUERY, pages: int = 1) -> float:
    """All-in cost of one Apify google-images-scraper run: not per photo used,
    per search performed — the run fee and page fee fire whether or not the
    caller ends up downloading every scraped result."""
    return round(
        APIFY_RUN_STARTED_PRICE
        + APIFY_IMAGE_SCRAPED_PRICE * results_per_query
        + APIFY_SERP_PAGE_PRICE * pages,
        4,
    )


def voice_price(model: str, characters: int) -> float:
    if model not in VOICE_PRICES:
        raise KeyError(f"Unpriced voice model: {model}. Add it to VOICE_PRICES first.")
    return round(VOICE_PRICES[model] * characters / 1_000_000, 4)


def music_price(duration_ms: int) -> float:
    return round(MUSIC_PRICE_PER_MINUTE * duration_ms / 60_000, 4)


def sfx_price(duration_seconds: float) -> float:
    return round(SFX_PRICE_PER_MINUTE * duration_seconds / 60, 4)


class BudgetExceeded(RuntimeError):
    """Raised before spending, never after."""


def enforce_budget(estimate: Estimate, ceiling_usd: float) -> None:
    """Hard stop. A pipeline that silently overspends is a bug, not a feature."""
    if estimate.total > ceiling_usd:
        raise BudgetExceeded(
            f"Estimated ${estimate.total:.4f} exceeds ceiling ${ceiling_usd:.2f}.\n"
            f"{estimate.render()}\n"
            "Either raise MAX_SPEND_PER_RUN_USD or fix the plan. "
            "Most overruns are a premium model doing cheap-model work."
        )
