"""Descriptive associations between features and transition classes (questions C, D, E, F).

Per model and transition class, report feature means and a Kruskal-Wallis test
across the four transition classes, with Benjamini-Hochberg correction across
features (exploratory; association only, no causal language).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

NUM_FEATS = [
    "evidence_set_size", "n_evidence_sentences", "n_evidence_pages",
    "evidence_len_words", "claim_len_words", "claim_evidence_len_ratio",
    "claim_negation", "claim_comparative", "claim_numbers", "claim_dates",
    "claim_pronouns", "claim_modals", "claim_conjunctions",
    "evidence_negation", "evidence_numbers",
    "lexical_overlap", "jaccard_content", "numerical_overlap",
    "claim_entity_count", "evidence_entity_count", "entity_overlap",
    "cosine_sim_claim_evidence", "nli_entailment", "nli_contradiction", "nli_neutral",
    "nli_disagrees_with_fever",
]


def bh_adjust(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / (np.arange(len(p)) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(ranked)
    out[order] = np.clip(ranked, 0, 1)
    return out


def feature_associations():
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    t4 = [config.TRANSITION_ROBUST, config.TRANSITION_RESCUE,
          config.TRANSITION_RESISTANT, config.TRANSITION_REGRESSION]
    out = []
    for model in config.MODELS:
        tcol = f"{model}_transition"
        for f in NUM_FEATS:
            if f not in df.columns or not pd.api.types.is_numeric_dtype(df[f]):
                continue
            groups = [df.loc[df[tcol] == t, f].dropna() for t in t4]
            if any(len(g) < 20 for g in groups):
                continue
            try:
                h, p = stats.kruskal(*groups)
            except ValueError:
                continue
            row = {"model": model, "feature": f, "kw_p": p,
                   "kw_h": h, "n": int(sum(len(g) for g in groups))}
            for t, g in zip(t4, groups):
                row[f"mean_{t}"] = g.mean()
            out.append(row)
    res = pd.DataFrame(out)
    res["kw_p_bh"] = bh_adjust(res["kw_p"].to_numpy())
    res.to_csv(config.TABLES_DIR / "feature_associations.csv", index=False)
    sig = res[res["kw_p_bh"] < 0.05]
    print(f"{len(sig)}/{len(res)} features differ across transition classes after BH correction")
    print(sig[["model", "feature", "kw_p_bh"]].to_string(index=False))
    return res


if __name__ == "__main__":
    feature_associations()
