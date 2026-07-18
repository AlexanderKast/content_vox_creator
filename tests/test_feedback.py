"""Unit tests for factory.feedback and the performance/jobs schema. In-memory
SQLite only, no Metricool call — this tests the local logic, not the fetch.

Run with:
    python -m unittest tests.test_feedback
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory import db, feedback  # noqa: E402

WEEK = 7 * 24 * 3600


def _connect():
    return db.connect(":memory:")


class SchemaMigrationTest(unittest.TestCase):
    def test_jobs_table_has_new_columns(self):
        conn = _connect()
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
        self.assertIn("formula", columns)
        self.assertIn("published_url", columns)
        self.assertIn("published_at", columns)

    def test_create_job_stores_formula(self):
        conn = _connect()
        db.create_job(conn, "job-1", "video", "alexander", "topic", formula="F1")
        row = conn.execute("SELECT formula FROM jobs WHERE id = ?", ("job-1",)).fetchone()
        self.assertEqual(row["formula"], "F1")

    def test_retrying_a_job_does_not_wipe_accumulated_spend(self):
        # Real bug, found on the first live build: a mid-build failure (bad
        # key, transient 400) means re-running the same job_id — the assets
        # already paid for stay cached, but the old INSERT OR REPLACE reset
        # spend_usd to 0 on the retry, silently under-reporting real spend.
        conn = _connect()
        db.create_job(conn, "job-1", "video", "alexander", "topic")
        db.record_asset(conn, "hash-1", "job-1", "cutout", "wavespeed/flux-2-klein-4b", "/tmp/a.png", 0.008)
        db.record_asset(conn, "hash-2", "job-1", "voice", "elevenlabs/multilingual-v2", "/tmp/v.mp3", 0.08)

        db.create_job(conn, "job-1", "video", "alexander", "topic")  # simulated retry

        self.assertAlmostEqual(db.job_spend(conn, "job-1"), 0.088, places=4)


class IngestTest(unittest.TestCase):
    def test_ingest_inherits_formula_from_job_when_not_given(self):
        conn = _connect()
        db.create_job(conn, "job-1", "video", "alexander", "topic", formula="F2")
        feedback.ingest_performance(
            conn, published_url="https://instagram.com/p/x", published_at=time.time(),
            metrics={"reach": 1000, "likes": 50, "comments": 5}, job_id="job-1",
        )
        row = conn.execute("SELECT formula FROM performance WHERE job_id = ?", ("job-1",)).fetchone()
        self.assertEqual(row["formula"], "F2")

    def test_missing_metric_stays_null_not_zero(self):
        conn = _connect()
        feedback.ingest_performance(
            conn, published_url="https://instagram.com/p/y", published_at=time.time(),
            metrics={"reach": 500}, formula="F3",
        )
        row = conn.execute("SELECT likes, comments FROM performance").fetchone()
        self.assertIsNone(row["likes"])
        self.assertIsNone(row["comments"])


class WinnersTest(unittest.TestCase):
    def _seed(self, conn, reach: float, weeks_ago: float, formula="F1"):
        feedback.ingest_performance(
            conn, published_url=f"https://instagram.com/p/{reach}",
            published_at=time.time() - weeks_ago * WEEK,
            metrics={"reach": reach, "likes": 100, "comments": 10}, formula=formula,
        )

    def test_flags_piece_at_3x_average_ready_to_rerender_in_window(self):
        conn = _connect()
        self._seed(conn, 1000, weeks_ago=1)
        self._seed(conn, 1100, weeks_ago=1)
        self._seed(conn, 6000, weeks_ago=3.5)  # ~3x the average of all three (~2700)

        winners = feedback.detect_winners(conn)
        self.assertEqual(len(winners), 1)
        self.assertTrue(winners[0]["ready_to_rerender"])

    def test_winner_outside_window_is_not_ready(self):
        conn = _connect()
        self._seed(conn, 1000, weeks_ago=1)
        self._seed(conn, 1000, weeks_ago=1)
        self._seed(conn, 10000, weeks_ago=1)  # winner, but too fresh (1 week < 3-4)

        winners = feedback.detect_winners(conn)
        self.assertEqual(len(winners), 1)
        self.assertFalse(winners[0]["ready_to_rerender"])

    def test_insufficient_data_returns_empty(self):
        conn = _connect()
        self._seed(conn, 1000, weeks_ago=1)
        self.assertEqual(feedback.detect_winners(conn), [])


class MixHealthTest(unittest.TestCase):
    def _seed(self, conn, formula, n):
        for i in range(n):
            feedback.ingest_performance(
                conn, published_url=f"https://instagram.com/p/{formula}-{i}",
                published_at=time.time(), metrics={"reach": 1000}, formula=formula,
            )

    def test_balanced_70_30_has_no_warning(self):
        conn = _connect()
        self._seed(conn, "F1", 7)
        self._seed(conn, "F3", 3)
        health = feedback.mix_health(conn)
        self.assertEqual(health["tutorial_pct"], 70.0)
        self.assertIsNone(health["warning"])

    def test_all_tutorial_triggers_warning(self):
        conn = _connect()
        self._seed(conn, "F1", 10)
        health = feedback.mix_health(conn)
        self.assertEqual(health["tutorial_pct"], 100.0)
        self.assertIsNotNone(health["warning"])

    def test_no_pieces_in_window_has_no_crash(self):
        conn = _connect()
        health = feedback.mix_health(conn)
        self.assertEqual(health["total_pieces"], 0)
        self.assertIsNone(health["warning"])


class FormulaCorrelationTest(unittest.TestCase):
    def test_below_threshold_marked_unreliable(self):
        conn = _connect()
        for i in range(5):
            feedback.ingest_performance(
                conn, published_url=f"https://instagram.com/p/{i}",
                published_at=time.time(), metrics={"reach": 1000}, formula="F1",
            )
        correlation = feedback.formula_correlation(conn)
        self.assertFalse(correlation["reliable"])

    def test_at_or_above_threshold_marked_reliable(self):
        conn = _connect()
        for i in range(feedback.MIN_PIECES_FOR_FORMULA_SIGNAL):
            feedback.ingest_performance(
                conn, published_url=f"https://instagram.com/p/{i}",
                published_at=time.time(), metrics={"reach": 1000}, formula="F1",
            )
        correlation = feedback.formula_correlation(conn)
        self.assertTrue(correlation["reliable"])
        self.assertEqual(correlation["by_formula"]["F1"]["count"], feedback.MIN_PIECES_FOR_FORMULA_SIGNAL)


class BuildReportTest(unittest.TestCase):
    def test_report_runs_clean_on_empty_db(self):
        conn = _connect()
        report = feedback.build_report(conn)
        for heading in ("# Reporte de rendimiento", "## Publicado", "## Ganadores", "## Que formula gana", "## Mezcla 70/30"):
            self.assertIn(heading, report)

    def test_report_runs_clean_with_data(self):
        conn = _connect()
        feedback.ingest_performance(
            conn, published_url="https://instagram.com/p/z", published_at=time.time(),
            metrics={"reach": 5000, "likes": 200, "comments": 40}, formula="F1",
        )
        report = feedback.build_report(conn)
        self.assertIn("instagram.com/p/z", report)


if __name__ == "__main__":
    unittest.main()
