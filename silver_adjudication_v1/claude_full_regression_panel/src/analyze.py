"""Freeze-before-unblind, Claude mechanism taxonomy, and the Grok comparison.

Order of operations is enforced by code, not by discipline:

1. ``freeze`` — every stage freeze verified, consensus/agreement/transition
   artifacts hashed into ``freezes/freeze_manifest.json``.
2. ``unblind`` — only then is the cohort's nature (all items are GPT
   regressions) used, the existing Evidex taxonomy rules applied to the Claude
   A/B/C consensus, and the private CF -> SA -> claim_id map joined.
3. ``compare`` — Claude vs Grok mechanism proportions, claim-level agreement,
   confusion matrix, stage-level comparison, shared vs model-specific split.
4. ``stats`` — bootstrap CIs.

Taxonomy rules are copied verbatim (modulo the fixed ``cohort == "regression"``)
from ``silver_adjudication_v1/src/join_analysis_v2.py::unblind_join.taxonomy``.
``tests/`` asserts this implementation reproduces the frozen Grok
``silver_taxonomy`` labels exactly from Grok consensus alone.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402
import run_judges  # noqa: E402

TAX_RESIDUAL = "silver_partial_or_ambiguous_warrant"
TAX_STRUCTURE = "silver_structured_evidence_sensitive"
TAX_TITLE = "silver_title_context_sensitive"
TAX_UTILIZATION = "silver_clear_evidence_utilization_failure"
TAX_OTHER = "silver_unresolved"

BROAD = {
    TAX_RESIDUAL: "residual_ambiguity",
    TAX_STRUCTURE: "representation_sensitive",
    TAX_TITLE: "representation_sensitive",
    TAX_UTILIZATION: "evidence_utilization_failure",
    TAX_OTHER: "other",
}
BROAD_ORDER = ["evidence_utilization_failure", "representation_sensitive",
               "residual_ambiguity", "other"]
TAX_ORDER = [TAX_UTILIZATION, TAX_STRUCTURE, TAX_TITLE, TAX_RESIDUAL, TAX_OTHER]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _amb(s: pd.Series) -> pd.Series:
    return s.isin(["Ambiguous", "Unresolved"])


def taxonomy_row(r, cohort: str = "regression") -> str:
    """Existing Evidex silver taxonomy rules, unchanged.

    The original had an NLI sub-branch inside the residual case that returned
    the same label on both paths, so no NLI field is consulted here.
    """
    if r["still_ambiguous_after_C"]:
        return TAX_RESIDUAL
    if r["resolved_only_by_structure"] or r["reversed_after_structure"] or \
            (r["consensus_A"] in ("Ambiguous", "Unresolved") and
             r["consensus_C"] in ("Supported", "Refuted")):
        return TAX_STRUCTURE
    if r["reversed_after_titles"] or r["resolved_by_titles"]:
        return TAX_TITLE
    if cohort in ("regression", "resistant") and \
            r["consensus_C"] in ("Supported", "Refuted"):
        return TAX_UTILIZATION
    return TAX_OTHER


# --- 1. freeze ---------------------------------------------------------------

def _manifest_entries() -> dict:
    for stage in cfg.STAGES:
        run_judges.verify_frozen(stage)
    required = [cfg.ID_MAP_CSV, cfg.COHORT_SOURCE,
                cfg.FREEZES_DIR / "consensus_changes.parquet",
                cfg.FREEZES_DIR / "verdict_changes.parquet",
                cfg.TABLES_DIR / "judge_behavior.csv",
                cfg.TABLES_DIR / "representation_sensitivity.csv",
                cfg.TABLES_DIR / "stage_transition_counts.csv"]
    for stage in cfg.STAGES:
        required += [cfg.stage_blinded(stage), cfg.stage_freeze(stage),
                     cfg.consensus_path(stage),
                     cfg.TABLES_DIR / f"consensus_stage_{stage}.csv",
                     cfg.TABLES_DIR / f"agreement_stage_{stage}.csv",
                     cfg.TABLES_DIR / f"judgment_completeness_stage_{stage}.csv"]
    entries = {"model": cfg.LOCKED_MODEL, "cohort_n": cfg.EXPECTED_COHORT_N,
               "judges": len(cfg.JUDGES), "stages": cfg.STAGES,
               "judgments_total": cfg.EXPECTED_TOTAL, "files": {}}
    for p in required:
        if not p.exists():
            raise SystemExit(f"missing before freeze: {p}")
        entries["files"][p.name] = sha256(p)
    total = 0
    for stage in cfg.STAGES:
        f = json.loads(cfg.stage_freeze(stage).read_text(encoding="utf-8"))
        total += f["n_judgments"]
    if total != cfg.EXPECTED_TOTAL:
        raise SystemExit(f"frozen judgment total {total} != {cfg.EXPECTED_TOTAL}")
    entries["commit"] = _git_commit()
    return entries


def _git_commit() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=cfg.REPO_ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def freeze_manifest() -> dict:
    entries = _manifest_entries()
    if cfg.FREEZE_MANIFEST.exists():
        prev = json.loads(cfg.FREEZE_MANIFEST.read_text(encoding="utf-8"))
        drift = {k: (prev.get("files", {}).get(k), v)
                 for k, v in entries["files"].items()
                 if prev.get("files", {}).get(k) != v}
        if drift:
            raise SystemExit(f"pre-unblinding manifest mismatch: {sorted(drift)}")
        for key in ("model", "cohort_n", "judges", "judgments_total"):
            if prev.get(key) != entries[key]:
                raise SystemExit(f"pre-unblinding manifest mismatch on {key}")
        print("pre-unblinding freeze verified (unchanged)")
        return prev
    cfg.FREEZE_MANIFEST.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"pre-unblinding freeze -> {cfg.FREEZE_MANIFEST}")
    return entries


def verify_manifest() -> dict:
    if not cfg.FREEZE_MANIFEST.exists():
        raise SystemExit("pre-unblinding manifest missing; refuse to unblind")
    return freeze_manifest()


# --- 2. unblind + Claude taxonomy -------------------------------------------

def unblind() -> pd.DataFrame:
    verify_manifest()
    changes = pd.read_parquet(cfg.FREEZES_DIR / "consensus_changes.parquet")
    cons = {s: pd.read_parquet(cfg.consensus_path(s)).set_index("item_id") for s in cfg.STAGES}
    df = changes.rename(columns={"item_id": "claude_item_id"})
    for s in cfg.STAGES:
        df[f"mean_confidence_{s}"] = df["claude_item_id"].map(cons[s]["mean_confidence"])
        df[f"sd_confidence_{s}"] = df["claude_item_id"].map(cons[s]["sd_confidence"])

    df["claude_taxonomy"] = df.apply(taxonomy_row, axis=1)
    df["claude_broad"] = df["claude_taxonomy"].map(BROAD)

    idmap = pd.read_csv(cfg.ID_MAP_CSV)
    df = df.merge(idmap, on="claude_item_id", validate="one_to_one")

    cohort = pd.read_parquet(cfg.COHORT_PARQUET).set_index("claim_id")
    df["cohort"] = df["claim_id"].map(cohort["cohort"])
    if not (df["cohort"] == "regression").all():
        raise SystemExit("unblinded cohort contains non-regression items")
    df["regression_type"] = df["claim_id"].map(cohort["regression_type"])
    df["gold_label"] = df["claim_id"].map(cohort["gold_label"])
    df["gpt54_transition"] = df["claim_id"].map(cohort["gpt-5.4_transition"])
    df["gpt54mini_transition"] = df["claim_id"].map(cohort["gpt-5.4-mini_transition"])

    grok = pd.read_parquet(cfg.CURSOR_UNBLINDED).set_index("item_id")
    grok = grok.loc[grok["cohort"] == "regression"]
    for col, new in [("consensus_A", "grok_consensus_A"), ("consensus_B", "grok_consensus_B"),
                     ("consensus_C", "grok_consensus_C"), ("rule_A", "grok_rule_A"),
                     ("rule_C", "grok_rule_C"), ("silver_taxonomy", "grok_taxonomy"),
                     ("resolved_by_titles", "grok_resolved_by_titles"),
                     ("resolved_only_by_structure", "grok_resolved_only_by_structure"),
                     ("still_ambiguous_after_C", "grok_still_ambiguous_after_C"),
                     ("reversed_after_titles", "grok_reversed_after_titles"),
                     ("reversed_after_structure", "grok_reversed_after_structure"),
                     ("nli_disagrees", "nli_disagrees"), ("nli2_disagrees", "nli2_disagrees")]:
        df[new] = df["source_item_id"].map(grok[col])
    if df["grok_taxonomy"].isna().any():
        raise SystemExit("Grok taxonomy missing for some regressions; join failed")
    df["grok_broad"] = df["grok_taxonomy"].map(BROAD)
    for s in cfg.STAGES:
        df[f"grok_ambiguous_{s}"] = _amb(df[f"grok_consensus_{s}"])

    df.to_parquet(cfg.UNBLINDED_PARQUET, index=False)
    df.to_csv(cfg.TABLES_DIR / "claude_full_unblinded.csv", index=False)
    print(f"unblinded join n={len(df)} -> {cfg.UNBLINDED_PARQUET.name}")
    print(df["claude_taxonomy"].value_counts().to_string())
    return df


# --- 3. Grok comparison ------------------------------------------------------

def _prop_ci(k: int, n: int) -> tuple[float, float]:
    """Wilson score interval (percent)."""
    if n == 0:
        return (float("nan"), float("nan"))
    z, p = 1.959963985, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h) * 100, min(1.0, c + h) * 100)


def compare() -> dict:
    df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
    n = len(df)

    rows = []
    for panel, col, order in [("grok", "grok_broad", BROAD_ORDER),
                              ("claude", "claude_broad", BROAD_ORDER)]:
        for cat in order:
            k = int((df[col] == cat).sum())
            lo, hi = _prop_ci(k, n)
            rows.append({"panel": panel, "level": "broad", "category": cat, "n": k,
                         "pct": 100.0 * k / n, "ci_low": lo, "ci_high": hi})
    for panel, col in [("grok", "grok_taxonomy"), ("claude", "claude_taxonomy")]:
        for cat in TAX_ORDER:
            k = int((df[col] == cat).sum())
            lo, hi = _prop_ci(k, n)
            rows.append({"panel": panel, "level": "fine", "category": cat, "n": k,
                         "pct": 100.0 * k / n, "ci_low": lo, "ci_high": hi})
    mech = pd.DataFrame(rows)
    mech.to_csv(cfg.TABLES_DIR / "mechanism_proportions.csv", index=False)

    # Claim-level agreement.
    exact = float((df["claude_taxonomy"] == df["grok_taxonomy"]).mean())
    broad = float((df["claude_broad"] == df["grok_broad"]).mean())
    fine_cm = pd.crosstab(df["grok_taxonomy"], df["claude_taxonomy"]).reindex(
        index=TAX_ORDER, columns=TAX_ORDER, fill_value=0)
    broad_cm = pd.crosstab(df["grok_broad"], df["claude_broad"]).reindex(
        index=BROAD_ORDER, columns=BROAD_ORDER, fill_value=0)
    fine_cm.to_csv(cfg.TABLES_DIR / "taxonomy_confusion_fine.csv")
    broad_cm.to_csv(cfg.TABLES_DIR / "taxonomy_confusion_broad.csv")

    # Cohen's kappa on the broad categories.
    obs = broad
    marg = sum((df["grok_broad"] == c).mean() * (df["claude_broad"] == c).mean()
               for c in BROAD_ORDER)
    kappa = (obs - marg) / (1 - marg) if marg < 1 else float("nan")

    moves = (df.loc[df["claude_broad"] != df["grok_broad"]]
             .groupby(["grok_broad", "claude_broad"]).size()
             .rename("n").reset_index().sort_values("n", ascending=False))
    moves.to_csv(cfg.TABLES_DIR / "taxonomy_moves.csv", index=False)

    # Stage-level comparison.
    stage_rows = []
    for s in cfg.STAGES:
        gk = int(df[f"grok_ambiguous_{s}"].sum())
        ck = int(df[f"ambiguous_{s}"].sum())
        g_lo, g_hi = _prop_ci(gk, n)
        c_lo, c_hi = _prop_ci(ck, n)
        b = int((df[f"grok_ambiguous_{s}"] & ~df[f"ambiguous_{s}"]).sum())
        c_only = int((~df[f"grok_ambiguous_{s}"] & df[f"ambiguous_{s}"]).sum())
        mcnemar_p = float(stats.binomtest(b, b + c_only, 0.5).pvalue) if (b + c_only) else 1.0
        stage_rows.append({
            "measure": f"stage_{s}_ambiguity", "grok_n": gk, "grok_pct": 100.0 * gk / n,
            "grok_ci_low": g_lo, "grok_ci_high": g_hi,
            "claude_n": ck, "claude_pct": 100.0 * ck / n,
            "claude_ci_low": c_lo, "claude_ci_high": c_hi,
            "delta_pp": 100.0 * (ck - gk) / n,
            "discordant_grok_only": b, "discordant_claude_only": c_only,
            "mcnemar_p": mcnemar_p,
        })
    for label, ccol, gcol in [("title_resolution", "resolved_by_titles", "grok_resolved_by_titles"),
                              ("structure_resolution", "resolved_only_by_structure",
                               "grok_resolved_only_by_structure"),
                              ("final_ambiguous_after_C", "still_ambiguous_after_C",
                               "grok_still_ambiguous_after_C"),
                              ("reversal_after_titles", "reversed_after_titles",
                               "grok_reversed_after_titles"),
                              ("reversal_after_structure", "reversed_after_structure",
                               "grok_reversed_after_structure")]:
        gk, ck = int(df[gcol].sum()), int(df[ccol].sum())
        g_lo, g_hi = _prop_ci(gk, n)
        c_lo, c_hi = _prop_ci(ck, n)
        b = int((df[gcol] & ~df[ccol]).sum())
        c_only = int((~df[gcol] & df[ccol]).sum())
        stage_rows.append({
            "measure": label, "grok_n": gk, "grok_pct": 100.0 * gk / n,
            "grok_ci_low": g_lo, "grok_ci_high": g_hi,
            "claude_n": ck, "claude_pct": 100.0 * ck / n,
            "claude_ci_low": c_lo, "claude_ci_high": c_hi,
            "delta_pp": 100.0 * (ck - gk) / n,
            "discordant_grok_only": b, "discordant_claude_only": c_only,
            "mcnemar_p": float(stats.binomtest(b, b + c_only, 0.5).pvalue) if (b + c_only) else 1.0,
        })
    stage_tab = pd.DataFrame(stage_rows)
    stage_tab.to_csv(cfg.TABLES_DIR / "stage_level_comparison.csv", index=False)

    # Final decisive/ambiguous status crosstab.
    final = pd.crosstab(df["grok_consensus_C"], df["consensus_C"])
    final.to_csv(cfg.TABLES_DIR / "final_status_crosstab.csv")

    # Shared vs model-specific regressions.
    df["shared"] = df["regression_type"] == "both"
    sub_rows = []
    for name, mask in [("shared_both_models", df["shared"]),
                       ("single_model_only", ~df["shared"]),
                       ("gpt54_only", df["regression_type"] == "gpt54_only"),
                       ("mini_only", df["regression_type"] == "mini_only")]:
        m = int(mask.sum())
        if m == 0:
            continue
        for panel, col in [("claude", "claude_broad"), ("grok", "grok_broad")]:
            for cat in BROAD_ORDER:
                k = int((mask & (df[col] == cat)).sum())
                lo, hi = _prop_ci(k, m)
                sub_rows.append({"subgroup": name, "n_subgroup": m, "panel": panel,
                                 "category": cat, "n": k, "pct": 100.0 * k / m,
                                 "ci_low": lo, "ci_high": hi})
        for panel, col in [("claude", "still_ambiguous_after_C"),
                           ("grok", "grok_still_ambiguous_after_C")]:
            k = int((mask & df[col]).sum())
            lo, hi = _prop_ci(k, m)
            sub_rows.append({"subgroup": name, "n_subgroup": m, "panel": panel,
                             "category": "still_ambiguous_after_C", "n": k,
                             "pct": 100.0 * k / m, "ci_low": lo, "ci_high": hi})
    pd.DataFrame(sub_rows).to_csv(cfg.TABLES_DIR / "shared_vs_specific.csv", index=False)

    summary = {
        "n": n,
        "exact_taxonomy_agreement": exact,
        "broad_category_agreement": broad,
        "broad_cohen_kappa": float(kappa),
        "claude": {c: int((df["claude_broad"] == c).sum()) for c in BROAD_ORDER},
        "grok": {c: int((df["grok_broad"] == c).sum()) for c in BROAD_ORDER},
    }
    (cfg.TABLES_DIR / "comparison_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("\nbroad confusion (rows Grok, cols Claude):")
    print(broad_cm.to_string())
    print("\nstage-level comparison:")
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(stage_tab.to_string(index=False))
    return summary


# --- 4. bootstrap statistics -------------------------------------------------

def boot_rate_ci(mask: pd.Series, seed_offset: int = 0):
    v = mask.astype(int).to_numpy()
    r = np.random.default_rng(cfg.RANDOM_SEED + seed_offset)
    draws = [r.choice(v, size=len(v), replace=True).mean() for _ in range(cfg.BOOTSTRAP_ITERS)]
    return (float(v.mean() * 100), float(np.percentile(draws, 2.5) * 100),
            float(np.percentile(draws, 97.5) * 100))


def statistics() -> pd.DataFrame:
    df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
    rows = []

    def add(tag, mask, family="primary", seed=0):
        m, lo, hi = boot_rate_ci(mask, seed)
        rows.append({"analysis": tag, "family": family, "n": len(df),
                     "rate_pct": m, "ci_low": lo, "ci_high": hi})

    for i, cat in enumerate(BROAD_ORDER):
        add(f"claude_{cat}", df["claude_broad"] == cat, seed=i + 1)
        add(f"grok_{cat}", df["grok_broad"] == cat, seed=i + 11)
    for i, s in enumerate(cfg.STAGES):
        add(f"claude_stage_{s}_ambiguity", df[f"ambiguous_{s}"], seed=i + 21)
        add(f"grok_stage_{s}_ambiguity", df[f"grok_ambiguous_{s}"], seed=i + 31)
    add("taxonomy_exact_agreement", df["claude_taxonomy"] == df["grok_taxonomy"], seed=41)
    add("taxonomy_broad_agreement", df["claude_broad"] == df["grok_broad"], seed=42)

    shared = df["regression_type"] == "both"
    a = int((shared & df["still_ambiguous_after_C"]).sum())
    b = int((shared & ~df["still_ambiguous_after_C"]).sum())
    c = int((~shared & df["still_ambiguous_after_C"]).sum())
    d = int((~shared & ~df["still_ambiguous_after_C"]).sum())
    orv = (max(a, 0.5) / max(b, 0.5)) / (max(c, 0.5) / max(d, 0.5))
    _, p = stats.fisher_exact(np.array([[a, b], [c, d]]))
    se = np.sqrt(sum(1 / max(x, 0.5) for x in (a, b, c, d)))
    rows.append({"analysis": "claude_residual_amb_shared_vs_specific_OR",
                 "family": "exploratory", "n": a + b + c + d, "odds_ratio": orv,
                 "ci_low": float(np.exp(np.log(orv) - 1.96 * se)),
                 "ci_high": float(np.exp(np.log(orv) + 1.96 * se)), "p_value": float(p)})

    out = pd.DataFrame(rows)
    out.to_csv(cfg.TABLES_DIR / "statistical_tests.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("freeze", "all"):
        freeze_manifest()
    if cmd in ("verify", "all"):
        verify_manifest()
    if cmd in ("unblind", "all"):
        unblind()
    if cmd in ("compare", "all"):
        compare()
    if cmd in ("stats", "all"):
        statistics()
