"""Claude consensus, within-panel agreement, and A->B->C transition variables.

Consensus rules are the existing Evidex panel-of-five rules, unchanged:
- ``high_consensus`` decisive verdict when >=4/5 judges say Supported or Refuted
- ``Ambiguous`` when the modal verdict is Ambiguous (with no decisive 4/5), or
  when there is no decisive 4/5 and >=3/5 sufficiency ratings are weak
- ``Unresolved`` otherwise

Transition variables replicate ``silver_adjudication_v1/src/
representation_sensitivity.py`` definitions exactly. Nothing here reads Grok,
GLM, FEVER, GPT, NLI, or cohort metadata.
"""
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


def load_judgments(stage: str) -> pd.DataFrame:
    run_judges.verify_frozen(stage)
    rows = []
    outdir = cfg.stage_judgments_dir(stage)
    for judge in cfg.JUDGES:
        for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
            for r in run_judges.load_batch_file(p):
                if run_judges.valid_record(r, stage, judge):
                    rows.append({
                        "item_id": r["item_id"], "judge": judge, "stage": stage,
                        "verdict": r["verdict"],
                        "sufficiency": r["evidence_sufficiency"],
                        "confidence": r["confidence"],
                        "issue_flags": ";".join(r["issue_flags"]),
                    })
    df = pd.DataFrame(rows).drop_duplicates(subset=["item_id", "judge"], keep="first")
    return df


def consensus_for_item(sub: pd.DataFrame):
    counts = Counter(sub["verdict"])
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


def aggregate(stage: str) -> pd.DataFrame:
    df = load_judgments(stage)
    rows = []
    for item_id, sub in df.groupby("item_id"):
        label, rule, _ = consensus_for_item(sub)
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
    if len(res) != cfg.EXPECTED_COHORT_N:
        raise SystemExit(f"Stage {stage} consensus covers {len(res)} items, "
                         f"expected {cfg.EXPECTED_COHORT_N}")
    res.to_parquet(cfg.consensus_path(stage), index=False)
    dist = res["consensus"].value_counts().rename("n").reset_index()
    dist.to_csv(cfg.TABLES_DIR / f"consensus_stage_{stage}.csv", index=False)
    print(f"Stage {stage} Claude consensus:")
    print(dist.to_string(index=False))
    return res


