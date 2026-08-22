"""Export the high-value manual review cohort (CSV for human annotation).

Priority scoring: both-model regressions > one-model regression >
shared resistant failures > NLI disagreement > semantic outliers >
coreference/title-loss proxies (multi-sentence/multi-page evidence, pronouns) >
suspicious label/evidence flags. Human judgment fields are left blank.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def provisional_category(row):
    cats = []
    if row.get("both_regress"):
        cats.append("shared_regression")
    if row.get("nli_disagrees_with_fever") and row.get("nli_margin", 1) < 0.3:
        cats.append("weakly_warranted_or_ambiguous")
    if row.get("n_evidence_sentences", 1) >= 2 or row.get("n_evidence_pages", 1) >= 2:
        cats.append("multi_sentence_integration_or_title_context")
    if row.get("claim_pronouns", 0) >= 1:
        cats.append("possible_coreference_or_title_loss")
    if row.get("claim_numbers", 0) > 0 or row.get("claim_comparative", 0) > 0:
        cats.append("numerical_or_comparative_reasoning")
    if row.get("claim_negation", 0) >= 1:
        cats.append("negation_or_scope")
    if row.get("flag_low_semantic_sim") or row.get("flag_low_lexical_overlap"):
        cats.append("possible_representation_failure")
    if row.get("both_models_fail_same_direction"):
        cats.append("possible_benchmark_annotation_issue")
    return ";".join(cats) if cats else "unexplained"


def export_manual_review(n=250):
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    df["both_regress"] = ((df["gpt-5.4_transition"] == config.TRANSITION_REGRESSION) &
                          (df["gpt-5.4-mini_transition"] == config.TRANSITION_REGRESSION))
    df["one_regress"] = ((df["gpt-5.4_transition"] == config.TRANSITION_REGRESSION) ^
                         (df["gpt-5.4-mini_transition"] == config.TRANSITION_REGRESSION))
    df["shared_resistant"] = ((df["gpt-5.4_transition"] == config.TRANSITION_RESISTANT) &
                              (df["gpt-5.4-mini_transition"] == config.TRANSITION_RESISTANT))

    score = (
        8 * df["both_regress"]
        + 6 * df["one_regress"]
        + 4 * df["shared_resistant"]
        + 3 * df.get("nli_disagrees_with_fever", False).astype(int)
        + 2 * df.get("semantic_outlier", False).astype(int)
        + 2 * df.get("both_models_fail_same_direction", False).astype(int)
        + (df.get("n_evidence_sentences", 1) >= 2).astype(int)
        + (df.get("claim_pronouns", 0) >= 1).astype(int)
    )
    df["review_priority_score"] = score
    cand = df[score > 0].sort_values("review_priority_score", ascending=False)
    if len(cand) < n:  # top up with random low-score rows to reach n
        rest = df[score == 0].sample(n=n - len(cand), random_state=config.RANDOM_SEED)
        cand = pd.concat([cand, rest])

    out = cand.head(n).copy()
    export_cols = {
        "claim_id": "claim_id", "claim_text": "claim", "gold_label": "fever_label",
        "gold_evidence": "evidence",
        "n_evidence_pages": "evidence_page_count",
        "evidence_set_size": "evidence_set_size",
        "gpt54_claim_only_pred": "gpt54_claim_only_pred",
        "gpt54_evidence_pred": "gpt54_evidence_pred",
        "gpt54_transition": "gpt54_transition",
        "gpt54mini_claim_only_pred": "gpt54mini_claim_only_pred",
        "gpt54mini_evidence_pred": "gpt54mini_evidence_pred",
        "gpt54mini_transition": "gpt54mini_transition",
        "nli_entailment": "nli_entailment", "nli_contradiction": "nli_contradiction",
        "nli_neutral": "nli_neutral",
        "cosine_sim_claim_evidence": "semantic_similarity",
        "review_priority_score": "priority_score",
    }
    res = out.rename(columns=export_cols)
    res["linguistic_flags"] = out.apply(lambda r: ";".join(
        f for f, cond in [
            ("negation", r.get("claim_negation", 0) > 0),
            ("numbers", r.get("claim_numbers", 0) > 0),
            ("dates", r.get("claim_dates", 0) > 0),
            ("pronouns", r.get("claim_pronouns", 0) > 0),
            ("comparative", r.get("claim_comparative", 0) > 0),
            ("multi_sentence_evidence", r.get("n_evidence_sentences", 1) > 1),
        ] if cond), axis=1)
    res["proposed_diagnostic_category"] = out.apply(provisional_category, axis=1)
    res["human_category"] = ""
    res["human_evidence_sufficient"] = ""
    res["human_label_agree"] = ""
    res["human_notes"] = ""
    keep = [v for v in export_cols.values()] + [
        "evidence_pages_json", "linguistic_flags", "proposed_diagnostic_category",
        "human_category", "human_evidence_sufficient", "human_label_agree", "human_notes",
    ]
    keep = [k for k in keep if k in res.columns]
    res[keep].to_csv(config.MANUAL_REVIEW_CSV, index=False)
    print(f"Manual review cohort: {len(res)} rows -> {config.MANUAL_REVIEW_CSV}")
    print("composition:",
          f"both_regress={int(out['both_regress'].sum())}, "
          f"one_regress={int(out['one_regress'].sum())}, "
          f"shared_resistant={int(out['shared_resistant'].sum())}")


if __name__ == "__main__":
    export_manual_review()
