"""The learning loop — measure what got published, adjust what gets made next.

Read-only against Metricool, always. This module never publishes, schedules,
or deletes anything; `ingest_performance` only ever writes to the local
`performance` table. Whatever fetches the actual numbers from Metricool
(a Claude Code session with the Metricool MCP connector, or later a
standalone API-key-based provider once one exists) hands them to
`ingest_performance` as a plain dict — this module doesn't care how the
numbers arrived, only that it never invents one that's missing.

Every number that isn't in the raw Metricool payload stays None end to end
and is reported as "no disponible", never silently dropped or defaulted to
0 — a fabricated metric is worse than an admitted gap.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from . import config

# Which pillar each formula belongs to, for the 70/30 mix check. F5 (SERIE)
# is scored by whichever formula runs inside it — the caller resolves that
# before calling mix_health (see PILLAR_MAP usage below); F3 pieces are
# filmed by Alexander, not built by this factory, and still count here.
PILLAR_MAP: dict[str, str] = {
    "F1": "tutorial-valor",
    "F2": "tutorial-valor",
    "F4": "tutorial-valor",
    "F3": "personalidad-opinion",
}

TARGET_TUTORIAL_PCT = 70.0
MIX_WARNING_TOLERANCE_PCT = 15.0  # how far off 70/30 triggers a warning

WINNER_MULTIPLIER = 3.0
WINNER_MIN_WEEKS = 3.0
WINNER_MAX_WEEKS = 4.0

MIN_PIECES_FOR_FORMULA_SIGNAL = 20


# Real Metricool field names (verified live against the Instagram "reels"
# connector 2026-07-17: getAnalyticsAvailableMetrics(network="instagram",
# connector="reels") — "saved", not "saves"; "retention" exists for reels
# ("average percentage of video viewed") but NOT for the generic "posts"
# connector, so it will be legitimately absent for non-Reel content.
METRIC_FIELDS = ("reach", "retention", "comments", "saved", "shares", "likes")


@dataclass(frozen=True)
class PerformanceRow:
    id: int
    job_id: str | None
    formula: str | None
    published_url: str
    published_at: float
    fetched_at: float
    reach: float | None
    retention: float | None
    comments: float | None
    saved: float | None
    shares: float | None
    likes: float | None

    @property
    def comments_to_likes_ratio(self) -> float | None:
        if not self.likes:
            return None
        if self.comments is None:
            return None
        return round(self.comments / self.likes, 4)

    @property
    def weeks_since_published(self) -> float:
        return (time.time() - self.published_at) / (7 * 24 * 3600)


def ingest_performance(
    conn: sqlite3.Connection,
    *,
    published_url: str,
    published_at: float,
    metrics: dict,
    job_id: str | None = None,
    formula: str | None = None,
) -> None:
    """Store one Metricool pull. `metrics` should carry whatever subset of
    METRIC_FIELDS Metricool actually returned — missing keys become NULL,
    never 0, never an assumption."""
    if job_id is not None and formula is None:
        row = conn.execute("SELECT formula FROM jobs WHERE id = ?", (job_id,)).fetchone()
        formula = row["formula"] if row else None
        conn.execute(
            "UPDATE jobs SET published_url = ?, published_at = ? WHERE id = ?",
            (published_url, published_at, job_id),
        )

    conn.execute(
        """
        INSERT INTO performance
            (job_id, formula, published_url, published_at, fetched_at,
             reach, retention, comments, saved, shares, likes, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id, formula, published_url, published_at, time.time(),
            metrics.get("reach"), metrics.get("retention"), metrics.get("comments"),
            metrics.get("saved"), metrics.get("shares"), metrics.get("likes"),
            json.dumps(metrics, ensure_ascii=False),
        ),
    )
    conn.commit()


def _rows(conn: sqlite3.Connection, since: float | None = None) -> list[PerformanceRow]:
    query = "SELECT * FROM performance"
    params: tuple = ()
    if since is not None:
        query += " WHERE published_at >= ?"
        params = (since,)
    query += " ORDER BY published_at DESC"
    return [
        PerformanceRow(
            id=r["id"], job_id=r["job_id"], formula=r["formula"],
            published_url=r["published_url"], published_at=r["published_at"],
            fetched_at=r["fetched_at"], reach=r["reach"], retention=r["retention"],
            comments=r["comments"], saved=r["saved"], shares=r["shares"], likes=r["likes"],
        )
        for r in conn.execute(query, params)
    ]


