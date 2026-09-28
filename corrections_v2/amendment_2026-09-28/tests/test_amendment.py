"""Checks of amendment A1's validator. No inference, no network, no WSL.

Run: python -m unittest discover -s corrections_v2/amendment_2026-09-28/tests -v
The full recomputation check is `python corrections_v2/amendment_2026-09-28/amended_analysis.py verify`.
"""
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

AMEND = Path(__file__).resolve().parents[1]
ROOT = AMEND.parents[1]
sys.path.insert(0, str(AMEND))

import amended_analysis as aa  # noqa: E402
from analysis_io import digest, read_json  # noqa: E402


class CapTests(unittest.TestCase):
    def test_only_the_cap_line_differs_from_frozen_source(self):
        frozen = inspect.getsource(aa.analysis_io.provenance_for_job).splitlines()
        amended = frozen[:]
        index = next(i for i, line in enumerate(frozen) if line.strip() == aa.FROZEN_CAP_LINE)
        amended[index] = amended[index].replace("> 3", "> 9")
        self.assertEqual(sum(a != b for a, b in zip(frozen, amended)), 1)
        self.assertTrue(callable(aa.amended_provenance_for_job()))


class SessionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(aa.SESSION_EVIDENCE.read_text("utf-8"))
        cls.rows = cls.evidence["records"]

    def test_counts(self):
        summary = self.evidence["summary"]
        self.assertEqual(summary["attempt_records"], 102)
        self.assertEqual(summary["by_classification"], {"own_record": 88, "collision_record": 13, "not_launched": 1})
        self.assertEqual(summary["launched_attempt_slots"], 101)
        self.assertEqual(summary["distinct_slot_agents"], 101)
        self.assertEqual(summary["slot_agents_parsed_in_attempt_evidence"], 99)
        self.assertEqual(summary["runner_exit_2_events"], 16)
        self.assertEqual(summary["unexplained_exit_2_events"], [])

    def test_records_unchanged(self):
        for row in self.rows:
            self.assertEqual(digest(ROOT / row["record"]), row["record_sha256"], row["record"])

    def test_collision_records_are_not_the_launched_attempt(self):
        own_sessions = {r["record_session"] for r in self.rows if r["classification"] == "own_record"}
        for row in (r for r in self.rows if r["classification"] == "collision_record"):
            record = read_json(ROOT / row["record"])
            self.assertEqual((record["session_id"], record["reason"]), ("unknown", aa.COLLISION_REASON))
            self.assertNotIn(row["slot_agent"], own_sessions)
            self.assertTrue(row["runner_log_lines"]["exit_2"])
            self.assertGreaterEqual(len(row["runner_log_lines"]["start"]), 2)

    def test_own_records_match_their_slot_logs(self):
        for row in (r for r in self.rows if r["classification"] == "own_record"):
            self.assertEqual(row["record_session"], row["slot_agent"], row["record"])


class StatusTests(unittest.TestCase):
    def status_with(self, edit):
        evidence = json.loads(aa.SESSION_EVIDENCE.read_text("utf-8"))
        edit(evidence["records"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session_evidence.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            with mock.patch.object(aa, "SESSION_EVIDENCE", path):
                return aa.amended_status()

    def test_ready_on_archived_evidence_and_rejects_tampering(self):
        self.assertEqual(self.status_with(lambda rows: None)["status"], "ready_under_amendment_A1")

        def tamper(rows):
            collisions = [r for r in rows if r["classification"] == "collision_record"]
            collisions[0]["slot_agent"] = collisions[1]["slot_agent"]
            collisions[2]["established"] = False
            collisions[3]["record_sha256"] = "0" * 64
        status = self.status_with(tamper)
        self.assertEqual(status["status"], "incomplete_under_amendment_A1")
        errors = status["amended_provenance_errors"]
        self.assertIn("reused_session", errors)
        self.assertEqual(sum("not established" in v for v in errors.values()), 1)
        self.assertEqual(sum("changed since" in v for v in errors.values()), 1)


if __name__ == "__main__":
    unittest.main()
