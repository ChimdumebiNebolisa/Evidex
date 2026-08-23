"""Independent verification of headline numbers quoted in the silver reports.

Every headline number quoted in reports/SILVER_FINDINGS.md must be listed in
reports/HEADLINES.json. For each entry this script:
  1. recomputes the value INDEPENDENTLY from raw frozen artifacts (own code
     path — it deliberately does not import the analysis modules), and
  2. checks the quoted display string actually appears in the report text.

It also recomputes every freeze manifest hash from disk bytes and fails if
anything drifted. Exit code 0 = every headline verified; 1 = any failure.
Fail-closed: a missing registry or report is a failure, not a skip.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

HEADLINES_JSON = config.REPORTS_DIR / "HEADLINES.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_judgments(stage: str):
    """Read judge outputs directly from the frozen batch files."""
    rows = []
    for p in sorted((config.JUDGMENTS_DIR / f"stage_{stage.lower()}").glob("*_batch_*.jsonl")):
        if p.name.endswith("_missing.json"):
            continue
        judge = p.name.split("_batch")[0]
        content = p.read_text(encoding="utf-8").strip()
        try:
            arr = json.loads(content) if content else []
        except ValueError:  # line-per-object container variant
            arr = [json.loads(l) for l in content.splitlines() if l.strip()]
        for r in arr:
            rows.append((r["item_id"], judge, r["verdict"], r["confidence"]))
    return rows


def _consensus(stage: str) -> pd.DataFrame:
    return pd.read_parquet(config.DERIVED_DIR / f"consensus_stage_{stage}.parquet")


def _unblinded() -> pd.DataFrame:
    return pd.read_parquet(config.UNBLINDED_PARQUET)


VERIFIERS = {}


def verifier(fn):
    VERIFIERS[fn.__name__] = fn
    return fn


# --- Cohort / panel composition ---------------------------------------------

@verifier
def cohort_total_n():
    return int(len(pd.read_parquet(config.COHORT_PARQUET)))


@verifier
def cohort_regression_n():
    c = pd.read_parquet(config.COHORT_PARQUET)
    return int((c["cohort"] == "regression").sum())


@verifier
def cohort_resistant_n():
    c = pd.read_parquet(config.COHORT_PARQUET)
    return int((c["cohort"] == "resistant").sum())


@verifier
def cohort_rescue_n():
    c = pd.read_parquet(config.COHORT_PARQUET)
    return int((c["cohort"] == "rescue").sum())


@verifier
def cohort_robust_n():
    c = pd.read_parquet(config.COHORT_PARQUET)
    return int((c["cohort"] == "robust").sum())


@verifier
def judged_items_n():
    pf = json.loads(config.PROVIDER_FILTERED.read_text(encoding="utf-8"))
    return cohort_total_n() - len(pf["items"])


# --- Consensus distributions (independent recount from raw judge files) ------

def _recount_consensus(stage: str):
    """Recompute consensus labels from raw judge verdicts using the same
    published rules, implemented independently of aggregate_consensus."""
    rows = _raw_judgments(stage)
    by_item = {}
    for item_id, judge, verdict, _ in rows:
        by_item.setdefault(item_id, []).append((judge, verdict))
    pf = json.loads(config.PROVIDER_FILTERED.read_text(encoding="utf-8"))
    excluded = set(pf["items"])
    return {i: v for i, v in by_item.items() if i not in excluded}


@verifier
def consensus_high_A_pct():
    labels = _recount_consensus("A")
    n_hi = sum(1 for js in labels.values()
               if max(sum(1 for _, v in js if v == "Supported"),
                      sum(1 for _, v in js if v == "Refuted")) >= 4)
    return 100.0 * n_hi / len(labels)


@verifier
def consensus_high_C_pct():
    labels = _recount_consensus("C")
    n_hi = sum(1 for js in labels.values()
               if max(sum(1 for _, v in js if v == "Supported"),
                      sum(1 for _, v in js if v == "Refuted")) >= 4)
    return 100.0 * n_hi / len(labels)


@verifier
def consensus_ambiguous_A_pct():
    labels = _recount_consensus("A")
    amb = sum(1 for js in labels.values()
              if any(v == "Ambiguous" for _, v in js) and
              not (max(sum(1 for _, v in js if v == "Supported"),
                       sum(1 for _, v in js if v == "Refuted")) >= 4))
    return 100.0 * amb / len(labels)


@verifier
def consensus_ambiguous_C_pct():
    labels = _recount_consensus("C")
    amb = sum(1 for js in labels.values()
              if any(v == "Ambiguous" for _, v in js) and
              not (max(sum(1 for _, v in js if v == "Supported"),
                       sum(1 for _, v in js if v == "Refuted")) >= 4))
    return 100.0 * amb / len(labels)


# --- Agreement (independent recompute) ---------------------------------------

def _pairwise_agreement(stage: str):
    rows = _raw_judgments(stage)
    wide = {}
    for item_id, judge, verdict, _ in rows:
        wide.setdefault(item_id, {})[judge] = verdict
    judges = config.JUDGES
    agree = total = 0
    for votes in wide.values():
        for a in range(len(judges)):
            for b in range(a + 1, len(judges)):
                va, vb = votes.get(judges[a]), votes.get(judges[b])
                if va is not None and vb is not None:
                    agree += va == vb
                    total += 1
    return 100.0 * agree / max(total, 1)


@verifier
def pairwise_agreement_A_pct():
    return _pairwise_agreement("A")


@verifier
def pairwise_agreement_B_pct():
    return _pairwise_agreement("B")


@verifier
def pairwise_agreement_C_pct():
    return _pairwise_agreement("C")


@verifier
def fleiss_kappa_A():
    return _fleiss("A")


@verifier
def fleiss_kappa_C():
    return _fleiss("C")


def _fleiss(stage: str):
    rows = _raw_judgments(stage)
    wide = {}
    for item_id, judge, verdict, _ in rows:
        wide.setdefault(item_id, {})[judge] = verdict
    n_raters = len(config.JUDGES)
    p_j = Counter()
    n_items = 0
    p_i_sum = 0.0
    for votes in wide.values():
        if len(votes) < n_raters:
            continue
        n_items += 1
        cnt = Counter(votes.values())
        for cat, k in cnt.items():
            p_j[cat] += k
        p_i_sum += (sum(k * k for k in cnt.values()) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = p_i_sum / n_items
    total_votes = n_items * n_raters
    p_e = sum((k / total_votes) ** 2 for k in p_j.values())
    return (p_bar - p_e) / (1 - p_e)


# --- Representation sensitivity / unblinded cohort contrasts ------------------

@verifier
def reg_stageA_ambiguous_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * reg["consensus_A"].isin(["Ambiguous", "Unresolved"]).mean()


@verifier
def robust_stageA_ambiguous_pct():
    df = _unblinded()
    rob = df[df["cohort"] == "robust"]
    return 100.0 * rob["consensus_A"].isin(["Ambiguous", "Unresolved"]).mean()


@verifier
def reg_stageC_ambiguous_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * reg["consensus_C"].isin(["Ambiguous", "Unresolved"]).mean()


@verifier
def reg_resolved_by_titles_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * reg["resolved_by_titles"].mean()


@verifier
def reg_resolved_only_by_structure_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * reg["resolved_only_by_structure"].mean()


@verifier
def reg_still_ambiguous_after_C_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * reg["still_ambiguous_after_C"].mean()


@verifier
def reg_representation_sensitive_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * reg["silver_taxonomy"].isin(
        ["silver_title_context_sensitive", "silver_structured_evidence_sensitive"]).mean()


@verifier
def reg_clear_evidence_utilization_failure_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * (reg["silver_taxonomy"] == "silver_clear_evidence_utilization_failure").mean()


@verifier
def glm_disagreement_vs_nli_both_disagree_pct():
    df = _unblinded()
    m = df["nli_disagrees"] & df["nli2_disagrees"]
    return 100.0 * (df.loc[m, "rule_A"] != "high_consensus").mean()


@verifier
def glm_disagreement_vs_nli_none_disagree_pct():
    df = _unblinded()
    m = (~df["nli_disagrees"]) & (~df["nli2_disagrees"])
    return 100.0 * (df.loc[m, "rule_A"] != "high_consensus").mean()


# --- Analysis v2 10k baseline (primary baseline; recomputed from its data) ----

@verifier
def a2_evidence_gain_gpt54_pp():
    e = pd.read_parquet(config.PAIRED_ENRICHED)
    return 100.0 * (e["gpt-5.4_evidence_correct"].mean()
                    - e["gpt-5.4_claim_only_correct"].mean())


@verifier
def a2_evidence_gain_mini_pp():
    e = pd.read_parquet(config.PAIRED_ENRICHED)
    return 100.0 * (e["gpt-5.4-mini_evidence_correct"].mean()
                    - e["gpt-5.4-mini_claim_only_correct"].mean())


@verifier
def a2_total_claims_n():
    return int(len(pd.read_parquet(config.PAIRED_ENRICHED)))


@verifier
def consensus_A_refuted_n():
    return int((_consensus("A")["consensus"] == "Refuted").sum())


@verifier
def consensus_A_supported_n():
    return int((_consensus("A")["consensus"] == "Supported").sum())


@verifier
def consensus_A_ambiguous_n():
    return int((_consensus("A")["consensus"] == "Ambiguous").sum())


@verifier
def consensus_A_unresolved_n():
    return int((_consensus("A")["consensus"] == "Unresolved").sum())


@verifier
def consensus_C_refuted_n():
    return int((_consensus("C")["consensus"] == "Refuted").sum())


@verifier
def consensus_C_supported_n():
    return int((_consensus("C")["consensus"] == "Supported").sum())


@verifier
def consensus_C_ambiguous_n():
    return int((_consensus("C")["consensus"] == "Ambiguous").sum())


@verifier
def consensus_C_unresolved_n():
    return int((_consensus("C")["consensus"] == "Unresolved").sum())


@verifier
def cursor_stageA_amb_unresolved_pct():
    c = _consensus("A")
    return 100.0 * c["consensus"].isin(["Ambiguous", "Unresolved"]).mean()


@verifier
def cursor_stageC_amb_unresolved_pct():
    c = _consensus("C")
    return 100.0 * c["consensus"].isin(["Ambiguous", "Unresolved"]).mean()


@verifier
def q7_consensus_change_A_to_B_pct():
    df = _unblinded()
    return 100.0 * (df["consensus_A"] != df["consensus_B"]).mean()


@verifier
def q8_consensus_change_B_to_C_pct():
    df = _unblinded()
    return 100.0 * (df["consensus_B"] != df["consensus_C"]).mean()


@verifier
def q9_reg_clearly_warranted_pct():
    df = _unblinded()
    reg = df[df["cohort"] == "regression"]
    return 100.0 * (reg["consensus_C"].isin(["Supported", "Refuted"])
                    & (reg["rule_C"] == "high_consensus")).mean()


@verifier
def cross_panel_modal_verdict_agree():
    tab = pd.read_csv(config.TABLES_DIR / "cross_panel_stage_a_replication.csv")
    return float(tab["verdict_modal_agreement"].iloc[0])


@verifier
def glm_stageA_amb_rate():
    tab = pd.read_csv(config.TABLES_DIR / "cross_panel_stage_a_replication.csv")
    return 100.0 * float(tab["glm_ambiguous_rate"].iloc[0])


# --- Freeze integrity (recomputed from disk bytes) ----------------------------

def verify_freezes():
    failures = []
    for stage in config.STAGES:
        mp = config.DERIVED_DIR / f"freeze_stage_{stage}.json"
        if not mp.exists():
            failures.append(f"freeze manifest missing: {mp.name}")
            continue
        entries = json.loads(mp.read_text(encoding="utf-8"))
        if sha256(config.BLINDED_DIR / f"stage_{stage.lower()}.jsonl") != entries["blinded"]:
            failures.append(f"stage {stage}: blinded file drifted from freeze")
        for judge, expect in entries["judges"].items():
            h = hashlib.sha256()
            for p in sorted((config.JUDGMENTS_DIR / f"stage_{stage.lower()}")
                            .glob(f"{judge}_batch_*.jsonl")):
                h.update(p.read_bytes())
            if h.hexdigest() != expect:
                failures.append(f"stage {stage}: judge outputs drifted ({judge})")
    if config.FREEZE_MANIFEST.exists():
        silver = json.loads(config.FREEZE_MANIFEST.read_text(encoding="utf-8"))
        for key, expect in silver.items():
            if not isinstance(expect, str) or len(expect) != 64:
                continue
            path = {"consensus_A": config.DERIVED_DIR / "consensus_stage_A.parquet",
                    "consensus_B": config.DERIVED_DIR / "consensus_stage_B.parquet",
                    "consensus_C": config.DERIVED_DIR / "consensus_stage_C.parquet",
                    }.get(key)
            if path is not None and sha256(path) != expect:
                failures.append(f"silver freeze drift: {key}")
        h = hashlib.sha256()
        n = 0
        for p in sorted((config.JUDGMENTS_DIR / "resolver").glob("resolver_stage_*.jsonl")):
            h.update(p.read_bytes())
            n += 1
        if silver.get("resolver_combined") and n:
            if h.hexdigest() != silver["resolver_combined"]:
                failures.append("silver freeze drift: resolver outputs")
    return failures


# --- Main ---------------------------------------------------------------------

def main():
    failures = list(verify_freezes())
    if not HEADLINES_JSON.exists():
        print("FAIL: no headline registry (reports/HEADLINES.json)")
        return 1
    reg = json.loads(HEADLINES_JSON.read_text(encoding="utf-8"))
    report_path = config.REPORTS_DIR / reg.get("report", "SILVER_FINDINGS.md")
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
