"""Evidex post hoc correction pipeline. Offline only; never invokes models."""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from analysis_core import (CATEGORIES, DECISIVE, LABELS, aggregate, agreement, bh,
                           cohort_statistics, cross_family, fisher, per_judge_transitions,
                           rate, transitions)
from analysis_io import (MANIFEST, MODELS, PANEL_ROOTS, ROOT, SPEC_FREEZE, digest,
                         freeze_judgments, freeze_path, freeze_spec, frozen_rows, inspect,
                         load_manifest, panel_jobs, preparation_gate, read_json, read_rows,
                         result_manifest, safe_path, stamp, verify_file_map, verify_spec,
                         version_name, write_json, write_once, sha256, lf_bytes)
sys.path.insert(0, str(ROOT / "silver_adjudication_v1/src"))
from taxonomy_v2 import classify


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def table(path, rows):
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def retained_ab(root, panel, expected):
    base = root / PANEL_ROOTS[panel]
    by_stage, provenance = {}, {}
    for stage in "AB":
        unique = {}
        for path in sorted((base / "judgments" / f"stage_{stage.lower()}").glob("*_batch_*.jsonl")):
            name = path.relative_to(root).as_posix()
            provenance[name] = digest(path)
            for row in read_rows(path):
                if row["stage"] != stage:
                    raise ValueError("retained judgment stage mismatch")
                normalized = dict(row, judge_id="judge_" + row["judge_id"].rsplit("_", 1)[1])
                key = (row["item_id"], normalized["judge_id"])
                if key in unique and unique[key] != normalized:
                    raise ValueError("conflicting historical duplicate")
                unique.setdefault(key, normalized)
        by_stage[stage] = list(unique.values())
        aggregate(by_stage[stage], expected)  # No incomplete historical trajectories.
        freeze = base / f"freezes/freeze_stage_{stage}.json"
        provenance[freeze.relative_to(root).as_posix()] = digest(freeze)
    historical = {"files_observed_raw_sha256": provenance,
                  "identity": "corrections_v2/baseline/historical_inputs.json",
                  "reason_retained": "Identical A/B visible inputs and documented stage-isolated contexts",
                  "limitation": "Provider transcripts were not independently verified",
                  "duplicates": "Identical historical duplicates collapse to first in sorted path order; conflicts fail",
                  "judge_slot_mapping": "Historical numeric suffix 1..5 maps to new judge_1..judge_5; not the same continuing conversation"}
    return by_stage, historical


def panel_analysis(root, manifest, panel, new_rows):
    config = next(p for p in manifest["panels"] if p["panel"] == panel)
    ids = config["item_ids"]
    mapping = dict(zip(ids, config["source_ids"]))
    stages, provenance = retained_ab(root, panel, ids)
    stages["C"] = [r for r in new_rows if r["panel"] == panel]
    cons = {s: aggregate(rows, ids) for s, rows in stages.items()}
    base = root / PANEL_ROOTS[panel]
    historic_file = base / ("freezes/silver_unblinded.parquet" if panel == "grok" else "freezes/claude_full_unblinded.parquet")
    historical = pd.read_parquet(historic_file).set_index("item_id" if panel == "grok" else "claude_item_id")
    grok_meta = pd.read_parquet(root / PANEL_ROOTS["grok"] / "freezes/silver_unblinded.parquet").set_index("item_id")
    audits = {r["item_id"]: r for r in read_rows(root / "corrections_v2/generated/evidence_audit.jsonl")}
    records, consensus_rows = [], []
    for iid in sorted(ids):
        source = mapping[iid]
        meta = grok_meta.loc[source]
        for s in "AB":
            if cons[s][iid]["consensus"] != historical.loc[iid, f"consensus_{s}"]:
                raise ValueError("retained A/B consensus no longer matches historical frozen labels")
        abc = [cons[s][iid]["consensus"] for s in "ABC"]
        fields = ["claim_id", "cohort", "regression_type", "gold_label", "nli_disagrees", "nli2_disagrees",
                  "gpt54_transition", "gpt54mini_transition"]
        row = {k: meta[k] for k in fields}
        row.update(panel=panel, item_id=iid, source_item_id=source, **transitions(*abc))
        row.update(classify(*abc, row["gold_label"], row["cohort"],
                            c_adds_text=audits[source]["c_adds_sentence_text"],
                            input_version="retained_v1_AB_fresh_corrected_v2_C"))
        for s in "ABC":
            row[f"rule_{s}"] = cons[s][iid]["rule"]
            row[f"mean_confidence_{s}"] = cons[s][iid]["mean_confidence"]
            row[f"order_sensitive_{s}"] = cons[s][iid]["order_sensitive_label"]
            consensus_rows.append(dict(panel=panel, item_id=iid, stage=s, **cons[s][iid]))
        records.append(row)
    return pd.DataFrame(records).sort_values("source_item_id").reset_index(drop=True), stages, consensus_rows, provenance


