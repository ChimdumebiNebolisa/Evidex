"""Verify this correction's generated artifacts and historical preservation."""
import json
from collections import Counter

import pandas as pd

from reproduce import ROOT, SV, OUT, digest, read_jsonl, write_json
from rerun import validate_job


def main():
    recorded = json.loads((OUT / "input_hashes.json").read_text())
    for name, expected in recorded.items():
        assert digest(ROOT / name) == expected, f"source changed: {name}"
    audit = read_jsonl(OUT / "evidence_audit.jsonl")
    assert len(audit) == len({r["item_id"] for r in audit}) == 1061
    assert all(r["ordered_pointers_match"] for r in audit)
    # Reproduced historical defects, not targets for corrected results.
    assert sum(r["chosen_text_mismatch"] for r in audit) == 936
    assert sum(r["chosen_text_mismatch"] and r["regression"] for r in audit) == 190
    old_b = read_jsonl(SV / "data/blinded/stage_b.jsonl")
    new_b = read_jsonl(OUT / "stage_b_corrected.jsonl")
    assert new_b == old_b
    corrected = read_jsonl(OUT / "stage_c_corrected.jsonl")
    tracker = pd.read_csv(ROOT / "experiment_tracker_with_evidence_balanced_10000_v1.csv").set_index("claim_id")
    by_id = {r["item_id"]: r for r in audit}
    for record, stage_b in zip(corrected, new_b):
        assert {k: record[k] for k in stage_b} == stage_b
        original = tracker.loc[by_id[record["item_id"]]["claim_id"]]
        s = record["structured_evidence"]
        assert [r["sentence"] for r in s["chosen_set"]] == json.loads(original.evidence_sentences_json)
        assert len(s["alternative_sets"]) == len(s["alternative_annotation_indices"])
        assert len(s["alternative_sets"]) + 1 == s["n_annotation_sets"]
    validation = read_jsonl(OUT / "sentence_validation.jsonl")
    assert all(r["status"] == "available" and r["archive_text"] == r["text"] for r in validation)
    manifest = json.loads((OUT / "rerun_manifest.json").read_text())
    actual_packets = {p.relative_to(ROOT).as_posix() for p in (ROOT / "corrections_v2/blind_io").rglob("*.json") if not p.name.endswith(".output.json")}
    assert actual_packets == {j["packet"] for j in manifest["jobs"]}, "stale or missing prepared packets"
    assert len(manifest["jobs"]) == 85
    assert sum(j["n_judgments"] for j in manifest["jobs"] if j["panel"] != "claude_historical_residual_optional") == 6430
    for panel in manifest["panels"]:
        assert panel["stage_b_changed"] == 0 and panel["stages_to_rerun"] == ["C"]
        jobs = [j for j in manifest["jobs"] if j["panel"] == panel["panel"]]
        counts = Counter(iid for j in jobs for iid in j["item_ids"])
        assert set(counts) == set(panel["item_ids"]) and set(counts.values()) == {5}
        assert "SA-000352" not in panel["source_ids"]
        for job in jobs:
            validate_job(job)
            packet = json.loads((ROOT / job["packet"]).read_text(encoding="utf-8"))
            assert packet["item_ids"] == job["item_ids"]
            assert packet["n_items"] == len(packet["items"]) == job["n_judgments"]
            assert packet["judge_id"] == job["judge_id"] and packet["stage"] == job["stage"]
            assert not any(word in job["launch_prompt"].lower() for word in
                           ("regression", "residual", "fever gold", "source_item_id", "claim_id", "taxonomy"))
            for item in packet["items"]:
                assert set(item) == {"item_id", "claim", "evidence_sentences", "page_titles", "structured_evidence"}
    links = read_jsonl(OUT / "impact_items.jsonl")
    assert len(links) == sum(j["n_judgments"] for j in manifest["jobs"]) == 7585
    assert len({(r["job_id"], r["panel_item_id"]) for r in links}) == len(links)
    historical = json.loads((OUT / "impact_manifest.json").read_text())["historical_dependencies"]
    for row in links:
        dep = historical[row["historical_dependency_panel"]]
        assert row["historical_judgment_key"] in dep["judgment_files_by_item_and_judge"]
    taxonomy = pd.read_csv(OUT / "taxonomy_rule_only.csv")
    assert taxonomy.judgment_input_version.eq("historical_v1_packets").all()
    assert taxonomy.corrected_packet_result.eq("PENDING_FRESH_JUDGMENTS").all()
    assert not taxonomy[taxonomy.category == "decisive_judge_fever_disagreement"].agrees_fever_C.any()
    for stage in "ABC":
        assert taxonomy.loc[~taxonomy[f"decisive_{stage}"], f"agrees_fever_{stage}"].isna().all()
    code = [ROOT / "fever_evidence.py", ROOT / "resolve_gold_evidence.py",
            SV / "src/reconstruct_evidence.py", SV / "src/taxonomy_legacy_v1.py", SV / "src/taxonomy_v2.py",
            SV / "src/join_analysis_v2.py", SV / "claude_full_regression_panel/src/analyze.py"]
    code += list((ROOT / "corrections_v2").glob("*.py"))
    code += list((ROOT / "corrections_v2/tests").glob("*.py"))
    write_json(OUT / "code_hashes.json", {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(code)})
    write_json(OUT / "verification_results.json", {"source_hashes_unchanged": len(recorded),
               "exact_selected_sets": len(audit), "stage_b_identical": True,
               "prepared_jobs": len(manifest["jobs"]), "planned_judgments_including_optional": len(links),
               "corrected_inference_executed": False, "corrected_consensus_available": False})
    print(f"PASS: {len(recorded)} source hashes unchanged; 1,061 exact selected sets; A/B retained; 85 prepared C jobs; 7,585 dependency links; no corrected judgments asserted.")


if __name__ == "__main__":
    main()
