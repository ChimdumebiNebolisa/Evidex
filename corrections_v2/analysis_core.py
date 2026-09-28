"""Pure offline corrected analysis. No inference, filesystem writes or fallbacks."""
from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

DECISIVE = {"Supported", "Refuted"}
LABELS = ["Supported", "Refuted", "Ambiguous", "Unresolved"]
SUFF = ["clearly_sufficient", "probably_sufficient", "partial_or_ambiguous",
        "probably_insufficient", "clearly_insufficient"]
CATEGORIES = ["sentence_only_gold_agreeing", "title_disclosure_gold_agreeing",
              "structured_disclosure_gold_agreeing", "additional_evidence_gold_agreeing",
              "nonmonotonic_judge_path", "decisive_judge_fever_disagreement", "final_nondecisive"]
BOOTSTRAPS = 2000


def consensus(rows):
    """Historical Counter tie semantics, made explicit in judge-number order.

    Ambiguous wins a modal tie ONLY when first encountered in that fixed order.
    Report every possible label under reordering without replacing the result.
    """
    if len(rows) != 5 or {r["judge_id"] for r in rows} != {f"judge_{i}" for i in range(1, 6)}:
        raise ValueError("consensus requires exactly five distinct judge slots")
    rows = sorted(rows, key=lambda r: r["judge_id"])
    counts = Counter(r["verdict"] for r in rows)
    modal, n = counts.most_common(1)[0]
    tied = [v for v in LABELS[:3] if counts[v] == n]
    weak = sum(r["evidence_sufficiency"] in SUFF[2:] for r in rows)
    decisive = max(counts["Supported"], counts["Refuted"])

    def rule(mode):
        if decisive >= 4:
            return ("Supported" if counts["Supported"] > counts["Refuted"] else "Refuted", "high_consensus")
        if mode == "Ambiguous" and n >= 2 and decisive <= 3:
            return "Ambiguous", "ambiguous_majority"
        if decisive <= 3 and weak >= 3:
            return "Ambiguous", "ambiguous_weak_sufficiency"
        return "Unresolved", "unresolved"

    label, reason = rule(modal)
    possible = sorted({rule(v)[0] for v in tied})
    return {"consensus": label, "rule": reason, "modal_verdict": modal,
            "modal_tie": len(tied) > 1, "tied_modes": tied,
            "order_sensitive_label": len(possible) > 1, "labels_under_reordering": possible,
            "judge_order": [r["judge_id"] for r in rows],
            "n_supported": counts["Supported"], "n_refuted": counts["Refuted"],
            "n_ambiguous": counts["Ambiguous"], "weak_sufficiency_n": weak,
            "mean_confidence": float(np.mean([r["confidence"] for r in rows])),
            "sd_confidence": float(np.std([r["confidence"] for r in rows])),
            "modal_sufficiency": Counter(r["evidence_sufficiency"] for r in rows).most_common(1)[0][0]}


def aggregate(rows, expected):
    grouped = {}
    seen = set()
    for r in rows:
        key = (r["item_id"], r["judge_id"])
        if key in seen:
            raise ValueError(f"duplicate judgment: {key}")
        seen.add(key)
        grouped.setdefault(r["item_id"], []).append(r)
    if set(grouped) != set(expected):
        raise ValueError("missing/unexpected items; no partial consensus")
    return {iid: consensus(grouped[iid]) for iid in sorted(expected)}


def transitions(a, b, c):
    return {"consensus_A": a, "consensus_B": b, "consensus_C": c,
            "ambiguous_A": a not in DECISIVE, "ambiguous_B": b not in DECISIVE,
            "ambiguous_C": c not in DECISIVE,
            "resolved_by_titles": a not in DECISIVE and b in DECISIVE,
            "resolved_at_C": b not in DECISIVE and c in DECISIVE,
            "still_ambiguous_after_C": c not in DECISIVE,
            "reversed_after_titles": a in DECISIVE and b in DECISIVE and a != b,
            "reversed_at_C": b in DECISIVE and c in DECISIVE and b != c,
            "change_A_B": a != b, "change_B_C": b != c, "change_A_C": a != c}