def descriptive_rates(frame, panel):
    rows = []
    groups = [("all", frame.index.notna())]
    groups += [(c, frame.cohort.eq(c)) for c in ("regression", "resistant", "rescue", "robust")]
    groups += [("regression_" + c, frame.cohort.eq("regression") & frame.regression_type.eq(c))
               for c in ("both", "gpt54_only", "mini_only")]
    for group, mask in groups:
        sub = frame.loc[mask]
        for index, category in enumerate(CATEGORIES):
            rows.append({"panel": panel, "subgroup": group, "measure": category,
                         **rate(sub.category.eq(category), 20260913 + index + 1)})
        for s in "ABC":
            rows.append({"panel": panel, "subgroup": group, "measure": f"nondecisive_{s}",
                         **rate(sub[f"ambiguous_{s}"], 20260913 + 21 + "ABC".index(s))})
            decisive = sub[sub[f"consensus_{s}"].isin(DECISIVE)]
            rows.append({"panel": panel, "subgroup": group, "measure": f"FEVER_agreement_decisive_{s}",
                         **rate(decisive[f"consensus_{s}"].eq(decisive.gold_label))})
        for feature in ("resolved_by_titles", "resolved_at_C", "reversed_after_titles", "reversed_at_C", "change_A_B", "change_B_C", "change_A_C"):
            rows.append({"panel": panel, "subgroup": group, "measure": feature, **rate(sub[feature])})
    return rows


def draw_figures(out, frames):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams["svg.hashsalt"] = "evidex-post-hoc-correction-v2"
    plots = out / "plots"
    plots.mkdir()
    for panel, data in frames.items():
        fig, ax = plt.subplots(figsize=(10, 5))
        values = [100 * data.category.eq(c).mean() for c in CATEGORIES]
        ax.barh(CATEGORIES, values, color="#326b8b")
        ax.set(xlabel=f"Percent of {len(data)} claims", title=f"{panel}: proposed v2 descriptive taxonomy")
        ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(plots / f"{panel}_taxonomy.svg", metadata={"Date": None})
        plt.close(fig)
        for left, right in [("A", "B"), ("B", "C")]:
            matrix = pd.crosstab(data[f"consensus_{left}"], data[f"consensus_{right}"]).reindex(index=LABELS, columns=LABELS, fill_value=0)
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.imshow(matrix, cmap="Blues")
            ax.set(xticks=range(4), yticks=range(4), xticklabels=LABELS, yticklabels=LABELS,
                   xlabel=right, ylabel=left, title=f"{panel}: claim-level transitions")
            for i in range(4):
                for j in range(4):
                    ax.text(j, i, str(matrix.iloc[i, j]), ha="center", va="center")
            fig.tight_layout()
            fig.savefig(plots / f"{panel}_{left}_{right}.svg", metadata={"Date": None})
            plt.close(fig)


