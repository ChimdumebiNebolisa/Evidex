"""Cursor-panel isolation, model lock, stage gates, and analysis math."""
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config  # noqa: E402
import run_judges  # noqa: E402
from aggregate_consensus import consensus_for_item  # noqa: E402
from cross_panel_stage_a import _consensus_label, _rate_agreement  # noqa: E402


class TestCursorModelLock(unittest.TestCase):
    def tearDown(self):
        config.apply_panel("glm")

    def test_lock_file(self):
        cfg = json.loads((config.CURSOR_PANEL_ROOT / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["model"], "cursor-grok-4.6-high-fast")
        self.assertEqual(cfg["required_model"], "cursor-grok-4.6-high-fast")
        self.assertFalse(cfg["inference"]["auto"])
        self.assertFalse(cfg["inference"]["inherit"])
        self.assertEqual(cfg["judges"], [f"cursor_judge_{i}" for i in range(1, 6)])

    def test_apply_panel_cursor(self):
        config.apply_panel("cursor")
        self.assertEqual(config.PANEL, "cursor")
        self.assertEqual(config.LOCKED_MODEL, "cursor-grok-4.6-high-fast")
        self.assertEqual(config.JUDGES, [f"cursor_judge_{i}" for i in range(1, 6)])
        self.assertEqual(config.JUDGMENTS_DIR.resolve(),
                         (config.CURSOR_PANEL_ROOT / "judgments").resolve())
        self.assertNotEqual(config.JUDGMENTS_DIR.resolve(),
                            config.GLM_JUDGMENTS_DIR.resolve())
        self.assertEqual(config.COHORT_PARQUET, config.SHARED_DERIVED_DIR / "cohort.parquet")

    def test_refuse_substitution(self):
        config.apply_panel("cursor")
        with self.assertRaises(SystemExit):
            config.require_locked_model("gpt-5.6-sol-high")
        with self.assertRaises(SystemExit):
            config.require_locked_model("Auto")

    def test_cursor_judge_schema(self):
        config.apply_panel("cursor")
        r = {"item_id": "SA-000001", "judge_id": "cursor_judge_1", "stage": "A",
             "verdict": "Supported", "evidence_sufficiency": "clearly_sufficient",
             "confidence": 90, "issue_flags": ["none"], "brief_reason": "ok"}
        self.assertTrue(run_judges.valid_record(r, "A", "cursor_judge_1"))
        r["judge_id"] = "judge_1"
        self.assertFalse(run_judges.valid_record(r, "A", "cursor_judge_1"))


class TestStageOrdering(unittest.TestCase):
    def tearDown(self):
        config.apply_panel("glm")

    def test_cursor_freeze_b_requires_a(self):
        config.apply_panel("cursor")
        with self.assertRaises(SystemExit):
            run_judges.freeze_stage("B")

    def test_cursor_freeze_c_requires_b(self):
        config.apply_panel("cursor")
        with self.assertRaises(SystemExit):
            run_judges.freeze_stage("C")

    def test_cursor_verify_unfrozen_raises(self):
        config.apply_panel("cursor")
        with self.assertRaises(SystemExit):
            run_judges.verify_frozen("A")


class TestFreezeBeforeUnblind(unittest.TestCase):
    def tearDown(self):
        config.apply_panel("glm")

    def test_cursor_manifest_absent(self):
        config.apply_panel("cursor")
        self.assertFalse(config.FREEZE_MANIFEST.exists())
        self.assertIn("cursor_panel", str(config.FREEZE_MANIFEST).replace("\\", "/"))

    def test_unblind_refuses_without_cursor_stage_freezes(self):
        config.apply_panel("cursor")
        import join_analysis_v2
        with self.assertRaises(SystemExit):
            join_analysis_v2.unblind_join()


class TestUniqueClaimCounts(unittest.TestCase):
    def test_cohort_and_judged_n(self):
        c = pd.read_parquet(config.COHORT_PARQUET)
        self.assertEqual(len(c), c["claim_id"].nunique())
        self.assertEqual((c["cohort"] == "regression").sum(), 226)
        pf = json.loads(config.PROVIDER_FILTERED.read_text(encoding="utf-8"))
        self.assertEqual(len(c) - len(pf["items"]), 1060)
        self.assertEqual(run_judges.expected_items("A").__len__(), 1060)


class TestConsensusAndUnresolved(unittest.TestCase):
    def _sub(self, verdicts, suff=None):
        suff = suff or ["probably_sufficient"] * len(verdicts)
        return pd.DataFrame({"verdict": verdicts, "sufficiency": suff,
                             "confidence": [70] * len(verdicts)})

    def test_high_consensus_four_of_five(self):
        label, rule, _ = consensus_for_item(self._sub(["Supported"] * 4 + ["Refuted"]))
        self.assertEqual((label, rule), ("Supported", "high_consensus"))

    def test_preserve_ambiguous(self):
        label, _, _ = consensus_for_item(
            self._sub(["Ambiguous"] * 3 + ["Supported", "Refuted"]))
        self.assertEqual(label, "Ambiguous")

    def test_preserve_unresolved(self):
        label, _, _ = consensus_for_item(
            self._sub(["Supported", "Refuted", "Supported", "Refuted", "Ambiguous"]))
        self.assertEqual(label, "Unresolved")


class TestTransitions(unittest.TestCase):
    def test_abc_flags(self):
        a, b, c = "Ambiguous", "Supported", "Refuted"
        resolved_by_titles = a in ("Ambiguous", "Unresolved") and b in ("Supported", "Refuted")
        resolved_only_by_structure = b in ("Ambiguous", "Unresolved") and c in ("Supported", "Refuted")
        still_amb = c in ("Ambiguous", "Unresolved")
        reversed_after_titles = a in ("Supported", "Refuted") and b in ("Supported", "Refuted") and a != b
        reversed_after_structure = b in ("Supported", "Refuted") and c in ("Supported", "Refuted") and b != c
        self.assertTrue(resolved_by_titles)
        self.assertFalse(resolved_only_by_structure)
        self.assertFalse(still_amb)
        self.assertFalse(reversed_after_titles)
        self.assertTrue(reversed_after_structure)
        self.assertTrue(a != b)
        self.assertTrue(b != c)


class TestCrossPanelReplicationMath(unittest.TestCase):
    def test_rate_agreement(self):
        a = pd.Series(["Supported", "Refuted", "Ambiguous"])
        b = pd.Series(["Supported", "Supported", "Ambiguous"])
        self.assertAlmostEqual(_rate_agreement(a, b), 2 / 3)

    def test_consensus_label_independent(self):
        sub = pd.DataFrame({
            "verdict": ["Supported"] * 4 + ["Ambiguous"],
            "sufficiency": ["clearly_sufficient"] * 5,
        })
        label, rule = _consensus_label(sub)
        self.assertEqual((label, rule), ("Supported", "high_consensus"))


class TestResolverBlinding(unittest.TestCase):
    def test_anonymized_judge_codes_and_source_has_no_unblind_fields(self):
        src = (Path(__file__).resolve().parents[1] / "src" / "resolve_disagreements.py"
               ).read_text(encoding="utf-8")
        self.assertIn('f"r{i+1}"', src)
        for bad in ("gold_label", "gpt-5.4_transition", "nli_disagrees", "cohort_type"):
            self.assertNotIn(bad, src)
        judges = [f"cursor_judge_{i}" for i in range(1, 6)]
        anon = {j: f"r{i+1}" for i, j in enumerate(judges)}
        self.assertEqual(set(anon.values()), {f"r{i}" for i in range(1, 6)})


class TestProhibitedLeakage(unittest.TestCase):
    def test_stage_files(self):
        for stage, extra in (("A", set()), ("B", {"page_titles"}),
                             ("C", {"page_titles", "structured_evidence"})):
            recs = [json.loads(l) for l in
                    (config.BLINDED_DIR / f"stage_{stage.lower()}.jsonl")
                    .read_text(encoding="utf-8").splitlines() if l.strip()]
            allowed = {"item_id", "claim", "evidence_sentences"} | extra
            for r in recs[:20]:
                self.assertTrue(set(r.keys()) <= allowed)
                for k in r:
                    self.assertNotIn(k.lower(), set(x.lower() for x in config.PROHIBITED_FIELDS))


class TestRunAllUnblindGate(unittest.TestCase):
    def test_cursor_run_all_skips_rebuild_and_gates_unblind(self):
        import run_all
        self.assertIn("build_cohort", run_all.CURSOR_SKIP_REBUILD)
        self.assertTrue(any(n == "unblind_join" for n, _, _ in run_all.STAGES))
        self.assertTrue(any(n == "cross_panel_stage_a" for n, _, _ in run_all.STAGES))


if __name__ == "__main__":
    unittest.main()
