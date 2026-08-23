"""Tests for the Claude residual Stage C panel."""
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import derive_and_blind  # noqa: E402
import panel_config as cfg  # noqa: E402
import run_judges  # noqa: E402
from consensus_agreement import consensus_for_item  # noqa: E402


class TestModelLock(unittest.TestCase):
    def test_lock_file(self):
        lock = cfg.load_lock()
        self.assertEqual(lock["model"], "claude-opus-5-thinking-high")
        self.assertEqual(lock["required_model"], "claude-opus-5-thinking-high")
        self.assertFalse(lock["inference"]["auto"])
        self.assertEqual(cfg.JUDGES, [f"claude_judge_{i}" for i in range(1, 6)])

    def test_refuse_substitution(self):
        with self.assertRaises(SystemExit):
            cfg.require_locked_model("cursor-grok-4.6-high-fast")
        with self.assertRaises(SystemExit):
            cfg.require_locked_model("Auto")


class TestCohortDerivation(unittest.TestCase):
    def test_residual_count(self):
        resid = derive_and_blind.reconstruct_residual()
        self.assertEqual(len(resid), 231)
        self.assertTrue(set(resid["consensus"]) <= {"Ambiguous", "Unresolved"})

    def test_blinded_n_and_opaque_ids(self):
        items = [json.loads(l) for l in cfg.BLINDED_JSONL.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
        self.assertEqual(len(items), 231)
        ids = [r["item_id"] for r in items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith("CR-") for i in ids))
        self.assertFalse(any(i.startswith("SA-") for i in ids))

    def test_unique_source_mapping(self):
        m = pd.read_csv(cfg.ID_MAP_CSV)
        self.assertEqual(len(m), 231)
        self.assertEqual(m["claude_item_id"].nunique(), 231)
        self.assertEqual(m["source_item_id"].nunique(), 231)


class TestBlinding(unittest.TestCase):
    def test_no_leakage(self):
        errs = derive_and_blind.leakage_errors()
        self.assertEqual(errs, [])

    def test_allowed_keys_only(self):
        rec = json.loads(cfg.BLINDED_JSONL.read_text(encoding="utf-8").splitlines()[0])
        self.assertTrue(set(rec.keys()) <= cfg.ALLOWED_ITEM_KEYS)


class TestConsensusRules(unittest.TestCase):
    def _sub(self, verdicts, suff=None):
        suff = suff or ["probably_sufficient"] * len(verdicts)
        return pd.DataFrame({"verdict": verdicts, "sufficiency": suff, "confidence": [70] * 5})

    def test_high_consensus(self):
        label, rule, _ = consensus_for_item(self._sub(["Supported"] * 4 + ["Refuted"]))
        self.assertEqual((label, rule), ("Supported", "high_consensus"))

    def test_preserve_ambiguous(self):
        label, _, _ = consensus_for_item(self._sub(["Ambiguous"] * 3 + ["Supported", "Refuted"]))
        self.assertEqual(label, "Ambiguous")

    def test_preserve_unresolved(self):
        label, _, _ = consensus_for_item(
            self._sub(["Supported", "Refuted", "Supported", "Refuted", "Ambiguous"]))
        self.assertEqual(label, "Unresolved")


class TestFreezeBeforeUnblind(unittest.TestCase):
    def test_unblind_refuses_without_manifest(self):
        if cfg.FREEZE_MANIFEST.exists():
            self.skipTest("manifest already written")
        import analyze
        with self.assertRaises(SystemExit):
            analyze.verify_manifest()


class TestJudgeSchema(unittest.TestCase):
    def test_valid_record(self):
        r = {"item_id": "CR-000001", "judge_id": "claude_judge_1", "stage": "C",
             "verdict": "Ambiguous", "evidence_sufficiency": "partial_or_ambiguous",
             "confidence": 55, "issue_flags": ["partial_warrant"], "brief_reason": "ok"}
        self.assertTrue(run_judges.valid_record(r, "claude_judge_1"))
        r["judge_id"] = "cursor_judge_1"
        self.assertFalse(run_judges.valid_record(r, "claude_judge_1"))


if __name__ == "__main__":
    unittest.main()
