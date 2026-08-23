"""Independent verification of headline numbers in CLAUDE_FINDINGS.md.

Recomputes each registered value from frozen artifacts without importing
analyze.py. Also recomputes freeze hashes from disk bytes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402

HEADLINES_JSON = cfg.REPORTS_DIR / "HEADLINES.json"
WEAK_SUFF = {"partial_or_ambiguous", "probably_insufficient", "clearly_insufficient"}
VERDICTS = ["Supported", "Refuted", "Ambiguous"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_batch(path: Path) -> list:
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    try:
        arr = json.loads(content)
    except ValueError:
        arr = [json.loads(l) for l in content.splitlines() if l.strip()]
    if not isinstance(arr, list):
        raise ValueError(path.name)
    return arr


def _raw_rows():
    rows = []
    for judge in cfg.JUDGES:
        for p in sorted((cfg.JUDGMENTS_DIR / judge).glob(f"{judge}_batch_*.jsonl")):
            for r in _load_batch(p):
                rows.append({
                    "item_id": r["item_id"], "judge": r["judge_id"],
                    "verdict": r["verdict"],
                    "sufficiency": r["evidence_sufficiency"],
                    "confidence": r["confidence"],
                })
    return pd.DataFrame(rows).drop_duplicates(subset=["item_id", "judge"], keep="first")


def _consensus_label(verdicts, suff):
    counts = Counter(verdicts)
    modal, modal_n = counts.most_common(1)[0]
    decisive = counts.get("Supported", 0), counts.get("Refuted", 0)
    max_decisive = max(decisive)
    weak = sum(1 for s in suff if s in WEAK_SUFF)
    if max_decisive >= 4:
        label = "Supported" if decisive[0] > decisive[1] else "Refuted"
        return label, "high_consensus"
    if modal == "Ambiguous" and modal_n >= 2 and max_decisive <= 3:
        return "Ambiguous", "ambiguous_majority"
    if max_decisive <= 3 and weak >= 3:
        return "Ambiguous", "ambiguous_weak_sufficiency"
    return "Unresolved", "unresolved"


def _recount_consensus():
    df = _raw_rows()
    out = []
    for item_id, sub in df.groupby("item_id"):
        label, rule = _consensus_label(list(sub["verdict"]), list(sub["sufficiency"]))
        out.append({"item_id": item_id, "consensus": label, "rule": rule,
                    "mean_confidence": float(sub["confidence"].mean())})
    return pd.DataFrame(out)


def _unblinded():
    return pd.read_parquet(cfg.UNBLINDED_PARQUET)


def _boot(mask, seed_offset):
    v = np.asarray(mask).astype(int)
    r = np.random.default_rng(cfg.RANDOM_SEED + seed_offset)
    stats_ = [r.choice(v, size=len(v), replace=True).mean() for _ in range(cfg.BOOTSTRAP_ITERS)]
    return float(v.mean() * 100), float(np.percentile(stats_, 2.5) * 100), float(np.percentile(stats_, 97.5) * 100)


VERIFIERS = {}


def verifier(fn):
    VERIFIERS[fn.__name__] = fn
    return fn


@verifier
def residual_n():
    items = [l for l in cfg.BLINDED_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    src = json.loads(cfg.RESIDUAL_SOURCE.read_text(encoding="utf-8"))
    assert src["n"] == len(items)
    return int(len(items))


@verifier
def n_judges():
    return int(len(cfg.JUDGES))


@verifier
def n_raw_judgments():
    return int(len(_raw_rows()))


@verifier
def consensus_ambiguous_n():
    return int((_recount_consensus()["consensus"] == "Ambiguous").sum())


@verifier
def consensus_supported_n():
    return int((_recount_consensus()["consensus"] == "Supported").sum())


@verifier
def consensus_refuted_n():
    return int((_recount_consensus()["consensus"] == "Refuted").sum())


@verifier
def consensus_unresolved_n():
    return int((_recount_consensus()["consensus"] == "Unresolved").sum())


@verifier
def persistent_n():
    c = _recount_consensus()
    return int(c["consensus"].isin(["Ambiguous", "Unresolved"]).sum())


@verifier
def grok_only_n():
    c = _recount_consensus()
    return int((c["consensus"].isin(["Supported", "Refuted"]) &
                (c["rule"] == "high_consensus")).sum())


@verifier
def persistent_ambiguity_pct():
    return _boot(_recount_consensus()["consensus"].isin(["Ambiguous", "Unresolved"]), 1)[0]


@verifier
def persistent_ci_low():
    return _boot(_recount_consensus()["consensus"].isin(["Ambiguous", "Unresolved"]), 1)[1]


@verifier
def persistent_ci_high():
    return _boot(_recount_consensus()["consensus"].isin(["Ambiguous", "Unresolved"]), 1)[2]


@verifier
def claude_resolved_pct():
    return _boot(_recount_consensus()["consensus"].isin(["Supported", "Refuted"]), 2)[0]


@verifier
def pairwise_agreement_pct():
    df = _raw_rows()
    wide = df.pivot_table(index="item_id", columns="judge", values="verdict", aggfunc="first")
    pair = [(wide[a] == wide[b]).mean() for a, b in combinations(cfg.JUDGES, 2)]
    return float(np.mean(pair) * 100)


@verifier
def fleiss_kappa():
    df = _raw_rows()
    wide = df.pivot_table(index="item_id", columns="judge", values="verdict", aggfunc="first")
    mat = np.zeros((len(wide), len(VERDICTS)))
    for j, c in enumerate(VERDICTS):
        mat[:, j] = (wide == c).sum(axis=1).to_numpy()
    n_items, n_cats = mat.shape
    n_raters = mat[0].sum()
    p_j = mat.sum(axis=0) / (n_items * n_raters)
    p_i = ((mat ** 2).sum(axis=1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = p_i.mean()
    p_e = (p_j ** 2).sum()
    return float((p_bar - p_e) / (1 - p_e))


@verifier
def high_consensus_rate_pct():
    c = _recount_consensus()
    return 100.0 * float((c["rule"] == "high_consensus").mean())


@verifier
def mean_confidence():
    return float(_raw_rows()["confidence"].mean())


@verifier
def cross_family_agree_pct():
    df = _unblinded()
    return 100.0 * float((df["claude_consensus"] == df["cursor_consensus_C"]).mean())


@verifier
def claude_internal_disagreement_n():
    df = _unblinded()
    return int((df["cross_family_taxonomy"] == "claude_internal_disagreement").sum())


@verifier
def fever_agree_n():
    df = _unblinded()
    dec = df[df["claude_decisive"]]
    gold = dec["gold_label"].replace({"SUPPORTS": "Supported", "REFUTES": "Refuted"})
    return int((dec["claude_consensus"] == gold).sum())


@verifier
def fever_disagree_n():
    df = _unblinded()
    dec = df[df["claude_decisive"]]
    gold = dec["gold_label"].replace({"SUPPORTS": "Supported", "REFUTES": "Refuted"})
    return int((dec["claude_consensus"] != gold).sum())


@verifier
def fever_agree_pct():
    df = _unblinded()
    dec = df[df["claude_decisive"]]
    gold = dec["gold_label"].replace({"SUPPORTS": "Supported", "REFUTES": "Refuted"})
    ok = dec["claude_consensus"] == gold
    return _boot(ok, 6)[0]


@verifier
def shared_reg_n():
    return int((_unblinded()["regression_type"] == "both").sum())


@verifier
def shared_reg_persistent_pct():
    df = _unblinded()
    sub = df[df["regression_type"] == "both"]
    return 100.0 * float(sub["claude_ambiguous"].mean())


@verifier
def model_specific_n():
    df = _unblinded()
    return int(((df["cohort"] == "regression") & (df["regression_type"] != "both")).sum())


@verifier
def model_specific_persistent_pct():
    df = _unblinded()
    sub = df[(df["cohort"] == "regression") & (df["regression_type"] != "both")]
    return 100.0 * float(sub["claude_ambiguous"].mean())


@verifier
def regression_residual_n():
    return int((_unblinded()["cohort"] == "regression").sum())


@verifier
def regression_persistent_pct():
    df = _unblinded()
    sub = df[df["cohort"] == "regression"]
    return 100.0 * float(sub["claude_ambiguous"].mean())


@verifier
def resistant_residual_n():
    return int((_unblinded()["cohort"] == "resistant").sum())


@verifier
def resistant_persistent_pct():
    df = _unblinded()
    sub = df[df["cohort"] == "resistant"]
    return 100.0 * float(sub["claude_ambiguous"].mean())


@verifier
def rescue_residual_n():
    return int((_unblinded()["cohort"] == "rescue").sum())


@verifier
def robust_residual_n():
    return int((_unblinded()["cohort"] == "robust").sum())


@verifier
def or_reg_vs_resistant():
    df = _unblinded()
    reg, res = df["cohort"] == "regression", df["cohort"] == "resistant"
    a = int((reg & df["claude_ambiguous"]).sum())
    b = int((reg & ~df["claude_ambiguous"]).sum())
    c = int((res & df["claude_ambiguous"]).sum())
    d = int((res & ~df["claude_ambiguous"]).sum())
    return float((a / max(b, 0.5)) / (c / max(d, 0.5)))


@verifier
def conf_persistent():
    df = _unblinded()
    return float(df.loc[df["claude_ambiguous"], "mean_confidence"].mean())


@verifier
def conf_resolved():
    df = _unblinded()
    return float(df.loc[df["claude_decisive"], "mean_confidence"].mean())


@verifier
def cursor_stage_c_ambiguous_n():
    return int((_unblinded()["cursor_consensus_C"] == "Ambiguous").sum())


@verifier
def cursor_stage_c_unresolved_n():
    return int((_unblinded()["cursor_consensus_C"] == "Unresolved").sum())


@verifier
def join_n():
    df = _unblinded()
    return int(len(df))


def verify_freezes():
    failures = []
    if not cfg.FREEZE_JUDGES.exists() or not cfg.FREEZE_MANIFEST.exists():
        return ["missing freeze_judgments.json or freeze_manifest.json"]
    judges = json.loads(cfg.FREEZE_JUDGES.read_text(encoding="utf-8"))
    if sha256(cfg.BLINDED_JSONL) != judges["blinded"]:
        failures.append("blinded file drifted from judgment freeze")
    if judges.get("model") != cfg.LOCKED_MODEL:
        failures.append("frozen model lock drifted")
    for judge in cfg.JUDGES:
        h = hashlib.sha256()
        for p in sorted((cfg.JUDGMENTS_DIR / judge).glob(f"{judge}_batch_*.jsonl")):
            h.update(p.read_bytes())
        if h.hexdigest() != judges["judges"][judge]:
            failures.append(f"judge outputs drifted ({judge})")
    manifest = json.loads(cfg.FREEZE_MANIFEST.read_text(encoding="utf-8"))
    paths = {
        "blinded_stage_c.jsonl": cfg.BLINDED_JSONL,
        "id_map.csv": cfg.ID_MAP_CSV,
        "residual_source.json": cfg.RESIDUAL_SOURCE,
        "consensus_raw.parquet": cfg.FREEZES_DIR / "consensus_raw.parquet",
        "consensus_raw.csv": cfg.TABLES_DIR / "consensus_raw.csv",
        "agreement.csv": cfg.TABLES_DIR / "agreement.csv",
        "judge_behavior.csv": cfg.TABLES_DIR / "judge_behavior.csv",
        "freeze_judgments": cfg.FREEZE_JUDGES,
    }
    for key, expect in manifest.items():
        path = paths.get(key)
        if path is None:
            failures.append(f"unknown manifest key {key}")
            continue
        if sha256(path) != expect:
            failures.append(f"pre-unblinding freeze drift: {key}")
    return failures


def main():
    failures = list(verify_freezes())
    if not HEADLINES_JSON.exists():
        print("FAIL: no headline registry")
        return 1
    reg = json.loads(HEADLINES_JSON.read_text(encoding="utf-8"))
    report_path = cfg.REPORTS_DIR / reg.get("report", "CLAUDE_FINDINGS.md")
    if not report_path.exists():
        print(f"FAIL: report missing: {report_path}")
        return 1
    report = report_path.read_text(encoding="utf-8")
    n_ok = 0
    for h in reg["headlines"]:
        hid = h["id"]
        if hid not in VERIFIERS:
            failures.append(f"{hid}: no verifier implemented")
            continue
        try:
            got = VERIFIERS[hid]()
        except Exception as e:  # noqa: BLE001
            failures.append(f"{hid}: verifier error: {e}")
            continue
        exp = h["expected"]
        if isinstance(exp, (int, float)) and isinstance(got, (int, float)):
            ok_val = abs(float(got) - float(exp)) <= h.get("tol", 0.051)
        else:
            ok_val = got == exp
        if not ok_val:
            failures.append(f"{hid}: expected {exp}, recomputed {got}")
            continue
        disp = h.get("display")
        if disp is not None and disp not in report:
            failures.append(f"{hid}: display {disp!r} not found in {report_path.name}")
            continue
        n_ok += 1
        print(f"ok  {hid}: {got}" + (f"  [{disp}]" if disp else ""))
    print(f"\n{n_ok}/{len(reg['headlines'])} headline numbers verified")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("ALL HEADLINES VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
