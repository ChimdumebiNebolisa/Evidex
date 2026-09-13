"""Verification suite for the Claude full-regression A->B->C panel.

Covers cohort size, blinding, model lock, schema validation, methodological
equivalence with the frozen Cursor/Grok pipeline, completeness, freeze
integrity, and non-mutation of the older frozen experiments.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src"
SV_ROOT = Path(__file__).resolve().parents[2]
SV_SRC = SV_ROOT / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SV_SRC))
sys.path.insert(0, str(SV_ROOT))

import analyze  # noqa: E402
import consensus_agreement as ca  # noqa: E402
import derive_and_blind as dab  # noqa: E402
import panel_config as cfg  # noqa: E402
import run_judges  # noqa: E402


class TestCohort(unittest.TestCase):
    def test_regression_cohort_is_exactly_226(self):
        claim_ids, audit = dab.derive_regression_claim_ids()
        self.assertEqual(len(claim_ids), 226)
        self.assertEqual(audit["n_regressions"], 226)
        self.assertEqual(audit["n_both_models"] + audit["n_gpt54_only"]
                         + audit["n_mini_only"], 226)

    def test_blinded_stages_have_226_unique_items(self):
        for stage in cfg.STAGES:
            ids = run_judges.expected_items(stage)
            self.assertEqual(len(ids), 226, stage)
            self.assertEqual(len(set(ids)), 226, stage)

    def test_id_map_is_private_and_one_to_one(self):
        idmap = pd.read_csv(cfg.ID_MAP_CSV)
        self.assertEqual(len(idmap), 226)
        self.assertEqual(idmap["claude_item_id"].nunique(), 226)
        self.assertEqual(idmap["source_item_id"].nunique(), 226)
        self.assertEqual(idmap["claim_id"].nunique(), 226)
        for stage in cfg.STAGES:
            text = cfg.stage_blinded(stage).read_text(encoding="utf-8")
            self.assertNotIn("SA-", text, f"source ids leaked into stage {stage}")
            self.assertNotIn("claim_id", text, f"claim_id leaked into stage {stage}")


class TestBlinding(unittest.TestCase):
    def test_no_leakage(self):
        for stage in cfg.STAGES:
            self.assertEqual(dab.leakage_errors(stage), [], stage)
        self.assertEqual(dab.id_neutrality_errors(), [])

    def test_stage_disclosure_is_strictly_progressive(self):
        keys = {}
        for stage in cfg.STAGES:
            recs = [json.loads(l) for l in
                    cfg.stage_blinded(stage).read_text(encoding="utf-8").splitlines() if l.strip()]
            keys[stage] = set().union(*[set(r) for r in recs])
        self.assertTrue(keys["A"] < keys["B"] < keys["C"])
        self.assertEqual(keys["A"], {"item_id", "claim", "evidence_sentences"})
        self.assertEqual(keys["B"] - keys["A"], {"page_titles"})
        self.assertEqual(keys["C"] - keys["B"], {"structured_evidence"})

    def test_stage_evidence_matches_shared_pipeline_representation(self):
        """Stage evidence is reused verbatim; no new retrieval."""
        idmap = pd.read_csv(cfg.ID_MAP_CSV).set_index("claude_item_id")
        for stage in cfg.STAGES:
            shared = {json.loads(l)["item_id"]: json.loads(l) for l in
                      cfg.SHARED_BLINDED[stage].read_text(encoding="utf-8").splitlines()
                      if l.strip()}
            for line in cfg.stage_blinded(stage).read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                src = shared[idmap.loc[rec["item_id"], "source_item_id"]]
                for k in rec:
                    if k == "item_id":
                        continue
                    self.assertEqual(rec[k], src.get(k, [] if k == "page_titles" else {}),
                                     f"stage {stage} {rec['item_id']} field {k}")

    def test_no_prohibited_text_in_judge_facing_metadata(self):
        """Judge-facing metadata, including every path a judge is given, must
        not reveal that the cohort is a regression set."""
        packets = 0
        for stage in cfg.STAGES:
            self.assertEqual(cfg.blinding_text_errors(cfg.stage_packets_rel(stage)), [])
            self.assertEqual(cfg.blinding_text_errors(cfg.stage_inbox_rel(stage)), [])
            for p in sorted(cfg.stage_packets_dir(stage).glob("*.json")):
                packets += 1
                packet = json.loads(p.read_text(encoding="utf-8"))
                meta = json.dumps({k: v for k, v in packet.items() if k != "items"})
                self.assertEqual(cfg.blinding_text_errors(meta), [], p.name)
                self.assertEqual(cfg.blinding_text_errors(p.as_posix()), [], p.name)
        self.assertGreater(packets, 0, "no packets to check")


class TestModelLock(unittest.TestCase):
    def test_config_lock(self):
        lock = cfg.load_lock()
        self.assertEqual(lock["model"], "claude-opus-5-thinking-high")
        self.assertFalse(lock["inference"]["auto"])
        self.assertFalse(lock["inference"]["inherit"])
        self.assertFalse(lock["inference"]["web_browse"])
        self.assertEqual(lock["expected_judgments_total"], 3390)

    def test_substitution_refused(self):
        for bad in ("cursor-grok-4.6-high-fast", "grok-4.6", "GLM-5.3",
                    "claude-opus-5", "auto", "inherit"):
            with self.assertRaises(SystemExit, msg=bad):
                cfg.require_locked_model(bad)
        cfg.require_locked_model(cfg.LOCKED_MODEL)  # must not raise

    def test_frozen_stage_manifests_record_the_locked_model(self):
        for stage in cfg.STAGES:
            path = cfg.stage_freeze(stage)
            if not path.exists():
                self.skipTest(f"stage {stage} not frozen yet")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["model"],
                             cfg.LOCKED_MODEL)


class TestSchema(unittest.TestCase):
    GOOD = {"item_id": "CF-000001", "judge_id": "claude_full_judge_1", "stage": "A",
            "verdict": "Supported", "evidence_sufficiency": "probably_sufficient",
            "confidence": 80, "issue_flags": ["none"], "brief_reason": "ok"}

    def test_accepts_valid(self):
        self.assertTrue(run_judges.valid_record(dict(self.GOOD), "A", "claude_full_judge_1"))

    def test_rejects_invalid(self):
        cases = [
            {"verdict": "Maybe"}, {"verdict": "supported"},
            {"evidence_sufficiency": "sufficient"},
            {"confidence": 101}, {"confidence": -1}, {"confidence": "80"},
            {"confidence": True}, {"issue_flags": []}, {"issue_flags": "none"},
            {"issue_flags": ["nonexistent_flag"]}, {"brief_reason": ""},
            {"judge_id": "claude_full_judge_2"}, {"stage": "B"},
        ]
        for patch in cases:
            r = dict(self.GOOD)
            r.update(patch)
            self.assertFalse(run_judges.valid_record(r, "A", "claude_full_judge_1"), patch)

    def test_vocabulary_matches_shared_pipeline(self):
        import config as shared  # noqa: PLC0415
        self.assertEqual(cfg.VERDICTS, shared.VERDICTS)
        self.assertEqual(cfg.SUFFICIENCY, shared.SUFFICIENCY)
        self.assertEqual(cfg.ISSUE_FLAGS, shared.ISSUE_FLAGS)

    def test_rubric_is_the_shared_unmodified_rubric(self):
        rubric = (cfg.PROMPTS_DIR / "judge_rubric.md").read_text(encoding="utf-8")
        out = subprocess.run(["git", "diff", "--stat", "HEAD", "--",
                              "silver_adjudication_v1/prompts/"],
                             cwd=cfg.REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "", "shared prompts were modified")
        for stage in cfg.STAGES:
            for p in sorted(cfg.stage_packets_dir(stage).glob("*.json")):
                self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["rubric"], rubric)


class TestMethodologicalEquivalence(unittest.TestCase):
    def test_consensus_rules_identical_to_shared_implementation(self):
        import aggregate_consensus as shared  # noqa: PLC0415
        from itertools import product  # noqa: PLC0415
        suffs = ["clearly_sufficient", "partial_or_ambiguous", "clearly_insufficient"]
        for verdicts in product(cfg.VERDICTS, repeat=5):
            for suff in product(suffs, repeat=2):
                sub = pd.DataFrame({
                    "verdict": list(verdicts),
                    "sufficiency": [suff[0]] * 3 + [suff[1]] * 2,
                })
                self.assertEqual(ca.consensus_for_item(sub)[:2],
                                 shared.consensus_for_item(sub)[:2], (verdicts, suff))

    def test_taxonomy_reproduces_frozen_grok_labels(self):
        """The taxonomy implementation must recover the frozen Grok
        silver_taxonomy for all 226 regressions from Grok consensus alone."""
        grok = pd.read_parquet(cfg.CURSOR_UNBLINDED)
        reg = grok[grok["cohort"] == "regression"].copy()
        self.assertEqual(len(reg), 226)
        recomputed = reg.apply(lambda r: analyze.taxonomy_row(r, "regression"), axis=1)
        self.assertTrue((recomputed == reg["silver_taxonomy"]).all(),
                        "taxonomy rules drifted from the frozen Grok labels")

    def test_broad_mapping_partitions_the_taxonomy(self):
        self.assertEqual(set(analyze.BROAD), set(analyze.TAX_ORDER))
        self.assertEqual(set(analyze.BROAD.values()), set(analyze.BROAD_ORDER))


class TestCompleteness(unittest.TestCase):
    def _frozen_stages(self):
        return [s for s in cfg.STAGES if cfg.stage_freeze(s).exists()]

    def test_per_stage_judgment_counts(self):
        frozen = self._frozen_stages()
        if not frozen:
            self.skipTest("no stage frozen yet")
        for stage in frozen:
            df = ca.load_judgments(stage)
            self.assertEqual(len(df), cfg.EXPECTED_PER_STAGE, stage)
            self.assertEqual(df["item_id"].nunique(), 226, stage)
            self.assertEqual(df["judge"].nunique(), 5, stage)
            self.assertEqual(len(df.drop_duplicates(["item_id", "judge"])), 1130, stage)

    def test_total_is_3390_when_all_stages_frozen(self):
        if len(self._frozen_stages()) < 3:
            self.skipTest("not all stages frozen yet")
        total = sum(len(ca.load_judgments(s)) for s in cfg.STAGES)
        self.assertEqual(total, cfg.EXPECTED_TOTAL)

    def test_no_duplicate_stage_judge_item_records(self):
        frozen = self._frozen_stages()
        if not frozen:
            self.skipTest("no stage frozen yet")
        seen = set()
        for stage in frozen:
            for judge in cfg.JUDGES:
                for p in sorted(cfg.stage_judgments_dir(stage).glob(f"{judge}_batch_*.jsonl")):
                    for r in run_judges.load_batch_file(p):
                        key = (stage, judge, r["item_id"])
                        self.assertNotIn(key, seen, key)
                        seen.add(key)

    def test_verdicts_and_flags_within_vocabulary(self):
        frozen = self._frozen_stages()
        if not frozen:
            self.skipTest("no stage frozen yet")
        for stage in frozen:
            df = ca.load_judgments(stage)
            self.assertTrue(df["verdict"].isin(cfg.VERDICTS).all())
            self.assertTrue(df["sufficiency"].isin(cfg.SUFFICIENCY).all())
            self.assertTrue(df["confidence"].between(0, 100).all())
            flags = {f for row in df["issue_flags"] for f in row.split(";")}
            self.assertTrue(flags <= set(cfg.ISSUE_FLAGS), flags - set(cfg.ISSUE_FLAGS))


class TestFreezeIntegrity(unittest.TestCase):
    def test_stage_freezes_verify(self):
        any_frozen = False
        for stage in cfg.STAGES:
            if cfg.stage_freeze(stage).exists():
                any_frozen = True
                run_judges.verify_frozen(stage)
        if not any_frozen:
            self.skipTest("nothing frozen yet")

    def test_unblinding_requires_manifest(self):
        if not cfg.FREEZE_MANIFEST.exists():
            with self.assertRaises(SystemExit):
                analyze.verify_manifest()
        else:
            analyze.verify_manifest()

    def test_progressive_disclosure_gate(self):
        for stage, pred in cfg.STAGE_PREDECESSOR.items():
            if cfg.stage_freeze(stage).exists():
                self.assertTrue(cfg.stage_freeze(pred).exists(),
                                f"stage {stage} frozen without stage {pred}")


class TestOldExperimentsUntouched(unittest.TestCase):
    PROTECTED = [
        "silver_adjudication_v1/cursor_panel",
        "silver_adjudication_v1/claude_residual_panel",
        "silver_adjudication_v1/judgments",
        "silver_adjudication_v1/data",
        "silver_adjudication_v1/prompts",
        "silver_adjudication_v1/src",
        "analysis_v2",
    ]

    def test_no_uncommitted_changes_to_frozen_experiments(self):
        out = subprocess.run(["git", "status", "--porcelain", "--"] + self.PROTECTED,
                             cwd=cfg.REPO_ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "", "frozen artifacts were modified")

    def test_no_diff_against_branch_point(self):
        base = subprocess.run(["git", "merge-base", "HEAD", "main"], cwd=cfg.REPO_ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
        out = subprocess.run(["git", "diff", "--name-only", base, "HEAD", "--"] + self.PROTECTED,
                             cwd=cfg.REPO_ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "", "frozen artifacts changed since branch point")

    def test_old_claude_residual_judgments_not_spliced(self):
        for stage in cfg.STAGES:
            for p in sorted(cfg.stage_judgments_dir(stage).glob("*_batch_*.jsonl")):
                text = p.read_text(encoding="utf-8")
                self.assertNotIn("CR-", text, f"{p.name} contains residual-panel item ids")
                self.assertNotIn("claude_judge_", text.replace("claude_full_judge_", ""),
                                 f"{p.name} contains residual-panel judge ids")


if __name__ == "__main__":
    unittest.main(verbosity=2)