def per_judge_transitions(stages):
    indexed = {s: {(r["item_id"], r["judge_id"]): r for r in rows} for s, rows in stages.items()}
    if not (set(indexed["A"]) == set(indexed["B"]) == set(indexed["C"])):
        raise ValueError("unmatched per-judge trajectories")
    out = []
    for iid, judge in sorted(indexed["A"]):
        a, b, c = [indexed[s][iid, judge] for s in "ABC"]
        out.append({"item_id": iid, "judge_id": judge,
                    **transitions(a["verdict"], b["verdict"], c["verdict"]),
                    "confidence_delta_A_C": c["confidence"] - a["confidence"],
                    "sufficiency_improved_A_C": SUFF.index(c["evidence_sufficiency"]) < SUFF.index(a["evidence_sufficiency"])})
    return out


def agreement(rows):
    wide = pd.DataFrame(rows).pivot(index="item_id", columns="judge_id", values="verdict")
    if wide.isna().any().any() or len(wide.columns) != 5:
        raise ValueError("agreement requires complete five-judge panels")
    mat = np.array([(wide == c).sum(axis=1) for c in LABELS[:3]]).T
    n = len(wide)
    p = mat.sum(axis=0) / (5 * n)
    observed = ((mat * (mat - 1)).sum(axis=1) / 20).mean()
    expected = (p * p).sum()
    # Historical convention: agreement=1 when all ratings have one category.
    kappa = 1.0 if expected == 1 else (observed - expected) / (1 - expected)
    totals = mat.sum(axis=0)
    de = ((5 * n) ** 2 - (totals * totals).sum()) / (5 * n * (5 * n - 1))
    alpha = 1.0 if de == 0 else 1 - (1 - observed) / de
    pair = [float((wide[a] == wide[b]).mean()) for a, b in combinations(wide.columns, 2)]
    return {"n_items": n, "n_judgments": len(rows), "pairwise_agreement_mean": float(np.mean(pair)),
            "pairwise_agreement_min": min(pair), "fleiss_kappa": float(kappa),
            "krippendorff_alpha_nominal": float(alpha)}


def rate(values, seed=20260822):
    v = np.asarray(values, dtype=bool).astype(int)
    n, k = len(v), int(v.sum())
    if not n:
        return {"status": "not_estimable_empty_denominator", "n": 0, "k": 0,
                "rate_pct": None, "ci_low": None, "ci_high": None}
    rng = np.random.default_rng(seed)
    draws = rng.choice(v, size=(BOOTSTRAPS, n), replace=True).mean(axis=1)
    z, p = 1.959963985, k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"status": "estimated", "n": n, "k": k, "rate_pct": 100 * p,
            "ci_low": float(np.percentile(draws, 2.5) * 100),
            "ci_high": float(np.percentile(draws, 97.5) * 100),
            "wilson_low": max(0.0, center - half) * 100, "wilson_high": min(1.0, center + half) * 100,
            "bootstrap_iters": BOOTSTRAPS, "seed": seed}


def fisher(exposed, control, *, all_cells_floor=False):
    a, b = sum(exposed), len(exposed) - sum(exposed)
    c, d = sum(control), len(control) - sum(control)
    cells = [int(x) for x in (a, b, c, d)]
    result = {"n": sum(cells), "cells": cells, "odds_ratio": None, "ci_low": None, "ci_high": None}
    if not len(exposed) or not len(control):
        return dict(result, status="not_estimable_empty_group", p_value=None)
    result["p_value"] = float(stats.fisher_exact([[a, b], [c, d]]).pvalue)
    if not all_cells_floor and (a == 0 or c == 0):
        return dict(result, status="undefined_historical_OR_zero_event_cell")
    aa, bb, cc, dd = ([max(x, .5) for x in cells] if all_cells_floor else [a, max(b, .5), c, max(d, .5)])
    odds = (aa / bb) / (cc / dd)
    se = np.sqrt(sum(1 / max(x, .5) for x in cells))
    return dict(result, status="estimated", odds_ratio=float(odds),
                ci_low=float(np.exp(np.log(odds) - 1.96 * se)),
                ci_high=float(np.exp(np.log(odds) + 1.96 * se)))


