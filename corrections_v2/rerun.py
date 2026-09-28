"""Inspect exact prepared jobs or validate delivered files. Never calls a model."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corrections_v2/generated/rerun_manifest.json"
SUFFICIENCY = {"clearly_sufficient", "probably_sufficient", "partial_or_ambiguous",
               "probably_insufficient", "clearly_insufficient"}
FLAGS = {"none", "possible_missing_title_context", "possible_coreference_or_entity_resolution",
         "possible_missing_surrounding_context", "multi_sentence_integration",
         "numerical_or_temporal_reasoning", "negation_or_scope", "entity_or_attribute_confusion",
         "partial_warrant", "apparent_internal_contradiction", "other"}


def validate_packet(job, root=ROOT):
    packet = root / job["packet"]
    if hashlib.sha256(packet.read_bytes()).hexdigest() != job["packet_sha256"]:
        raise ValueError(f"packet changed: {job['job_id']}")
    data = json.loads(packet.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or
            data.get("item_ids") != job["item_ids"] or data.get("judge_id") != job["judge_id"] or
            data.get("stage") != job["stage"] or data.get("n_items") != job["n_judgments"] or
            not isinstance(data.get("items"), list) or
            not all(isinstance(r, dict) for r in data["items"]) or
            [r.get("item_id") for r in data["items"]] != job["item_ids"]):
        raise ValueError(f"packet metadata inconsistent: {job['job_id']}")


def validate_job(job, root=ROOT):
    validate_packet(job, root)
    path = root / job["output"]
    if not path.exists():
        return "missing"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return validate_rows(job, rows)


def validate_rows(job, rows):
    """Validate records without writing or reading a delivered output file."""
    if (not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows) or
            [r.get("item_id") for r in rows] != job["item_ids"]):
        raise ValueError(f"wrong items/order or duplicate: {job['job_id']}")
    for r in rows:
        if (r.get("judge_id") != job["judge_id"] or r.get("stage") != job["stage"] or
                r.get("verdict") not in {"Supported", "Refuted", "Ambiguous"} or
                r.get("evidence_sufficiency") not in SUFFICIENCY or
                type(r.get("confidence")) is not int or not 0 <= r["confidence"] <= 100 or
                not isinstance(r.get("issue_flags"), list) or not r["issue_flags"] or
                not all(isinstance(flag, str) and flag in FLAGS for flag in r["issue_flags"]) or
                not isinstance(r.get("brief_reason"), str) or not r["brief_reason"].strip()):
            raise ValueError(f"invalid record: {job['job_id']}:{r.get('item_id')}")
    return "valid"


def completion_status(manifest, scope="required", root=ROOT):
    """Schema/completeness checks only, never an inference/provenance claim.

    Both group statuses are reported; only selected groups affect exit status.
    Mock outputs belong in isolated fixture roots, never the live output tree.
    """
    if scope not in {"required", "optional", "all"}:
        raise ValueError(f"unknown scope: {scope}")
    optional = {p["panel"] for p in manifest["panels"] if p["optional"]}
    groups = {s: {"expected_jobs": 0, "expected_judgments": 0, "valid_jobs": 0,
                  "valid_judgments": 0, "missing_jobs": [], "invalid_jobs": {},
                  "preparation_errors": {}} for s in ("required", "optional")}
    for job in manifest["jobs"]:
        group = groups["optional" if job["panel"] in optional else "required"]
        group["expected_jobs"] += 1
        group["expected_judgments"] += job["n_judgments"]
        try:
            validate_packet(job, root)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            group["preparation_errors"][job["job_id"]] = str(exc)
            continue
        try:
            status = validate_job(job, root)
            if status == "missing":
                group["missing_jobs"].append(job["job_id"])
            else:
                group["valid_jobs"] += 1
                group["valid_judgments"] += job["n_judgments"]
        except (OSError, ValueError, TypeError, KeyError) as exc:
            group["invalid_jobs"][job["job_id"]] = str(exc)
    for name, group in groups.items():
        expected = (70, 6430) if name == "required" else (15, 1155)
        if (group["expected_jobs"], group["expected_judgments"]) != expected:
            group["preparation_errors"]["manifest"] = f"expected {expected[0]} jobs / {expected[1]} judgments"
        selected_ids = [j["job_id"] for j in manifest["jobs"]
                        if (j["panel"] in optional) == (name == "optional")]
        if len(set(selected_ids)) != len(selected_ids):
            group["preparation_errors"]["manifest_duplicate"] = "duplicate job identifiers"
        group["status"] = "complete" if not group["preparation_errors"] and group["valid_jobs"] == group["expected_jobs"] else "incomplete"
    selected = list(groups.values()) if scope == "all" else [groups[scope]]
    prep = not any(g["preparation_errors"] for g in selected)
    schemas = ("invalid" if any(g["invalid_jobs"] for g in selected) else
               "valid_present_outputs" if any(g["valid_jobs"] for g in selected) else "no_outputs")
    ok = prep and all(g["status"] == "complete" for g in selected)
    result = {"scope": scope, "selected_scope_passed": ok,
              "preparation_integrity": "valid" if prep else "invalid",
              "preparation_integrity_scope": "selected packet bytes/metadata and fixed workload; verify_outputs.py checks the entire package",
              "output_schema_validity": schemas,
              "required_judgment_completeness": groups["required"],
              "optional_judgment_completeness": groups["optional"],
              "execution_provenance_completeness": "not_assessed_no_execution_log_validator",
              "inference_execution": "not_verified_by_output_presence",
              "corrected_consensus_availability": "not_computed_or_validated_by_this_command",
              "launched_by_this_command": 0}
    return result, 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "show-job", "validate"])
    parser.add_argument("job_id", nargs="?")
    parser.add_argument("--scope", choices=["required", "optional", "all"], default="required",
                        help="Completion scope; default required primary panels only")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    jobs = manifest["jobs"]
    if args.action == "list":
        for j in jobs:
            print(f"{j['job_id']} {j['model']} {j['n_judgments']} judgments")
    elif args.action == "show-job":
        selected = [j for j in jobs if j["job_id"] == args.job_id]
        if len(selected) != 1:
            parser.error("supply an exact job ID from list")
        print(json.dumps(selected[0], indent=2))
    else:
        result, status = completion_status(manifest, args.scope)
        print(json.dumps(result, indent=2))
        raise SystemExit(status)


if __name__ == "__main__":
    main()
