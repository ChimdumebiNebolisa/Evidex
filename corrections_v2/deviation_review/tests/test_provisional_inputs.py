"""Fast checks of the post-judgment deviation-review inputs. No inference, no network, no WSL.

Run: python -m unittest discover -s corrections_v2/deviation_review/tests -v
The full recomputation check is `python corrections_v2/deviation_review/provisional_analysis.py verify`.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REVIEW = Path(__file__).resolve().parents[1]
ROOT = REVIEW.parents[1]
sys.path.insert(0, str(REVIEW))
sys.path.insert(0, str(ROOT / "corrections_v2"))

import provisional_analysis as pa  # noqa: E402
from analysis_io import load_manifest  # noqa: E402


class PortabilityTests(unittest.TestCase):
    def test_no_machine_specific_paths(self):
        source = (REVIEW / "provisional_analysis.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"[A-Za-z]:\\\\?Users")
        self.assertNotRegex(source, r"import subprocess|[\"']wsl[\"']|\\\\wsl")
        self.assertNotIn("evidex_execution_records", source)

    def test_alternatives_are_tracked_repo_relative_paths(self):
        for rel, _, _ in pa.ALTERNATIVES.values():
            self.assertFalse(Path(rel).is_absolute(), rel)
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_every_combination_alternative_is_registered(self):
        needed = {(j, s) for j, slots in {**pa.BYPASSED, **pa.GROK_BYPASSED}.items() for s in slots
                  if s != pa.ACCEPTED_SLOT[j] or j in pa.BYPASSED}
        self.assertTrue(needed <= set(pa.ALTERNATIVES))


class InputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(ROOT)

    def test_all_alternatives_validate(self):
        loaded, report = pa.load_alternatives(self.manifest)
        self.assertEqual(len(loaded), 8)
        self.assertTrue(all(r["schema_valid"] for r in report))
        grok = next(r for r in report if r["job_id"] == "p01_C_j5_b09")
        self.assertEqual((grok["size"], grok["n_rows"]), (33544, 100))
        self.assertEqual(grok["sha256"], "184e3b68947ee6067258e4d1a6a72ae7b55640bd7dbcbb83733fbfadde3011e3")

    def test_altered_bytes_are_rejected(self):
        key = ("p02_C_j2_b02", 1)
        rel, size, sha = pa.ALTERNATIVES[key]
        data = bytearray((ROOT / rel).read_bytes())
        data[-2] = ord(" ") if data[-2] != ord(" ") else ord("\t")
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "altered.json"
            copy.write_bytes(bytes(data))
            with mock.patch.dict(pa.ALTERNATIVES, {key: (str(copy), size, sha)}):
                with self.assertRaises(SystemExit):
                    pa.load_alternatives(self.manifest)


class RecoveredOutputTests(unittest.TestCase):
    def test_recovered_files_match_manifest_and_are_unrepaired(self):
        manifest = json.loads((REVIEW / "evidence/recovered_wsl_outputs/manifest.json").read_text(encoding="utf-8"))
        recorded = {(u["job_id"], u["attempt"]): u for u in
                    json.loads((REVIEW / "evidence/unstaged_failed_outputs.json").read_text(encoding="utf-8"))}
        self.assertEqual(len(manifest["files"]), 3)
        for entry in manifest["files"]:
            data = (ROOT / entry["path"]).read_bytes()
            expected = recorded[(entry["job_id"], entry["attempt"])]
            self.assertEqual(len(data), expected["size"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected["sha256"])
            self.assertFalse(entry["contents_repaired"])
            if not expected["schema_valid"]:
                with self.assertRaises(ValueError):
                    json.loads(data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
