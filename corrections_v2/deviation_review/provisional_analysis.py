"""PROVISIONAL deviation analysis of correction-v2 Stage C. NOT the frozen-protocol primary analysis.

Uses the frozen analysis code unchanged (imported, never edited) on the 70 accepted outputs even
though frozen-protocol execution provenance is incomplete for six jobs (retry cap) and the
first-schema-valid rule was not followed for p02_C_j2_b02, p02_C_j2_b03 and p01_C_j5_b09. Writes only under
corrections_v2/deviation_review/provisional_results/. Creates no judgment freeze, no result
manifest, no follow-up packets, and nothing under corrections_v2/results/.
"""
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "corrections_v2"))

import pandas as pd  # noqa: E402

import analysis_pipeline as ap  # noqa: E402
from analysis_core import aggregate, cohort_statistics, cross_family, per_judge_transitions, agreement  # noqa: E402
from analysis_io import (SPEC_FREEZE, digest, inspect, load_manifest, panel_jobs, preparation_gate,  # noqa: E402
                         read_rows, stamp, verify_spec)
from rerun import validate_rows  # noqa: E402

LABEL = "PROVISIONAL_DEVIATION_ANALYSIS__NOT_FROZEN_PROTOCOL_PRIMARY"
OUT_BASE = ROOT / "corrections_v2/deviation_review/provisional_results"
STAGING = Path(r"C:\Users\Chimdumebi\evidex_execution_records")
BYPASSED = {"p02_C_j2_b02": [1, 2, 3], "p02_C_j2_b03": [1, 2, 3, 4]}
GROK_BYPASSED = {"p01_C_j5_b09": [1, 2]}
UNSTAGED = {("p01_C_j5_b09", 1)}


def staged_rows(job, slot):
    if (job["job_id"], slot) in UNSTAGED:
        path = f"/home/evidex/isolated/{job['job_id']}/attempt-{slot:02d}/workspace/{job['output']}"
        data = subprocess.run(["wsl", "-u", "root", "-e", "cat", path], capture_output=True, check=True).stdout
        source = hashlib.sha256(data).hexdigest()
    else:
        path = STAGING / job["job_id"] / f"attempt-{slot:02d}" / "workspace.output.json"
        data = path.read_bytes()
        source = digest(path)
    rows = json.loads(data.decode("utf-8"))
    if validate_rows(job, rows) != "valid":
        raise ValueError(f"output not schema-valid: {path}")
    return [dict(r, panel=job["panel"], job_id=job["job_id"]) for r in rows], source


