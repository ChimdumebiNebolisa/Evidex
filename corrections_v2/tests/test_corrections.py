import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "silver_adjudication_v1/src"))
from fever_evidence import evidence_set_id, selected_evidence_set, sentence_text_from_lines
from reconstruct_evidence import reconstruct, normalized_page
from resolve_gold_evidence import parse_evidence_sets
from taxonomy_legacy_v1 import taxonomy_row
from taxonomy_v2 import classify


def fixture():
    raw = [[[1, 2, "Cafe\u0301", 2], [1, 2, "Other", 0]],
           [[1, 3, "Cafe\u0301", 3]], [[1, 4, "Missing", 0]],
           [[2, 2, "Cafe\u0301", 2], [2, 2, "Other", 0]]]
    sets = parse_evidence_sets(json.dumps(raw))
    row = {"claim_text": "A claim", "raw_evidence": json.dumps(raw),
           "evidence_set_id": evidence_set_id(sets[0]),
           "evidence_pages_json": json.dumps(["Caf\u00e9", "Other"]),
           "evidence_sentences_json": json.dumps(["First.", "Second."]),
           "gold_evidence": "First. Second."}
    a = {"item_id": "T1", "claim": "A claim", "evidence_sentences": "First. Second."}
    pages = {"Caf\u00e9": "2\tFirst.\tanchor\tTarget\n3\tAlternative.", "Other": "0\tSecond."}
    return row, a, pages


