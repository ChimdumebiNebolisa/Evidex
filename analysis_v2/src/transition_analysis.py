"""Research question A (core paired behavior) and I (cross-model concordance).

Produces transition matrices, rescue/regression rates by gold label, and
cross-model concordance tables. Writes machine-readable CSVs in tables/.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

T4 = [config.TRANSITION_ROBUST, config.TRANSITION_RESCUE,
      config.TRANSITION_RESISTANT, config.TRANSITION_REGRESSION]


def transition_analysis():
    config.ensure_dirs()
    df = pd.read_parquet(config.PAIRED_PARQUET)

    # A1. Transition counts and rates per model.
    rows = []
    for m in config.MODELS:
        vc = df[f"{m}_transition"].value_counts()
        n = len(df)
        co_err = (df[f"{m}_claim_only_correct"] == False).sum()  # noqa: E712
        co_ok = (df[f"{m}_claim_only_correct"] == True).sum()  # noqa: E712
        rows.append({
            "model": m, "n": n,
            "robust": vc.get(config.TRANSITION_ROBUST, 0),
            "rescue": vc.get(config.TRANSITION_RESCUE, 0),
            "resistant": vc.get(config.TRANSITION_RESISTANT, 0),
            "regression": vc.get(config.TRANSITION_REGRESSION, 0),
            "rescue_rate_of_claim_only_errors": vc.get(config.TRANSITION_RESCUE, 0) / co_err,
            "regression_rate_of_claim_only_correct": vc.get(config.TRANSITION_REGRESSION, 0) / co_ok,
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(config.TABLES_DIR / "transition_summary.csv", index=False)

    # A7 + B prep. Transitions by gold label.
    by_label = []
    for m in config.MODELS:
        for lbl in config.LABELS:
            sub = df[df["gold_label"] == lbl]
            vc = sub[f"{m}_transition"].value_counts()
            by_label.append({
                "model": m, "gold_label": lbl, "n": len(sub),
                **{t: vc.get(t, 0) for t in T4},
                "regression_rate": vc.get(config.TRANSITION_REGRESSION, 0) / len(sub),
                "rescue_rate": vc.get(config.TRANSITION_RESCUE, 0) / len(sub),
            })
    pd.DataFrame(by_label).to_csv(config.TABLES_DIR / "transition_by_label.csv", index=False)

    # Direction-of-error asymmetry in the evidence condition (question B baseline).
    asym = []
    for m in config.MODELS:
        for lbl in config.LABELS:
            sub = df[df["gold_label"] == lbl]
            n_err = (sub[f"{m}_evidence_correct"] == False).sum()  # noqa: E712
            asym.append({"model": m, "gold_label": lbl,
                         "evidence_errors": n_err, "n": len(sub)})
    pd.DataFrame(asym).to_csv(config.TABLES_DIR / "evidence_error_asymmetry.csv", index=False)

    # A1/A7-complete. Full four-way tables: 2x2 claim_only-correctness x
    # evidence-correctness per model (with margins), overall and by gold label.
    fourway = []
    for m in config.MODELS:
        for lbl in [None, "Supported", "Refuted"]:
            sub = df if lbl is None else df[df["gold_label"] == lbl]
            co = sub[f"{m}_claim_only_correct"]
            ev = sub[f"{m}_evidence_correct"]
            fourway.append({
                "model": m, "gold_label": lbl or "ALL", "n": len(sub),
                "co_correct_ev_correct": int((co & ev).sum()),
                "co_correct_ev_wrong": int((co & ~ev).sum()),
                "co_wrong_ev_correct": int((~co & ev).sum()),
                "co_wrong_ev_wrong": int((~co & ~ev).sum()),
                "claim_only_correct": int(co.sum()), "claim_only_wrong": int((~co).sum()),
                "evidence_correct": int(ev.sum()), "evidence_wrong": int((~ev).sum()),
            })
    pd.DataFrame(fourway).to_csv(config.TABLES_DIR / "transition_four_way_tables.csv", index=False)

    # A4/A5/I. Cross-model transition concordance.
    ct = pd.crosstab(df["gpt-5.4_transition"], df["gpt-5.4-mini_transition"])
    ct = ct.reindex(index=T4, columns=T4, fill_value=0)
    ct.to_csv(config.TABLES_DIR / "cross_model_transition_matrix.csv")

    conc = {
        "both_robust": int((df["gpt-5.4_transition"].eq(config.TRANSITION_ROBUST) &
                            df["gpt-5.4-mini_transition"].eq(config.TRANSITION_ROBUST)).sum()),
        "both_rescued": int((df["gpt-5.4_transition"].eq(config.TRANSITION_RESCUE) &
                             df["gpt-5.4-mini_transition"].eq(config.TRANSITION_RESCUE)).sum()),
        "both_regress": int((df["gpt-5.4_transition"].eq(config.TRANSITION_REGRESSION) &
                             df["gpt-5.4-mini_transition"].eq(config.TRANSITION_REGRESSION)).sum()),
        "both_resistant": int((df["gpt-5.4_transition"].eq(config.TRANSITION_RESISTANT) &
                               df["gpt-5.4-mini_transition"].eq(config.TRANSITION_RESISTANT)).sum()),
        "one_regresss_only": int(((df["gpt-5.4_transition"].eq(config.TRANSITION_REGRESSION)) ^
                                  (df["gpt-5.4-mini_transition"].eq(config.TRANSITION_REGRESSION))).sum()),
        "agree_claim_only_pred": float(df["agree_co"].mean()),
        "agree_evidence_pred": float(df["agree_ev"].mean()),
        "agree_transition": float(df["agree_transition"].mean()),
    }
    pd.Series(conc, name="value").to_csv(config.TABLES_DIR / "cross_model_concordance.csv")

    print(summary.to_string(index=False))
    print("\nCross-model concordance:")
    for k, v in conc.items():
        print(f"  {k}: {v}")
    return df


if __name__ == "__main__":
    transition_analysis()
