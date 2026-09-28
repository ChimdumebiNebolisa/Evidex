"""PROVISIONAL deviation analysis of correction-v2 Stage C. NOT the frozen-protocol primary analysis.

Uses the frozen analysis code unchanged (imported, never edited) on the 70 accepted outputs even
though frozen-protocol execution provenance is incomplete for six jobs (retry cap) and the
first-schema-valid rule was not followed for p02_C_j2_b02, p02_C_j2_b03 and p01_C_j5_b09. Creates no
judgment freeze, no result manifest, no follow-up packets, and nothing under corrections_v2/results/.

Every input is a tracked, repo-relative file. Alternative (never-accepted) outputs are checked for
size, SHA-256 and schema validity, against both the constants below and the recorded evidence,
before any analysis runs.

  python corrections_v2/deviation_review/provisional_analysis.py verify
      Recompute everything into a temporary directory and compare it with the committed results.
      Writes nothing in the repository. Exit 0 = identical apart from the creation timestamp.
  python corrections_v2/deviation_review/provisional_analysis.py run --tag YYYY-MM-DD
      Write a new, separately named result set under provisional_results/. Never overwrites.
"""
import argparse
import hashlib
import itertools
import json
import sys
import tempfile
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
REVIEW = "corrections_v2/deviation_review"
RESULTS = f"{REVIEW}/provisional_results"
COMMITTED_TAG = "2026-09-28"
BYPASSED = {"p02_C_j2_b02": [1, 2, 3], "p02_C_j2_b03": [1, 2, 3, 4]}
GROK_BYPASSED = {"p01_C_j5_b09": [1, 2]}
ACCEPTED_SLOT = {"p02_C_j2_b02": 3, "p02_C_j2_b03": 4, "p01_C_j5_b09": 2}

# (job, slot) -> (tracked path, size, sha256). Claude slots are the runs' own raw outputs archived
# in execution/; the Grok slot-1 file was recovered from WSL (its run ended in an error).
ALTERNATIVES = {
    ("p02_C_j2_b02", 1): ("corrections_v2/execution/p02_C_j2_b02/attempt-01.raw.txt", 27738,
                          "6b64ed30368b1f042ee25446e85d42a44faf12d977c89df2cc65db76ab11b150"),
    ("p02_C_j2_b02", 2): ("corrections_v2/execution/p02_C_j2_b02/attempt-02.raw.txt", 26863,
                          "676a76a3226eb7892c9222d74e1fa71e7335109b6cdf00717777e21a4d7379b4"),
    ("p02_C_j2_b02", 3): ("corrections_v2/execution/p02_C_j2_b02/attempt-03.raw.txt", 26858,
                          "1a74c7d8efa390caf3eb7f1cf7afe34bb72f9f11edfe9d477d6acca935353a29"),
    ("p02_C_j2_b03", 1): ("corrections_v2/execution/p02_C_j2_b03/attempt-01.raw.txt", 25387,
                          "e64e7a0db301da36613784d12ebdce940dd4fd6716efdcb79a0d8f4eb8714cfd"),
    ("p02_C_j2_b03", 2): ("corrections_v2/execution/p02_C_j2_b03/attempt-02.raw.txt", 25914,
                          "978acd62a3712088cc1a3f597cfe5b2d57e0f3969a0a0eaa5e144641c1a40061"),
    ("p02_C_j2_b03", 3): ("corrections_v2/execution/p02_C_j2_b03/attempt-03.raw.txt", 26133,
                          "8438ff2120c5f8f42a185a41c2a084881106dca969f3623d1f05ff2b8051a002"),
    ("p02_C_j2_b03", 4): ("corrections_v2/execution/p02_C_j2_b03/attempt-04.raw.txt", 25763,
                          "1001dbbfa31cfe8e46923bede882f1cab09031dcff2d8110823cedd8248aed52"),
    ("p01_C_j5_b09", 1): (f"{REVIEW}/evidence/recovered_wsl_outputs/p01_C_j5_b09/attempt-01.workspace.output.json",
                          33544, "184e3b68947ee6067258e4d1a6a72ae7b55640bd7dbcbb83733fbfadde3011e3"),
}


