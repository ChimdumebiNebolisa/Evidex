"""Unblinding gate + join of frozen silver outputs to Analysis v2 data.

REFUSES to run unless:
- all three stage freeze manifests exist and verify (blinded inputs and
  judge outputs unchanged since freeze)
- consensus exists for all stages
- resolver outputs are complete for all stages
- the final silver freeze manifest exists

Then joins silver labels (per stage consensus, resolver outcomes, stage
changes) to: FEVER gold label, GPT-5.4/-mini transitions and predictions,
cohort type, NLI diagnostics (both models), cosine similarity, evidence
structure and linguistic features. Raw blinded judge files are never touched.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import run_judges  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_silver():
    """Final freeze over consensus + resolver + agreement outputs.

    Refuses to freeze until resolver outputs are complete for all stages
    (freezing an incomplete resolver set would permanently block the
    append-only manifest once the missing outputs arrive)."""
    _require_resolver_complete()
    entries = {}
    for stage in config.STAGES:
        p = config.DERIVED_DIR / f"consensus_stage_{stage}.parquet"
        entries[f"consensus_{stage}"] = sha256(p)
    total = 0
    outdir = config.JUDGMENTS_DIR / "resolver"
    h = hashlib.sha256()
    for p in sorted(outdir.glob("resolver_stage_*.jsonl")):
        h.update(p.read_bytes())
        total += 1
    entries["resolver_combined"] = h.hexdigest()
    entries["resolver_file_count"] = total
    for name in ("agreement_all_stages.csv", "agreement_stage_A.csv",
                 "agreement_stage_B.csv", "agreement_stage_C.csv",
                 "judge_behavior.csv", "judge_verdict_distributions.csv"):
        p = config.TABLES_DIR / name
        if not p.exists():
            raise SystemExit(f"agreement output missing: {name}; "
                             "run agreement analysis before the silver freeze")
        entries[f"table_{name}"] = sha256(p)
    if config.FREEZE_MANIFEST.exists():
        prev = json.loads(config.FREEZE_MANIFEST.read_text(encoding="utf-8"))
        if prev != entries:
            raise SystemExit("silver freeze manifest mismatch: outputs changed after freeze")
        print("Silver freeze verified (unchanged)")
    else:
        config.FREEZE_MANIFEST.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        print(f"Silver FROZEN -> {config.FREEZE_MANIFEST}")
    return entries


def _require_resolver_complete():
    """Refuse to unblind until resolver outputs are complete for all stages."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from resolve_disagreements import validate_resolver_outputs
    for stage in config.STAGES:
        if not (config.DERIVED_DIR / f"resolver_inputs_stage_{stage}.jsonl").exists():
            raise SystemExit(f"resolver inputs missing for stage {stage}; not unblinding")
        missing, bad = validate_resolver_outputs(stage)
        if missing or bad:
            raise SystemExit(f"resolver incomplete for stage {stage} "
                             f"(missing {len(missing)}, malformed {bad}); not unblinding")