def detect_winners(
    conn: sqlite3.Connection,
    *,
    multiplier: float = WINNER_MULTIPLIER,
    min_weeks: float = WINNER_MIN_WEEKS,
    max_weeks: float = WINNER_MAX_WEEKS,
) -> list[dict]:
    """Pieces that beat `multiplier`x the account's average reach, listing
    whether they've cleared the 3-4 week re-render window yet. The baseline
    for each piece is the average of every OTHER piece (leave-one-out) —
    folding a piece into its own baseline understates how much it
    over-performed, and for small accounts can make the threshold
    mathematically unreachable. Needs at least 2 pieces with a reach number."""
    rows = [r for r in _rows(conn) if r.reach is not None]
    if len(rows) < 2:
        return []

    total_reach = sum(r.reach for r in rows)
    n = len(rows)

    winners = []
    for row in rows:
        others_average = (total_reach - row.reach) / (n - 1)
        if others_average <= 0:
            continue
        piece_multiplier = row.reach / others_average
        if piece_multiplier < multiplier:
            continue
        weeks = row.weeks_since_published
        hooks_path = (
            config.OUT_DIR / f"{row.job_id}.hooks.md" if row.job_id else None
        )
        winners.append({
            "job_id": row.job_id,
            "published_url": row.published_url,
            "formula": row.formula,
            "reach": row.reach,
            "account_average_reach": round(others_average, 2),
            "multiplier": round(piece_multiplier, 2),
            "weeks_since_published": round(weeks, 1),
            "ready_to_rerender": min_weeks <= weeks <= max_weeks,
            "hooks_file": str(hooks_path) if hooks_path and hooks_path.exists() else None,
        })
    return winners


def mix_health(conn: sqlite3.Connection, *, days: int = 30) -> dict:
    """70/30 tutorial-valor / personalidad-opinion split over the last N
    days. Pieces whose formula isn't in PILLAR_MAP (no formula recorded, or
    F5 without a resolved inner formula) are counted separately and never
    silently folded into either pillar."""
    since = time.time() - days * 24 * 3600
    rows = _rows(conn, since=since)

    tutorial = sum(1 for r in rows if r.formula and PILLAR_MAP.get(r.formula) == "tutorial-valor")
    opinion = sum(1 for r in rows if r.formula and PILLAR_MAP.get(r.formula) == "personalidad-opinion")
    unclassified = len(rows) - tutorial - opinion
    classified_total = tutorial + opinion

    if classified_total == 0:
        return {
            "days": days, "total_pieces": len(rows), "classified_total": 0,
            "tutorial_pct": None, "opinion_pct": None, "unclassified": unclassified,
            "warning": None if len(rows) == 0 else (
                "Ninguna pieza publicada en los ultimos "
                f"{days} dias tiene formula clasificable — no se puede evaluar la mezcla."
            ),
        }

    tutorial_pct = round(100 * tutorial / classified_total, 1)
    opinion_pct = round(100 * opinion / classified_total, 1)
    off_target = abs(tutorial_pct - TARGET_TUTORIAL_PCT)
    warning = None
    if off_target > MIX_WARNING_TOLERANCE_PCT:
        skew = "tutorial" if tutorial_pct > TARGET_TUTORIAL_PCT else "opinion/personalidad"
        warning = (
            f"Mezcla desbalanceada hacia {skew}: {tutorial_pct}% tutorial-valor vs "
            f"{opinion_pct}% personalidad-opinion (objetivo ~70/30). Los mayores virales "
            "de los referentes fueron de emocion/opinion — si esto se va a 100% tutorial, "
            "el alcance cae aunque la conversion se vea bien."
        )

    return {
        "days": days, "total_pieces": len(rows), "classified_total": classified_total,
        "tutorial_pct": tutorial_pct, "opinion_pct": opinion_pct,
        "unclassified": unclassified, "warning": warning,
    }