class EvidenceTests(unittest.TestCase):
    def test_link_fields_not_sentence(self):
        line = "19\tAn entire sentence about Neil Gaiman.\tNeil Gaiman\tNeil Gaiman"
        self.assertEqual(line.split("\t")[-1], "Neil Gaiman")  # legacy defect
        self.assertEqual(sentence_text_from_lines(line, 19), "An entire sentence about Neil Gaiman.")
        self.assertIsNone(sentence_text_from_lines("0", 0))
        self.assertIsNone(sentence_text_from_lines("0\t", 0))
        self.assertIsNone(sentence_text_from_lines(line, 3))
        self.assertEqual(sentence_text_from_lines("0\ttext\r\n1\tnext", 0), "text")

    def test_selected_id_order_unicode_and_boundaries(self):
        row, a, pages = fixture()
        b, c, check = reconstruct(row, a, pages)
        self.assertEqual(normalized_page("Cafe\u0301"), "Caf\u00e9")
        self.assertEqual(b["page_titles"], ["Cafe\u0301", "Other"])
        s = c["structured_evidence"]
        self.assertEqual([x["sentence"] for x in s["chosen_set"]], ["First.", "Second."])
        self.assertEqual([x["line_index"] for x in s["chosen_set"]], [2, 0])
        self.assertEqual(s["alternative_annotation_indices"], [1, 2, 3])
        self.assertEqual(s["alternative_full_text_available"], [True, False, True])
        self.assertEqual(s["alternative_sets"][2], s["chosen_set"])
        self.assertTrue(any(x["status"] == "missing_page" and x["role"] == "alternative" for x in check))

    def test_missing_chosen_uses_only_exact_original_text(self):
        row, a, pages = fixture()
        del pages["Other"]
        _, c, checks = reconstruct(row, a, pages)
        self.assertFalse(c["structured_evidence"]["chosen_archive_text_available"])
        self.assertEqual(c["structured_evidence"]["chosen_set"][1]["sentence"], "Second.")
        self.assertTrue(any(x["status"] == "missing_page_using_original_selected_text" for x in checks))

    def test_archive_conflict_fails(self):
        row, a, pages = fixture()
        pages["Other"] = "0\tDifferent text."
        with self.assertRaisesRegex(ValueError, "canonical_text_conflict"):
            reconstruct(row, a, pages)

    def test_never_guess_shortest_or_same_page_set(self):
        row, _, _ = fixture()
        sets = parse_evidence_sets(row["raw_evidence"])
        with self.assertRaisesRegex(ValueError, "identity_unavailable"):
            selected_evidence_set(sets, "missing", ["Caf\u00e9", "Other"], ["First.", "Second."])
        with self.assertRaisesRegex(ValueError, "order_or_length"):
            selected_evidence_set(sets, row["evidence_set_id"], ["Other", "Caf\u00e9"], ["Second.", "First."])
        # Same page and same length, different line; ID must select the latter.
        s = [{"set_index": 0, "pointers": [("Page", 0)]}, {"set_index": 1, "pointers": [("Page", 1)]}]
        self.assertEqual(selected_evidence_set(s, evidence_set_id(s[1]), ["Page"], ["Text"]), s[1])

    def test_real_emperor_norton(self):
        import pandas as pd
        old = json.loads((ROOT / "silver_adjudication_v1/data/blinded/stage_c.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(old["item_id"], "SA-000001")
        self.assertEqual(old["structured_evidence"]["chosen_set"][0]["sentence"], "Neil Gaiman")
        row = pd.read_csv(ROOT / "experiment_tracker_with_evidence_balanced_10000_v1.csv").set_index("claim_id").loc[42669].to_dict()
        text = json.loads(row["evidence_sentences_json"])[0]
        a = {k: old[k] for k in ("item_id", "claim", "evidence_sentences")}
        _, c, _ = reconstruct(row, a, {"Emperor_Norton": "19\t" + text + "\tNeil Gaiman\tNeil Gaiman"})
        self.assertEqual(c["structured_evidence"]["chosen_set"][0]["sentence"], text)
        self.assertNotEqual(text, "Neil Gaiman")

    def test_real_singapore_airlines(self):
        import pandas as pd
        old = json.loads((ROOT / "silver_adjudication_v1/data/blinded/stage_c.jsonl").read_text(encoding="utf-8").splitlines()[1])
        self.assertEqual(old["item_id"], "SA-000002")
        self.assertEqual(old["structured_evidence"]["chosen_set"][0]["sentence"], "Singapore Airlines")
        row = pd.read_csv(ROOT / "experiment_tracker_with_evidence_balanced_10000_v1.csv").set_index("claim_id").loc[104811].to_dict()
        text = json.loads(row["evidence_sentences_json"])[0]
        pointer = old["structured_evidence"]["chosen_set"][0]
        a = {k: old[k] for k in ("item_id", "claim", "evidence_sentences")}
        pages = {normalized_page(pointer["page_title"]): str(pointer["line_index"]) + "\t" + text + "\tSingapore Airlines\tSingapore Airlines"}
        _, c, _ = reconstruct(row, a, pages)
        self.assertEqual(c["structured_evidence"]["chosen_set"][0]["sentence"], text)

    def test_real_historical_cache_and_local_snapshot(self):
        snapshot = ROOT / "corrections_v2/inputs/historical_pages.json"
        pages = json.loads(snapshot.read_text(encoding="utf-8"))
        old = json.loads((ROOT / "silver_adjudication_v1/data/blinded/stage_c.jsonl").read_text(encoding="utf-8").splitlines()[0])
        pointer = old["structured_evidence"]["chosen_set"][0]
        actual = sentence_text_from_lines(pages[normalized_page(pointer["page_title"])], pointer["line_index"])
        self.assertEqual(actual, old["evidence_sentences"])
        self.assertNotEqual(actual, pointer["sentence"])


class TaxonomyTests(unittest.TestCase):
    def classify(self, a, b, c, gold="Supported", adds=False):
        return classify(a, b, c, gold, "regression", c_adds_text=adds, input_version="test")

    def test_disagreement_not_utilization(self):
        from corrections_v2.reproduce import flags
        old = taxonomy_row(flags("Refuted", "Refuted", "Refuted"))
        self.assertEqual(old, "silver_clear_evidence_utilization_failure")
        new = self.classify("Refuted", "Refuted", "Refuted")
        self.assertEqual(new["category"], "decisive_judge_fever_disagreement")
        self.assertFalse(new["sentence_only_utilization_compatible"])

    def test_titles_not_absorbed_by_c(self):
        from corrections_v2.reproduce import flags
        self.assertEqual(taxonomy_row(flags("Ambiguous", "Supported", "Supported")), "silver_structured_evidence_sensitive")
        result = self.classify("Ambiguous", "Supported", "Supported", adds=True)
        self.assertEqual(result["category"], "title_disclosure_gold_agreeing")
        self.assertEqual(result["first_decisive_stage"], "B")

    def test_c_does_not_establish_a_sufficiency(self):
        result = self.classify("Ambiguous", "Unresolved", "Supported", adds=True)
        self.assertEqual(result["category"], "additional_evidence_gold_agreeing")
        self.assertFalse(result["sentence_only_utilization_compatible"])
        self.assertIsNone(result["agrees_fever_A"])
        self.assertEqual(self.classify("Ambiguous", "Unresolved", "Supported")["category"], "structured_disclosure_gold_agreeing")

    def test_nonmonotonic_and_nondecisive(self):
        self.assertEqual(self.classify("Supported", "Refuted", "Supported")["category"], "nonmonotonic_judge_path")
        self.assertEqual(self.classify("Supported", "Unresolved", "Supported")["category"], "nonmonotonic_judge_path")
        result = self.classify("Supported", "Supported", "Unresolved")
        self.assertEqual(result["category"], "final_nondecisive")
        self.assertTrue(result["sentence_only_utilization_compatible"])
        with self.assertRaises(ValueError):
            self.classify("missing", "Supported", "Supported")

    def test_actual_frozen_disagreements(self):
        import pandas as pd
        sv = ROOT / "silver_adjudication_v1"
        for path, column, expected in [
            (sv / "cursor_panel/freezes/silver_unblinded.parquet", "silver_taxonomy", 36),
            (sv / "claude_full_regression_panel/freezes/claude_full_unblinded.parquet", "claude_taxonomy", 46),
        ]:
            df = pd.read_parquet(path)
            rows = df[(df.cohort == "regression") & (df[column] == "silver_clear_evidence_utilization_failure") & (df.consensus_C != df.gold_label)]
            self.assertEqual(len(rows), expected)
            for row in rows.to_dict("records"):
                result = self.classify(row["consensus_A"], row["consensus_B"], row["consensus_C"], gold=row["gold_label"])
                self.assertEqual(result["category"], "decisive_judge_fever_disagreement")


if __name__ == "__main__":
    unittest.main()
