"""Build the silver-adjudication cohort from the canonical Analysis v2 data.

Cohort (unique claims, priority assignment regression > resistant > rescue >
robust so no claim appears twice):
  - all 226 regression claims (>=1 model), flagged both/gpt54_only/mini_only
  - evidence-resistant claims (resistant for >=1 model and NOT in regression)
  - matched rescue controls (wrong_to_correct for >=1 model, not in the above)
  - matched robust controls (correct_to_correct for both models, not in above)

Controls are greedily matched without replacement to the combined
regression+resistant pool on: gold label, evidence_set_size,
n_evidence_pages, claim-length tercile, evidence-length tercile.
Outputs data/derived/cohort.parquet and tables/cohort_composition.csv,
tables/matching_balance.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def tercile(series: pd.Series) -> pd.Series:
    return pd.qcut(series.rank(method="first"), 3, labels=["short", "mid", "long"])


def match_key(row):
    return (row["gold_label"], row["evidence_set_size"], row["n_evidence_pages"],
            row["claim_tercile"], row["evidence_tercile"])


def build_cohort():
    config.ensure_dirs()
    df = pd.read_parquet(config.PAIRED_ENRICHED)

    reg54 = df["gpt-5.4_transition"] == config.T_REGRESSION
    regm = df["gpt-5.4-mini_transition"] == config.T_REGRESSION
    res54 = df["gpt-5.4_transition"] == config.T_RESISTANT
    resm = df["gpt-5.4-mini_transition"] == config.T_RESISTANT
    sc54 = df["gpt-5.4_transition"] == config.T_RESCUE
    scum = df["gpt-5.4-mini_transition"] == config.T_RESCUE
    rob = (df["gpt-5.4_transition"] == config.T_ROBUST) & \
          (df["gpt-5.4-mini_transition"] == config.T_ROBUST)

    regression = df[reg54 | regm].copy()
    regression["cohort"] = "regression"
    regression["regression_type"] = np.where(
        reg54[regression.index] & regm[regression.index], "both",
        np.where(reg54[regression.index], "gpt54_only", "mini_only"))

    taken = set(regression["claim_id"])
    resistant = df[(res54 | resm) & ~df["claim_id"].isin(taken)].copy()
    resistant["cohort"] = "resistant"
    resistant["regression_type"] = ""
    taken |= set(resistant["claim_id"])

    df["claim_tercile"] = tercile(df["claim_len_words"])
    df["evidence_tercile"] = tercile(df["evidence_len_words"])

    target = pd.concat([regression, resistant], ignore_index=False)
    target_keys = {r["claim_id"]: match_key(r) for _, r in
                   df.loc[df["claim_id"].isin(target["claim_id"])].iterrows()}
    key_counts = pd.Series([k for k in target_keys.values()]).value_counts()

    def draw_controls(pool_mask, n_want, label):
        rng = np.random.default_rng(config.RANDOM_SEED + (1 if label == "rescue" else 2))
        pool = df[pool_mask & ~df["claim_id"].isin(taken)].copy()
        pool = pool.sort_values("claim_id")
        chosen = []
        # Strata proportional to the target pool; within stratum, random draw.
        by_key = {}
        for _, r in pool.iterrows():
            by_key.setdefault(match_key(r), []).append(r["claim_id"])
        for key, want_n in key_counts.items():
            ids = by_key.get(key, [])
            rng.shuffle(ids)
            chosen.extend(ids[:int(want_n)])
        if len(chosen) < n_want:  # top up from nearest unmatched controls
            remaining = sorted(set(pool["claim_id"]) - set(chosen))
            rng.shuffle(remaining)
            chosen.extend(remaining[: n_want - len(chosen)])
        sub = df[df["claim_id"].isin(chosen[:n_want])].copy()
        sub["cohort"] = label
        sub["regression_type"] = ""
        return sub

    rescue = draw_controls(sc54 | scum, config.N_RESCUE_CONTROLS, "rescue")
    taken |= set(rescue["claim_id"])
    robust = draw_controls(rob, config.N_ROBUST_CONTROLS, "robust")

    cohort = pd.concat([regression, resistant, rescue, robust], ignore_index=True)
    keep = ["claim_id", "claim_text", "gold_label", "gold_evidence",
            "evidence_sentences_json", "evidence_pages_json", "evidence_set_size",
            "evidence_set_id", "n_evidence_sentences", "n_evidence_pages",
            "claim_len_words", "evidence_len_words", "cohort", "regression_type",
            "gpt-5.4_transition", "gpt-5.4-mini_transition",
            "gpt54_claim_only_pred", "gpt54_evidence_pred",
            "gpt54mini_claim_only_pred", "gpt54mini_evidence_pred",
            "nli_disagrees_with_fever", "nli2_disagrees_with_fever",
            "weakly_warranted", "cosine_sim_claim_evidence"]
    cohort = cohort[keep].sort_values("claim_id").reset_index(drop=True)
    cohort.to_parquet(config.COHORT_PARQUET, index=False)

    # Composition table.
    comp = cohort.groupby(["cohort", "regression_type"]).size().rename("n").reset_index()
    comp.to_csv(config.TABLES_DIR / "cohort_composition.csv", index=False)

    # Matching balance: covariate distribution target vs controls.
    bal_rows = []
    for lbl in ["regression", "resistant", "rescue", "robust"]:
        sub = cohort[cohort["cohort"] == lbl]
        bal_rows.append({
            "group": lbl, "n": len(sub),
            "pct_supported": (sub["gold_label"] == "Supported").mean(),
            "mean_evidence_set_size": sub["evidence_set_size"].mean(),
            "mean_n_pages": sub["n_evidence_pages"].mean(),
            "mean_claim_len": sub["claim_len_words"].mean(),
            "mean_evidence_len": sub["evidence_len_words"].mean(),
        })
    bal = pd.DataFrame(bal_rows)
    bal.to_csv(config.TABLES_DIR / "matching_balance.csv", index=False)

    print(comp.to_string(index=False))
    print("\nBalance:")
    print(bal.round(3).to_string(index=False))
    assert len(cohort) == cohort["claim_id"].nunique(), "duplicate claims in cohort"
    print(f"\nCohort: {len(cohort)} unique claims -> {config.COHORT_PARQUET}")
    return cohort


if __name__ == "__main__":
    build_cohort()
