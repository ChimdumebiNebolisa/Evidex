"""Post-unblinding cohort comparisons (Q1-Q10) with uncertainty.

Confirmatory family (pre-listed): Q1-Q10 contrasts from the protocol.
Exploratory: everything else. BH correction applied across the reported
family. Tests: Fisher exact (sparse cells), odds ratios with 95% CI,
percentile bootstrap CIs (2,000 iters, seed 20260822), paired McNemar for
within-claim stage changes. No causal language; stage contrasts are
within-item controlled-disclosure comparisons.
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
    for feat, tag in [("consensus_A", "Q1_stageA_ambiguous"), ("consensus_C", "Q10_stageC_ambiguous")]:
        amb = df[feat].isin(["Ambiguous", "Unresolved"])
        for name, mask in [("regression", reg), ("resistant", res), ("rescue", rsc), ("robust", rob)]:
            rate_row(f"{tag}_{name}", mask, amb)
        a, b = int((reg & amb).sum()), int((reg & ~amb).sum())
        c, d = int((rob & amb).sum()), int((rob & ~amb).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_reg_vs_robust_OR", "family": "confirmatory",
                     "n": a + b + c + d, "odds_ratio": orv, "ci_low": lo, "ci_high": hi,
                     "p_value": p})

    # Q2/Q3: resolution by titles / structure, regression vs robust.
    for feat, tag in [("resolved_by_titles", "Q2_resolved_by_titles"),
                      ("resolved_only_by_structure", "Q3_resolved_by_structure")]:
        for name, mask in [("regression", reg), ("resistant", res), ("rescue", rsc), ("robust", rob)]:
            rate_row(f"{tag}_{name}", mask, df[feat])
        a, b = int((reg & df[feat]).sum()), int((reg & ~df[feat]).sum())
        c, d = int((rob & df[feat]).sum()), int((rob & ~df[feat]).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_reg_vs_robust_OR", "family": "confirmatory",
                     "odds_ratio": orv, "ci_low": lo, "ci_high": hi, "p_value": p})

    # Q4: do resistant failures resemble regressions or robust?
    for feat, tag in [("consensus_A", "Q4a_stageA_amb"), ("still_ambiguous_after_C", "Q4b_stageC_amb")]:
        amb = df[feat] if feat in df.columns else df[feat]
        a, b = int((res & amb).sum()), int((res & ~amb).sum())
        c, d = int((rob & amb).sum()), int((rob & ~amb).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_res_vs_robust_OR", "family": "confirmatory",
                     "odds_ratio": orv, "ci_low": lo, "ci_high": hi, "p_value": p})

    # Q5: shared vs model-specific regressions: representation sensitivity.
    both = df["regression_type"] == "both"
    for feat, tag in [("resolved_by_titles", "Q5a_titles"), ("resolved_only_by_structure", "Q5b_structure"),
                      ("still_ambiguous_after_C", "Q5c_still_amb")]:
        a, b = int((both & df[feat]).sum()), int((both & ~df[feat]).sum())
        c, d = int((~both & df[feat]).sum()), int((~both & ~df[feat]).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": f"{tag}_shared_vs_specific_OR", "family": "confirmatory",
                     "odds_ratio": orv, "ci_low": lo, "ci_high": hi, "p_value": p})

    # Q6: within-GLM disagreement vs NLI disagreement (correlation).
    for nlif, tag in [("nli_disagrees", "Q6_nli1"), ("nli2_disagrees", "Q6_nli2")]:
        glm_dis = df["rule_A"] != "high_consensus"
        tab = pd.crosstab(glm_dis, df[nlif])
        chi2, p, _, _ = stats.chi2_contingency(tab.to_numpy())
        phi = np.sqrt(chi2 / len(df))
        rows.append({"analysis": f"{tag}_vs_glm_disagreement", "family": "confirmatory",
                     "chi2": chi2, "cramers_phi": phi, "p_value": p})

    # Q7: does Stage C reduce disagreement on NLI-weak cases (paired McNemar).
    from statsmodels.stats.contingency_tables import mcnemar
    weak = df["nli_disagrees"] & df["nli2_disagrees"]
    dis_a = (df.loc[weak, "rule_A"] != "high_consensus").to_numpy()
    dis_c = (df.loc[weak, "rule_C"] != "high_consensus").to_numpy()
    if dis_a.sum() + dis_c.sum() > 0:
        res_m = mcnemar([[int((dis_a & dis_c).sum()), int((dis_a & ~dis_c).sum())],
                         [int((~dis_a & dis_c).sum()), int((~dis_a & ~dis_c).sum())]],
                        exact=False, correction=True)
        rows.append({"analysis": "Q7_stageC_disagreement_on_nli_weak_mcnemar",
                     "family": "confirmatory", "n": int(weak.sum()),
                     "mcnemar_chi2": res_m.statistic, "p_value": res_m.pvalue})

    # Q8: regressions still clearly sufficient after Stage C.
    suff_clear = df["consensus_C"].isin(["Supported", "Refuted"]) & (df["rule_C"] == "high_consensus")
    rate_row("Q8_reg_clearly_warranted_after_C", reg, suff_clear)
    rate_row("Q8b_robust_clearly_warranted_after_C", rob, suff_clear)

    # Q9: representation-sensitive share among regressions.
    rep_sens = df["silver_taxonomy"].isin(
        ["silver_title_context_sensitive", "silver_structured_evidence_sensitive"])
    rate_row("Q9_reg_representation_sensitive", reg, rep_sens)
    rate_row("Q9b_res_representation_sensitive", res, rep_sens)
    rate_row("Q9c_robust_representation_sensitive", rob, rep_sens)

    # Exploratory: Supported vs Refuted contrasts.
    for lbl in config.VERDICTS[:2]:
        m = df["gold_label"] == lbl
        rate_row(f"EXPL_stageA_amb_{lbl}", m, df["consensus_A"].isin(["Ambiguous", "Unresolved"]),
                 family="exploratory")

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
