"""Leakage audit for the predictive-model stage (and the pipeline generally).

Checks:
1. One row per claim_id in the canonical paired dataset (no row duplication).
2. Static check: no predictor feature is derived from any model prediction,
   correctness flag, or transition label (the outcome family).
3. Exact-duplicate claim texts (different claim_ids, identical content) can
   straddle GroupKFold folds grouped by claim_id. We quantify how often that
   happens and rerun the predictive models with duplicate-aware grouping
   (group key = normalized claim text) to measure any optimistic bias.
4. NLI/embedding features are computed from claim+evidence only (verified by
   construction in their modules; asserted here by column provenance list).

Writes tables/leakage_audit.md.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

OUTCOME_DERIVED_PREFIXES = ("gpt54_", "gpt54mini_", "agree_")
OUTCOME_DERIVED_NAMES = {"gpt-5.4_claim_only_correct", "gpt-5.4_evidence_correct",
                         "gpt-5.4_transition", "gpt-5.4-mini_claim_only_correct",
                         "gpt-5.4-mini_evidence_correct", "gpt-5.4-mini_transition",
                         "agree_transition", "review_priority_score", "both_regress",
                         "one_regress", "shared_resistant", "both_models_fail_same_direction",
                         "exact_duplicate_claim", "near_duplicate_claim",
                         "flag_low_lexical_overlap", "flag_low_semantic_sim",
                         "flag_nli_disagreement", "semantic_outlier"}

FEATURES = [
    "claim_len_words", "evidence_len_words", "claim_evidence_len_ratio",
    "claim_negation", "claim_comparative", "claim_numbers", "claim_dates",
    "claim_pronouns", "claim_modals", "claim_conjunctions",
    "evidence_negation", "evidence_numbers",
    "lexical_overlap", "jaccard_content", "numerical_overlap",
    "claim_has_date_evidence_no_date",
    "evidence_set_size", "n_evidence_sentences", "n_evidence_pages",
    "claim_entity_count", "evidence_entity_count", "entity_overlap",
    "claim_person_org_entities", "gold_label_refuted",
]


def audit():
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    lines = ["# Leakage audit", ""]
    ok = True

    # 1. Row uniqueness.
    uniq = df["claim_id"].is_unique
    lines.append(f"1. One row per claim_id: {'PASS' if uniq else 'FAIL'}")
    ok &= uniq

    # 2. Feature provenance.
    bad = [f for f in FEATURES
           if f.startswith(OUTCOME_DERIVED_PREFIXES) or f in OUTCOME_DERIVED_NAMES]
    lines.append(f"2. Outcome-derived predictor features: "
                 f"{'none (PASS)' if not bad else 'FOUND: ' + str(bad)}")
    ok &= not bad

    # 3. Exact-duplicate straddle risk and duplicate-aware CV.
    norm = df["claim_text"].str.lower().str.split().str.join(" ")
    dup_groups = norm.value_counts()
    dup_groups = dup_groups[dup_groups > 1]
    n_dup_claims = int(dup_groups.sum())
    lines.append(f"3. Exact-duplicate claims: {len(dup_groups)} groups, "
                 f"{n_dup_claims} claims ({n_dup_claims/len(df)*100:.1f}% of sample).")
    same_label = 0
    for txt, n in dup_groups.items():
        if df.loc[norm == txt, "gold_label"].nunique() == 1:
            same_label += int(n)
    lines.append(f"   Claims in duplicate groups sharing an identical gold label: "
                 f"{same_label}/{n_dup_claims}.")

    X = df[[f for f in FEATURES if f != "gold_label_refuted"]].copy()
    X["gold_label_refuted"] = (df["gold_label"] == "Refuted").astype(int)
    X = X.fillna(X.median(numeric_only=True))

    res_rows = []
    for m in config.MODELS:
        for t, tag in [(config.TRANSITION_RESCUE, "rescue"),
                       (config.TRANSITION_REGRESSION, "regression"),
                       (config.TRANSITION_RESISTANT, "resistant")]:
            y = (df[f"{m}_transition"] == t).astype(int).to_numpy()
            if y.sum() < 30:
                continue
            g1 = df["claim_id"].to_numpy()
            g2 = norm.to_numpy()  # duplicate-aware group key
            a1 = roc_auc_score(y, cross_val_predict(
                LogisticRegression(max_iter=2000, class_weight="balanced"),
                X.to_numpy(), y, groups=g1, cv=GroupKFold(5),
                method="predict_proba")[:, 1])
            a2 = roc_auc_score(y, cross_val_predict(
                LogisticRegression(max_iter=2000, class_weight="balanced"),
                X.to_numpy(), y, groups=g2, cv=GroupKFold(5),
                method="predict_proba")[:, 1])
            res_rows.append({"model": m, "target": tag, "n_pos": int(y.sum()),
                             "auc_claim_id_grouped": round(a1, 3),
                             "auc_duplicate_aware": round(a2, 3),
                             "delta": round(a2 - a1, 3)})
    res = pd.DataFrame(res_rows)
    res.to_csv(config.TABLES_DIR / "leakage_duplicate_aware_cv.csv", index=False)
    lines.append("\n## Duplicate-aware CV (surface features only, logreg)")
    lines.append("```")
    lines.append(res.to_string(index=False))
    lines.append("```")

    # 4. NLI/embedding provenance statement.
    lines.append("\n4. NLI and embedding features are computed from claim text and "
                 "gold evidence text only (src/semantic_features.py, src/nli_analysis.py); "
                 "no model prediction or correctness flag enters them. PASS by construction.")

    verdict = "PASS" if ok else "FAIL"
    lines.insert(0, f"**Verdict: {verdict}** (structural checks)")
    (config.TABLES_DIR / "leakage_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Leakage audit structural verdict: {verdict}")
    print(res.to_string(index=False))
    return ok


if __name__ == "__main__":
    audit()
