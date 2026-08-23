"""Freeze-before-unblind, then cross-family and FEVER joins."""
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _amb(s: pd.Series) -> pd.Series:
    return s.isin(["Ambiguous", "Unresolved"])


def freeze_manifest():
    run_judges.verify_frozen()
    required = [
        cfg.BLINDED_JSONL, cfg.ID_MAP_CSV, cfg.RESIDUAL_SOURCE,
        cfg.FREEZES_DIR / "consensus_raw.parquet",
        cfg.TABLES_DIR / "consensus_raw.csv",
        cfg.TABLES_DIR / "agreement.csv",
        cfg.TABLES_DIR / "judge_behavior.csv",
    ]
    entries = {}
    for p in required:
        if not p.exists():
            raise SystemExit(f"missing before freeze: {p}")
        entries[p.name] = sha256(p)
    entries["freeze_judgments"] = sha256(cfg.FREEZE_JUDGES)
    if cfg.FREEZE_MANIFEST.exists():
        prev = json.loads(cfg.FREEZE_MANIFEST.read_text(encoding="utf-8"))
        if prev != entries:
            raise SystemExit("pre-unblinding manifest mismatch")
        print("pre-unblinding freeze verified (unchanged)")
    else:
        cfg.FREEZE_MANIFEST.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        print(f"pre-unblinding freeze -> {cfg.FREEZE_MANIFEST}")
    return entries


def verify_manifest():
    if not cfg.FREEZE_MANIFEST.exists():
        raise SystemExit("pre-unblinding manifest missing; refuse unblind")
    entries = json.loads(cfg.FREEZE_MANIFEST.read_text(encoding="utf-8"))
    freeze_manifest()
    print("manifest hashes verified")
    return entries


def boot_rate_ci(mask: pd.Series, seed_offset=0):
    v = mask.astype(int).to_numpy()
    r = np.random.default_rng(cfg.RANDOM_SEED + seed_offset)
    stats_ = [r.choice(v, size=len(v), replace=True).mean() for _ in range(cfg.BOOTSTRAP_ITERS)]
    return float(v.mean() * 100), float(np.percentile(stats_, 2.5) * 100), float(np.percentile(stats_, 97.5) * 100)


def fisher_or(a, b, c, d):
    orv = (a / max(b, 0.5)) / (c / max(d, 0.5))
    _, p = stats.fisher_exact(np.array([[a, b], [c, d]]))
    se = np.sqrt(1 / max(a, 0.5) + 1 / max(b, 0.5) + 1 / max(c, 0.5) + 1 / max(d, 0.5))
    return orv, np.exp(np.log(orv) - 1.96 * se), np.exp(np.log(orv) + 1.96 * se), p