def run_primary(out, manifest, raw, meta):
    if out.exists():
        raise ValueError(f"provisional result already exists; choose a new name: {out}")
    out.mkdir(parents=True)
    frames, all_consensus, retained, rates, cases = {}, [], {}, [], []
    packet_lookup = {r["item_id"]: r for r in read_rows(ROOT / "corrections_v2/generated/stage_c_corrected.jsonl")}
    for name in ("grok", "claude_full"):
        frame, stages, cons, prov = ap.panel_analysis(ROOT, manifest, name, raw)
        frames[name] = frame
        all_consensus += cons
        retained[name] = prov
        rates += ap.descriptive_rates(frame, name)
        ap.table(out / f"tables/{name}_claims.csv", frame)
        ap.table(out / f"tables/{name}_per_judge_transitions.csv", per_judge_transitions(stages))
        ap.table(out / f"tables/{name}_agreement.csv", [dict(stage=s, **agreement(stages[s])) for s in "ABC"])
        for left, right in [("A", "B"), ("B", "C"), ("A", "C")]:
            matrix = pd.crosstab(frame[f"consensus_{left}"], frame[f"consensus_{right}"]).reindex(
                index=ap.LABELS, columns=ap.LABELS, fill_value=0)
            ap.table(out / f"tables/{name}_{left}_{right}.csv", matrix.rename_axis(left).reset_index())
        if name == "grok":
            ap.table(out / "tables/grok_Q1_Q12.csv", cohort_statistics(frame))
        for category in ap.CATEGORIES + ["order_sensitive"]:
            selected = frame[frame.order_sensitive_C if category == "order_sensitive" else frame.category.eq(category)]
            if len(selected):
                case = selected.sort_values("source_item_id").iloc[0].to_dict()
                cases.append(dict(selection=category, **case, corrected_packet=packet_lookup[case["source_item_id"]]))
    ap.table(out / "tables/descriptive_rates.csv", rates)
    ap.write_json(out / "consensus.json", ap.clean(all_consensus))
    ap.write_json(out / "retained_AB_provenance.json", retained)
    ap.write_json(out / "representative_cases.json", ap.clean(cases))
    summary, comparison, confusion, final_matrix = cross_family(frames["grok"], frames["claude_full"])
    ap.write_json(out / "cross_family_summary.json", ap.clean(summary))
    ap.table(out / "tables/cross_family_tests.csv", comparison)
    ap.table(out / "tables/taxonomy_confusion.csv", confusion.rename_axis("grok_category").reset_index())
    ap.table(out / "tables/final_status_confusion.csv", final_matrix.rename_axis("grok_C").reset_index())
    ap.draw_figures(out, frames)
    status = dict(meta, label=LABEL, denominators={k: len(v) for k, v in frames.items()}, created_at_utc=stamp(),
                  followup_packets_generated=False, judgment_freeze_created=False, inference_launched=False)
    ap.write_json(out / "status.json", status)
    files = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(out.rglob("*")) if p.is_file()}
    ap.write_json(out / "provisional_file_hashes.json", {"label": LABEL, "files": files})
    return frames, comparison