def followups(root, out, version, grok, raw, manifest):
    """Fresh selection from corrected RAW Grok C, never historical C/resolver."""
    packet_items = {}
    for job in panel_jobs(manifest, "grok"):
        for row in read_json(root / job["packet"])["items"]:
            packet_items[row["item_id"]] = row
    source_ids = sorted(grok.loc[grok.ambiguous_C, "source_item_id"].tolist())
    shuffled = source_ids.copy()
    rng = np.random.default_rng(20260823)
    rng.shuffle(shuffled)
    mapping = [{"item_id": f"V2R-{i:06d}", "source_item_id": source} for i, source in enumerate(shuffled, 1)]
    rubric = (root / "silver_adjudication_v1/prompts/judge_rubric.md").read_text(encoding="utf-8")
    resolver_rubric = (root / "silver_adjudication_v1/prompts/resolver_rubric.md").read_text(encoding="utf-8")
    new_items = [dict(packet_items[m["source_item_id"]], item_id=m["item_id"]) for m in mapping]
    resolver_items = []
    anon_rng = np.random.default_rng(20260822 + 7)
    for source in source_ids:
        ratings = sorted([r for r in raw if r["panel"] == "grok" and r["item_id"] == source], key=lambda r: r["judge_id"])
        anon_rng.shuffle(ratings)
        item = packet_items[source]
        resolver_items.append({"item_id": source, "claim": item["claim"], "stage": "C",
                               "evidence": {k: v for k, v in item.items() if k not in {"item_id", "claim"}},
                               "judgments": [{"judge": f"r{i+1}", "verdict": r["verdict"],
                                              "evidence_sufficiency": r["evidence_sufficiency"],
                                              "confidence": r["confidence"], "issue_flags": r["issue_flags"],
                                              "brief_reason": ""} for i, r in enumerate(ratings)]})
    jobs, panels = [], []
    opaque_version = sha256(version.encode())[:12]
    for panel, namespace, items, size, judges, prompt_rubric in [
            ("new_residual", "p04", new_items, 77, [f"judge_{i}" for i in range(1, 6)], rubric),
            ("resolver", "p05", resolver_items, 100, ["resolver"], resolver_rubric)]:
        ids = [r["item_id"] for r in items]
        for judge in judges:
            for start in range(0, len(items), size):
                batch = items[start:start + size]
                job_id = f"{namespace}_{opaque_version}_C_{judge}_b{start // size + 1:02}"
                stem = f"corrections_v2/followup_io/{namespace}/{opaque_version}/{job_id}"
                packet_name, output_name = stem + ".json", stem + ".output.json"
                packet = {"judge_id": judge, "stage": "C", "n_items": len(batch),
                          "item_ids": [r["item_id"] for r in batch], "items": batch,
                          "output_path": output_name, "rubric": prompt_rubric,
                          "disclosure_note": "Judge only supplied evidence. Null text is unavailable. Do not browse or infer hidden metadata."}
                write_once(root / packet_name, packet)
                prompt = (f"Read exactly {packet_name} and no other file. Follow its rubric. Do not browse, "
                          "search the repository, use git, or inspect any other judgments. "
                          f"Write one JSON array of {len(batch)} records to {output_name}. "
                          + ("Use the packet's judge_id and stage. " if panel != "resolver" else "Use stage C and the resolver output schema. ")
                          + "Use a fresh isolated context with no inherited conversation. Return only WROTE <count> records.")
                jobs.append({"job_id": job_id, "panel": panel, "model": MODELS[panel], "stage": "C",
                             "judge_id": judge, "packet": packet_name, "packet_sha256": digest(root / packet_name),
                             "output": output_name, "item_ids": packet["item_ids"], "n_judgments": len(batch),
                             "launch_prompt": prompt, "execution_status": "NOT_LAUNCHED"})
        panels.append({"panel": panel, "model": MODELS[panel], "item_ids": ids,
                       "source_ids": shuffled if panel == "new_residual" else source_ids,
                       "items": len(items), "judgments": len(items) * len(judges), "optional": False})
    result = {"parent_analysis": version, "selection": "corrected raw Grok C in {Ambiguous, Unresolved}",
              "residual_seed": 20260823, "resolver_anonymization_seed": 20260829,
              "status": "PREPARED_NOT_EXECUTED", "panels": panels, "jobs": jobs,
              "resolver_policy": "Separate secondary outcomes, never replace raw consensus or select the primary residual cohort"}
    write_json(out / "followup_manifest.json", result)
    table(out / "tables/new_residual_id_map.csv", mapping)
    write_json(out / "followup_status.json", {"new_residual": "pending_fresh_judgments" if source_ids else "empty_cohort_no_jobs",
                                              "resolver": "pending_fresh_judgments" if source_ids else "no_resolver_needed",
                                              "residual_items": len(source_ids), "claude_judgments": 5 * len(source_ids),
                                              "resolver_judgments": len(source_ids), "scientific_estimates": None})
    return jobs


