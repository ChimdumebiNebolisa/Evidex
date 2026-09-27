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


def validate_job(job):
    packet = ROOT / job["packet"]
    if hashlib.sha256(packet.read_bytes()).hexdigest() != job["packet_sha256"]:
        raise ValueError(f"packet changed: {job['job_id']}")
    path = ROOT / job["output"]
    if not path.exists():
        return "missing"
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or [r.get("item_id") for r in rows] != job["item_ids"]:
        raise ValueError(f"wrong items/order or duplicate: {job['job_id']}")
    for r in rows:
        if (r.get("judge_id") != job["judge_id"] or r.get("stage") != job["stage"] or
                r.get("verdict") not in {"Supported", "Refuted", "Ambiguous"} or
                r.get("evidence_sufficiency") not in SUFFICIENCY or
                type(r.get("confidence")) is not int or not 0 <= r["confidence"] <= 100 or
                not isinstance(r.get("issue_flags"), list) or not r["issue_flags"] or
                not set(r["issue_flags"]) <= FLAGS or
                not isinstance(r.get("brief_reason"), str) or not r["brief_reason"].strip()):
            raise ValueError(f"invalid record: {job['job_id']}:{r.get('item_id')}")
    return "valid"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "show-job", "validate"])
    parser.add_argument("job_id", nargs="?")
    args = parser.parse_args()
    jobs = json.loads(MANIFEST.read_text(encoding="utf-8"))["jobs"]
    if args.action == "list":
        for j in jobs:
            print(f"{j['job_id']} {j['model']} {j['n_judgments']} judgments")
    elif args.action == "show-job":
        selected = [j for j in jobs if j["job_id"] == args.job_id]
        if len(selected) != 1:
            parser.error("supply an exact job ID from list")
        print(json.dumps(selected[0], indent=2))
    else:
        missing = [j["job_id"] for j in jobs if validate_job(j) == "missing"]
        print(json.dumps({"expected_jobs": len(jobs), "missing": missing, "launched_by_this_command": 0}, indent=2))
        if missing:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
