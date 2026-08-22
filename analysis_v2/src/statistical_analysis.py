"""Confirmatory paired statistics.

- McNemar tests for the evidence effect per model (rescue vs regression discordance).
- Bootstrap CIs for transition rates and evidence gain.
- Model x model transition-rate comparisons (two-proportion z with continuity fix
  replaced by chi-square on the discordant pairs).
- Label asymmetry tests (Supported vs Refuted error direction, per model).
- Cohen's kappa for cross-model prediction agreement.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.inter_rater import cohens_kappa

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

rng = np.random.default_rng(config.RANDOM_SEED)


def boot_ci(values, stat=np.mean, iters=config.BOOTSTRAP_ITERS, seed=config.RANDOM_SEED):
    """Percentile bootstrap CI for a statistic of an array of 0/1 (or numeric) values."""
    r = np.random.default_rng(seed)
    vals = np.asarray(values)
    stats_ = np.array([stat(r.choice(vals, size=len(vals), replace=True)) for _ in range(iters)])
    return stat(vals), np.percentile(stats_, 2.5), np.percentile(stats_, 97.5)


def mcnemar_evidence_effect(df, model):
    """McNemar on paired correctness: claim_only vs claim_plus_evidence."""
    co = df[f"{model}_claim_only_correct"].to_numpy()
    ev = df[f"{model}_evidence_correct"].to_numpy()
    b = int((co & ~ev).sum())  # correct -> wrong (regression)
    c = int((~co & ev).sum())  # wrong -> correct (rescue)
    res = mcnemar([[int((co & ev).sum()), b], [c, int((~co & ~ev).sum())],], exact=False, correction=True)
    return b, c, res.statistic, res.pvalue


def run():
    config.ensure_dirs()
    df = pd.read_parquet(config.PAIRED_PARQUET)
    out = []

    # 1. McNemar per model (confirmatory).
    for m in config.MODELS:
        b, c, stat_, p = mcnemar_evidence_effect(df, m)
        acc_gain = df[f"{m}_evidence_correct"].mean() - df[f"{m}_claim_only_correct"].mean()
        gain_s, gain_lo, gain_hi = boot_ci(
            df[f"{m}_evidence_correct"].astype(int) - df[f"{m}_claim_only_correct"].astype(int)
        )
        reg_rate = (df[f"{m}_transition"] == config.TRANSITION_REGRESSION).mean()
        rr, rl, rh = boot_ci((df[f"{m}_transition"] == config.TRANSITION_REGRESSION).astype(int))
        resc_rate = (df[f"{m}_transition"] == config.TRANSITION_RESCUE).mean()
        sr, sl, sh = boot_ci((df[f"{m}_transition"] == config.TRANSITION_RESCUE).astype(int))
        out.append({
            "analysis": "mcnemar_evidence_effect", "model": m,
            "regressions(b)": b, "rescues(c)": c,
            "mcnemar_chi2": stat_, "p_value": p,
            "accuracy_gain_pp": acc_gain * 100,
            "gain_ci": f"[{gain_lo*100:.2f}, {gain_hi*100:.2f}]",
            "regression_rate": reg_rate, "regression_ci": f"[{rl*100:.2f}, {rh*100:.2f}]",
            "rescue_rate": resc_rate, "rescue_ci": f"[{sl*100:.2f}, {sh*100:.2f}]",
        })

    # 2. Transition-rate differences between models.
    # The two models are evaluated on the SAME claims, so these are paired
    # comparisons: McNemar on the discordant pairs of each transition indicator
    # (NOT an independent-samples chi-square).
    for t in ["wrong_to_correct", "correct_to_wrong", "wrong_to_wrong"]:
        a = (df[f"gpt-5.4_transition"] == t).to_numpy()
        b = (df[f"gpt-5.4-mini_transition"] == t).to_numpy()
        n01 = int((~a & b).sum())  # mini only
        n10 = int((a & ~b).sum())  # gpt-5.4 only
        res = mcnemar([[int((a & b).sum()), n10], [n01, int((~a & ~b).sum())]],
                      exact=False, correction=True)
        out.append({"analysis": "model_diff_transition_paired_mcnemar", "transition": t,
                    "gpt54_n": int(a.sum()), "mini_n": int(b.sum()),
                    "discordant_gpt54_only": n10, "discordant_mini_only": n01,
                    "mcnemar_chi2": res.statistic, "p_value": res.pvalue})

    # 3. Label asymmetry: error direction in evidence condition per model per gold label.
    for m in config.MODELS:
        for lbl in config.LABELS:
            sub = df[df["gold_label"] == lbl]
            for t in ["correct_to_wrong", "wrong_to_wrong", "wrong_to_correct"]:
                rate = (sub[f"{m}_transition"] == t).mean()
                r, lo, hi = boot_ci((sub[f"{m}_transition"] == t).astype(int),
                                    seed=config.RANDOM_SEED + hash((m, lbl, t)) % 10000)
                out.append({"analysis": "transition_by_label", "model": m, "gold_label": lbl,
                            "transition": t, "n": len(sub), "rate": rate,
                            "ci": f"[{lo*100:.2f}, {hi*100:.2f}]"})
        # Per-model label contrast on regression rate (confirmatory, 2x2 chi2).
        sup = df[df["gold_label"] == "Supported"]
        ref = df[df["gold_label"] == "Refuted"]
        r_sup = int((sup[f"{m}_transition"] == config.TRANSITION_REGRESSION).sum())
        r_ref = int((ref[f"{m}_transition"] == config.TRANSITION_REGRESSION).sum())
        chi2, p = stats.chi2_contingency(
            [[r_sup, len(sup) - r_sup], [r_ref, len(ref) - r_ref]])[:2]
        out.append({"analysis": "regression_label_contrast", "model": m,
                    "regress_Supported": r_sup, "regress_Refuted": r_ref,
                    "chi2": chi2, "p_value": p})

    # 4. Cross-model agreement: Cohen's kappa on predictions.
    for cond, col_a, col_b in [
        ("claim_only", "gpt54_claim_only_pred", "gpt54mini_claim_only_pred"),
        ("claim_plus_evidence", "gpt54_evidence_pred", "gpt54mini_evidence_pred"),
    ]:
        tab = pd.crosstab(df[col_a], df[col_b]).reindex(
            index=config.LABELS, columns=config.LABELS, fill_value=0)
        k = cohens_kappa(tab.to_numpy())
        out.append({"analysis": "cohens_kappa", "condition": cond,
                    "kappa": k.kappa, "agree_rate": float((df[col_a] == df[col_b]).mean())})

    res = pd.DataFrame(out)
    res.to_csv(config.TABLES_DIR / "statistical_tests.csv", index=False)
    with pd.option_context("display.max_columns", None, "display.width", 250):
        print(res.to_string(index=False))
    return res


if __name__ == "__main__":
    run()