def residual_analysis(root, out, panel, manifest, raw, parent):
    config = next(p for p in manifest["panels"] if p["panel"] == panel)
    mapping = dict(zip(config["item_ids"], config["source_ids"]))
    parent_frame = pd.read_csv(root / f"corrections_v2/results/{parent}/tables/grok_claims.csv")
    parent_frame = parent_frame.set_index("source_item_id")
    cons = aggregate(raw, config["item_ids"]) if panel != "resolver" else {}
    rows = []
    for r in (raw if panel == "resolver" else [{"item_id": iid, **c} for iid, c in cons.items()]):
        source = mapping[r["item_id"]]
        meta = parent_frame.loc[source]
        label = r["resolver_outcome"] if panel == "resolver" else r["consensus"]
        rows.append({"item_id": r["item_id"], "source_item_id": source, "claim_id": meta.claim_id,
                     "cohort": meta.cohort, "regression_type": meta.regression_type,
                     "gold_label": meta.gold_label, "grok_raw_C": meta.consensus_C,
                     "fresh_C": label, "nondecisive": label not in DECISIVE,
                     "decisive_agrees_fever": label == meta.gold_label if label in DECISIVE else None,
                     **{k: v for k, v in r.items() if k != "item_id"}})
    table(out / "tables/claims.csv", rows)
    write_json(out / "consensus.json", clean(rows))
    frame = pd.DataFrame(rows)
    if not rows:
        return {"status": "empty_selected_cohort", "n": 0, "scientific_estimates": None}
    frame = frame.sort_values("source_item_id").reset_index(drop=True)
    summaries = []
    subgroup_masks = [("all", frame.index.notna())] + [(c, frame.cohort.eq(c)) for c in ("regression", "resistant", "rescue", "robust")]
    subgroup_masks += [("shared_regression", frame.cohort.eq("regression") & frame.regression_type.eq("both")),
                       ("specific_regression", frame.cohort.eq("regression") & ~frame.regression_type.eq("both"))]
    for name, mask in subgroup_masks:
        summaries.append({"analysis": "nondecisive_" + name, **rate(frame.loc[mask, "nondecisive"], 20260824)})
    dec = frame[~frame.nondecisive]
    summaries.append({"analysis": "decisive_FEVER_agreement", **rate(dec.decisive_agrees_fever, 20260829)})
    summaries.append({"analysis": "raw_cross_family_agreement" if panel != "resolver" else "resolver_raw_agreement",
                      **rate(frame.fresh_C.eq(frame.grok_raw_C))})
    reg, res = frame.cohort.eq("regression"), frame.cohort.eq("resistant")
    summaries.append({"analysis": "persistent_regression_vs_resistant_OR", "family": "exploratory",
                      **fisher(frame.loc[reg, "nondecisive"].tolist(), frame.loc[res, "nondecisive"].tolist())})
    conf = "confidence" if panel == "resolver" else "mean_confidence"
    a, b = frame.loc[frame.nondecisive, conf], frame.loc[~frame.nondecisive, conf]
    summaries.append({"analysis": "confidence_persistent_vs_resolved_MWU", "family": "exploratory",
                      "n": len(frame), "p_value": float(stats.mannwhitneyu(a, b, alternative="two-sided").pvalue) if len(a) and len(b) else None,
                      "status": "estimated" if len(a) and len(b) else "not_estimable_empty_group"})
    bh([r for r in summaries if r.get("family") == "exploratory"])
    table(out / "tables/statistical_tests.csv", summaries)
    if panel != "resolver":
        write_json(out / "agreement.json", agreement(raw))
    # Plot only the complete conditional cohort, never its pending placeholder.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.bar(LABELS, [int(frame.fresh_C.eq(x).sum()) for x in LABELS])
    ax.set(ylabel="Claims", title=f"{panel}: complete conditional cohort (n={len(frame)})")
    (out / "plots").mkdir()
    fig.savefig(out / "plots/outcomes.svg", metadata={"Date": None})
    plt.close(fig)
    write_json(out / "representative_cases.json", clean([frame[frame.fresh_C.eq(x)].sort_values("source_item_id").iloc[0].to_dict()
                                                         for x in LABELS if frame.fresh_C.eq(x).any()]))
    return {"status": "complete", "n": len(frame), "selection": "new_corrected_Grok_residual" if panel == "new_residual" else
            "fixed_historical_231_sensitivity" if panel == "claude_historical_residual_optional" else "secondary_resolver_only",
            "primary_consensus_replaced": False}


