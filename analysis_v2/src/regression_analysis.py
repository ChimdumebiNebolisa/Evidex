"""Research question G: interpretable prediction of transition classes.

Logistic regression (with and without L2) and a shallow gradient-boosted tree
to predict, per model: evidence rescue, evidence-induced regression, and
evidence-resistant failure, from claim/evidence features available *before*
seeing either prediction. Grouped (claim-level) train/test split; the same
claim never crosses partitions (trivially true here since one row per claim,
but enforced via GroupKFold on claim_id anyway for future-proofing).

No feature is derived from the outcome being predicted.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

FEATURES = [
    "claim_len_words", "evidence_len_words", "claim_evidence_len_ratio",
    "claim_negation", "claim_comparative", "claim_numbers", "claim_dates",
    "claim_pronouns", "claim_modals", "claim_conjunctions",
    "evidence_negation", "evidence_numbers",
    "lexical_overlap", "jaccard_content", "numerical_overlap",
    "claim_has_date_evidence_no_date",
    "evidence_set_size", "n_evidence_sentences", "n_evidence_pages",
    "claim_entity_count", "evidence_entity_count", "entity_overlap",
    "claim_person_org_entities",
    "gold_label_refuted",
]
OPTIONAL = ["cosine_sim_claim_evidence", "nli_entailment", "nli_contradiction", "nli_neutral"]


def regression_analysis():
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    feats = [f for f in FEATURES + OPTIONAL if f in df.columns]
    X = df[feats].copy()
    X["gold_label_refuted"] = (df["gold_label"] == "Refuted").astype(int)
    X = X.fillna(X.median(numeric_only=True))
    groups = df["claim_id"].to_numpy()

    rows = []
    for model in config.MODELS:
        tcol = f"{model}_transition"
        for transition, tag in [
            (config.TRANSITION_RESCUE, "rescue"),
            (config.TRANSITION_REGRESSION, "regression"),
            (config.TRANSITION_RESISTANT, "resistant"),
        ]:
            y = (df[tcol] == transition).astype(int).to_numpy()
            n_pos = int(y.sum())
            if n_pos < 30:
                continue
            gkf = GroupKFold(n_splits=5)
            for name, clf in [
                ("logreg_l2", LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced")),
                ("logreg_strong_l2", LogisticRegression(max_iter=2000, C=0.1, class_weight="balanced")),
                ("hgb", HistGradientBoostingClassifier(max_depth=3, max_iter=150,
                                                       random_state=config.RANDOM_SEED)),
            ]:
                probs = cross_val_predict(clf, X.to_numpy(), y, groups=groups,
                                          cv=gkf, method="predict_proba")[:, 1]
                rows.append({
                    "model": model, "target": tag, "n_positive": n_pos, "classifier": name,
                    "roc_auc": roc_auc_score(y, probs),
                    "pr_auc": average_precision_score(y, probs),
                    "brier": brier_score_loss(y, probs),
                })

            # Coefficients from a single fitted L2 model for interpretability.
            lr = LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced")
            lr.fit(X.to_numpy(), y)
            coef_df = pd.DataFrame({"feature": feats, "coef": lr.coef_[0]})
            coef_df["abs_coef"] = coef_df.coef.abs()
            coef_df = coef_df.sort_values("abs_coef", ascending=False)
            coef_df.to_csv(config.TABLES_DIR / f"regression_coefs_{tag}_{model.replace('.', '_')}.csv",
                           index=False)

    res = pd.DataFrame(rows)
    res.to_csv(config.TABLES_DIR / "predictive_models.csv", index=False)
    print(res.to_string(index=False))
    return res


if __name__ == "__main__":
    regression_analysis()