def bh_adjust(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / (np.arange(len(p)) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(ranked)
    out[order] = np.clip(ranked, 0, 1)
    return out


def _taxonomy(r):
    claude_amb = r["claude_consensus"] in ("Ambiguous", "Unresolved")
    high = r["claude_rule"] == "high_consensus"
    if claude_amb and r["cursor_consensus_C"] in ("Ambiguous", "Unresolved"):
        return "cross_family_persistent_ambiguity"
    if (not claude_amb) and high:
        return "grok_only_ambiguity"
    if (not claude_amb) and not high:
        return "claude_internal_disagreement"
    return "claude_internal_disagreement"


def cross_family_and_unblind():
    verify_manifest()
    claude = pd.read_parquet(cfg.FREEZES_DIR / "consensus_raw.parquet").rename(columns={
        "item_id": "claude_item_id", "consensus": "claude_consensus",
        "rule": "claude_rule",
    })
    idmap = pd.read_csv(cfg.ID_MAP_CSV)
    cursor = pd.read_parquet(cfg.CURSOR_UNBLINDED).rename(columns={
        "item_id": "source_item_id", "consensus_C": "cursor_consensus_C",
        "rule_C": "cursor_rule_C",
    })
    df = claude.merge(idmap, on="claude_item_id")
    df = df.merge(cursor, on="source_item_id")
    df["item_id"] = df["claude_item_id"]

    df["claude_ambiguous"] = _amb(df["claude_consensus"])
    df["claude_decisive"] = df["claude_consensus"].isin(["Supported", "Refuted"])
    df["claude_high_decisive"] = df["claude_decisive"] & (df["claude_rule"] == "high_consensus")
    df["cross_family_taxonomy"] = df.apply(_taxonomy, axis=1)

    # FEVER agreement only for decisive Claude items.
    gold = df["gold_label"].replace({"SUPPORTS": "Supported", "REFUTES": "Refuted"})
    df["claude_agrees_fever"] = np.where(
        df["claude_decisive"], df["claude_consensus"] == gold, pd.NA)

    def fever_tax(r):
        if r["cross_family_taxonomy"] != "grok_only_ambiguity":
            return r["cross_family_taxonomy"]
        if r["claude_agrees_fever"] == True:  # noqa: E712
            return "cross_family_decisive_feversame"
        if r["claude_agrees_fever"] == False:  # noqa: E712
            return "cross_family_decisive_feverdifferent"
        return "grok_only_ambiguity"

    df["cross_family_taxonomy_fever"] = df.apply(fever_tax, axis=1)
    df.to_parquet(cfg.UNBLINDED_PARQUET, index=False)
    df.to_csv(cfg.TABLES_DIR / "cross_family_full.csv", index=False)
    print(f"unblinded join n={len(df)}")
    return df


def statistics():
    df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
    rows = []

    def add_rate(tag, mask, feat, family="primary", seed=0):
        sub = feat.loc[mask]
        m, lo, hi = boot_rate_ci(sub, seed)
        rows.append({"analysis": tag, "family": family, "n": int(mask.sum()),
                     "rate_pct": m, "ci_low": lo, "ci_high": hi})

    all_m = df.index.notna()
    add_rate("persistent_ambiguity", all_m, df["claude_ambiguous"], seed=1)
    add_rate("claude_resolved", all_m, df["claude_decisive"], seed=2)
    add_rate("claude_high_consensus_resolved", all_m, df["claude_high_decisive"], seed=3)
    add_rate("grok_only_ambiguity", all_m,
             df["cross_family_taxonomy"] == "grok_only_ambiguity", seed=4)
    add_rate("claude_internal_disagreement", all_m,
             df["cross_family_taxonomy"] == "claude_internal_disagreement", seed=5)

    agree = (df["claude_consensus"] == df["cursor_consensus_C"]).mean() * 100
    rows.append({"analysis": "cross_family_consensus_agree_pct", "family": "primary",
                 "n": len(df), "rate_pct": float(agree)})

    dec = df[df["claude_decisive"]]
    if len(dec):
        fever_ok = dec["claude_agrees_fever"].astype("boolean")
        m, lo, hi = boot_rate_ci(fever_ok.fillna(False), 6)
        rows.append({"analysis": "claude_decisive_agrees_fever", "family": "primary",
                     "n": int(fever_ok.notna().sum()), "rate_pct": m, "ci_low": lo, "ci_high": hi})

    # Exploratory subgroups.
    shared = df["regression_type"] == "both"
    spec = (df["cohort"] == "regression") & ~shared
    for name, mask in [
        ("shared_regression", shared),
        ("model_specific_regression", spec),
        ("regression", df["cohort"] == "regression"),
        ("resistant", df["cohort"] == "resistant"),
        ("rescue", df["cohort"] == "rescue"),
        ("robust", df["cohort"] == "robust"),
    ]:
        if mask.sum() == 0:
            continue
        add_rate(f"persistent_amb_{name}", mask, df["claude_ambiguous"],
                 family="exploratory", seed=10)

    # Residual regressions vs residual resistant.
    reg, res = df["cohort"] == "regression", df["cohort"] == "resistant"
    if reg.sum() and res.sum():
        a, b = int((reg & df["claude_ambiguous"]).sum()), int((reg & ~df["claude_ambiguous"]).sum())
        c, d = int((res & df["claude_ambiguous"]).sum()), int((res & ~df["claude_ambiguous"]).sum())
        orv, lo, hi, p = fisher_or(a, b, c, d)
        rows.append({"analysis": "persistent_amb_reg_vs_resistant_OR", "family": "exploratory",
                     "n": a + b + c + d, "odds_ratio": orv, "ci_low": lo, "ci_high": hi,
                     "p_value": p})

    # Confidence: persistent vs resolved.
    pers = df[df["claude_ambiguous"]]["mean_confidence"]
    resol = df[df["claude_decisive"]]["mean_confidence"]
    if len(pers) and len(resol):
        _, p = stats.mannwhitneyu(pers, resol, alternative="two-sided")
        rows.append({"analysis": "confidence_persistent_vs_resolved_mwu",
                     "family": "exploratory", "n": len(pers) + len(resol),
                     "mean_persistent": float(pers.mean()),
                     "mean_resolved": float(resol.mean()), "p_value": p})

    out = pd.DataFrame(rows)
    if "p_value" in out.columns:
        exp = out["family"].eq("exploratory") & out["p_value"].notna()
        if exp.any():
            out.loc[exp, "p_bh"] = bh_adjust(out.loc[exp, "p_value"].to_numpy())
    out.to_csv(cfg.TABLES_DIR / "statistical_tests.csv", index=False)
    with pd.option_context("display.max_columns", None, "display.width", 220):
        print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("freeze", "all"):
        freeze_manifest()
    if cmd in ("unblind", "all"):
        cross_family_and_unblind()
    if cmd in ("stats", "all"):
        statistics()