def analyze(root, manifest, panel, version, parent=None):
    status, raw = frozen_rows(manifest, panel, root, parent if panel in {"new_residual", "resolver"} else None)
    if raw is None:
        return status, 1
    if panel in {"new_residual", "resolver", "claude_historical_residual_optional"}:
        if not parent:
            raise ValueError("conditional analysis requires --parent with a frozen corrected Grok analysis")
        result_manifest(root, parent)
    final = root / f"corrections_v2/results/{version_name(version)}"
    out = final.with_name("." + final.name + ".incomplete")
    if out.exists() or final.exists():
        # No overwrite, even when a new result would look identical.
        raise ValueError("result version already exists; verify it or choose a new explicit version")
    out.mkdir(parents=True)
    frames, additional_files = {}, []
    if panel in {"new_residual", "resolver", "claude_historical_residual_optional"}:
        summary = residual_analysis(root, out, panel, manifest, raw, parent)
    else:
        names = ["grok", "claude_full"] if panel == "primary" else [panel]
        all_consensus, retained, rates, cases = [], {}, [], []
        packet_lookup = {r["item_id"]: r for r in read_rows(root / "corrections_v2/generated/stage_c_corrected.jsonl")}
        for name in names:
            frame, stages, cons, prov = panel_analysis(root, manifest, name, raw)
            frames[name] = frame
            all_consensus += cons
            retained[name] = prov
            rates += descriptive_rates(frame, name)
            table(out / f"tables/{name}_claims.csv", frame)
            table(out / f"tables/{name}_per_judge_transitions.csv", per_judge_transitions(stages))
            table(out / f"tables/{name}_agreement.csv", [dict(stage=s, **agreement(stages[s])) for s in "ABC"])
            for left, right in [("A", "B"), ("B", "C"), ("A", "C")]:
                matrix = pd.crosstab(frame[f"consensus_{left}"], frame[f"consensus_{right}"]).reindex(index=LABELS, columns=LABELS, fill_value=0)
                table(out / f"tables/{name}_{left}_{right}.csv", matrix.rename_axis(left).reset_index())
            if name == "grok":
                table(out / "tables/grok_Q1_Q12.csv", cohort_statistics(frame))
                additional_files = followups(root, out, version, frame, raw, manifest)
            for category in CATEGORIES + ["order_sensitive"]:
                selected = frame[frame.order_sensitive_C if category == "order_sensitive" else frame.category.eq(category)]
                if len(selected):
                    case = selected.sort_values("source_item_id").iloc[0].to_dict()
                    cases.append(dict(selection=category, **case, corrected_packet=packet_lookup[case["source_item_id"]]))
        table(out / "tables/descriptive_rates.csv", rates)
        write_json(out / "consensus.json", clean(all_consensus))
        write_json(out / "retained_AB_provenance.json", retained)
        write_json(out / "representative_cases.json", clean(cases))
        if panel == "primary":
            summary, comparison, confusion, final_matrix = cross_family(frames["grok"], frames["claude_full"])
            write_json(out / "cross_family_summary.json", summary)
            table(out / "tables/cross_family_tests.csv", comparison)
            table(out / "tables/taxonomy_confusion.csv", confusion.rename_axis("grok_category").reset_index())
            table(out / "tables/final_status_confusion.csv", final_matrix.rename_axis("grok_C").reset_index())
        draw_figures(out, frames)
        summary = {"status": "complete_raw_consensus_analysis", "panel": panel,
                   "denominators": {k: len(v) for k, v in frames.items()},
                   "cross_family": "complete" if panel == "primary" else "pending_other_primary_panel",
                   "resolver_dependent": "separate_pending_fresh_resolver_outputs",
                   "new_residual": "prepared_not_executed" if "grok" in frames else "pending_corrected_Grok",
                   "taxonomy": "proposed_v2_coauthor_review", "scientific_claims": "post_hoc_descriptive_not_causal"}
    summary.update(version=version, inference_launched=False, spec_sha256=digest(root / SPEC_FREEZE),
                   provenance_basis=status["provenance_basis"])
    write_json(out / "status.json", summary)
    out.rename(final)
    out = final
    files = {p.relative_to(root).as_posix(): digest(p) for p in sorted(out.rglob("*")) if p.is_file()}
    files.update({j["packet"]: j["packet_sha256"] for j in additional_files})
    frozen = freeze_path(root, panel, parent if panel in {"new_residual", "resolver"} else None)
    files[frozen.relative_to(root).as_posix()] = digest(frozen)
    artifact = {"version": version, "panel": panel, "parent": parent, "created_at_utc": stamp(),
                "spec_sha256": digest(root / SPEC_FREEZE), "judgment_freeze": frozen.relative_to(root).as_posix(),
                "files": files, "excludes_self": True}
    write_once(out / "artifact_manifest.json", artifact)
    return summary, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze-spec", "status", "freeze", "analyze", "verify-result", "show-job", "export-job", "export-handoff"])
    parser.add_argument("--panel", choices=["primary", *MODELS], default="primary")
    parser.add_argument("--version")
    parser.add_argument("--parent")
    parser.add_argument("--job")
    args = parser.parse_args()
    try:
        preparation_gate(ROOT)
        if args.action == "freeze-spec":
            result, code = freeze_spec(ROOT), 0
        else:
            spec = verify_spec(ROOT)
            dynamic = args.panel in {"new_residual", "resolver"}
            if dynamic and not args.parent:
                raise ValueError("dynamic panels require --parent")
            manifest = load_manifest(ROOT, args.parent if dynamic else None)
            if args.action == "export-handoff":
                if dynamic:
                    raise ValueError("export later jobs individually using their parent manifest")
                result, code = export_handoff(ROOT, manifest), 0
            elif args.action == "status":
                result, _, _ = inspect(manifest, args.panel, ROOT, spec)
                code = 0 if result["status"] == "ready_to_freeze" else 1
            elif args.action == "freeze":
                result = freeze_judgments(manifest, args.panel, ROOT, args.parent if dynamic else None)
                code = 0 if result["status"] == "frozen" else 1
            elif args.action in {"show-job", "export-job"}:
                matches = [j for j in panel_jobs(manifest, args.panel) if j["job_id"] == args.job]
                if len(matches) != 1:
                    raise ValueError("choose an exact job ID from the manifest")
                result, code = matches[0], 0
                if args.action == "export-job":
                    import zipfile
                    from rerun import validate_packet
                    job = matches[0]
                    validate_packet(job, ROOT)
                    target = ROOT / f"corrections_v2/handoff_jobs/{job['job_id']}.zip"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        with zipfile.ZipFile(target) as archive:
                            if archive.namelist() != [job["packet"]] or archive.read(job["packet"]) != (ROOT / job["packet"]).read_bytes():
                                raise ValueError("existing export differs; do not replace")
                    else:
                        with zipfile.ZipFile(target, "x") as archive:
                            info = zipfile.ZipInfo(job["packet"], date_time=(2000, 1, 1, 0, 0, 0))
                            archive.writestr(info, (ROOT / job["packet"]).read_bytes())
                    result = {"export": str(target), "sha256": digest(target), "packet_sha256": job["packet_sha256"],
                              "model": job["model"], "prompt": job["launch_prompt"],
                              "isolation": "Export contains one packet, not a sandbox. Operator must enforce filesystem/tool isolation."}
            elif args.action == "verify-result":
                result = result_manifest(ROOT, args.version)
                frozen = read_json(ROOT / result["judgment_freeze"])
                verify_file_map(ROOT, frozen["files"])
                result, code = {"status": "verified", "version": args.version}, 0
            else:
                if not args.version:
                    raise ValueError("analyze requires --version")
                result, code = analyze(ROOT, manifest, args.panel, args.version, args.parent)
        print(json.dumps(clean(result), indent=2, allow_nan=False))
        return code
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked_invalid_inputs", "error": str(exc),
                          "scientific_estimates": None, "inference_launched": False}, indent=2))
        return 2


