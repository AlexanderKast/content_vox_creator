"""Cost model and dry-run estimator.

The reference system generates first and finds out the bill later. We refuse to
spend before we know the number. Every paid call is priced here.

Prices verified 2026-07-16. They move — re-check before trusting a big batch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# USD per single image, by provider/model slug.
IMAGE_PRICES: dict[str, float] = {
    # Cheap tier — cutouts. A green-screen sticker is a drawing, not a photograph.
    "wavespeed/z-image": 0.005,
    "wavespeed/flux-klein": 0.010,
    "runware/flux-1-schnell": 0.0013,
    # Mid tier — complex scenes where prompt adherence actually matters.
    "wavespeed/nano-banana-2-fast": 0.045,
    "wavespeed/nano-banana-pro": 0.070,
    "kie/nano-banana-pro": 0.090,
    "fal/seedream-v4.5": 0.030,
    # Character tier — we pay for consistency, not for pixels.
    "magnific/character": 0.080,
}

# USD per real photo scraped from the web.
PHOTO_PRICE_PER_IMAGE: float = 0.0029

# USD per 1M characters of synthesized speech.
VOICE_PRICES: dict[str, float] = {
    "elevenlabs/multilingual-v2": 120.0,
    "elevenlabs/flash-v2.5": 60.0,
}

# USD per generated music track (flat approximation).
MUSIC_PRICE: float = 0.02


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


def voice_price(model: str, characters: int) -> float:
    if model not in VOICE_PRICES:
        raise KeyError(f"Unpriced voice model: {model}. Add it to VOICE_PRICES first.")
    return round(VOICE_PRICES[model] * characters / 1_000_000, 4)


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
