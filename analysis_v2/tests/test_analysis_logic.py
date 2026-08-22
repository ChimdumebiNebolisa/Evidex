"""Tests for critical analysis logic. Run: python -m pytest tests/ (or unittest)."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config  # noqa: E402
from build_paired_dataset import transition_class  # noqa: E402
from feature_associations import bh_adjust  # noqa: E402
from linguistic_features import lex_features  # noqa: E402
from statistical_analysis import boot_ci  # noqa: E402


class TestTransitionLabeling(unittest.TestCase):
    def test_four_classes(self):
        self.assertEqual(transition_class(True, True), config.TRANSITION_ROBUST)
        self.assertEqual(transition_class(False, True), config.TRANSITION_RESCUE)
        self.assertEqual(transition_class(False, False), config.TRANSITION_RESISTANT)
        self.assertEqual(transition_class(True, False), config.TRANSITION_REGRESSION)


class TestPairingInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_parquet(config.PAIRED_PARQUET)

    def test_one_row_per_claim(self):
        self.assertEqual(len(self.df), self.df["claim_id"].nunique())

    def test_label_balance(self):
        vc = self.df["gold_label"].value_counts()
        self.assertEqual(vc["Supported"], 5000)
        self.assertEqual(vc["Refuted"], 5000)

    def test_transition_consistency(self):
        for m in config.MODELS:
            co = self.df[f"{m}_claim_only_correct"]
            ev = self.df[f"{m}_evidence_correct"]
            t = self.df[f"{m}_transition"]
            self.assertTrue(((t == config.TRANSITION_RESCUE) == (co & ~ev)).all() or
                            ((t == config.TRANSITION_RESCUE) == (~co & ev)).all())
            self.assertTrue(((t == config.TRANSITION_REGRESSION) == (co & ~ev)).all())

    def test_predictions_are_valid_labels(self):
        for c in ["gpt54_claim_only_pred", "gpt54_evidence_pred",
                  "gpt54mini_claim_only_pred", "gpt54mini_evidence_pred"]:
            self.assertTrue(set(self.df[c].unique()) <= set(config.LABELS))


class TestLexFeatures(unittest.TestCase):
    def test_overlap_and_negation(self):
        f = lex_features("The film was not released in 2010.",
                         "The film was released in 2010.")
        self.assertEqual(f["claim_negation"], 1)
        self.assertEqual(f["evidence_negation"], 0)
        self.assertGreater(f["lexical_overlap"], 0.5)
        self.assertEqual(f["numerical_overlap"], 1.0)

    def test_empty_evidence(self):
        f = lex_features("Claim.", "")
        self.assertEqual(f["evidence_len_words"], 0)
        self.assertEqual(f["numerical_overlap"], 1.0)


class TestStatsHelpers(unittest.TestCase):
    def test_boot_ci_covers_mean(self):
        vals = np.r_[np.ones(90), np.zeros(10)]
        m, lo, hi = boot_ci(vals, iters=500, seed=1)
        self.assertAlmostEqual(m, 0.9)
        self.assertLessEqual(lo, 0.9)
        self.assertGreaterEqual(hi, 0.9)

    def test_bh_adjust_monotone(self):
        p = np.array([0.01, 0.02, 0.5, 0.8])
        adj = bh_adjust(p)
        self.assertTrue((np.diff(adj[np.argsort(p)]) >= -1e-12).all())
        self.assertTrue((adj >= p - 1e-12).all())


class TestGroupIsolation(unittest.TestCase):
    def test_groupkfold_no_claim_leak(self):
        from sklearn.model_selection import GroupKFold
        rng = np.random.default_rng(0)
        claims = rng.integers(0, 500, size=2000)
        gkf = GroupKFold(n_splits=5)
        for tr, te in gkf.split(np.zeros(2000), groups=claims):
            self.assertEqual(set(claims[tr]) & set(claims[te]), set())


if __name__ == "__main__":
    unittest.main()