def export_handoff(root, manifest):
    """Self-contained dispatch material; the offline analysis stays in the repo."""
    import io
    import zipfile
    from rerun import validate_packet

    def archive_bytes(entries):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
        return stream.getvalue()

    entries = {}
    for name in ["corrections_v2/CURSOR_HANDOFF.md", "corrections_v2/protocol/analysis_spec_2026-09-27.md",
                 SPEC_FREEZE, "corrections_v2/protocol/execution.template.json", MANIFEST]:
        entries["OPERATOR_ONLY/" + name] = lf_bytes((root / name).read_bytes())
    entries["OPERATOR_ONLY/START_HERE.txt"] = (
        "Operator material is never judge-visible. Read corrections_v2/CURSOR_HANDOFF.md.\n"
        "Required: p01 + p02 (70 jobs / 6430 judgments). p03 is optional (15 / 1155).\n"
        "Availability/routing NOT verified. Do not substitute locked models.\n"
        "Each jobs/*.zip contains exactly one rubric-bearing input packet.\n"
        "Extract one job into a separately enforced packet-only, offline, fresh-context sandbox.\n"
        "Dispatch its exact model + launch_prompt from the private manifest.\n"
        "Capture raw output + execution evidence; return them to the original verified repository\n"
        "for validation, freezing and offline analysis. No other repository file is needed by a judge.\n"
    ).encode()
    for job in manifest["jobs"]:
        validate_packet(job, root)
        entries[f"jobs/{job['job_id']}.zip"] = archive_bytes({job["packet"]: (root / job["packet"]).read_bytes()})
    data = archive_bytes(entries)
    target = root / "corrections_v2/handoff/cursor_handoff_2026-09-27.zip"
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError("existing dated handoff differs; do not overwrite")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
    return {"status": "prepared_not_executed", "bundle": target.relative_to(root).as_posix(),
            "sha256": digest(target), "required_jobs": 70, "optional_jobs": 15,
            "model_availability": "unverified", "inference_launched": False}


if __name__ == "__main__":
    raise SystemExit(main())