def recorded_hashes():
    """Hashes each alternative must match in the recorded evidence (not only in this file)."""
    evidence = {j["job_id"]: j for j in json.loads((ROOT / REVIEW / "evidence/attempt_evidence.json").read_text("utf-8"))}
    recovered = {(f["job_id"], f["attempt"]): f for f in
                 json.loads((ROOT / REVIEW / "evidence/recovered_wsl_outputs/manifest.json").read_text("utf-8"))["files"]}
    unstaged = {(f["job_id"], f["attempt"]): f for f in
                json.loads((ROOT / REVIEW / "evidence/unstaged_failed_outputs.json").read_text("utf-8"))}
    expected = {}
    for job_id, slot in ALTERNATIVES:
        if (job_id, slot) in unstaged:
            u, r = unstaged[(job_id, slot)], recovered[(job_id, slot)]
            expected[(job_id, slot)] = {(u["sha256"], u["size"], u["schema_valid"]),
                                        (r["sha256"], r["size"], r["schema_valid"])}
        else:
            a = next(x for x in evidence[job_id]["attempts"] if x["attempt"] == slot)
            expected[(job_id, slot)] = {((a.get("routing") or {}).get("output_sha256"), None, True),
                                        (a["model_output"]["sha256"], None, a["model_output"]["schema_valid"])}
    return expected


def load_alternatives(manifest):
    """Validate the bytes and schema of every alternative before any analysis; return rows by (job, slot)."""
    jobs = {j["job_id"]: j for j in panel_jobs(manifest, "primary")}
    expected = recorded_hashes()
    loaded, report = {}, []
    for (job_id, slot), (rel, size, sha) in sorted(ALTERNATIVES.items()):
        path = ROOT / rel
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if len(data) != size or actual != sha:
            raise SystemExit(f"alternative bytes changed: {rel} ({len(data)} bytes, {actual})")
        for rec_sha, rec_size, rec_valid in expected[(job_id, slot)]:
            if rec_sha != actual or (rec_size is not None and rec_size != len(data)) or rec_valid is not True:
                raise SystemExit(f"alternative disagrees with recorded evidence: {rel}")
        if slot == ACCEPTED_SLOT[job_id] and digest(ROOT / jobs[job_id]["output"]) != actual:
            raise SystemExit(f"archived accepted-slot output differs from the delivered output: {rel}")
        rows = json.loads(data.decode("utf-8"))
        if validate_rows(jobs[job_id], rows) != "valid":
            raise SystemExit(f"alternative output not schema-valid: {rel}")
        loaded[(job_id, slot)] = ([dict(r, panel=jobs[job_id]["panel"], job_id=job_id) for r in rows], actual)
        report.append({"job_id": job_id, "slot": slot, "path": rel, "size": len(data), "sha256": actual,
                       "n_rows": len(rows), "schema_valid": True})
    return loaded, report


def run_primary(out, key_prefix, manifest, raw, meta):
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
    files = {f"{key_prefix}/{p.relative_to(out).as_posix()}": digest(p) for p in sorted(out.rglob("*")) if p.is_file()}
    ap.write_json(out / "provisional_file_hashes.json", {"label": LABEL, "files": files})
    return frames, comparison