def paired(left, right, *, exact):
    left, right = np.asarray(left, bool), np.asarray(right, bool)
    if len(left) != len(right) or not len(left):
        return {"status": "not_estimable_empty_or_unpaired", "n": len(left), "p_value": None}
    b, c = int((left & ~right).sum()), int((~left & right).sum())
    if exact:
        p, statistic = (float(stats.binomtest(b, b + c, .5).pvalue) if b + c else 1.0), None
    elif b + c:
        statistic = (abs(b - c) - 1) ** 2 / (b + c)
        p = float(stats.chi2.sf(statistic, 1))
    else:
        # Historical asymptotic formula divides by zero. Do not invent p=1.
        statistic, p = None, None
    return {"status": "estimated" if p is not None else "undefined_no_discordant_pairs",
            "n": len(left), "left_only": b, "right_only": c,
            "delta_right_minus_left_pp": float((right.mean() - left.mean()) * 100),
            "method": "exact_McNemar_binomial" if exact else "McNemar_chi2_continuity_corrected",
            "statistic": statistic, "p_value": p}


def bh(rows):
    valid = [r for r in rows if r.get("p_value") is not None]
    ordered = sorted(valid, key=lambda r: r["p_value"])
    running = 1.0
    for rank in range(len(ordered), 0, -1):
        row = ordered[rank - 1]
        running = min(running, row["p_value"] * len(ordered) / rank)
        row["p_bh"] = float(running)
        row["bh_family_size"] = len(ordered)


def cohort_statistics(df):
    """Q1-Q12 endpoints adapted explicitly to descriptive v2 categories."""
    rows = []
    masks = {c: df.cohort.eq(c) for c in ("regression", "resistant", "rescue", "robust")}
    reg, res, rob = [masks[x] for x in ("regression", "resistant", "robust")]

    def add_rate(name, mask, feature):
        rows.append({"analysis": name, "family": "post_hoc_Q1_Q12", **rate(df.loc[mask, feature])})

    def add_or(name, exposed, control, feature):
        rows.append({"analysis": name, "family": "post_hoc_Q1_Q12",
                     **fisher(df.loc[exposed, feature].tolist(), df.loc[control, feature].tolist())})

    for tag, feature in [("Q1_stageA_nondecisive", "ambiguous_A"),
                         ("Q2_title_resolution", "resolved_by_titles"), ("Q3_C_resolution", "resolved_at_C")]:
        for cohort, mask in masks.items():
            add_rate(f"{tag}_{cohort}", mask, feature)
        add_or(tag + "_reg_vs_robust_OR", reg, rob, feature)
    for tag, feature in [("Q4a_stageA_nondecisive", "ambiguous_A"), ("Q4b_stageC_nondecisive", "ambiguous_C")]:
        add_or(tag + "_resistant_vs_robust_OR", res, rob, feature)
        add_or(tag + "_resistant_vs_regression_OR", res, reg, feature)
    shared = reg & df.regression_type.eq("both")
    for feature in ("resolved_by_titles", "resolved_at_C", "ambiguous_C"):
        add_or("Q5_" + feature + "_shared_vs_specific_OR", shared, reg & ~shared, feature)
    for stage in "ABC":
        for cohort, mask in [("all", df.index.notna()), ("regression", reg)]:
            add_rate(f"Q6_stage_{stage}_{cohort}", mask, f"ambiguous_{stage}")
    for left, right in [("A", "B"), ("B", "C"), ("A", "C")]:
        rows.append({"analysis": f"Q6_{left}_{right}_McNemar", "family": "post_hoc_Q1_Q12",
                     **paired(df[f"ambiguous_{left}"], df[f"ambiguous_{right}"], exact=False)})
    for tag, feature in [("Q7", "change_A_B"), ("Q8", "change_B_C"),
                         ("Q11", "ambiguous_C")]:
        for cohort, mask in [("all", df.index.notna()), ("regression", reg)]:
            add_rate(f"{tag}_{feature}_{cohort}", mask, feature)
    df = df.copy()
    df["high_decisive_C"] = df.consensus_C.isin(DECISIVE) & df.rule_C.eq("high_consensus")
    df["gold_agreeing_C"] = df.consensus_C.eq(df.gold_label)
    df["gold_disagreeing_C"] = df.high_decisive_C & ~df.gold_agreeing_C
    for feature in ("high_decisive_C", "gold_agreeing_C", "gold_disagreeing_C"):
        for cohort in ("regression", "robust"):
            add_rate(f"Q9_{feature}_{cohort}", masks[cohort], feature)
    # No claim that additional text at C is a formatting/representation effect.
    for category in CATEGORIES[1:4]:
        df["category_event"] = df.category.eq(category)
        for cohort in ("regression", "resistant", "robust"):
            add_rate(f"Q10_{category}_{cohort}", masks[cohort], "category_event")
    for nli in ("nli_disagrees", "nli2_disagrees"):
        for stage in "AC":
            tab = pd.crosstab(df[f"ambiguous_{stage}"], df[nli]).reindex(index=[False, True], columns=[False, True], fill_value=0)
            row = {"analysis": f"Q12_{nli}_stage_{stage}", "family": "post_hoc_Q1_Q12", "n": len(df)}
            if (tab.sum(axis=0) == 0).any() or (tab.sum(axis=1) == 0).any():
                row.update(status="not_estimable_constant_margin", p_value=None)
            else:
                chi, p, _, _ = stats.chi2_contingency(tab.to_numpy())
                row.update(status="estimated", p_value=float(p), chi2=float(chi), cramers_phi=float(np.sqrt(chi / len(df))))
            rows.append(row)
    bh(rows)
    return rows


