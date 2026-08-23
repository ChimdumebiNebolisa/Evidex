"""Post-unblinding cohort comparisons (Q1-Q12) with uncertainty.

Confirmatory family (pre-listed): the 12 protocol questions. Exploratory:
everything else. BH correction applied across the reported family. Tests:
Fisher exact, odds ratios with 95% CI, percentile bootstrap CIs
(2,000 iters, seed 20260822), paired McNemar for within-claim stage changes.

Cursor A/B/C numbers are within-Cursor-panel progressive disclosure.
GLM Stage A is not mixed into A->B->C transition math.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def bh_adjust(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / (np.arange(len(p)) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(ranked)
    out[order] = np.clip(ranked, 0, 1)
    return out


def boot_rate_ci(mask: pd.Series, seed_offset=0):
    v = mask.astype(int).to_numpy()
    r = np.random.default_rng(config.RANDOM_SEED + seed_offset)
    stats_ = [r.choice(v, size=len(v), replace=True).mean() for _ in range(config.BOOTSTRAP_ITERS)]
    return v.mean() * 100, np.percentile(stats_, 2.5) * 100, np.percentile(stats_, 97.5) * 100


def fisher_or(a, b, c, d):
    """a=exposed+event, b=exposed no event, c=control event, d=control no event."""
    orv = (a / max(b, 0.5)) / (c / max(d, 0.5))
    table = np.array([[a, b], [c, d]])
    _, p = stats.fisher_exact(table)
    se = np.sqrt(1 / max(a, 0.5) + 1 / max(b, 0.5) + 1 / max(c, 0.5) + 1 / max(d, 0.5))
    return orv, np.exp(np.log(orv) - 1.96 * se), np.exp(np.log(orv) + 1.96 * se), p


def _amb(series: pd.Series) -> pd.Series:
    return series.isin(["Ambiguous", "Unresolved"])


def compare_cohorts():
    df = pd.read_parquet(config.UNBLINDED_PARQUET)
    rows = []

    def rate_row(tag, mask, feature, seed_offset=0, family="confirmatory"):
        sub = df[mask]
        m, lo, hi = boot_rate_ci(sub[feature], seed_offset)
        rows.append({"analysis": tag, "family": family, "n": len(sub), "rate_pct": m,
                     "ci_low": lo, "ci_high": hi})

    reg = df["cohort"] == "regression"
    res = df["cohort"] == "resistant"
    rsc = df["cohort"] == "rescue"
    rob = df["cohort"] == "robust"

    # Q1: Stage A ambiguity, regression vs robust.
    amb_a = _amb(df["consensus_A"])
    for name, mask in [("regression", reg), ("resistant", res), ("rescue", rsc), ("robust", rob)]:
        rate_row(f"Q1_stageA_ambiguous_{name}", mask, amb_a)
    a, b = int((reg & amb_a).sum()), int((reg & ~amb_a).sum())
    c, d = int((rob & amb_a).sum()), int((rob & ~amb_a).sum())
    orv, lo, hi, p = fisher_or(a, b, c, d)
    rows.append({"analysis": "Q1_stageA_ambiguous_reg_vs_robust_OR", "family": "confirmatory",
                 "n": a + b + c + d, "odds_ratio": orv, "ci_low": lo, "ci_high": hi,
                 "p_value": p})

    # Q2/Q3: titles / structured evidence resolve regressions vs robust.
    for feat, tag in [("resolved_by_titles", "Q2_resolved_by_titles"),
                      ("resolved_only_by_structure", "Q3_resolved_by_structure")]:
        for name, mask in [("regression", reg), ("resistant", res), ("rescue", rsc), ("robust", rob)]:
            rate_row(f"{tag}_{name}", mask, df[feat])
        a, b = int((reg & df[feat]).sum()), int((reg & ~df[feat]).sum())
        c, d = int((rob & df[feat]).sum()), int((rob & ~df[feat]).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_reg_vs_robust_OR", "family": "confirmatory",
                     "n": a + b + c + d, "odds_ratio": orv, "ci_low": lo, "ci_high": hi,
                     "p_value": p})

    # Q4: do resistant failures resemble regressions (vs robust)?
    amb_c = _amb(df["consensus_C"])
    for feat, tag in [(amb_a, "Q4a_stageA_amb"), (df["still_ambiguous_after_C"], "Q4b_stageC_amb")]:
        a, b = int((res & feat).sum()), int((res & ~feat).sum())
        c, d = int((rob & feat).sum()), int((rob & ~feat).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_res_vs_robust_OR", "family": "confirmatory",
                     "n": a + b + c + d, "odds_ratio": orv, "ci_low": lo, "ci_high": hi,
                     "p_value": p})
        a, b = int((res & feat).sum()), int((res & ~feat).sum())
        c, d = int((reg & feat).sum()), int((reg & ~feat).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_res_vs_reg_OR", "family": "confirmatory",
                     "n": a + b + c + d, "odds_ratio": orv, "ci_low": lo, "ci_high": hi,
                     "p_value": p})

    # Q5: shared vs model-specific regressions: representation sensitivity.
    both = df["regression_type"] == "both"
    in_reg = reg
    for feat, tag in [("resolved_by_titles", "Q5a_titles"),
                      ("resolved_only_by_structure", "Q5b_structure"),
                      ("still_ambiguous_after_C", "Q5c_still_amb")]:
        a, b = int((both & df[feat]).sum()), int((both & ~df[feat]).sum())
        spec = in_reg & ~both
        c, d = int((spec & df[feat]).sum()), int((spec & ~df[feat]).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_shared_vs_specific_OR", "family": "confirmatory",
                     "n": a + b + c + d, "odds_ratio": orv, "ci_low": lo, "ci_high": hi,
                     "p_value": p})

    # Q6: ambiguity decline A -> B -> C (within-Cursor-panel).
    amb_b = _amb(df["consensus_B"])
    for stage, amb in [("A", amb_a), ("B", amb_b), ("C", amb_c)]:
        rate_row(f"Q6_ambiguous_stage_{stage}_all", df.index.notna(), amb)
        rate_row(f"Q6_ambiguous_stage_{stage}_regression", reg, amb)
    from statsmodels.stats.contingency_tables import mcnemar
    for left, right, tag in [(amb_a, amb_b, "Q6_A_to_B"), (amb_b, amb_c, "Q6_B_to_C"),
                             (amb_a, amb_c, "Q6_A_to_C")]:
        table = [[int((left & right).sum()), int((left & ~right).sum())],
                 [int((~left & right).sum()), int((~left & ~right).sum())]]
        res_m = mcnemar(table, exact=False, correction=True)
        rows.append({"analysis": f"{tag}_ambiguity_mcnemar", "family": "confirmatory",
                     "n": len(df), "mcnemar_chi2": res_m.statistic, "p_value": res_m.pvalue})

    # Q7/Q8: consensus verdict changes A->B and B->C.
    change_ab = df["consensus_A"] != df["consensus_B"]
    change_bc = df["consensus_B"] != df["consensus_C"]
    rate_row("Q7_consensus_change_A_to_B_all", df.index.notna(), change_ab)
    rate_row("Q7_consensus_change_A_to_B_regression", reg, change_ab)
    rate_row("Q8_consensus_change_B_to_C_all", df.index.notna(), change_bc)
    rate_row("Q8_consensus_change_B_to_C_regression", reg, change_bc)

    # Q9: regressions still clearly warranted after Stage C.
    suff_clear = df["consensus_C"].isin(["Supported", "Refuted"]) & (df["rule_C"] == "high_consensus")
    rate_row("Q9_reg_clearly_warranted_after_C", reg, suff_clear)
    rate_row("Q9b_robust_clearly_warranted_after_C", rob, suff_clear)

    # Q10: representation-sensitive share among regressions.
    rep_sens = df["silver_taxonomy"].isin(
        ["silver_title_context_sensitive", "silver_structured_evidence_sensitive"])
    rate_row("Q10_reg_representation_sensitive", reg, rep_sens)
    rate_row("Q10b_res_representation_sensitive", res, rep_sens)
    rate_row("Q10c_robust_representation_sensitive", rob, rep_sens)

    # Q11: residual partial/ambiguous after Stage C.
    rate_row("Q11_reg_still_ambiguous_after_C", reg, df["still_ambiguous_after_C"])
    rate_row("Q11b_all_still_ambiguous_after_C", df.index.notna(), df["still_ambiguous_after_C"])

    # Q12: Cursor silver ambiguity vs the two local NLI diagnostics.
    cursor_amb_c = amb_c
    for nlif, tag in [("nli_disagrees", "Q12_nli1"), ("nli2_disagrees", "Q12_nli2")]:
        tab = pd.crosstab(cursor_amb_c, df[nlif])
        chi2, p, _, _ = stats.chi2_contingency(tab.to_numpy())
        phi = np.sqrt(chi2 / len(df))
        rows.append({"analysis": f"{tag}_vs_cursor_stageC_ambiguity", "family": "confirmatory",
                     "n": len(df), "chi2": chi2, "cramers_phi": phi, "p_value": p})
        tab_a = pd.crosstab(amb_a, df[nlif])
        chi2a, pa, _, _ = stats.chi2_contingency(tab_a.to_numpy())
        phia = np.sqrt(chi2a / len(df))
        rows.append({"analysis": f"{tag}_vs_cursor_stageA_ambiguity", "family": "confirmatory",
                     "n": len(df), "chi2": chi2a, "cramers_phi": phia, "p_value": pa})

    out = pd.DataFrame(rows)
    ps = out["p_value"].dropna()
    if len(ps):
        out.loc[out["p_value"].notna(), "p_bh"] = bh_adjust(ps.to_numpy())
    out.to_csv(config.TABLES_DIR / "statistical_tests.csv", index=False)
    with pd.option_context("display.max_columns", None, "display.width", 250):
        print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    compare_cohorts()
