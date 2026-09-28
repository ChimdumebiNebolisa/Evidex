"""Task-specific, offline audit and rerun preparation (no model calls).

All writes are confined to corrections_v2/generated and corrections_v2/blind_io.
Old packets and judgments are inputs, never corrected in place.
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SV = ROOT / "silver_adjudication_v1"
OUT = ROOT / "corrections_v2/generated"
sys.path.insert(0, str(ROOT / "corrections_v2"))
from provenance import (digest, write_json, verify_historical, verify_snapshot,
                        implementation_inventory, seal_outputs)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SV / "src"))
from fever_evidence import evidence_set_id, selected_evidence_set
from resolve_gold_evidence import parse_evidence_sets
from reconstruct_evidence import load_needed_pages, normalized_page, reconstruct, parse_wiki_line
from taxonomy_legacy_v1 import taxonomy_row
from taxonomy_v2 import classify


def read_jsonl(path):
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def write_rows(name, rows):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def flags(a, b, c):
    dec = {"Supported", "Refuted"}
    return {"consensus_A": a, "consensus_B": b, "consensus_C": c,
            "still_ambiguous_after_C": c not in dec,
            "resolved_by_titles": a not in dec and b in dec,
            "resolved_only_by_structure": b not in dec and c in dec,
            "reversed_after_titles": a in dec and b in dec and a != b,
            "reversed_after_structure": b in dec and c in dec and b != c}


def behavior():
    data = pd.read_csv(ROOT / "experiment_results_balanced_10000_v1.csv")
    assert len(data) == 40000 and not data.duplicated(["claim_id", "model", "condition"]).any()
    assert data.groupby("claim_id")["true_label"].nunique().eq(1).all()
    assert data.model_output.isin(["Supported", "Refuted"]).all()
    data["recomputed_correct"] = data.model_output == data.true_label
    assert (data.recomputed_correct == data.correct.eq("Yes")).all()
    original = pd.read_csv(ROOT / "experiment_tracker_with_evidence_balanced_10000_v1.csv").set_index("claim_id")
    for column in ("gold_evidence", "evidence_sentences_json", "evidence_pages_json", "evidence_set_id"):
        assert data[column].eq(data.claim_id.map(original[column])).all(), column
    results, regressions = {}, {}
    for model, sub in data.groupby("model"):
        p = sub.pivot(index="claim_id", columns="condition", values="recomputed_correct")
        assert len(p) == 10000 and not p.isna().any().any()
        a, b = p.claim_only, p.claim_plus_evidence
        results[model] = {"claim_only_correct": int(a.sum()), "evidence_correct": int(b.sum()),
                          "persistent_success": int((a & b).sum()), "improvement": int((~a & b).sum()),
                          "persistent_failure": int((~a & ~b).sum()), "regression": int((a & ~b).sum())}
        regressions[model] = set(p.index[a & ~b])
    a, b = regressions["gpt-5.4"], regressions["gpt-5.4-mini"]
    results["union"] = {"n": len(a | b), "shared": len(a & b), "gpt54_only": len(a - b), "mini_only": len(b - a)}
    write_json(OUT / "behavioral_counts.json", results)
    return a | b


def pointer_key(records):
    return [(normalized_page(r["page_title"]), r["line_index"]) for r in records]


def evidence(regression_ids, snapshot=None):
    tracker = pd.read_csv(ROOT / "experiment_tracker_with_evidence_balanced_10000_v1.csv").set_index("claim_id")
    source = pd.read_csv(ROOT / "fever_balanced_10000_v1_source.csv").set_index("claim_id")
    idmap = pd.read_csv(SV / "data/derived/id_map.csv")
    stages = {s: {r["item_id"]: r for r in read_jsonl(SV / f"data/blinded/stage_{s}.jsonl")} for s in "abc"}
    needed = {page for cid in idmap.claim_id for es in parse_evidence_sets(source.loc[cid, "raw_evidence"])
              for page, _ in es["pointers"]}
    pages, source_paths = load_needed_pages(needed, snapshot)
    audits, validation, b_out, c_out = [], [], {}, {}
    for m in idmap.to_dict("records"):
        cid, iid = m["claim_id"], m["item_id"]
        row = tracker.loc[cid].to_dict()
        assert json.loads(row["raw_evidence"]) == json.loads(source.loc[cid, "raw_evidence"])
        b, c, checks = reconstruct(row, stages["a"][iid], pages)
        b_out[iid], c_out[iid] = b, c
        for check in checks:
            validation.append(dict(item_id=iid, claim_id=cid, **check))
        old = stages["c"][iid]["structured_evidence"]
        canonical = c["structured_evidence"]
        chosen_mismatch = [r["sentence"] for r in old["chosen_set"]] != json.loads(row["evidence_sentences_json"])
        pointer_match = pointer_key(old["chosen_set"]) == pointer_key(canonical["chosen_set"])
        causes = Counter()
        for previous in old["chosen_set"]:
            page, index = previous["page_title"], previous["line_index"]
            lines = pages.get(normalized_page(page))
            actual = None if lines is None else parse_wiki_line(lines, index)
            if previous["sentence"] == actual:
                continue
            if previous["sentence"] is None:
                causes["unavailable_in_old_packet"] += 1
                # Observable frozen-packet absence + archived recovery. Do not
                # depend on a gitignored cache existing on this machine.
                if lines is not None:
                    causes["title_normalization_or_cache_recovery"] += 1
            elif actual is None:
                causes["unavailable_in_local_archive"] += 1
            else:
                chunks = [x.split("\t") for x in lines.split("\n") if x.split("\t")[0] == str(index)]
                causes["link_field_extraction" if chunks and chunks[0][-1] == previous["sentence"] else "other_text_mismatch"] += 1
        annotation_keys = [pointer_key(canonical["chosen_set"])] + [pointer_key(alt) for alt in canonical["alternative_sets"]]
        old_alternatives_changed = 0
        old_alternatives_missing = 0
        alternative_causes = Counter()
        for alt in old["alternative_sets"]:
            assert pointer_key(alt) in annotation_keys, (iid, "unknown alternative pointers")
            for r in alt:
                lines = pages.get(normalized_page(r["page_title"]))
                actual = None if lines is None else parse_wiki_line(lines, r["line_index"])
                old_alternatives_changed += r["sentence"] != actual
                old_alternatives_missing += actual is None
                if r["sentence"] != actual:
                    if r["sentence"] is None:
                        alternative_causes["unavailable_in_old_packet"] += 1
                    elif actual is None:
                        alternative_causes["unavailable_in_local_archive"] += 1
                    else:
                        chunks = [x.split("\t") for x in lines.split("\n") if x.split("\t")[0] == str(r["line_index"])]
                        alternative_causes["link_field_extraction" if chunks and chunks[0][-1] == r["sentence"] else "other_text_mismatch"] += 1
        new_sentences = set(json.loads(row["evidence_sentences_json"]))
        adds = any(r["sentence"] is not None and r["sentence"] not in new_sentences
                   for alt in canonical["alternative_sets"] for r in alt)
        old_adds = any(r["sentence"] is not None and r["sentence"] not in new_sentences
                       for alt in old["alternative_sets"] for r in alt)
        audits.append({"item_id": iid, "claim_id": cid, "regression": cid in regression_ids,
                       "evidence_set_id": row["evidence_set_id"],
                       "selected_annotation_index": canonical["chosen_annotation_index"],
                       "ordered_pointers_match": pointer_match, "chosen_text_mismatch": chosen_mismatch,
                       "mismatch_causes": dict(causes), "stage_b_changed": b != stages["b"][iid],
                       "stage_c_changed": c != stages["c"][iid],
                       "alternative_sentences_changed": old_alternatives_changed,
                       "alternative_sentences_unavailable": old_alternatives_missing,
                       "alternative_mismatch_causes": dict(alternative_causes),
                       "old_alternative_sets": len(old["alternative_sets"]),
                       "corrected_alternative_sets": len(canonical["alternative_sets"]),
                       "c_adds_sentence_text": adds, "old_c_adds_sentence_text": old_adds,
                       "old_chosen": old["chosen_set"], "corrected_chosen": canonical["chosen_set"]})
    write_rows("evidence_audit.jsonl", audits)
    write_rows("sentence_validation.jsonl", validation)
    write_rows("stage_b_corrected.jsonl", list(b_out.values()))
    write_rows("stage_c_corrected.jsonl", list(c_out.values()))
    summary = {"claims": len(audits), "chosen_mismatches": sum(r["chosen_text_mismatch"] for r in audits),
               "regression_chosen_mismatches": sum(r["chosen_text_mismatch"] and r["regression"] for r in audits),
               "pointer_mismatches": sum(not r["ordered_pointers_match"] for r in audits),
               "stage_b_changed": sum(r["stage_b_changed"] for r in audits),
               "stage_c_changed": sum(r["stage_c_changed"] for r in audits),
               "claims_with_alternative_text_changes": sum(r["alternative_sentences_changed"] > 0 for r in audits),
               "claims_with_new_sentences_at_C": sum(r["c_adds_sentence_text"] for r in audits),
               "chosen_mismatch_cause_claim_counts": dict(Counter(k for r in audits for k in r["mismatch_causes"])),
               "alternative_mismatch_cause_claim_counts": dict(Counter(k for r in audits for k in r["alternative_mismatch_causes"])),
               "sentence_validation_status": dict(Counter(r["role"] + ":" + r["status"] for r in validation))}
    write_json(OUT / "evidence_summary.json", summary)
    return audits, b_out, c_out, source_paths


def consensus_from_raw(panel_root, stage, expected):
    groups = {}
    for path in sorted((panel_root / "judgments" / f"stage_{stage.lower()}").glob("*_batch_*.jsonl")):
        for r in read_jsonl(path):
            key = (r["item_id"], r["judge_id"])
            if key in groups and groups[key] != r:
                raise ValueError(f"conflicting active judgment:{path}:{key}")
            assert r["stage"] == stage
            groups.setdefault(key, r)
    by_item = {}
    for (iid, _), r in groups.items():
        by_item.setdefault(iid, []).append(r)
    assert set(by_item) == set(expected)
    result = {}
    for iid, rows in by_item.items():
        assert len(rows) == 5
        counts = Counter(r["verdict"] for r in rows)
        mode, n = counts.most_common(1)[0]
        weak = sum(r["evidence_sufficiency"] in {"partial_or_ambiguous", "probably_insufficient", "clearly_insufficient"} for r in rows)
        d = max(counts["Supported"], counts["Refuted"])
        if d >= 4:
            value = "Supported" if counts["Supported"] > counts["Refuted"] else "Refuted"
        elif (mode == "Ambiguous" and n >= 2) or weak >= 3:
            value = "Ambiguous"
        else:
            value = "Unresolved"
        result[iid] = value
    return result


def taxonomy(audits):
    audit = {r["item_id"]: r for r in audits}
    outputs, summaries = [], {}
    panels = [
        ("grok", SV / "cursor_panel", "silver_unblinded.parquet", "item_id", "item_id", "silver_taxonomy"),
        ("claude", SV / "claude_full_regression_panel", "claude_full_unblinded.parquet", "claude_item_id", "source_item_id", "claude_taxonomy"),
    ]
    for name, root, frozen, idcol, sourcecol, taxcol in panels:
        data = pd.read_parquet(root / "freezes" / frozen)
        cons = {s: consensus_from_raw(root, s, data[idcol]) for s in "ABC"}
        subset = []
        for row in data.to_dict("records"):
            iid = row[idcol]
            abc = [cons[s][iid] for s in "ABC"]
            assert abc == [row[f"consensus_{s}"] for s in "ABC"]
            legacy = taxonomy_row(flags(*abc), row["cohort"])
            assert legacy == row[taxcol]
            source = audit[row[sourcecol]]
            corrected = classify(*abc, row["gold_label"], row["cohort"],
                                 c_adds_text=source["old_c_adds_sentence_text"], input_version="historical_v1_packets")
            out = dict(panel=name, item_id=iid, source_item_id=row[sourcecol],
                       claim_id=row["claim_id"], cohort=row["cohort"], gold_label=row["gold_label"],
                       legacy=legacy, **flags(*abc), **corrected,
                       corrected_packet_result="PENDING_FRESH_JUDGMENTS")
            outputs.append(out)
            if row["cohort"] == "regression":
                subset.append(out)
        utilization = [r for r in subset if r["legacy"] == "silver_clear_evidence_utilization_failure"]
        summaries[name] = {"regressions": len(subset), "legacy_utilization": len(utilization),
                           "legacy_utilization_disagrees_fever": sum(not r["agrees_fever_C"] for r in utilization),
                           "legacy_title_resolutions_absorbed": sum(r["title_resolution"] and r["legacy"] == "silver_structured_evidence_sensitive" for r in subset),
                           "proposed_rule_only_on_old_inputs": dict(Counter(r["category"] for r in subset)),
                           "sentence_only_utilization_compatible": sum(r["sentence_only_utilization_compatible"] for r in subset)}
    pd.DataFrame(outputs).to_csv(OUT / "taxonomy_rule_only.csv", index=False,
                               encoding="utf-8", lineterminator="\n")
    write_json(OUT / "taxonomy_summary.json", summaries)
    return outputs


def prepare_reruns(audits, b_out, c_out):
    filtered = set(json.loads((SV / "data/derived/provider_filtered.json").read_text())["items"])
    specs = [("p01", "grok", SV / "cursor_panel", None, 100),
             ("p02", "claude_full", SV / "claude_full_regression_panel", "CF", 77),
             ("p03", "claude_historical_residual_optional", SV / "claude_residual_panel", "CR", 77)]
    rubric = (SV / "prompts/judge_rubric.md").read_text(encoding="utf-8")
    jobs, panels = [], []
    audit = {r["item_id"]: r for r in audits}
    for namespace, name, root, prefix, batch_size in specs:
        lock = json.loads((root / "config.json").read_text())
        if prefix:
            mapping = pd.read_csv(root / "data/id_map.csv").to_dict("records")
            ids = [(r["claude_item_id"], r["source_item_id"]) for r in mapping]
            old_c = {r["item_id"]: r for r in read_jsonl(root / "data/blinded_stage_c.jsonl")}
            shared_c = {r["item_id"]: r for r in read_jsonl(SV / "data/blinded/stage_c.jsonl")}
            for iid, sa in ids:
                assert dict(old_c[iid], item_id=sa) == shared_c[sa]
            if prefix == "CF":
                for stage, corrected in (("a", None), ("b", b_out)):
                    shared = {r["item_id"]: r for r in read_jsonl(SV / f"data/blinded/stage_{stage}.jsonl")}
                    old_stage = {r["item_id"]: r for r in read_jsonl(root / f"data/blinded_stage_{stage}.jsonl")}
                    for iid, sa in ids:
                        assert dict(old_stage[iid], item_id=sa) == shared[sa]
                        if corrected is not None:
                            assert corrected[sa] == shared[sa]
        else:
            ids = [(iid, iid) for iid in c_out if iid not in filtered]
        b_changed = [(iid, sa) for iid, sa in ids if audit[sa]["stage_b_changed"]]
        stages = ["B", "C"] if b_changed and prefix != "CR" else ["C"]
        panel_jobs = []
        for stage in stages:
            # Full batches: changing any item can affect its batch neighbors.
            records = [dict((b_out if stage == "B" else c_out)[sa], item_id=iid) for iid, sa in ids]
            for judge in range(1, 6):
                for start in range(0, len(records), batch_size):
                    batch = records[start:start + batch_size]
                    job_id = f"{namespace}_{stage}_j{judge}_b{start // batch_size + 1:02}"
                    rel = f"corrections_v2/blind_io/{namespace}/stage_{stage.lower()}/{job_id}"
                    packet_path, output_path = rel + ".json", rel + ".output.json"
                    packet = {"judge_id": f"judge_{judge}", "stage": stage,
                              "output_path": output_path, "n_items": len(batch),
                              "item_ids": [r["item_id"] for r in batch], "items": batch, "rubric": rubric,
                              "disclosure_note": f"Stage {stage}. Judge only supplied fields. Null text means unavailable; do not fill it using outside knowledge."}
                    write_json(ROOT / packet_path, packet)
                    prompt = (f"Read exactly {packet_path} and no other file. Follow its rubric. "
                              "Do not browse, search the repository, use git, or inspect any previous judgments. "
                              f"Write one JSON array of {len(batch)} judgments to {output_path}, with the packet's judge_id and stage. "
                              "Use a fresh isolated context. Return only WROTE <count> records.")
                    job = {"job_id": job_id, "panel": name, "model": lock["model"],
                           "stage": stage, "judge_id": f"judge_{judge}", "packet": packet_path,
                           "packet_sha256": digest(ROOT / packet_path), "output": output_path,
                           "item_ids": packet["item_ids"], "n_judgments": len(batch), "launch_prompt": prompt,
                           "execution_status": "NOT_LAUNCHED"}
                    jobs.append(job)
                    panel_jobs.append(job)
        panels.append({"panel": name, "model": lock["model"], "items": len(ids),
                       "source_ids": [sa for _, sa in ids], "item_ids": [iid for iid, _ in ids],
                       "chosen_text_affected": sum(audit[sa]["chosen_text_mismatch"] for _, sa in ids),
                       "stage_b_changed": len(b_changed), "stages_to_rerun": stages,
                       "calls_without_retries": len(panel_jobs), "judgments": sum(j["n_judgments"] for j in panel_jobs),
                       "optional": prefix == "CR"})
    manifest = {"version": "correction_v2", "status": "PREPARED_NOT_EXECUTED",
                "method": "one fresh Cursor Task context per job; five independent contexts per batch; no simulated panel",
                "retry_limit_per_job": 2, "panels": panels, "jobs": jobs,
                "retained_stage_freezes": {p.relative_to(ROOT).as_posix():
                    {"identity": "historical baseline inventory", "path": p.relative_to(ROOT).as_posix()}
                    for root in (SV / "cursor_panel", SV / "claude_full_regression_panel")
                    for p in (root / "freezes/freeze_stage_A.json", root / "freezes/freeze_stage_B.json")},
                "provider_filtered_not_retried": sorted(filtered),
                "resolver": "Optional historical Grok resolver sensitivity: select non-high-consensus cases only after corrected C. Count unknown until fresh judgments. Primary taxonomy uses raw consensus.",
                "new_residual_cohort": "After corrected Grok C, select new residuals; do not reuse the old 231 as that cohort. Five new Claude judgments per new-cohort item; batch size 77; count pending.",
                "model_availability": "Not tested by inference. No substitution; unavailable locks require separately versioned replication.",
                "cost": "Not estimated: historical execution used Cursor Task routing; no verified per-call pricing."}
    write_json(OUT / "rerun_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=Path, default=ROOT / "corrections_v2/inputs/historical_pages.json",
                        help="Pinned local snapshot; verified before writes; no shard fallback")
    args = parser.parse_args()
    # This gate precedes every output write. Never trust a freshly observed hash
    # as the expected historical identity.
    historical = verify_historical(ROOT)
    snapshot = verify_snapshot(args.pages, ROOT)
    if any((ROOT / "corrections_v2/blind_io").rglob("*.output.json")):
        raise SystemExit("Delivered judgments exist; do not regenerate their inputs in place.")
    OUT.mkdir(parents=True, exist_ok=True)
    regression_ids = behavior()
    audits, b_out, c_out, archive_sources = evidence(regression_ids, args.pages)
    taxonomy(audits)
    reruns = prepare_reruns(audits, b_out, c_out)
    write_json(OUT / "historical_integrity.json", historical)
    write_json(OUT / "snapshot_integrity.json", snapshot)
    write_json(OUT / "code_hashes.json", implementation_inventory(ROOT))
    write_json(OUT / "source_revision.json", {
        "scientific_artifact_commit": historical["scientific_artifact_commit"],
        "source_baseline_commit": historical["source_baseline_commit"],
        "correction_implementation_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "implementation_identity": "generated/code_hashes.json pins actual LF-equivalent code/configuration, including uncommitted edits",
        "snapshot_source_commit": snapshot["source_commit"]})
    # Complete downstream writes in one command, then seal exact output bytes.
    from build_report_data import main as build_report
    from audit_freezes import audit as audit_freezes
    build_report()
    audit_freezes()
    write_json(OUT / "verification_results.json", {
        "historical_files_verified": len(historical["files"]),
        "exact_recorded_bytes": historical["exact_recorded_bytes"],
        "eol_only_equivalent": historical["eol_only_equivalent"],
        "prepared_jobs": len(reruns["jobs"]), "required_jobs": 70,
        "required_judgments": 6430, "optional_jobs": 15, "optional_judgments": 1155,
        "inference_launched_by_workflow": 0, "corrected_consensus_available": False})
    seal_outputs(ROOT)
    from verify_outputs import main as verify_outputs
    verify_outputs()
    print(json.dumps({"evidence": json.loads((OUT / "evidence_summary.json").read_text()),
                      "taxonomy": json.loads((OUT / "taxonomy_summary.json").read_text()),
                      "reruns": [{k: v for k, v in p.items() if not k.endswith("ids")} for p in reruns["panels"]]}, indent=2))


if __name__ == "__main__":
    main()