def fleiss_kappa(mat: np.ndarray) -> float:
    n_items, _ = mat.shape
    n_raters = mat[0].sum()
    p_j = mat.sum(axis=0) / (n_items * n_raters)
    p_i = ((mat ** 2).sum(axis=1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = p_i.mean()
    p_e = (p_j ** 2).sum()
    return 1.0 if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def krippendorff_alpha_nominal(wide: pd.DataFrame, cats) -> float:
    values = wide.to_numpy()
    coincidence = {c: {d: 0.0 for d in cats} for c in cats}
    for i in range(len(values)):
        row = [v for v in values[i] if isinstance(v, str)]
        m = len(row)
        if m < 2:
            continue
        for a in range(m):
            for b in range(m):
                if a != b:
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
    do /= n
    de /= (n * (n - 1))
    return 1.0 if de == 0 else 1.0 - (do / de)


def agreement(stage: str) -> dict:
    df = load_judgments(stage)
    cons = pd.read_parquet(cfg.consensus_path(stage))
    wide = df.pivot_table(index="item_id", columns="judge", values="verdict", aggfunc="first")
    pair = [(wide[a] == wide[b]).mean() for a, b in combinations(cfg.JUDGES, 2)]
    mat = np.zeros((len(wide), len(cfg.VERDICTS)))
    for j, c in enumerate(cfg.VERDICTS):
        mat[:, j] = (wide == c).sum(axis=1).to_numpy()
    row = {
        "stage": stage,
        "agreement_family": cfg.AGREEMENT_FAMILY_LABEL,
        "n_items": len(wide),
        "n_judgments": len(df),
        "pairwise_agreement_mean": float(np.mean(pair)),
        "pairwise_agreement_min": float(np.min(pair)),
        "fleiss_kappa": float(fleiss_kappa(mat)),
        "krippendorff_alpha_nominal": float(krippendorff_alpha_nominal(wide, cfg.VERDICTS)),
        "high_consensus_rate": float((cons["rule"] == "high_consensus").mean()),
        "ambiguous_rate": float((cons["consensus"] == "Ambiguous").mean()),
        "unresolved_rate": float((cons["consensus"] == "Unresolved").mean()),
        "amb_or_unresolved_rate": float(cons["consensus"].isin(["Ambiguous", "Unresolved"]).mean()),
        "mean_confidence": float(df["confidence"].mean()),
        "mean_within_item_confidence_sd": float(
            df.groupby("item_id")["confidence"].std(ddof=0).mean()),
    }
    for c in cfg.VERDICTS:
        row[f"pct_{c}"] = float((df["verdict"] == c).mean() * 100)
    pd.DataFrame([row]).to_csv(cfg.TABLES_DIR / f"agreement_stage_{stage}.csv", index=False)
    print(pd.Series(row).to_string())
    return row


def judge_behavior() -> pd.DataFrame:
    frames = [load_judgments(s) for s in cfg.STAGES]
    df = pd.concat(frames, ignore_index=True)
    jb = df.groupby(["stage", "judge"]).agg(
        pct_supported=("verdict", lambda v: (v == "Supported").mean() * 100),
        pct_refuted=("verdict", lambda v: (v == "Refuted").mean() * 100),
        pct_ambiguous=("verdict", lambda v: (v == "Ambiguous").mean() * 100),
        mean_confidence=("confidence", "mean"),
        n=("verdict", "size"),
    ).reset_index()
    jb.to_csv(cfg.TABLES_DIR / "judge_behavior.csv", index=False)
    flags = (df.assign(flag=df["issue_flags"].str.split(";")).explode("flag")
             .groupby(["stage", "flag"]).size().rename("n").reset_index())
    flags.to_csv(cfg.TABLES_DIR / "issue_flags.csv", index=False)
    print(jb.to_string(index=False))
    return jb


def per_judge_transitions() -> pd.DataFrame:
    """Per-judge stage-to-stage change flags (definitions from
    silver_adjudication_v1/src/representation_sensitivity.py)."""
    frames = {s: load_judgments(s).set_index(["item_id", "judge"]) for s in cfg.STAGES}
    rows = []
    for item_id, judge in frames["A"].index:
        a, b, c = (frames[s].loc[(item_id, judge)] for s in cfg.STAGES)
        rows.append({
            "item_id": item_id, "judge": judge,
            "verdict_A": a["verdict"], "verdict_B": b["verdict"], "verdict_C": c["verdict"],
            "change_A_to_B": a["verdict"] != b["verdict"],
            "change_B_to_C": b["verdict"] != c["verdict"],
            "change_A_to_C": a["verdict"] != c["verdict"],
            "ambiguous_to_decisive_A_to_C": a["verdict"] == "Ambiguous" and c["verdict"] != "Ambiguous",
            "decisive_to_ambiguous_A_to_C": a["verdict"] != "Ambiguous" and c["verdict"] == "Ambiguous",
            "conf_delta_A_to_C": c["confidence"] - a["confidence"],
            "suff_A": a["sufficiency"], "suff_C": c["sufficiency"],
            "suff_improved_A_to_C": (cfg.SUFFICIENCY.index(c["sufficiency"]) <
                                     cfg.SUFFICIENCY.index(a["sufficiency"])),
            "flags_A": a["issue_flags"], "flags_C": c["issue_flags"],
        })
    df = pd.DataFrame(rows)
    df.to_parquet(cfg.FREEZES_DIR / "verdict_changes.parquet", index=False)
    counts = pd.DataFrame({
        "A_to_B": [df["change_A_to_B"].mean()],
        "B_to_C": [df["change_B_to_C"].mean()],
        "A_to_C": [df["change_A_to_C"].mean()],
        "amb_to_decisive_A_to_C": [df["ambiguous_to_decisive_A_to_C"].mean()],
        "decisive_to_amb_A_to_C": [df["decisive_to_ambiguous_A_to_C"].mean()],
        "mean_conf_delta_A_to_C": [df["conf_delta_A_to_C"].mean()],
        "suff_improved_A_to_C": [df["suff_improved_A_to_C"].mean()],
    })
    counts.to_csv(cfg.TABLES_DIR / "stage_transition_counts.csv", index=False)
    print(counts.T.to_string())
    return df


def consensus_transitions() -> pd.DataFrame:
    cons = {s: pd.read_parquet(cfg.consensus_path(s)).set_index("item_id") for s in cfg.STAGES}
    rows = []
    for item_id in cons["A"].index:
        a = cons["A"].loc[item_id, "consensus"]
        b = cons["B"].loc[item_id, "consensus"]
        c = cons["C"].loc[item_id, "consensus"]
        rows.append({
            "item_id": item_id, "consensus_A": a, "consensus_B": b, "consensus_C": c,
            "rule_A": cons["A"].loc[item_id, "rule"],
            "rule_B": cons["B"].loc[item_id, "rule"],
            "rule_C": cons["C"].loc[item_id, "rule"],
            "ambiguous_A": a in ("Ambiguous", "Unresolved"),
            "ambiguous_B": b in ("Ambiguous", "Unresolved"),
            "ambiguous_C": c in ("Ambiguous", "Unresolved"),
            "resolved_by_titles": a in ("Ambiguous", "Unresolved") and b in ("Supported", "Refuted"),
            "resolved_only_by_structure": (b in ("Ambiguous", "Unresolved"))
            and (c in ("Supported", "Refuted")),
            "still_ambiguous_after_C": c in ("Ambiguous", "Unresolved"),
            "reversed_after_titles": a in ("Supported", "Refuted") and b in ("Supported", "Refuted") and a != b,
            "reversed_after_structure": b in ("Supported", "Refuted") and c in ("Supported", "Refuted") and b != c,
        })
    df = pd.DataFrame(rows)
    df.to_parquet(cfg.FREEZES_DIR / "consensus_changes.parquet", index=False)
    summary = pd.DataFrame([{
        "n_items": len(df),
        "pct_ambiguous_A": df["ambiguous_A"].mean() * 100,
        "pct_ambiguous_B": df["ambiguous_B"].mean() * 100,
        "pct_ambiguous_C": df["ambiguous_C"].mean() * 100,
        "pct_resolved_by_titles": df["resolved_by_titles"].mean() * 100,
        "pct_resolved_only_by_structure": df["resolved_only_by_structure"].mean() * 100,
        "pct_still_ambiguous_after_C": df["still_ambiguous_after_C"].mean() * 100,
        "pct_reversed_after_titles": df["reversed_after_titles"].mean() * 100,
        "pct_reversed_after_structure": df["reversed_after_structure"].mean() * 100,
        "pct_consensus_change_A_to_B": (df["consensus_A"] != df["consensus_B"]).mean() * 100,
        "pct_consensus_change_B_to_C": (df["consensus_B"] != df["consensus_C"]).mean() * 100,
    }])
    summary.to_csv(cfg.TABLES_DIR / "representation_sensitivity.csv", index=False)
    print(summary.T.to_string())
    return df


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("consensus", "all"):
        for s in cfg.STAGES:
            aggregate(s)
    if cmd in ("agreement", "all"):
        for s in cfg.STAGES:
            agreement(s)
        judge_behavior()
    if cmd in ("transitions", "all"):
        per_judge_transitions()
        consensus_transitions()
