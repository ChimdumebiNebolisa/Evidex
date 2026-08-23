"""Raw five-judge consensus and within-Claude-panel agreement."""
from __future__ import annotations

import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402
import run_judges  # noqa: E402


def load_judgments() -> pd.DataFrame:
    run_judges.verify_frozen()
    rows = []
    for judge in cfg.JUDGES:
        for p in sorted((cfg.JUDGMENTS_DIR / judge).glob(f"{judge}_batch_*.jsonl")):
            for r in run_judges.load_batch_file(p):
                if run_judges.valid_record(r, judge):
                    rows.append({
                        "item_id": r["item_id"], "judge": judge,
                        "verdict": r["verdict"],
                        "sufficiency": r["evidence_sufficiency"],
                        "confidence": r["confidence"],
                        "issue_flags": ";".join(r["issue_flags"]),
                    })
    df = pd.DataFrame(rows).drop_duplicates(subset=["item_id", "judge"], keep="first")
    return df


def consensus_for_item(sub: pd.DataFrame):
    verdicts = list(sub["verdict"])
    counts = Counter(verdicts)
    modal, modal_n = counts.most_common(1)[0]
    decisive = counts.get("Supported", 0), counts.get("Refuted", 0)
    max_decisive = max(decisive)
    weak_suff = sub["sufficiency"].isin(cfg.WEAK_SUFF).sum()
    if max_decisive >= 4:
        label = "Supported" if decisive[0] > decisive[1] else "Refuted"
        return label, "high_consensus", modal_n
    if modal == "Ambiguous" and modal_n >= 2 and max_decisive <= 3:
        return "Ambiguous", "ambiguous_majority", modal_n
    if max_decisive <= 3 and weak_suff >= 3:
        return "Ambiguous", "ambiguous_weak_sufficiency", weak_suff
    return "Unresolved", "unresolved", modal_n


def aggregate():
    df = load_judgments()
    rows = []
    for item_id, sub in df.groupby("item_id"):
        label, rule, support = consensus_for_item(sub)
        v = Counter(sub["verdict"])
        rows.append({
            "item_id": item_id, "consensus": label, "rule": rule,
            "n_supported": v.get("Supported", 0), "n_refuted": v.get("Refuted", 0),
            "n_ambiguous": v.get("Ambiguous", 0),
            "mean_confidence": sub["confidence"].mean(),
            "sd_confidence": sub["confidence"].std(ddof=0),
            "modal_sufficiency": Counter(sub["sufficiency"]).most_common(1)[0][0],
            "issue_flags": ";".join(sorted({f for flags in sub["issue_flags"]
                                            for f in flags.split(";") if f and f != "none"})),
        })
    res = pd.DataFrame(rows)
    res.to_parquet(cfg.FREEZES_DIR / "consensus_raw.parquet", index=False)
    dist = res["consensus"].value_counts().rename("n").reset_index()
    dist.to_csv(cfg.TABLES_DIR / "consensus_raw.csv", index=False)
    print("raw Claude consensus:")
    print(dist.to_string(index=False))
    return res


def fleiss_kappa(mat: np.ndarray) -> float:
    n_items, n_cats = mat.shape
    n_raters = mat[0].sum()
    p_j = mat.sum(axis=0) / (n_items * n_raters)
    p_i = ((mat ** 2).sum(axis=1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = p_i.mean()
    p_e = (p_j ** 2).sum()
    if p_e == 1:
        return 1.0
    return (p_bar - p_e) / (1 - p_e)


def krippendorff_alpha_nominal(wide: pd.DataFrame, cats) -> float:
    values = wide.to_numpy()
    coincidence = {c: {d: 0.0 for d in cats} for c in cats}
    n_pairable = 0.0
    for i in range(len(values)):
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
    n_c = {c: sum(coincidence[c].values()) for c in cats}
    n = sum(n_c.values())
    if n <= 1:
        return float("nan")
    do = de = 0.0
    for c in cats:
        do += n_c[c] - coincidence[c][c]
        for d in cats:
            if c != d:
                de += n_c[c] * n_c[d]
    do = do / n
    de = de / (n * (n - 1))
    return 1.0 if de == 0 else 1.0 - (do / de)


def agreement():
    df = load_judgments()
    cons = pd.read_parquet(cfg.FREEZES_DIR / "consensus_raw.parquet")
    wide = df.pivot_table(index="item_id", columns="judge", values="verdict", aggfunc="first")
    pair = [(wide[a] == wide[b]).mean() for a, b in combinations(cfg.JUDGES, 2)]
    mat = np.zeros((len(wide), len(cfg.VERDICTS)))
    for j, c in enumerate(cfg.VERDICTS):
        mat[:, j] = (wide == c).sum(axis=1).to_numpy()
    rows = {
        "agreement_family": cfg.AGREEMENT_FAMILY_LABEL,
        "n_items": len(wide),
        "pairwise_agreement_mean": float(np.mean(pair)),
        "pairwise_agreement_min": float(np.min(pair)),
        "fleiss_kappa": float(fleiss_kappa(mat)),
        "krippendorff_alpha_nominal": float(krippendorff_alpha_nominal(wide, cfg.VERDICTS)),
        "high_consensus_rate": float((cons["rule"] == "high_consensus").mean()),
        "ambiguous_rate": float((cons["consensus"] == "Ambiguous").mean()),
        "unresolved_rate": float((cons["consensus"] == "Unresolved").mean()),
        "amb_or_unresolved_rate": float(cons["consensus"].isin(["Ambiguous", "Unresolved"]).mean()),
        "mean_confidence": float(df["confidence"].mean()),
        "mean_within_item_confidence_sd": float(df.groupby("item_id")["confidence"].std(ddof=0).mean()),
    }
    for c in cfg.VERDICTS:
        rows[f"pct_{c}"] = float((df["verdict"] == c).mean() * 100)
    pd.DataFrame([rows]).to_csv(cfg.TABLES_DIR / "agreement.csv", index=False)
    jb = df.groupby("judge").agg(
        pct_supported=("verdict", lambda v: (v == "Supported").mean() * 100),
        pct_refuted=("verdict", lambda v: (v == "Refuted").mean() * 100),
        pct_ambiguous=("verdict", lambda v: (v == "Ambiguous").mean() * 100),
        mean_confidence=("confidence", "mean"),
        n=("verdict", "size"),
    ).reset_index()
    jb.to_csv(cfg.TABLES_DIR / "judge_behavior.csv", index=False)
    print(pd.Series(rows).to_string())
    return rows


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("consensus", "all"):
        aggregate()
    if cmd in ("agreement", "all"):
        agreement()