def compute(base, tag):
    """Write the accepted-70 set, the first-valid sensitivity set and the summary under base/."""
    preparation_gate(ROOT)
    spec = verify_spec(ROOT)
    manifest = load_manifest(ROOT)
    status, raw, files = inspect(manifest, "primary", ROOT, spec)
    if status["missing_jobs"] or status["invalid_outputs_or_packets"] or status["valid_schema_judgments"] != 6430:
        raise SystemExit("accepted outputs are not all present and schema-valid")
    alternatives, input_report = load_alternatives(manifest)
    base_meta = {
        "analysis_role": "provisional inspection only; not frozen-protocol primary analysis; not publishable as primary",
        "frozen_protocol_status": status["status"],
        "frozen_protocol_provenance_errors": status["execution_provenance_errors"],
        "original_freeze": SPEC_FREEZE, "original_freeze_sha256": digest(ROOT / SPEC_FREEZE),
        "original_freeze_verified_unchanged": True,
        "analysis_code": "frozen analysis_core/analysis_pipeline/taxonomy imported unchanged",
        "deviation_evidence": f"{REVIEW}/attempt_table.md",
        "accepted_output_hashes": {k: v for k, v in files.items() if k.endswith(".output.json")},
    }
    accepted_name, first_valid_name = f"accepted70_{tag}", f"sensitivity_first_valid_{tag}"
    frames, comparison = run_primary(base / accepted_name, f"{RESULTS}/{accepted_name}", manifest, raw,
                                     dict(base_meta, input_selection="the 70 accepted outputs as delivered"))

    first_valid_raw = [r for r in raw if r["job_id"] not in BYPASSED and r["job_id"] not in GROK_BYPASSED]
    substituted = {}
    for job_id, slots in {**BYPASSED, **GROK_BYPASSED}.items():
        rows, sha = alternatives[(job_id, slots[0])]
        first_valid_raw += rows
        substituted[job_id] = {"slot": slots[0], "staged_output_sha256": sha}
    fv_frames, fv_comparison = run_primary(
        base / first_valid_name, f"{RESULTS}/{first_valid_name}", manifest, first_valid_raw,
        dict(base_meta, input_selection="accepted outputs except p02_C_j2_b02, p02_C_j2_b03 and p01_C_j5_b09 replaced "
                                        "by their first schema-valid (never-accepted) outputs", substituted=substituted))

    config = next(p for p in manifest["panels"] if p["panel"] == "claude_full")
    base_claude = [r for r in raw if r["panel"] == "claude_full" and r["job_id"] not in BYPASSED]
    reference = aggregate([r for r in raw if r["panel"] == "claude_full"], config["item_ids"])
    combos = []
    for s2, s3 in itertools.product(BYPASSED["p02_C_j2_b02"], BYPASSED["p02_C_j2_b03"]):
        cons = aggregate(base_claude + alternatives[("p02_C_j2_b02", s2)][0] + alternatives[("p02_C_j2_b03", s3)][0],
                         config["item_ids"])
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
                         + alternatives[("p01_C_j5_b09", 1)][0], grok_config["item_ids"])
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
    ap.write_json(base / f"sensitivity_summary_{tag}.json", ap.clean(diff))
    claude_only = cross_family(frames["grok"], fv_frames["claude_full"])
    separation = {
        "claude_first_valid_only_equals_combined_first_valid_cross_family":
            ap.clean(claude_only[0]) == ap.clean(cross_family(fv_frames["grok"], fv_frames["claude_full"])[0])
            and ap.clean(claude_only[1]) == ap.clean(fv_comparison),
        "grok_slot1_changes_regression_cohort_fields": sorted(
            c for c in fv_frames["grok"].columns if c != "mean_confidence_C"
            and not frames["grok"].loc[frames["grok"].cohort.eq("regression"), c].reset_index(drop=True).equals(
                fv_frames["grok"].loc[fv_frames["grok"].cohort.eq("regression"), c].reset_index(drop=True))),
    }
    return diff, input_report, separation


def brief(diff):
    out = {k: v for k, v in diff.items() if not k.startswith(("cross_family", "claude_all"))}
    combos = diff["claude_all_completed_run_combinations"]
    out["claude_combination_range"] = {
        "changed_vs_accepted": [min(c["claude_C_consensus_changed_vs_accepted"] for c in combos),
                                max(c["claude_C_consensus_changed_vs_accepted"] for c in combos)],
        "ambiguous_count": [min(c["claude_C_label_counts"].get("Ambiguous", 0) for c in combos),
                            max(c["claude_C_label_counts"].get("Ambiguous", 0) for c in combos)]}
    out["bh_significant_at_0.05"] = {k: {t["analysis"]: t["p_bh"] < 0.05 for t in diff[f"cross_family_tests_{k}"]}
                                     for k in ("accepted", "first_valid")}
    return ap.clean(out)


