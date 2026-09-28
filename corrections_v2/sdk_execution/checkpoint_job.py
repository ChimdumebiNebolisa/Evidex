"""Copy one accepted Linux SDK attempt into the repository archive. No inference."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rerun import MANIFEST, ROOT, validate_rows

EXECUTION = ROOT / "corrections_v2" / "execution"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def same_selection(left, right) -> bool:
    def normalized(value):
        return {
            "id": value.get("id"),
            "params": sorted(value.get("params") or [], key=lambda item: item["id"]),
        }
    return normalized(left) == normalized(right)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--attempt", required=True, type=int)
    parser.add_argument("--staging", required=True)
    parser.add_argument("--cursor-version", required=True)
    args = parser.parse_args()
    if args.attempt < 1 or args.attempt > 9:
        raise SystemExit("--attempt must be 1 through 9")

    manifest = load_json(MANIFEST)
    optional = {panel["panel"] for panel in manifest["panels"] if panel.get("optional")}
    jobs = [item for item in manifest["jobs"] if item["job_id"] == args.job]
    if len(jobs) != 1:
        raise SystemExit("choose an exact required job ID")
    job = jobs[0]
    if job["panel"] in optional:
        raise SystemExit("optional jobs are not authorized")

    label = f"{args.attempt:02d}"
    staging = Path(args.staging)
    routing = load_json(staging / f"attempt-{label}.routing.json")
    raw = staging / f"attempt-{label}.raw.txt"
    hooks = staging / f"attempt-{label}.hooks.jsonl"
    events = staging / f"attempt-{label}.sdk-events.jsonl"
    routing_txt = staging / f"attempt-{label}.routing.txt"
    if not raw.exists() or not routing_txt.exists() or not hooks.exists() or not events.exists():
        raise SystemExit("staging is missing raw, routing, hook audit, or SDK event stream")
    if routing.get("job_id") != args.job or routing.get("attempt") != args.attempt:
        raise SystemExit("routing job/attempt mismatch")
    if routing.get("status") != "pending_human_review":
        raise SystemExit("only pending_human_review staging may be checkpointed")
    if routing.get("requested_model") != job["model"]:
        raise SystemExit("requested model does not match the locked slug")
    if not routing.get("catalog_variant_verified") or not routing.get("sandbox_enabled"):
        raise SystemExit("catalog or sandbox evidence missing")
    if not same_selection(routing.get("run_model") or {}, routing.get("sdk_model_selection") or {}):
        raise SystemExit("run.model does not match dispatched selection")
    if not same_selection(routing.get("result_model") or {}, routing.get("sdk_model_selection") or {}):
        raise SystemExit("result.model does not match dispatched selection")
    for model in routing.get("init_models") or []:
        if not same_selection(model, routing["sdk_model_selection"]):
            raise SystemExit("init model does not match dispatched selection")
    for event in routing.get("tool_events") or []:
        if event.get("name") not in {"read", "piRead", "piWrite", "edit", "piEdit"}:
            raise SystemExit(f"non-allowlisted tool: {event}")
    if digest(raw) != routing["raw_response_sha256"]:
        raise SystemExit("raw hash mismatch")
    rows = json.loads(raw.read_text(encoding="utf-8"))
    if validate_rows(job, rows) != "valid":
        raise SystemExit("schema invalid")
    if hashlib.sha256(raw.read_bytes()).hexdigest() != routing["output_sha256"]:
        raise SystemExit("raw bytes must equal generated output bytes")

    if hooks.exists():
        for line in hooks.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("permission") == "allow" and record.get("reason") not in {
                "designated packet read",
                "designated output read",
                "designated output write",
            }:
                raise SystemExit(f"hook allowed unexpected access: {record}")

    dest_dir = EXECUTION / args.job
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_output = ROOT / job["output"]
    if dest_output.exists():
        raise SystemExit("delivered output already exists; refuse overwrite")
    for name in (
        f"attempt-{label}.raw.txt",
        f"attempt-{label}.routing.txt",
        f"attempt-{label}.hooks.jsonl",
        f"attempt-{label}.sdk-events.jsonl",
    ):
        source = staging / name
        target = dest_dir / name
        if not source.exists():
            raise SystemExit(f"missing staging file: {name}")
        if target.exists():
            raise SystemExit(f"archive already contains {name}")
        shutil.copy2(source, target)

    dest_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw, dest_output)
    raw_archive = dest_dir / f"attempt-{label}.raw.txt"
    routing_archive = dest_dir / f"attempt-{label}.routing.txt"
    record = {
        "job_id": args.job,
        "attempt": args.attempt,
        "status": "accepted",
        "requested_model": job["model"],
        "resolved_model": job["model"],
        "provider_model_version": None,
        "version_metadata_status": "not_exposed",
        "version_metadata_note": (
            "Catalog, dispatch, SDK init, run.model, result.model, fail-closed hook audit, "
            "SDK event stream, and usage records were inspected. Provider/backend version is not exposed."
        ),
        "cursor_version": args.cursor_version,
        "session_id": routing["agent_id"],
        "started_at_utc": routing["started_at_utc"],
        "completed_at_utc": routing["completed_at_utc"],
        "operator": "cursor-coordinator",
        "reviewer": "cursor-coordinator-gate",
        "routing_and_isolation_reviewed": True,
        "fresh_context": True,
        "inherited_context": False,
        "auto": False,
        "inherit": False,
        "web_browse": False,
        "external_retrieval": False,
        "temperature": "provider_default",
        "visible_input_files": [job["packet"]],
        "packet_sha256": job["packet_sha256"],
        "output_sha256": digest(dest_output),
        "raw_response": {
            "path": raw_archive.relative_to(ROOT).as_posix(),
            "sha256": digest(raw_archive),
        },
        "routing_evidence": {
            "path": routing_archive.relative_to(ROOT).as_posix(),
            "sha256": digest(routing_archive),
        },
    }
    record_path = dest_dir / f"attempt-{label}.json"
    if record_path.exists():
        raise SystemExit("attempt record already exists")
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "accepted",
        "job_id": args.job,
        "attempt": args.attempt,
        "output": job["output"],
        "output_sha256": record["output_sha256"],
        "session_id": record["session_id"],
        "record": record_path.relative_to(ROOT).as_posix(),
    }))


if __name__ == "__main__":
    main()
