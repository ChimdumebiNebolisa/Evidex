"""Reconstruct per-attempt execution evidence for the 70 required correction-v2 jobs.

Read-only with respect to execution records, outputs, staging archives and WSL
records. Writes only under corrections_v2/deviation_review/evidence/.
Launch facts are reported as "unknown" unless a surviving artifact establishes them.
"""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "corrections_v2"))
from rerun import validate_rows  # noqa: E402

STAGING = Path(r"C:\Users\Chimdumebi\evidex_execution_records")
TERMINALS = Path(r"C:\Users\Chimdumebi\.cursor\projects\c-Users-Chimdumebi-evidex\terminals")
EVIDENCE = ROOT / "corrections_v2/deviation_review/evidence"
FLAGGED = ["p01_C_j4_b08", "p01_C_j4_b09", "p02_C_j2_b03", "p02_C_j3_b01", "p02_C_j3_b02", "p02_C_j3_b03"]
SLOT = re.compile(r"attempt-(\d{2})")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_meta(path):
    from datetime import datetime, timezone
    stat = path.stat()
    return {"size": stat.st_size, "sha256": sha(path),
            "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()}


def summarize_events(path):
    types, tools, agents, runs, statuses = Counter(), Counter(), [], [], []
    error = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        types[event.get("type")] += 1
        for key, bucket in (("agent_id", agents), ("run_id", runs)):
            if event.get(key) and event[key] not in bucket:
                bucket.append(event[key])
        if event.get("type") == "status":
            statuses.append(event.get("status"))
            if event.get("status") == "ERROR":
                error = event.get("message")
        if event.get("type") == "tool_call" and event.get("status") == "completed":
            tools[event.get("name")] += 1
    return {"n_events": sum(types.values()), "types": dict(types), "completed_tools": dict(tools),
            "agent_ids": agents, "run_ids": runs, "statuses": statuses, "error_message": error}


def check_output(job, path):
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        return {"sha256": sha(path), "parse": f"invalid JSON: {type(exc).__name__}", "schema_valid": False}
    try:
        valid = validate_rows(job, rows) == "valid"
        detail = None
    except (ValueError, TypeError, KeyError) as exc:
        valid, detail = False, str(exc)
    return {"sha256": sha(path), "parse": "ok", "n_rows": len(rows) if isinstance(rows, list) else None,
            "schema_valid": valid, "schema_error": detail}


def runner_log_events():
    found = defaultdict(list)
    start = re.compile(r"^START (\S+) panel=\S+ attempt=(\d+)")
    failed = re.compile(r"^(ATTEMPT_FAILED|CHECKPOINT_FAILED) (\S+) attempt=(\d+) code=(-?\d+)")
    info = re.compile(r"^(\d\d:\d\d:\d\d\.\d+) INFO")
    for log in sorted(TERMINALS.glob("*.txt")):
        current = None
        for number, line in enumerate(log.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            line = re.sub(r"^\s*\d+\|", "", line)
            if m := start.match(line):
                current = (m.group(1), int(m.group(2)))
                found[current].append({"log": log.name, "line": number, "event": "START"})
            elif m := failed.match(line):
                found[(m.group(2), int(m.group(3)))].append(
                    {"log": log.name, "line": number, "event": m.group(1), "code": int(m.group(4))})
            elif current and line.startswith("ACCEPTED "):
                found[current].append({"log": log.name, "line": number, "event": "ACCEPTED"})
            elif current and ("workspace or record dir already exists" in line or "archive already contains" in line
                              or "delivered output already exists" in line):
                found[current].append({"log": log.name, "line": number, "event": "message", "text": line.strip()})
            elif current and (m := info.match(line)) and not any(e.get("launch_clock_utc") for e in found[current]
                                                                  if e["log"] == log.name):
                found[current].append({"log": log.name, "line": number, "event": "node_started",
                                       "launch_clock_utc": m.group(1)})
            elif line.startswith('{"status":"pending_human_review"'):
                data = json.loads(line)
                found[(data["job_id"], data["attempt"])].append(
                    {"log": log.name, "line": number, "event": "run_finished",
                     "agent_id": data.get("agent_id"), "run_id": data.get("run_id")})
    return found


def main():
    manifest = json.loads((ROOT / "corrections_v2/generated/rerun_manifest.json").read_text(encoding="utf-8"))
    required = [j for j in manifest["jobs"] if j["panel"] in {"grok", "claude_full"}]
    inventory = json.loads((EVIDENCE / "wsl_inventory.json").read_text(encoding="utf-8"))
    wsl = defaultdict(dict)
    for item in inventory:
        parts = item["path"].split("/")
        if len(parts) > 5 and parts[3] in {"records", "isolated"} and SLOT.fullmatch(parts[5]):
            kind = "records" if parts[3] == "records" else "workspace"
            wsl[(parts[4], int(parts[5][-2:]))][f"{kind}:{'/'.join(parts[6:])}"] = item
    logs = runner_log_events()

    jobs_out = []
    for job in required:
        job_id = job["job_id"]
        execution_dir = ROOT / "corrections_v2/execution" / job_id
        accepted_sha = sha(ROOT / job["output"]) if (ROOT / job["output"]).exists() else None
        slots = {int(p.stem[-2:]) for p in execution_dir.glob("attempt-*.json")}
        slots |= {int(p.name[-2:]) for p in (STAGING / job_id).glob("attempt-*") if p.is_dir()}
        slots |= {n for (j, n) in wsl if j == job_id}
        rows = []
        for n in sorted(slots):
            label = f"{n:02d}"
            record_path = execution_dir / f"attempt-{label}.json"
            record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else None
            stage_dir = STAGING / job_id / f"attempt-{label}"
            staging = {p.name: file_meta(p) for p in sorted(stage_dir.iterdir())} if stage_dir.is_dir() else {}
            wsl_files = wsl.get((job_id, n), {})
            wsl_records = {k.split(":", 1)[1]: v for k, v in wsl_files.items() if k.startswith("records:")}
            wsl_output = wsl_files.get(f"workspace:workspace/{job['output']}")
            mismatches = sorted(name for name, meta in wsl_records.items()
                                if name in staging and staging[name]["sha256"] != meta["sha256"])
            events_path = stage_dir / f"attempt-{label}.sdk-events.jsonl"
            events = summarize_events(events_path) if events_path.exists() else None
            dispatch = None
            if (stage_dir / "dispatch-error.json").exists():
                data = json.loads((stage_dir / "dispatch-error.json").read_text(encoding="utf-8"))
                dispatch = {"stage": data.get("stage"), "message": data.get("error", {}).get("message")}
            routing = None
            if (stage_dir / f"attempt-{label}.routing.json").exists():
                data = json.loads((stage_dir / f"attempt-{label}.routing.json").read_text(encoding="utf-8"))
                routing = {k: data.get(k) for k in ("agent_id", "run_id", "started_at_utc", "completed_at_utc",
                                                    "output_sha256", "run_model", "result_model")}
            output = None
            for candidate in ("workspace.output.json", f"attempt-{label}.raw.txt"):
                if (stage_dir / candidate).exists():
                    output = check_output(job, stage_dir / candidate) | {"file": candidate}
                    break
            log = logs.get((job_id, n), [])

            agent_ids = set((events or {}).get("agent_ids", [])) | {routing["agent_id"]} if routing else set(
                (events or {}).get("agent_ids", []))
            agent_ids |= {e["agent_id"] for e in log if e.get("agent_id")}
            run_ids = set((events or {}).get("run_ids", [])) | ({routing["run_id"]} if routing else set())
            if agent_ids:
                agent_created = "yes"
            elif dispatch and dispatch["stage"] == "Agent.create":
                agent_created = "no (Agent.create failed)"
            else:
                agent_created = "unknown"
            if run_ids:
                send = "yes"
            elif dispatch and dispatch["stage"] == "agent.send":
                send = "attempted; failed before a run ID was recorded"
            else:
                send = "unknown"
            record_session = record.get("session_id") if record else None
            rows.append({
                "attempt": n,
                "execution_record": None if record is None else {
                    "status": record.get("status"), "reason": record.get("reason"),
                    "session_id": record_session, "started_at_utc": record.get("started_at_utc"),
                    "completed_at_utc": record.get("completed_at_utc")},
                "agent_created": agent_created,
                "send_occurred": send,
                "agent_ids": sorted(agent_ids),
                "run_ids": sorted(run_ids),
                "events": events,
                "dispatch_error": dispatch,
                "routing": routing,
                "model_output": output,
                "output_is_accepted_output": bool(output and output["sha256"] == accepted_sha),
                "wsl_record_files": wsl_records,
                "wsl_workspace_output": wsl_output,
                "staging_files": staging,
                "staging_vs_wsl_hash_mismatches": mismatches,
                "record_session_matches_slot_evidence": (
                    None if not record_session or record_session == "unknown" or not agent_ids
                    else record_session in agent_ids),
                "runner_log": log,
            })
        accepted = [r["attempt"] for r in rows if (r["execution_record"] or {}).get("status") == "accepted"]
        valid_slots = [r["attempt"] for r in rows if r["model_output"] and r["model_output"]["schema_valid"]]
        jobs_out.append({
            "job_id": job_id, "panel": job["panel"], "n_judgments": job["n_judgments"],
            "accepted_attempts": accepted, "execution_record_count": len(list(execution_dir.glob("attempt-*.json"))),
            "slots_with_schema_valid_output": valid_slots,
            "earlier_schema_valid_output_than_accepted": bool(accepted and valid_slots and min(valid_slots) < accepted[0]),
            "attempts": rows,
        })
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "attempt_evidence.json").write_text(json.dumps(jobs_out, indent=2) + "\n", encoding="utf-8")
    summary = {
        "jobs": len(jobs_out),
        "jobs_with_exactly_one_accepted": sum(len(j["accepted_attempts"]) == 1 for j in jobs_out),
        "jobs_over_three_records": [j["job_id"] for j in jobs_out if j["execution_record_count"] > 3],
        "jobs_with_earlier_schema_valid_output": [
            {"job_id": j["job_id"], "valid_slots": j["slots_with_schema_valid_output"],
             "accepted": j["accepted_attempts"]} for j in jobs_out if j["earlier_schema_valid_output_than_accepted"]],
        "slots_where_record_session_contradicts_evidence": [
            (j["job_id"], r["attempt"]) for j in jobs_out for r in j["attempts"]
            if r["record_session_matches_slot_evidence"] is False],
        "slots_with_unknown_record_session_but_agent_evidence": [
            (j["job_id"], r["attempt"]) for j in jobs_out for r in j["attempts"]
            if (r["execution_record"] or {}).get("session_id") == "unknown" and r["agent_ids"]],
        "staging_vs_wsl_mismatches": [
            (j["job_id"], r["attempt"], r["staging_vs_wsl_hash_mismatches"]) for j in jobs_out for r in j["attempts"]
            if r["staging_vs_wsl_hash_mismatches"]],
        "slots_without_execution_record": [
            (j["job_id"], r["attempt"]) for j in jobs_out for r in j["attempts"] if r["execution_record"] is None],
    }
    (EVIDENCE / "attempt_evidence_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