def compare_results(new_base, committed_base, tag):
    """Return a list of differences, ignoring only created_at_utc and the hash entry of status.json."""
    problems = []
    for name in (f"accepted70_{tag}", f"sensitivity_first_valid_{tag}"):
        new, old = new_base / name, committed_base / name
        new_files = {p.relative_to(new).as_posix() for p in new.rglob("*") if p.is_file()}
        old_files = {p.relative_to(old).as_posix() for p in old.rglob("*") if p.is_file()}
        if new_files != old_files:
            problems.append(f"{name}: file sets differ: +{sorted(new_files - old_files)} -{sorted(old_files - new_files)}")
        for rel in sorted(new_files & old_files):
            a, b = (new / rel).read_bytes(), (old / rel).read_bytes()
            if rel == "status.json":
                ja, jb = json.loads(a), json.loads(b)
                ja.pop("created_at_utc"), jb.pop("created_at_utc")
                if ja != jb:
                    problems.append(f"{name}/status.json differs beyond created_at_utc")
            elif rel == "provisional_file_hashes.json":
                ja, jb = json.loads(a), json.loads(b)
                for j in (ja, jb):
                    j["files"] = {k: v for k, v in j["files"].items() if not k.endswith("/status.json")}
                if ja != jb:
                    problems.append(f"{name}/provisional_file_hashes.json differs beyond the status.json entry")
            elif a != b:
                problems.append(f"{name}/{rel}: bytes differ")
    summary = f"sensitivity_summary_{tag}.json"
    if (new_base / summary).read_bytes() != (committed_base / summary).read_bytes():
        problems.append(f"{summary}: bytes differ")
    return problems


def verify():
    committed = ROOT / RESULTS
    with tempfile.TemporaryDirectory(prefix="evidex_provisional_verify_") as tmp:
        diff, input_report, separation = compute(Path(tmp), COMMITTED_TAG)
        problems = compare_results(Path(tmp), committed, COMMITTED_TAG)
        committed_diff = json.loads((committed / f"sensitivity_summary_{COMMITTED_TAG}.json").read_text("utf-8"))
    checks = {
        "claude_changed_claim_ids": diff["claude_items_with_changed_C_consensus_first_valid_vs_accepted"]
        == committed_diff["claude_items_with_changed_C_consensus_first_valid_vs_accepted"],
        "grok_changed_claim_ids": diff["grok_C_consensus_changed_p01_C_j5_b09_slot1_vs_accepted"]
        == committed_diff["grok_C_consensus_changed_p01_C_j5_b09_slot1_vs_accepted"],
        "headline_counts": all(diff[k] == committed_diff[k] for k in
                               ("claude_full_accepted", "claude_full_first_valid", "grok_accepted", "grok_first_valid")),
        "test_decisions": all(diff[k] == committed_diff[k] for k in
                              ("cross_family_tests_accepted", "cross_family_tests_first_valid")),
        "twelve_combinations": diff["claude_all_completed_run_combinations"]
        == committed_diff["claude_all_completed_run_combinations"],
    }
    report = {"label": LABEL, "mode": "verify (temporary output; repository not written)",
              "inputs_validated_before_analysis": input_report, "semantic_checks": checks,
              "grok_sensitivity_separation": separation,
              "byte_differences": problems,
              "ignored_nondeterministic_fields": ["status.json:created_at_utc",
                                                  "provisional_file_hashes.json:<result>/status.json"],
              "result": "PASS" if not problems and all(checks.values()) else "FAIL"}
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "PASS" else 1


def run(tag):
    if tag == COMMITTED_TAG:
        raise SystemExit(f"{COMMITTED_TAG} results are committed; use verify, or a new tag")
    diff, _, _ = compute(ROOT / RESULTS, tag)
    print(json.dumps(brief(diff), indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    return verify() if args.command == "verify" else run(args.tag)


if __name__ == "__main__":
    sys.exit(main())
