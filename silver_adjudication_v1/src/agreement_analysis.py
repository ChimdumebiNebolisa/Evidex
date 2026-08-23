"""Within-panel agreement statistics per stage.

Metrics are explicitly within-model-family agreement (GLM-5.3 or the locked
Cursor model), NOT cross-family validation and not human validation.

Outputs tables/agreement_stage_<X>.csv, tables/judge_behavior.csv,
tables/judge_verdict_distributions.csv.
"""
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from aggregate_consensus import load_judgments  # noqa: E402


def krippendorff_alpha_nominal(wide: pd.DataFrame, cats) -> float:
    """Nominal Krippendorff's alpha from an items x judges verdict table."""
    values = wide.to_numpy()
    n_items, n_raters = values.shape
    coincidence = {c: {d: 0.0 for d in cats} for c in cats}
    n_pairable = 0.0
    for i in range(n_items):
        row = [v for v in values[i] if isinstance(v, str)]
        m = len(row)
        if m < 2:
            continue
        n_pairable += m
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                coincidence[row[a]][row[b]] += 1.0 / (m - 1)
    if n_pairable == 0:
        return float("nan")
    do = 0.0
    de = 0.0
    n_c = {c: sum(coincidence[c].values()) for c in cats}
    n = sum(n_c.values())
    if n <= 1:
        return float("nan")
    for c in cats:
        do += n_c[c] - coincidence[c][c]
        for d in cats:
            if c != d:
                de += n_c[c] * n_c[d]
    do = do / n
    de = de / (n * (n - 1))
    if de == 0:
        return 1.0
    return 1.0 - (do / de)


def fleiss_kappa(mat: np.ndarray) -> float:
    """mat: items x categories counts, each row sums to n raters."""
    n_items, n_cats = mat.shape
    n_raters = mat[0].sum()
    p_j = mat.sum(axis=0) / (n_items * n_raters)
    p_i = ((mat ** 2).sum(axis=1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = p_i.mean()
    p_e = (p_j ** 2).sum()
    if p_e == 1:
        return 1.0
    return (p_bar - p_e) / (1 - p_e)


def agreement(stage: str):
    df = load_judgments(stage)
    cats = config.VERDICTS
    rows = {"stage": stage}

    # Pairwise percent agreement.
    wide = df.pivot_table(index="item_id", columns="judge", values="verdict", aggfunc="first")
    pair_agree = []
    for a, b in combinations(config.JUDGES, 2):
        pair_agree.append((wide[a] == wide[b]).mean())
    rows["pairwise_agreement_mean"] = float(np.mean(pair_agree))
    rows["pairwise_agreement_min"] = float(np.min(pair_agree))

    # Fleiss' kappa (exact agreement over 3 verdict categories).
    mat = np.zeros((len(wide), len(cats)))
    for j, c in enumerate(cats):
        mat[:, j] = (wide == c).sum(axis=1).to_numpy()
    rows["fleiss_kappa"] = float(fleiss_kappa(mat))
    rows["krippendorff_alpha_nominal"] = float(krippendorff_alpha_nominal(wide, cats))
    rows["agreement_family"] = config.AGREEMENT_FAMILY_LABEL

    # Decisive-only agreement (excluding Ambiguous as its own category).
    dec = wide.replace({"Ambiguous": None}).dropna()
    pair_dec = []
    for a, b in combinations(config.JUDGES, 2):
        m = dec[a].notna() & dec[b].notna()
        pair_dec.append((dec.loc[m, a] == dec.loc[m, b]).mean())
    rows["pairwise_agreement_decisive_only"] = float(np.mean(pair_dec))
    rows["n_items"] = len(wide)

    # Verdict distribution + confidence dispersion.
    for c in cats:
        rows[f"pct_{c}"] = float((df["verdict"] == c).mean() * 100)
    rows["mean_confidence"] = float(df["confidence"].mean())
    rows["mean_within_item_confidence_sd"] = float(
        df.groupby("item_id")["confidence"].std(ddof=0).mean())

    res = pd.DataFrame([rows])
    res.to_csv(config.TABLES_DIR / f"agreement_stage_{stage}.csv", index=False)

    # Per-judge behavior.
    jb = df.groupby("judge").agg(
        pct_supported=("verdict", lambda v: (v == "Supported").mean() * 100),
        pct_refuted=("verdict", lambda v: (v == "Refuted").mean() * 100),
        pct_ambiguous=("verdict", lambda v: (v == "Ambiguous").mean() * 100),
        mean_confidence=("confidence", "mean"),
        n=("verdict", "size"),
    ).reset_index()
    jb.to_csv(config.TABLES_DIR / "judge_behavior.csv", index=False)
    dist = df.groupby(["judge", "verdict"]).size().unstack(fill_value=0)
    dist.to_csv(config.TABLES_DIR / "judge_verdict_distributions.csv")

    print(res.T.to_string())
    return res, jb


def all_stages():
    out = []
    for stage in config.STAGES:
        p = config.DERIVED_DIR / f"consensus_stage_{stage}.parquet"
        if not p.exists():
            continue
        r, _ = agreement(stage)
        out.append(r)
    if out:
        allres = pd.concat(out)
        allres.to_csv(config.TABLES_DIR / "agreement_all_stages.csv", index=False)
        print(allres.to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].upper() in config.STAGES:
        agreement(sys.argv[1].upper())
    else:
        all_stages()