def formula_correlation(conn: sqlite3.Connection) -> dict:
    """Average reach and comments/likes ratio per formula. Only trustworthy
    with real volume — below MIN_PIECES_FOR_FORMULA_SIGNAL total published
    pieces this is noise, not signal, and the report must say so instead of
    presenting numbers as if they meant something yet."""
    rows = _rows(conn)
    reliable = len(rows) >= MIN_PIECES_FOR_FORMULA_SIGNAL

    by_formula: dict[str, list[PerformanceRow]] = {}
    for row in rows:
        if row.formula:
            by_formula.setdefault(row.formula, []).append(row)

    stats = {}
    for formula, formula_rows in by_formula.items():
        reaches = [r.reach for r in formula_rows if r.reach is not None]
        ratios = [r.comments_to_likes_ratio for r in formula_rows if r.comments_to_likes_ratio is not None]
        stats[formula] = {
            "count": len(formula_rows),
            "avg_reach": round(sum(reaches) / len(reaches), 2) if reaches else None,
            "avg_comments_to_likes_ratio": round(sum(ratios) / len(ratios), 4) if ratios else None,
        }

    return {
        "total_pieces": len(rows),
        "reliable": reliable,
        "min_pieces_required": MIN_PIECES_FOR_FORMULA_SIGNAL,
        "by_formula": stats,
    }


def build_report(conn: sqlite3.Connection) -> str:
    rows = _rows(conn)
    winners = detect_winners(conn)
    mix = mix_health(conn)
    correlation = formula_correlation(conn)

    lines = ["# Reporte de rendimiento", ""]

    lines.append(f"## Publicado ({len(rows)} piezas con metricas)")
    if not rows:
        lines.append("Sin piezas publicadas registradas todavia.")
    else:
        for row in rows[:20]:
            reach_str = f"{row.reach:,.0f}" if row.reach is not None else "no disponible"
            ratio = row.comments_to_likes_ratio
            ratio_str = f"{ratio:.3f}" if ratio is not None else "no disponible"
            lines.append(
                f"- {row.published_url} — formula {row.formula or 'sin clasificar'} — "
                f"alcance {reach_str} — ratio comentarios/likes {ratio_str}"
            )
        if len(rows) > 20:
            lines.append(f"- ... y {len(rows) - 20} mas.")
    lines.append("")

    lines.append(f"## Ganadores (>= {WINNER_MULTIPLIER}x el promedio de la cuenta)")
    if not winners:
        lines.append("Ninguno todavia, o faltan datos suficientes para calcular un promedio.")
    else:
        for w in winners:
            status = "LISTO PARA RE-RENDER" if w["ready_to_rerender"] else f"esperar (semana {w['weeks_since_published']})"
            hook_note = f" — hooks en {w['hooks_file']}" if w["hooks_file"] else " — sin hooks.md guardado"
            lines.append(
                f"- {w['published_url']} — {w['multiplier']}x el promedio "
                f"({w['reach']:,.0f} vs {w['account_average_reach']:,.0f}) — {status}{hook_note}"
            )
    lines.append("")

    lines.append("## Que formula gana")
    if not correlation["by_formula"]:
        lines.append("Sin piezas con formula clasificada todavia.")
    else:
        if not correlation["reliable"]:
            lines.append(
                f"**Advertencia**: solo {correlation['total_pieces']} piezas publicadas — "
                f"menos de {correlation['min_pieces_required']}. Cualquier diferencia entre "
                "formulas aqui es ruido, no una senal confiable todavia."
            )
        for formula, stats in sorted(correlation["by_formula"].items()):
            reach_str = f"{stats['avg_reach']:,.0f}" if stats["avg_reach"] is not None else "no disponible"
            ratio_str = (
                f"{stats['avg_comments_to_likes_ratio']:.3f}"
                if stats["avg_comments_to_likes_ratio"] is not None else "no disponible"
            )
            lines.append(
                f"- {formula}: {stats['count']} pieza(s) — alcance promedio {reach_str} — "
                f"ratio comentarios/likes promedio {ratio_str}"
            )
    lines.append("")

    lines.append(f"## Mezcla 70/30 (ultimos {mix['days']} dias)")
    if mix["classified_total"] == 0:
        lines.append(mix["warning"] or "Sin piezas clasificables en el periodo.")
    else:
        lines.append(
            f"{mix['tutorial_pct']}% tutorial-valor / {mix['opinion_pct']}% personalidad-opinion "
            f"({mix['classified_total']} piezas clasificadas"
            + (f", {mix['unclassified']} sin clasificar)" if mix["unclassified"] else ")")
        )
        if mix["warning"]:
            lines.append(f"**Advertencia**: {mix['warning']}")
        else:
            lines.append("Mezcla saludable, dentro de rango.")

    return "\n".join(lines) + "\n"