def cross_family(grok, claude):
    g = grok[grok.cohort.eq("regression")].set_index("source_item_id").sort_index()
    c = claude.set_index("source_item_id").sort_index()
    if set(g.index) != set(c.index) or g.index.has_duplicates or c.index.has_duplicates:
        raise ValueError("cross-family comparison requires identical unique regression claims")
    c = c.loc[g.index]
    rows = []
    measures = [f"ambiguous_{s}" for s in "ABC"] + ["resolved_by_titles", "resolved_at_C", "reversed_after_titles", "reversed_at_C"]
    for measure in measures:
        rows.append({"analysis": measure, "family": "post_hoc_cross_family",
                     **paired(g[measure], c[measure], exact=True)})
    for cat in CATEGORIES:
        rows.append({"analysis": "category_" + cat, "family": "post_hoc_cross_family",
                     **paired(g.category.eq(cat), c.category.eq(cat), exact=True)})
    bh(rows)
    same = g.category.eq(c.category)
    expected = sum(g.category.eq(x).mean() * c.category.eq(x).mean() for x in CATEGORIES)
    summary = {"n": len(g), "exact_taxonomy_agreement": rate(same, 20260913 + 41),
               "fine_cohen_kappa": None if expected == 1 else float((same.mean() - expected) / (1 - expected)),
               "kappa_status": "undefined_constant_margin" if expected == 1 else "estimated",
               "broad_mapping": "not_defined_for_proposed_v2; no legacy mechanism labels reused"}
    confusion = pd.crosstab(g.category, c.category).reindex(index=CATEGORIES, columns=CATEGORIES, fill_value=0)
    final = pd.crosstab(g.consensus_C, c.consensus_C).reindex(index=LABELS, columns=LABELS, fill_value=0)
    for panel, data in [("grok", g), ("claude", c)]:
        shared = data.regression_type.eq("both")
        rows.append({"analysis": panel + "_nondecisive_shared_vs_specific_OR", "family": "post_hoc_subgroup",
                     **fisher(data.loc[shared, "ambiguous_C"].tolist(), data.loc[~shared, "ambiguous_C"].tolist(), all_cells_floor=True)})
    bh([r for r in rows if r["family"] == "post_hoc_subgroup"])
    return summary, rows, confusion, final
