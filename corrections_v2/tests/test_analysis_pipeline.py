"""Offline-only synthetic integration fixtures, always outside live results/I/O."""
import ast
import itertools
import json
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "corrections_v2"))
import analysis_core as core
import analysis_io as aio
import analysis_pipeline as pipeline


def ratings(verdicts, weak=0):
    return [{"item_id": "fixture", "judge_id": f"judge_{i+1}", "stage": "C",
             "verdict": v, "evidence_sufficiency": "partial_or_ambiguous" if i < weak else "clearly_sufficient",
             "confidence": 70, "issue_flags": ["none"], "brief_reason": "Synthetic fixture only."}
            for i, v in enumerate(verdicts)]


class ConsensusStatisticsTests(unittest.TestCase):
    def test_exhaustive_historical_consensus_equivalence(self):
        source = (ROOT / "silver_adjudication_v1/src/aggregate_consensus.py").read_text(encoding="utf-8")
        function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "consensus_for_item")
        scope = {"Counter": Counter, "pd": pd, "WEAK_SUFF": set(core.SUFF[2:])}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "historical_consensus", "exec"), scope)
        for verdicts in itertools.product(core.LABELS[:3], repeat=5):
            for weak in (0, 3, 5):
                rows = ratings(verdicts, weak)
                old = scope["consensus_for_item"](pd.DataFrame(rows).rename(columns={"evidence_sufficiency": "sufficiency"}))
                new = core.consensus(list(reversed(rows)))  # Arrival order must not matter.
                self.assertEqual((new["consensus"], new["rule"]), old[:2])

    def test_order_sensitive_tie_is_disclosed_not_redefined(self):
        a = core.consensus(ratings(["Ambiguous", "Supported", "Ambiguous", "Supported", "Refuted"]))
        b = core.consensus(ratings(["Supported", "Ambiguous", "Ambiguous", "Supported", "Refuted"]))
        self.assertEqual(a["consensus"], "Ambiguous")
        self.assertEqual(b["consensus"], "Unresolved")
        self.assertTrue(a["order_sensitive_label"])
        self.assertEqual(a["labels_under_reordering"], ["Ambiguous", "Unresolved"])
        self.assertFalse(core.consensus(ratings(["Supported", "Ambiguous", "Ambiguous", "Supported", "Refuted"], 3))["order_sensitive_label"])

    def test_consensus_never_accepts_missing_or_duplicate_slots(self):
        rows = ratings(["Supported"] * 5)
        for bad in (rows[:4], rows[:4] + [rows[0]]):
            with self.assertRaises(ValueError):
                core.aggregate(bad, ["fixture"])

    def test_statistics_edges_and_exact_values(self):
        self.assertIsNone(core.rate([])["rate_pct"])
        self.assertEqual(core.rate([True] * 8)["rate_pct"], 100)
        self.assertEqual(core.paired([True], [True], exact=True)["p_value"], 1)
        self.assertIsNone(core.paired([True], [True], exact=False)["p_value"])
        self.assertEqual(core.paired([True] * 5, [False] * 5, exact=True)["p_value"], .0625)
        zero = core.fisher([False] * 4, [True, False])
        self.assertIsNone(zero["odds_ratio"])
        self.assertIsNotNone(zero["p_value"])
        self.assertAlmostEqual(core.fisher([True, True, False], [True, False, False])["odds_ratio"], 4)
        p = [{"p_value": .01}, {"p_value": .04}, {"p_value": .03}, {"p_value": None}]
        core.bh(p)
        self.assertEqual([r.get("p_bh") for r in p], [.03, .04, .04, None])

    def test_inventory_reconciliation(self):
        import subprocess
        old = json.loads(subprocess.check_output(["git", "show", "0cc36f04ce8bbfd2a62848760c71550242be78c4:corrections_v2/generated/input_hashes.json"], cwd=ROOT))
        new = aio.read_json(ROOT / "corrections_v2/baseline/historical_inputs.json")["files"]
        self.assertEqual(len(old), 775)
        self.assertEqual(set(old) - set(new), {"corrections_v2/generated/historical_pages_used.json"})
        self.assertFalse(set(new) - set(old))
        self.assertEqual({k: v["recorded_raw_sha256"] for k, v in new.items()}, {k: old[k] for k in new})
        from provenance import verify_snapshot
        self.assertEqual(verify_snapshot(ROOT / "corrections_v2/inputs/historical_pages.json")["status"], "exact_lf_bytes")


class PipelineFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="evidex-analysis-fixtures-")
        cls.root = Path(cls.temp.name)
        # Only immutable needed inputs are copied. The repository-wide historical
        # gate is separately exercised live and by prior reproduction tests.
        names = set(aio.spec_files(ROOT))
        names.update(["corrections_v2/generated/evidence_audit.jsonl", "corrections_v2/generated/stage_c_corrected.jsonl"])
        cls.manifest = aio.read_json(ROOT / aio.MANIFEST)
        names.update(j["packet"] for j in cls.manifest["jobs"])
        for panel, base in aio.PANEL_ROOTS.items():
            for stage in "AB":
                names.add(base + f"/freezes/freeze_stage_{stage}.json")
                names.update(p.relative_to(ROOT).as_posix() for p in (ROOT / base / "judgments" / f"stage_{stage.lower()}").glob("*_batch_*.jsonl"))
            names.add(base + ("/freezes/silver_unblinded.parquet" if panel == "grok" else "/freezes/claude_full_unblinded.parquet"))
        for name in names:
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        with patch.object(aio, "preparation_gate"):
            aio.freeze_spec(cls.root)
        cls.deliver(cls.manifest)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def deliver(cls, manifest):
        patterns = [["Supported"] * 5, ["Refuted"] * 5, ["Ambiguous"] * 5,
                    ["Supported", "Supported", "Supported", "Refuted", "Refuted"],
                    ["Ambiguous", "Supported", "Ambiguous", "Supported", "Refuted"],
                    ["Supported", "Ambiguous", "Ambiguous", "Supported", "Refuted"]]
        for job in manifest["jobs"]:
            rows = []
            for iid in job["item_ids"]:
                if job["panel"] == "resolver":
                    row = {"item_id": iid, "stage": "C", "resolver_outcome": "Ambiguous",
                           "disagreement_type": "partial_warrant", "confidence": 55,
                           "brief_reason": "Synthetic resolver fixture only."}
                else:
                    slot = int(job["judge_id"].split("_")[-1]) - 1
                    row = ratings(patterns[int(iid.split("-")[-1]) % len(patterns)])[slot]
                    row["item_id"] = iid
                rows.append(row)
            aio.write_json(cls.root / job["output"], rows)
            directory = cls.root / "corrections_v2/execution" / job["job_id"]
            directory.mkdir(parents=True, exist_ok=True)
            raw, routing = directory / "attempt-01.raw.txt", directory / "attempt-01.routing.txt"
            aio.write_json(raw, rows)
            routing.write_text("SYNTHETIC TEST FIXTURE: no model call and no real provider routing.\n", encoding="utf-8")
            record = {"job_id": job["job_id"], "attempt": 1, "status": "accepted",
                      "requested_model": job["model"], "resolved_model": job["model"],
                      "provider_model_version": None, "version_metadata_status": "not_exposed",
                      "version_metadata_note": "Synthetic fixture, no provider invoked",
                      "session_id": "SYNTHETIC-" + job["job_id"], "cursor_version": "synthetic",
                      "operator": "fixture", "reviewer": "fixture", "routing_and_isolation_reviewed": True,
                      "started_at_utc": aio.stamp(), "completed_at_utc": aio.stamp(),
                      "fresh_context": True, "inherited_context": False, "auto": False, "inherit": False,
                      "web_browse": False, "external_retrieval": False, "temperature": "provider_default",
                      "visible_input_files": [job["packet"]], "packet_sha256": job["packet_sha256"],
                      "output_sha256": aio.digest(cls.root / job["output"]),
                      "raw_response": {"path": raw.relative_to(cls.root).as_posix(), "sha256": aio.digest(raw)},
                      "routing_evidence": {"path": routing.relative_to(cls.root).as_posix(), "sha256": aio.digest(routing)}}
            aio.write_json(directory / "attempt-01.json", record)

    def replace(self, path, value):
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        aio.write_json(path, value)

    def test_missing_outputs_pending_without_estimates(self):
        path = self.root / self.manifest["jobs"][0]["output"]
        original = path.read_bytes()
        path.unlink()
        self.addCleanup(path.write_bytes, original)
        status, code = pipeline.analyze(self.root, self.manifest, "primary", "must-not-exist")
        self.assertEqual(code, 1)
        self.assertEqual(status["status"], "pending")
        self.assertFalse((self.root / "corrections_v2/results/must-not-exist").exists())

    def test_output_presence_without_provenance_is_incomplete(self):
        job = self.manifest["jobs"][0]
        path = self.root / f"corrections_v2/execution/{job['job_id']}/attempt-01.json"
        self.replace(path, {"attempt": 1, "job_id": job["job_id"], "status": "accepted"})
        status, _, _ = aio.inspect(self.manifest, "primary", self.root, aio.verify_spec(self.root))
        self.assertEqual(status["status"], "incomplete")
        self.assertIn(job["job_id"], status["execution_provenance_errors"])

    def test_invalid_output_blocks(self):
        job = self.manifest["jobs"][0]
        self.replace(self.root / job["output"], [])
        status, _, _ = aio.inspect(self.manifest, "primary", self.root, aio.verify_spec(self.root))
        self.assertIn(job["job_id"], status["invalid_outputs_or_packets"])

    def test_wrong_route_and_reused_context_block(self):
        a, b = self.manifest["jobs"][:2]
        path = self.root / f"corrections_v2/execution/{b['job_id']}/attempt-01.json"
        original = aio.read_json(path)
        self.replace(path, dict(original, resolved_model="not-the-locked-model"))
        status, _, _ = aio.inspect(self.manifest, "primary", self.root, aio.verify_spec(self.root))
        self.assertIn(b["job_id"], status["execution_provenance_errors"])
        aio.write_json(path, dict(original, session_id="SYNTHETIC-" + a["job_id"]))
        status, _, _ = aio.inspect(self.manifest, "primary", self.root, aio.verify_spec(self.root))
        self.assertIn("reused_session", status["execution_provenance_errors"])

    def test_protocol_mutation_blocks(self):
        path = self.root / aio.SPEC
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_bytes(original + b"amendment without new freeze\n")
        with self.assertRaisesRegex(ValueError, "changed after freeze"):
            aio.verify_spec(self.root)

    def test_schema_valid_earlier_attempt_cannot_be_discarded(self):
        job = self.manifest["jobs"][0]
        path = self.root / f"corrections_v2/execution/{job['job_id']}/attempt-01.json"
        original = aio.read_json(path)
        self.replace(path, dict(original, status="invalid", reason="must not retry a valid verdict"))
        second = path.with_name("attempt-02.json")
        self.addCleanup(second.unlink, missing_ok=True)
        aio.write_json(second, dict(original, attempt=2, session_id="new-fixture-session"))
        with self.assertRaisesRegex(ValueError, "schema-valid earlier"):
            aio.provenance_for_job(job, self.root, aio.verify_spec(self.root))

    def test_context_reuse_across_optional_panel_blocks_selected_provenance(self):
        a, optional = self.manifest["jobs"][0], self.manifest["jobs"][-1]
        path = self.root / f"corrections_v2/execution/{optional['job_id']}/attempt-01.json"
        record = aio.read_json(path)
        self.replace(path, dict(record, session_id="SYNTHETIC-" + a["job_id"]))
        status, _, _ = aio.inspect(self.manifest, "primary", self.root, aio.verify_spec(self.root))
        self.assertIn("reused_session", status["execution_provenance_errors"])

    def test_handoff_contains_only_one_packet_per_judge_archive(self):
        import io
        import zipfile
        result = pipeline.export_handoff(self.root, self.manifest)
        with zipfile.ZipFile(self.root / result["bundle"]) as archive:
            jobs = [p for p in archive.namelist() if p.startswith("jobs/")]
            self.assertEqual(len(jobs), 85)
            for job in self.manifest["jobs"]:
                with zipfile.ZipFile(io.BytesIO(archive.read(f"jobs/{job['job_id']}.zip"))) as packet:
                    self.assertEqual(packet.namelist(), [job["packet"]])
                    self.assertEqual(packet.read(job["packet"]), (self.root / job["packet"]).read_bytes())

    def test_complete_end_to_end_primary_residual_resolver_and_optional(self):
        frozen = aio.freeze_judgments(self.manifest, "primary", self.root)
        self.assertEqual(frozen["status"], "frozen")
        path = aio.freeze_path(self.root, "primary")
        before = path.read_bytes()
        self.assertEqual(aio.freeze_judgments(self.manifest, "primary", self.root)["status"], "frozen")
        self.assertEqual(before, path.read_bytes())
        status, code = pipeline.analyze(self.root, self.manifest, "primary", "fixture001")
        self.assertEqual(code, 0)
        self.assertEqual(status["denominators"], {"grok": 1060, "claude_full": 226})
        result = aio.result_manifest(self.root, "fixture001")
        self.assertTrue(any(p.endswith(".svg") for p in result["files"]))
        primary = self.root / "corrections_v2/results/fixture001/tables/grok_claims.csv"
        primary_bytes = primary.read_bytes()
        frame = pd.read_csv(primary)
        follow = aio.load_manifest(self.root, "fixture001")
        residual = next(p for p in follow["panels"] if p["panel"] == "new_residual")
        self.assertEqual(set(residual["source_ids"]), set(frame.loc[frame.ambiguous_C, "source_item_id"]))
        self.assertEqual(residual["judgments"], 5 * len(residual["source_ids"]))
        for job in follow["jobs"]:
            packet = aio.read_json(self.root / job["packet"])
            self.assertNotIn("fixture001", job["packet"])
            for item in packet["items"]:
                self.assertFalse(set(item) & {"cohort", "gold_label", "source_item_id", "claim_id", "category"})
        pending, code = pipeline.analyze(self.root, follow, "new_residual", "not-yet", "fixture001")
        self.assertEqual(code, 1)
        self.assertEqual(pending["scientific_estimates"], "not_computed")
        self.deliver(follow)
        for panel, version in [("new_residual", "fixture002"), ("resolver", "fixture003")]:
            self.assertEqual(aio.freeze_judgments(follow, panel, self.root, "fixture001")["status"], "frozen")
            status, code = pipeline.analyze(self.root, follow, panel, version, "fixture001")
            self.assertEqual(code, 0)
            self.assertFalse(status["primary_consensus_replaced"])
            aio.result_manifest(self.root, version)
        optional = "claude_historical_residual_optional"
        self.assertEqual(aio.freeze_judgments(self.manifest, optional, self.root)["status"], "frozen")
        status, code = pipeline.analyze(self.root, self.manifest, optional, "fixture004", "fixture001")
        self.assertEqual(code, 0)
        self.assertEqual(status["n"], 231)
        self.assertEqual(status["selection"], "fixed_historical_231_sensitivity")
        self.assertEqual(primary_bytes, primary.read_bytes())
        with self.assertRaisesRegex(ValueError, "already exists"):
            pipeline.analyze(self.root, self.manifest, "primary", "fixture001")
        job = self.manifest["jobs"][0]
        rawpath = self.root / job["output"]
        self.replace(rawpath, [])
        with self.assertRaisesRegex(ValueError, "frozen bytes changed"):
            aio.result_manifest(self.root, "fixture001")


if __name__ == "__main__":
    unittest.main()