def main():
    preparation_gate(ROOT)
    spec = verify_spec(ROOT)
    manifest = load_manifest(ROOT)
    status, raw, files = inspect(manifest, "primary", ROOT, spec)
    if status["missing_jobs"] or status["invalid_outputs_or_packets"] or status["valid_schema_judgments"] != 6430:
        raise SystemExit("accepted outputs are not all present and schema-valid")
    base_meta = {
        "analysis_role": "provisional inspection only; not frozen-protocol primary analysis; not publishable as primary",
        "frozen_protocol_status": status["status"],
        "frozen_protocol_provenance_errors": status["execution_provenance_errors"],
        "original_freeze": SPEC_FREEZE, "original_freeze_sha256": digest(ROOT / SPEC_FREEZE),
        "original_freeze_verified_unchanged": True,
        "analysis_code": "frozen analysis_core/analysis_pipeline/taxonomy imported unchanged",
        "deviation_evidence": "corrections_v2/deviation_review/attempt_table.md",
        "accepted_output_hashes": {k: v for k, v in files.items() if k.endswith(".output.json")},
    }
    frames, comparison = run_primary(OUT_BASE / "accepted70_2026-09-28", manifest, raw,
                                     dict(base_meta, input_selection="the 70 accepted outputs as delivered"))

    jobs = {j["job_id"]: j for j in panel_jobs(manifest, "primary")}
    first_valid_raw = [r for r in raw if r["job_id"] not in BYPASSED and r["job_id"] not in GROK_BYPASSED]
    substituted = {}
    for job_id, slots in {**BYPASSED, **GROK_BYPASSED}.items():
        rows, sha = staged_rows(jobs[job_id], slots[0])
        first_valid_raw += rows
        substituted[job_id] = {"slot": slots[0], "staged_output_sha256": sha}
    fv_frames, fv_comparison = run_primary(
        OUT_BASE / "sensitivity_first_valid_2026-09-28", manifest, first_valid_raw,
        dict(base_meta, input_selection="accepted outputs except p02_C_j2_b02, p02_C_j2_b03 and p01_C_j5_b09 replaced "
                                        "by their first schema-valid (never-accepted) outputs", substituted=substituted))

    config = next(p for p in manifest["panels"] if p["panel"] == "claude_full")
    base_claude = [r for r in raw if r["panel"] == "claude_full" and r["job_id"] not in BYPASSED]
    staged = {(j, s): staged_rows(jobs[j], s)[0] for j, slots in BYPASSED.items() for s in slots}
    reference = aggregate([r for r in raw if r["panel"] == "claude_full"], config["item_ids"])
    combos = []
    for s2, s3 in itertools.product(BYPASSED["p02_C_j2_b02"], BYPASSED["p02_C_j2_b03"]):
        cons = aggregate(base_claude + staged[("p02_C_j2_b02", s2)] + staged[("p02_C_j2_b03", s3)], config["item_ids"])
        changed = sorted(i for i in cons if cons[i]["consensus"] != reference[i]["consensus"])
        labels = pd.Series([cons[i]["consensus"] for i in cons]).value_counts().to_dict()
        combos.append({"p02_C_j2_b02_slot": s2, "p02_C_j2_b03_slot": s3,
                       "is_accepted_selection": (s2, s3) == (3, 4), "is_first_valid_selection": (s2, s3) == (1, 1),
                       "claude_C_consensus_changed_vs_accepted": len(changed), "changed_items": changed,
                       "claude_C_label_counts": labels})

    grok_config = next(p for p in manifest["panels"] if p["panel"] == "grok")
    grok_all = [r for r in raw if r["panel"] == "grok"]
    grok_reference = aggregate(grok_all, grok_config["item_ids"])
    grok_alt = aggregate([r for r in grok_all if r["job_id"] != "p01_C_j5_b09"]
                         + staged_rows(jobs["p01_C_j5_b09"], 1)[0], grok_config["item_ids"])
    grok_changed = sorted(i for i in grok_alt if grok_alt[i]["consensus"] != grok_reference[i]["consensus"])

    def headline(frame):
        return {"n": len(frame), "C_label_counts": frame.consensus_C.value_counts().to_dict(),
                "category_counts": frame.category.value_counts().to_dict(),
                "nondecisive_C": int(frame.ambiguous_C.sum())}

    diff = {
        "label": LABEL,
        "claude_full_accepted": headline(frames["claude_full"]),
        "claude_full_first_valid": headline(fv_frames["claude_full"]),
        "claude_items_with_changed_C_consensus_first_valid_vs_accepted": sorted(
            set(frames["claude_full"].loc[frames["claude_full"].consensus_C.values
                                          != fv_frames["claude_full"].consensus_C.values, "source_item_id"])),
        "claude_items_with_changed_category_first_valid_vs_accepted": sorted(
            set(frames["claude_full"].loc[frames["claude_full"].category.values
                                          != fv_frames["claude_full"].category.values, "source_item_id"])),
        "cross_family_tests_accepted": ap.clean(comparison),
        "cross_family_tests_first_valid": ap.clean(fv_comparison),
        "grok_accepted": headline(frames["grok"]),
        "grok_first_valid": headline(fv_frames["grok"]),
        "grok_C_consensus_changed_p01_C_j5_b09_slot1_vs_accepted": {"n": len(grok_changed), "items": grok_changed},
        "claude_all_completed_run_combinations": combos,
    }
    ap.write_json(OUT_BASE / "sensitivity_summary_2026-09-28.json", ap.clean(diff))
    brief = {k: v for k, v in diff.items() if not k.startswith(("cross_family", "claude_all"))}
    brief["claude_combination_range"] = {
        "changed_vs_accepted": [min(c["claude_C_consensus_changed_vs_accepted"] for c in combos),
                                max(c["claude_C_consensus_changed_vs_accepted"] for c in combos)],
        "ambiguous_count": [min(c["claude_C_label_counts"].get("Ambiguous", 0) for c in combos),
                            max(c["claude_C_label_counts"].get("Ambiguous", 0) for c in combos)]}
    print(json.dumps(ap.clean(brief), indent=2))


if __name__ == "__main__":
    main()