def unblind_join():
    # --- Gate: verify every freeze ---
    for stage in config.STAGES:
        run_judges.verify_frozen(stage)
    freeze_silver()
    _require_resolver_complete()

    id_map = pd.read_csv(config.ID_MAP_CSV)
    cohort = pd.read_parquet(config.COHORT_PARQUET).set_index("claim_id")
    enriched = pd.read_parquet(config.PAIRED_ENRICHED).set_index("claim_id")

    rows = []
    for _, m in id_map.iterrows():
        cid, item_id = int(m["claim_id"]), m["item_id"]
        c = cohort.loc[cid]
        e = enriched.loc[cid]
        cons = {}
        for stage in config.STAGES:
            cc = pd.read_parquet(config.DERIVED_DIR / f"consensus_stage_{stage}.parquet"
                                 ).set_index("item_id").loc[item_id]
            cons[stage] = cc
        rows.append({
            "item_id": item_id, "claim_id": cid,
            "cohort": c["cohort"], "regression_type": c["regression_type"],
            "gold_label": c["gold_label"],
            "gpt54_transition": c["gpt-5.4_transition"],
            "gpt54mini_transition": c["gpt-5.4-mini_transition"],
            "consensus_A": cons["A"]["consensus"], "rule_A": cons["A"]["rule"],
            "consensus_B": cons["B"]["consensus"], "rule_B": cons["B"]["rule"],
            "consensus_C": cons["C"]["consensus"], "rule_C": cons["C"]["rule"],
            "sd_confidence_A": cons["A"]["sd_confidence"],
            "sd_confidence_C": cons["C"]["sd_confidence"],
            "nli_disagrees": bool(e["nli_disagrees_with_fever"]),
            "nli2_disagrees": bool(e["nli2_disagrees_with_fever"]),
            "weakly_warranted": bool(e["weakly_warranted"]),
            "cosine_sim": float(e["cosine_sim_claim_evidence"]),
            "evidence_set_size": int(c["evidence_set_size"]),
            "n_evidence_pages": int(c["n_evidence_pages"]),
            "claim_len_words": int(c["claim_len_words"]),
            "evidence_len_words": int(c["evidence_len_words"]),
        })
    df = pd.DataFrame(rows)

    # Resolver outcomes joined by item_id.
    res_rows = []
    for stage in config.STAGES:
        for p in sorted((config.JUDGMENTS_DIR / "resolver").glob(f"resolver_stage_{stage}_*.jsonl")):
            arr = json.loads(p.read_text(encoding="utf-8").strip() or "[]")
            for r in arr:
                res_rows.append({"item_id": r["item_id"], "stage": stage,
                                 "resolver_outcome": r["resolver_outcome"],
                                 "disagreement_type": r["disagreement_type"],
                                 "resolver_confidence": r["confidence"]})
    if res_rows:
        rr = pd.DataFrame(res_rows)
        for stage in config.STAGES:
            sub = rr[rr["stage"] == stage].set_index("item_id")
            df[f"resolver_outcome_{stage}"] = df["item_id"].map(sub["resolver_outcome"])
            df[f"disagreement_type_{stage}"] = df["item_id"].map(sub["disagreement_type"])

    # Consensus-level stage-change flags.
    cc = pd.read_parquet(config.DERIVED_DIR / "consensus_changes.parquet").set_index("item_id")
    for col in ["resolved_by_titles", "resolved_only_by_structure",
                "still_ambiguous_after_C", "reversed_after_titles", "reversed_after_structure"]:
        df[col] = df["item_id"].map(cc[col]).astype(bool)

    # Cautious derived silver taxonomy (rules, never 'ground truth').
    def taxonomy(r):
        if r["still_ambiguous_after_C"]:
            if r["nli_disagrees"] and r["nli2_disagrees"]:
                return "silver_partial_or_ambiguous_warrant"
            return "silver_partial_or_ambiguous_warrant"
        if r["resolved_only_by_structure"] or r["reversed_after_structure"] or \
                (r["consensus_A"] in ("Ambiguous", "Unresolved") and
                 r["consensus_C"] in ("Supported", "Refuted")):
            return "silver_structured_evidence_sensitive"
        if r["reversed_after_titles"] or r["resolved_by_titles"]:
            return "silver_title_context_sensitive"
        # After full structure judges still give a decisive verdict.
        if r["cohort"] in ("regression", "resistant") and \
                r["consensus_C"] in ("Supported", "Refuted"):
            return "silver_clear_evidence_utilization_failure"
        return "silver_unresolved"
    df["silver_taxonomy"] = df.apply(taxonomy, axis=1)

    df.to_parquet(config.UNBLINDED_PARQUET, index=False)
    df.to_csv(config.TABLES_DIR / "silver_by_cohort_full.csv", index=False)
    print(f"Unblinded join: {len(df)} items -> {config.UNBLINDED_PARQUET}")
    return df


if __name__ == "__main__":
    if "--freeze-only" in sys.argv:
        freeze_silver()
    else:
        unblind_join()
