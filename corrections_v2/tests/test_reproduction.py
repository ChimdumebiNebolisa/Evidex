"""Infrastructure fixtures only. Never write mock judgments in scientific I/O."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "corrections_v2"))
from provenance import (BASELINE, OUTPUT_MANIFEST, compare_historical, digest,
                        lf_bytes, seal_outputs, sha256, verify_historical,
                        verify_output_inventory, write_json)
from rerun import completion_status, validate_packet


def entry(data, kind="text"):
    return {"kind": kind, "recorded_raw_sha256": sha256(data),
            "baseline_blob_sha256": sha256(lf_bytes(data)),
            "lf_sha256": sha256(lf_bytes(data)) if kind == "text" else None}


class IntegrityTests(unittest.TestCase):
    def test_exact_and_eol_are_distinct(self):
        raw = b'{"value": 1}\r\nsecond\r\n'
        e = entry(raw)
        self.assertEqual(compare_historical(raw, e)["status"], "exact_recorded_bytes")
        self.assertEqual(compare_historical(lf_bytes(raw), e)["status"], "eol_only_equivalent")
        self.assertEqual(compare_historical(b'{"value": 1}\nsecond\r\n', e)["status"], "eol_only_equivalent")

    def test_non_eol_changes_rejected(self):
        raw = b'{"value": 1}\r\nsecond\r\n'
        for changed in (raw.replace(b"1", b"2"), raw.replace(b"second\r\n", b""),
                        raw.replace(b": ", b":"), raw.rstrip(), raw.replace(b"\r\n", b"\r")):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                compare_historical(changed, entry(raw))
        with self.assertRaises(ValueError):
            compare_historical(lf_bytes(raw), entry(raw, "binary"))

    def test_historical_gate_before_any_output_write(self):
        import reproduce
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source.csv").write_bytes(b"changed\n")
            write_json(root / BASELINE, {"scientific_artifact_commit": "fixture", "source_baseline_commit": "fixture",
                                        "files": {"source.csv": entry(b"original\r\n")}})
            with patch.object(reproduce, "ROOT", root), patch.object(sys, "argv", ["reproduce.py"]), \
                    patch.object(reproduce, "behavior") as behavior, patch.object(reproduce, "write_json") as writer:
                with self.assertRaisesRegex(ValueError, "source.csv"):
                    reproduce.main()
                behavior.assert_not_called()
                writer.assert_not_called()
            self.assertFalse((root / "corrections_v2/generated").exists())

    def test_inventories_no_self_reference_or_downstream_inputs(self):
        pinned = json.loads((ROOT / BASELINE).read_text())
        self.assertEqual(len(pinned["files"]), 774)
        self.assertFalse(any(p.startswith("corrections_v2/") for p in pinned["files"]))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_json(root / "corrections_v2/generated/report.json", {"x": 1})
            seal_outputs(root)
            first = (root / OUTPUT_MANIFEST).read_bytes()
            seal_outputs(root)
            self.assertEqual(first, (root / OUTPUT_MANIFEST).read_bytes())
            self.assertNotIn(OUTPUT_MANIFEST, json.loads(first)["files"])
            verify_output_inventory(root)
            write_json(root / "corrections_v2/generated/report.json", {"x": 2})
            with self.assertRaises(ValueError):
                verify_output_inventory(root)

    def test_utf8_lf_serialization_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "data.json"
            value = {"unicode": "Cléopâtre", "sentence": "one\r\ntwo"}
            write_json(path, value)
            before = path.read_bytes()
            write_json(path, value)
            self.assertEqual(before, path.read_bytes())
            self.assertNotIn(b"\r\n", before)
            self.assertIn("Cléopâtre".encode(), before)
            self.assertEqual(json.loads(before), value)  # Embedded text untouched.


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = copy.deepcopy(json.loads((ROOT / "corrections_v2/generated/rerun_manifest.json").read_text()))
        for job in self.manifest["jobs"]:
            packet = {"judge_id": job["judge_id"], "stage": job["stage"], "n_items": job["n_judgments"],
                      "item_ids": job["item_ids"], "items": [{"item_id": iid} for iid in job["item_ids"]]}
            write_json(self.root / job["packet"], packet)
            job["packet_sha256"] = digest(self.root / job["packet"])

    def deliver(self, optional=False):
        for job in self.manifest["jobs"]:
            if job["panel"] == "claude_historical_residual_optional" and not optional:
                continue
            rows = [{"item_id": iid, "judge_id": job["judge_id"], "stage": job["stage"],
                     "verdict": "Ambiguous", "evidence_sufficiency": "partial_or_ambiguous",
                     "confidence": 50, "issue_flags": ["other"], "brief_reason": "Synthetic schema fixture only."}
                    for iid in job["item_ids"]]
            write_json(self.root / job["output"], rows)

    def test_required_complete_without_optional(self):
        self.deliver()
        result, code = completion_status(self.manifest, root=self.root)
        self.assertEqual(code, 0)
        self.assertEqual(result["required_judgment_completeness"]["valid_jobs"], 70)
        self.assertEqual(result["required_judgment_completeness"]["valid_judgments"], 6430)
        self.assertEqual(result["optional_judgment_completeness"]["status"], "incomplete")
        self.assertIn("not_assessed", result["execution_provenance_completeness"])
        self.assertIn("not_computed", result["corrected_consensus_availability"])
        self.assertEqual(result["launched_by_this_command"], 0)

    def test_all_requires_optional(self):
        self.deliver()
        self.assertEqual(completion_status(self.manifest, "all", self.root)[1], 1)
        self.deliver(optional=True)
        result, code = completion_status(self.manifest, "all", self.root)
        self.assertEqual(code, 0)
        self.assertEqual(result["optional_judgment_completeness"]["valid_jobs"], 15)
        self.assertEqual(result["optional_judgment_completeness"]["valid_judgments"], 1155)

    def test_missing_required_fails(self):
        result, code = completion_status(self.manifest, root=self.root)
        self.assertEqual(code, 1)
        self.assertEqual(result["preparation_integrity"], "valid")
        self.assertEqual(result["output_schema_validity"], "no_outputs")
        self.assertEqual(len(result["required_judgment_completeness"]["missing_jobs"]), 70)

    def test_malformed_required_fails_and_optional_does_not_block_required(self):
        self.deliver(optional=True)
        optional = self.manifest["jobs"][-1]
        write_json(self.root / optional["output"], ["bad record"])
        self.assertEqual(completion_status(self.manifest, "required", self.root)[1], 0)
        self.assertEqual(completion_status(self.manifest, "all", self.root)[1], 1)
        job = self.manifest["jobs"][0]
        for bad in (["bad record"], [], [{"item_id": job["item_ids"][0], "issue_flags": [{}]}]):
            write_json(self.root / job["output"], bad)
            result, code = completion_status(self.manifest, "required", self.root)
            self.assertEqual(code, 1)
            self.assertEqual(result["output_schema_validity"], "invalid")

    def test_exact_new_packet_hashes_required(self):
        job = self.manifest["jobs"][0]
        path = self.root / job["packet"]
        data = path.read_bytes()
        for change in (data.replace(b"\n", b"\r\n"), data.replace(b'"C"', b'"B"')):
            path.write_bytes(change)
            with self.assertRaisesRegex(ValueError, "packet changed"):
                validate_packet(job, self.root)


if __name__ == "__main__":
    unittest.main()
