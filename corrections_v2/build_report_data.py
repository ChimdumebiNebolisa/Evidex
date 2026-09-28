"""Build the item-level impact links and representative-case evidence."""
import json
from pathlib import Path

import pandas as pd

from reproduce import OUT, ROOT, SV, read_jsonl, write_json, write_rows
from provenance import verify_historical


def main():
    verify_historical(ROOT)
    audit = {r["item_id"]: r for r in read_jsonl(OUT / "evidence_audit.jsonl")}
    tax = pd.read_csv(OUT / "taxonomy_rule_only.csv")
    tracker = pd.read_csv(ROOT / "experiment_tracker_with_evidence_balanced_10000_v1.csv").set_index("claim_id")
    manifest = json.loads((OUT / "rerun_manifest.json").read_text())
    historical_dependencies = {}
    roots = {"grok": SV / "cursor_panel", "claude_full": SV / "claude_full_regression_panel",
             "claude_historical_residual_optional": SV / "claude_residual_panel"}
    for panel, root in roots.items():
        index = {}
        for path in sorted((root / "judgments").rglob("*_batch_*.jsonl")):
            for row in read_jsonl(path):
                if row.get("stage") == "C" and "judge_id" in row:
                    key = row["item_id"] + ":j" + row["judge_id"].rsplit("_", 1)[-1]
                    index.setdefault(key, []).append(path.relative_to(ROOT).as_posix())
        residual = panel == "claude_historical_residual_optional"
        historical_dependencies[panel] = {
            "blinded_input": ((SV / "data/blinded/stage_c.jsonl") if panel == "grok" else root / "data/blinded_stage_c.jsonl").relative_to(ROOT).as_posix(),
            "judgment_files_by_item_and_judge": index,
            "consensus": (root / "freezes" / ("consensus_raw.parquet" if residual else "consensus_stage_C.parquet")).relative_to(ROOT).as_posix(),
            "taxonomy": (root / "freezes" / ("silver_unblinded.parquet" if panel == "grok" else "claude_unblinded.parquet" if residual else "claude_full_unblinded.parquet")).relative_to(ROOT).as_posix(),
            "tables": (root / "tables").relative_to(ROOT).as_posix(),
            "figures": (root / "figures").relative_to(ROOT).as_posix(),
            "manuscript": ["paper/sections/results.tex", "paper/sections/discussion.tex", "paper/sections/abstract.tex", "paper/sections/conclusion.tex"],
        }
    links = []
    for job in manifest["jobs"]:
        panel = next(p for p in manifest["panels"] if p["panel"] == job["panel"])
        sources = dict(zip(panel["item_ids"], panel["source_ids"]))
        for iid in job["item_ids"]:
            sa = sources[iid]
            r = audit[sa]
            links.append({"claim_id": r["claim_id"], "source_item_id": sa, "panel_item_id": iid,
                          "historical_dependency_panel": job["panel"],
                          "historical_judgment_key": iid + ":j" + job["judge_id"].rsplit("_", 1)[-1],
                          "selected_set_id": r["evidence_set_id"], "job_id": job["job_id"],
                          "source_prediction_file": "experiment_results_balanced_10000_v1.csv",
                          "source_annotation_file": "fever_balanced_10000_v1_source.csv",
                          "original_evidence_file": "experiment_tracker_with_evidence_balanced_10000_v1.csv",
                          "corrected_packet": job["packet"], "packet_sha256": job["packet_sha256"],
                          "future_judgments": job["output"], "future_consensus": "PENDING_FRESH_JUDGMENTS",
                          "future_taxonomy": "PENDING_FRESH_JUDGMENTS_AND_COAUTHOR_REVIEW",
                          "downstream_claim_group": "diagnostic_stage_C_and_taxonomy"})
    write_rows("impact_items.jsonl", links)
    examples = []
    for sa in ("SA-000001", "SA-000002", "SA-000329", "SA-001042"):
        row = audit[sa]
        examples.append({"kind": "evidence", "claim": tracker.loc[row["claim_id"], "claim_text"], **row})
    for panel, group in tax[(tax.cohort == "regression") &
                           (tax.legacy == "silver_clear_evidence_utilization_failure") &
                           (tax.consensus_C != tax.gold_label)].groupby("panel"):
        root = SV / ("cursor_panel" if panel == "grok" else "claude_full_regression_panel")
        chosen = group.head(3).to_dict("records")
        ids = {r["item_id"] for r in chosen}
        raw = [r for p in sorted((root / "judgments/stage_c").glob("*_batch_*.jsonl"))
               for r in read_jsonl(p) if r["item_id"] in ids]
        for row in chosen:
            examples.append({"kind": "taxonomy", "claim": tracker.loc[row["claim_id"], "claim_text"],
                             "gold_evidence": tracker.loc[row["claim_id"], "gold_evidence"],
                             **{k: (None if pd.isna(v) else v) for k, v in row.items()},
                             "historical_C_judge_records": [r for r in raw if r["item_id"] == row["item_id"]]})
    write_json(OUT / "representative_cases.json", examples)
    layers = [
        {"id": "behavior", "status": "valid_unchanged",
         "inputs": ["experiment_results_balanced_10000_v1.csv", "experiment_tracker_with_evidence_balanced_10000_v1.csv"],
         "outputs": ["analysis_v2/tables/transition_summary.csv", "paper/tables/tab_accuracy.tex", "analysis_v2/figures/fig1_transition_matrices.png"],
         "claims": ["RQ1 aggregate accuracies", "RQ2 four-way transitions and 226-claim union"],
         "reason": "Recomputed directly from all 40,000 labels; selected evidence text identical to historical tracker."},
        {"id": "stage_A_B", "status": "retain_existing_judgments_under_documented_isolation",
         "inputs": ["silver_adjudication_v1/data/blinded/stage_a.jsonl", "silver_adjudication_v1/data/blinded/stage_b.jsonl"],
         "outputs": ["silver_adjudication_v1/cursor_panel/freezes/consensus_stage_A.parquet", "silver_adjudication_v1/cursor_panel/freezes/consensus_stage_B.parquet",
                     "silver_adjudication_v1/claude_full_regression_panel/freezes/consensus_stage_A.parquet", "silver_adjudication_v1/claude_full_regression_panel/freezes/consensus_stage_B.parquet"],
         "claims": ["Stage A/B ambiguity", "GLM Stage A replication", "A-to-B title-associated changes"],
         "reason": "Exact fields preserved including raw title Unicode; fresh contexts per stage documented; no C outputs consumed by A/B. No provider transcripts independently prove runtime isolation."},
        {"id": "rule_only", "status": "recomputable_existing_judgments_historical_inputs_only",
         "inputs": ["silver_adjudication_v1/cursor_panel/judgments", "silver_adjudication_v1/claude_full_regression_panel/judgments", "silver_adjudication_v1/src/taxonomy_legacy_v1.py", "silver_adjudication_v1/src/taxonomy_v2.py"],
         "outputs": ["corrections_v2/generated/taxonomy_rule_only.csv"],
         "claims": ["legacy 36/113 and 46/149 FEVER disagreement", "title precedence", "A-only gold agreement"],
         "reason": "Consensus independently rebuilt from active raw records, legacy labels exactly reproduced. Cannot validate corrected packets."},
        {"id": "diagnostic_stage_C_and_taxonomy", "status": "fresh_judgments_required",
         "inputs": ["corrections_v2/inputs/historical_pages.json", "corrections_v2/generated/stage_c_corrected.jsonl", "corrections_v2/blind_io"],
         "outputs": ["silver_adjudication_v1/cursor_panel/tables/silver_by_cohort_full.csv", "silver_adjudication_v1/claude_full_regression_panel/tables/mechanism_proportions.csv",
                     "paper/tables/tab_mechanism.tex", "paper/tables/tab_cross_family.tex", "paper/tables/tab_shared.tex",
                     "silver_adjudication_v1/cursor_panel/figures", "silver_adjudication_v1/claude_full_regression_panel/figures"],
         "claims": ["50.0/11.9/38.1 split", "65.9/5.3/28.8 split", "74.3% and kappa .537", "no C reversal", "shared-regression residual rates", "utilization largest and rank-order replication"],
         "reason": "Changed C text, archive coverage and annotation-boundary metadata. Historical outputs remain archived; corrected replacements pending. Batches are the context unit, so rerun entire C panels."},
        {"id": "residual_panel", "status": "historical_cohort_optional_rerun_or_new_selection_required",
         "inputs": ["silver_adjudication_v1/claude_residual_panel/data/id_map.csv", "corrected_Grok_C_consensus_PENDING"],
         "outputs": ["silver_adjudication_v1/claude_residual_panel/tables", "silver_adjudication_v1/claude_residual_panel/figures"],
         "claims": ["134/231 persistent ambiguity (58%)"],
         "reason": "Old 231 cohort is selected on faulty Grok C. Fixed-cohort C rerun is a historical sensitivity test only. Newly selected corrected residuals require new blinded Claude jobs and a new denominator."},
        {"id": "added_information_ablation", "status": "new_analysis_requires_additional_judgments_not_prepared_or_run",
         "inputs": ["corrected chosen-only structured packets", "corrected chosen-plus-alternative packets"],
         "outputs": ["new versioned ablation tables_PENDING"],
         "claims": ["representation change versus new evidence content"],
         "reason": "149 cohort claims (41 regressions) have additional sentence text in C. A chosen-only C arm on fixed 226 regressions costs 226*5*2=2260 judgments / 30 contexts (100-item Grok and 77-item Claude batches); compares with prepared full-C arm. Not a causal analysis of GPT internals."},
    ]
    write_json(OUT / "impact_manifest.json", {"item_level_links": "impact_items.jsonl", "layers": layers,
                                             "historical_dependencies": historical_dependencies,
                                             "manuscript_wording": "../MANUSCRIPT_CHANGES.md"})
    print(f"{len(links)} item/judge dependency links; {len(examples)} representative cases")


if __name__ == "__main__":
    main()
