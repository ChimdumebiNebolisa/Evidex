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

    def test_manifest_and_judgment_freeze_exist(self):
        self.assertTrue(cfg.FREEZE_JUDGES.exists())
        self.assertTrue(cfg.FREEZE_MANIFEST.exists())
        import verify_headlines
        self.assertEqual(verify_headlines.verify_freezes(), [])

    def test_unblinded_exists_only_with_manifest(self):
        self.assertTrue(cfg.FREEZE_MANIFEST.exists())
        self.assertTrue(cfg.UNBLINDED_PARQUET.exists())


class TestRawJudgmentCompleteness(unittest.TestCase):
    def test_each_judge_231(self):
        expected = set(run_judges.expected_items())
        self.assertEqual(len(expected), 231)
        for judge in cfg.JUDGES:
            done, malformed = run_judges.judge_status(judge)
            self.assertEqual(malformed, [])
            self.assertEqual(done, expected)
            batches = sorted((cfg.JUDGMENTS_DIR / judge).glob(f"{judge}_batch_*.jsonl"))
            self.assertEqual(
                [p.name for p in batches],
                [f"{judge}_batch_01.jsonl", f"{judge}_batch_02.jsonl",
                 f"{judge}_batch_03.jsonl"],
            )

    def test_no_unblind_fields_in_raw_records(self):
        banned = {"gold_label", "cohort", "cursor_consensus_C", "nli_disagrees",
                  "gpt54_transition", "regression_type"}
        for judge in cfg.JUDGES:
            for p in (cfg.JUDGMENTS_DIR / judge).glob(f"{judge}_batch_*.jsonl"):
                for r in run_judges.load_batch_file(p):
                    self.assertTrue(banned.isdisjoint(r.keys()), p.name)


class TestCrossFamilyJoin(unittest.TestCase):
    def test_unique_item_counts(self):
        df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
        self.assertEqual(len(df), 231)
        self.assertEqual(df["claude_item_id"].nunique(), 231)
        self.assertEqual(df["source_item_id"].nunique(), 231)
        self.assertEqual(df["item_id"].nunique(), 231)
        self.assertTrue(df["item_id"].str.startswith("CR-").all())
        self.assertTrue(df["source_item_id"].str.startswith("SA-").all())
        self.assertEqual(set(df["cursor_consensus_C"]), {"Ambiguous", "Unresolved"})
        self.assertEqual((df["cursor_consensus_C"] == "Ambiguous").sum(), 212)
        self.assertEqual((df["cursor_consensus_C"] == "Unresolved").sum(), 19)

    def test_subgroup_counts(self):
        df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
        self.assertEqual((df["cohort"] == "regression").sum(), 86)
        self.assertEqual((df["cohort"] == "resistant").sum(), 112)
        self.assertEqual((df["cohort"] == "rescue").sum(), 24)
        self.assertEqual((df["cohort"] == "robust").sum(), 9)
        self.assertEqual((df["regression_type"] == "both").sum(), 24)
        self.assertEqual(
            ((df["cohort"] == "regression") & (df["regression_type"] != "both")).sum(), 62)

    def test_primary_taxonomy_partition(self):
        df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
        tax = df["cross_family_taxonomy"].value_counts().to_dict()
        self.assertEqual(tax.get("cross_family_persistent_ambiguity"), 134)
        self.assertEqual(tax.get("grok_only_ambiguity"), 97)
        self.assertEqual(tax.get("claude_internal_disagreement", 0), 0)
        self.assertEqual(sum(tax.values()), 231)
        stats = pd.read_csv(cfg.TABLES_DIR / "statistical_tests.csv")
        names = set(stats["analysis"])
        for n in ("persistent_ambiguity", "claude_resolved", "grok_only_ambiguity",
                  "claude_decisive_agrees_fever", "persistent_amb_shared_regression"):
            self.assertIn(n, names)


class TestHeadlineVerification(unittest.TestCase):
    def test_registry_and_script(self):
        p = cfg.REPORTS_DIR / "HEADLINES.json"
        self.assertTrue(p.exists())
        reg = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(reg["model"], "claude-opus-5-thinking-high")
        self.assertGreaterEqual(len(reg["headlines"]), 20)
        findings = (cfg.REPORTS_DIR / "CLAUDE_FINDINGS.md").read_text(encoding="utf-8")
        self.assertIn("claude-opus-5-thinking-high", findings)
        self.assertIn("independent human", findings.lower())
        self.assertIn("mixed", findings.lower())
        import verify_headlines
        self.assertEqual(verify_headlines.main(), 0)


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
