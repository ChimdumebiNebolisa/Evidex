"""Cross-panel Stage A replication: frozen GLM-5.3 vs frozen Cursor Stage A.

This is a replication analysis, not independent human validation. It must
run only after Cursor Stage A is frozen. It does not write into GLM paths
and is never shown to Cursor judges.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import run_judges  # noqa: E402

WEAK_SUFF = {"partial_or_ambiguous", "probably_insufficient", "clearly_insufficient"}


def _load_panel_judgments(judgments_dir: Path, judges: list, stage: str = "A"):
    rows = []
    outdir = judgments_dir / f"stage_{stage.lower()}"
    for judge in judges:
        for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
            for r in run_judges.load_batch_file(p):
                if run_judges.valid_record(r, stage, judge):
                    rows.append({
                        "item_id": r["item_id"], "judge": judge,
                        "verdict": r["verdict"],
                        "sufficiency": r["evidence_sufficiency"],
                        "confidence": r["confidence"],
                    })
    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit(f"no valid Stage {stage} judgments under {outdir}")
    return df.drop_duplicates(subset=["item_id", "judge"], keep="first")


def _consensus_label(sub: pd.DataFrame):
    counts = Counter(sub["verdict"])
    modal, modal_n = counts.most_common(1)[0]
    decisive = counts.get("Supported", 0), counts.get("Refuted", 0)
    max_decisive = max(decisive)
    weak_suff = sub["sufficiency"].isin(WEAK_SUFF).sum()
    if max_decisive >= 4:
        label = "Supported" if decisive[0] > decisive[1] else "Refuted"
        return label, "high_consensus"
    if modal == "Ambiguous" and modal_n >= 2 and max_decisive <= 3:
        return "Ambiguous", "ambiguous_majority"
    if max_decisive <= 3 and weak_suff >= 3:
        return "Ambiguous", "ambiguous_weak_sufficiency"
    return "Unresolved", "unresolved"


def _item_consensus(df: pd.DataFrame):
    rows = []
    for item_id, sub in df.groupby("item_id"):
        label, rule = _consensus_label(sub)
        rows.append({
            "item_id": item_id, "consensus": label, "rule": rule,
            "n_ambiguous": int((sub["verdict"] == "Ambiguous").sum()),
            "modal_sufficiency": Counter(sub["sufficiency"]).most_common(1)[0][0],
        })
    return pd.DataFrame(rows).set_index("item_id")


def _pairwise(df: pd.DataFrame, judges: list):
    wide = df.pivot_table(index="item_id", columns="judge", values="verdict",
                          aggfunc="first")
    scores = []
    for a, b in combinations(judges, 2):
        if a in wide.columns and b in wide.columns:
            scores.append(float((wide[a] == wide[b]).mean()))
    return float(np.mean(scores)) if scores else float("nan")


def _rate_agreement(a: pd.Series, b: pd.Series):
    m = a.notna() & b.notna()
    return float((a[m] == b[m]).mean())


def replicate_stage_a(*, write: bool = True):
    cursor_a = config.CURSOR_PANEL_ROOT / "freezes" / "freeze_stage_A.json"
    glm_a = config.GLM_DERIVED_DIR / "freeze_stage_A.json"
    if not cursor_a.exists():
        raise SystemExit("Cursor Stage A is not frozen; refuse cross-panel comparison")
    if not glm_a.exists():
        raise SystemExit("GLM Stage A freeze missing")

    glm_df = _load_panel_judgments(
        config.GLM_JUDGMENTS_DIR, [f"judge_{i}" for i in range(1, 6)], "A")
    cursor_judges = [f"cursor_judge_{i}" for i in range(1, 6)]
    cur_df = _load_panel_judgments(config.CURSOR_PANEL_ROOT / "judgments",
                                   cursor_judges, "A")

    glm_cons = _item_consensus(glm_df)
    cur_cons = _item_consensus(cur_df)
    both = glm_cons.join(cur_cons, lsuffix="_glm", rsuffix="_cursor", how="inner")

    glm_modal = glm_df.groupby("item_id")["verdict"].agg(
        lambda s: Counter(s).most_common(1)[0][0])
    cur_modal = cur_df.groupby("item_id")["verdict"].agg(
        lambda s: Counter(s).most_common(1)[0][0])
    glm_suff = glm_df.groupby("item_id")["sufficiency"].agg(
        lambda s: Counter(s).most_common(1)[0][0])
    cur_suff = cur_df.groupby("item_id")["sufficiency"].agg(
        lambda s: Counter(s).most_common(1)[0][0])

    id_map = pd.read_csv(config.ID_MAP_CSV)
    cohort = pd.read_parquet(config.COHORT_PARQUET)
    meta = id_map.merge(cohort, on="claim_id")
    both = both.join(meta.set_index("item_id")[["cohort"]], how="left")

    rows = {
        "n_items_compared": int(len(both)),
        "verdict_modal_agreement": _rate_agreement(glm_modal, cur_modal),
        "consensus_agreement": _rate_agreement(both["consensus_glm"], both["consensus_cursor"]),
        "high_consensus_agreement": float(
            ((both["rule_glm"] == "high_consensus") ==
             (both["rule_cursor"] == "high_consensus")).mean()),
        "ambiguity_agreement": float((
            both["consensus_glm"].isin(["Ambiguous", "Unresolved"]) ==
            both["consensus_cursor"].isin(["Ambiguous", "Unresolved"])
        ).mean()),
        "sufficiency_modal_agreement": _rate_agreement(glm_suff, cur_suff),
        "glm_ambiguous_rate": float(
            both["consensus_glm"].isin(["Ambiguous", "Unresolved"]).mean()),
        "cursor_ambiguous_rate": float(
            both["consensus_cursor"].isin(["Ambiguous", "Unresolved"]).mean()),
        "glm_high_consensus_rate": float((both["rule_glm"] == "high_consensus").mean()),
        "cursor_high_consensus_rate": float(
            (both["rule_cursor"] == "high_consensus").mean()),
        "glm_pairwise_agreement": _pairwise(glm_df, [f"judge_{i}" for i in range(1, 6)]),
        "cursor_pairwise_agreement": _pairwise(cur_df, cursor_judges),
        "estimand": "cross-panel Stage A replication",
        "not": "independent human validation",
    }

    # Cohort-level ambiguity rate agreement (absolute difference).
    for name, mask in (
        ("regression", both["cohort"] == "regression"),
        ("resistant", both["cohort"] == "resistant"),
        ("rescue", both["cohort"] == "rescue"),
        ("robust", both["cohort"] == "robust"),
    ):
        sub = both[mask]
        g = float(sub["consensus_glm"].isin(["Ambiguous", "Unresolved"]).mean())
        c = float(sub["consensus_cursor"].isin(["Ambiguous", "Unresolved"]).mean())
        rows[f"{name}_glm_amb_rate"] = g
        rows[f"{name}_cursor_amb_rate"] = c
        rows[f"{name}_amb_rate_abs_diff"] = abs(g - c)

    tab = pd.crosstab(both["consensus_glm"], both["consensus_cursor"])
    chi2, p, _, _ = stats.chi2_contingency(tab.to_numpy())
    n = tab.to_numpy().sum()
    k = min(tab.shape)
    rows["consensus_cramers_v"] = float(np.sqrt(chi2 / (n * (k - 1)))) if n and k > 1 else 0.0
    rows["consensus_chi2_p"] = float(p)

    if write:
        out_dir = config.CURSOR_PANEL_ROOT / "tables"
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([rows]).to_csv(out_dir / "cross_panel_stage_a_replication.csv", index=False)
        tab.to_csv(out_dir / "cross_panel_stage_a_consensus_crosstab.csv")

        report = config.CURSOR_PANEL_ROOT / "reports"
        report.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Cross-panel Stage A replication",
            "",
            "This compares frozen GLM-5.3 Stage A to frozen Cursor-model Stage A.",
            "It is a **replication analysis**, not independent human validation.",
            "Cursor judges never saw GLM outputs. Partial GLM Stage B is excluded.",
            "",
            f"- Items compared: {rows['n_items_compared']}",
            f"- Modal verdict agreement: {rows['verdict_modal_agreement']:.3f}",
            f"- Consensus agreement: {rows['consensus_agreement']:.3f}",
            f"- Ambiguity agreement: {rows['ambiguity_agreement']:.3f}",
            f"- Sufficiency (modal) agreement: {rows['sufficiency_modal_agreement']:.3f}",
            f"- GLM Stage A ambiguous/unresolved rate: {rows['glm_ambiguous_rate']:.3f}",
            f"- Cursor Stage A ambiguous/unresolved rate: {rows['cursor_ambiguous_rate']:.3f}",
            f"- Cramér's V (consensus table): {rows['consensus_cramers_v']:.3f}",
            "",
            "Cohort-level ambiguity rates (GLM vs Cursor):",
        ]
        for name in ("regression", "resistant", "rescue", "robust"):
            lines.append(
                f"- {name}: GLM {rows[f'{name}_glm_amb_rate']:.3f} vs "
                f"Cursor {rows[f'{name}_cursor_amb_rate']:.3f} "
                f"(abs diff {rows[f'{name}_amb_rate_abs_diff']:.3f})"
            )
        (report / "CROSS_PANEL_STAGE_A_REPLICATION.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))
    return rows


if __name__ == "__main__":
    write = "--no-write" not in sys.argv and "--verify-only" not in sys.argv
    replicate_stage_a(write=write)
