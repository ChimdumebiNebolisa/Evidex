"""Post-judgment amendment A1 (2026-09-28) to the correction-v2 Stage C analysis.

Written after all 70 required Stage C outputs existed and after provisional results had been
inspected; see AMENDMENT_A1.md. It changes three execution rules and nothing else:

  1. up to 9 attempt records per job (frozen protocol: 3);
  2. an attempt record whose session is `unknown` counts as a launched attempt when the slot's
     surviving SDK event log names exactly one agent that appears in no other slot or record;
     that agent ID then takes part in the session-uniqueness check;
  3. the analysed output of every job is its checkpoint-accepted output (explicit selection);
     first-schema-valid alternatives are sensitivity analyses only.

The provenance check is the frozen analysis_io.provenance_for_job with the single constant
3 -> 9 substituted in its source; all other frozen checks run unchanged. The analysis is the
frozen analysis code, called through deviation_review/provisional_analysis.compute.

  python corrections_v2/amendment_2026-09-28/amended_analysis.py evaluate-collisions   (needs WSL; one-time)
  python corrections_v2/amendment_2026-09-28/amended_analysis.py status
  python corrections_v2/amendment_2026-09-28/amended_analysis.py run
"""
import argparse
import hashlib
import inspect as pyinspect
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "corrections_v2"))
sys.path.insert(0, str(ROOT / "corrections_v2/deviation_review"))

import analysis_io  # noqa: E402
from analysis_io import digest, load_manifest, panel_jobs, read_json, verify_spec  # noqa: E402
import provisional_analysis as pa  # noqa: E402

AMEND = "corrections_v2/amendment_2026-09-28"
RESULTS = f"{AMEND}/results"
EVALUATION = ROOT / AMEND / "collision_evaluation.json"
EVIDENCE = ROOT / "corrections_v2/deviation_review/evidence/attempt_evidence.json"
LABEL = "AMENDMENT_A1_2026-09-28__POST_JUDGMENT_NOT_PREREGISTERED"
MAX_ATTEMPTS = 9
FROZEN_CAP_LINE = "if len(paths) > 3:"


def amended_provenance_for_job():
    source = pyinspect.getsource(analysis_io.provenance_for_job)
    if source.count(FROZEN_CAP_LINE) != 1:
        raise SystemExit("frozen provenance_for_job no longer has exactly one cap line")
    namespace = dict(vars(analysis_io))
    exec(source.replace(FROZEN_CAP_LINE, f"if len(paths) > {MAX_ATTEMPTS}:"), namespace)
    return namespace["provenance_for_job"]


def execution_records():
    for path in sorted((ROOT / "corrections_v2/execution").glob("*/attempt-*.json")):
        yield path, read_json(path)


def slot_evidence():
    return {(j["job_id"], a["attempt"]): a for j in json.loads(EVIDENCE.read_text("utf-8")) for a in j["attempts"]}


def evaluate_collisions():
    """Re-read each unknown-session slot's SDK event log from WSL and compare it with the recorded evidence."""
    if EVALUATION.exists():
        raise SystemExit(f"{EVALUATION.relative_to(ROOT)} exists; it is written once")
    evidence = slot_evidence()
    all_agents = [i for a in evidence.values() for i in (a.get("agent_ids") or [])]
    record_sessions = [r["session_id"] for _, r in execution_records()
                       if r.get("session_id") != "unknown" and not str(r.get("session_id")).startswith("not_launched:")]
    rows = []
    for path, record in execution_records():
        if record.get("session_id") != "unknown":
            continue
        key = (record["job_id"], record["attempt"])
        slot = evidence[key]
        name = f"attempt-{record['attempt']:02}.sdk-events.jsonl"
        recorded = slot["wsl_record_files"][name]
        data = subprocess.run(["wsl", "-u", "root", "-e", "cat", recorded["path"]], capture_output=True, check=True).stdout
        events = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
        agents = sorted({e["agent_id"] for e in events if e.get("agent_id")})
        runs = sorted({e["run_id"] for e in events if e.get("run_id")})
        statuses = [e["status"] for e in events if e.get("type") == "status"]
        agent = agents[0] if len(agents) == 1 else None
        checks = {
            "event_log_sha256_matches_recorded": hashlib.sha256(data).hexdigest() == recorded["sha256"],
            "event_log_size_matches_recorded": len(data) == recorded["size"],
            "exactly_one_agent": len(agents) == 1,
            "agent_matches_recorded_evidence": agents == sorted(slot.get("agent_ids") or []),
            "agent_unique_across_all_slots": agent is not None and all_agents.count(agent) == 1,
            "agent_absent_from_all_record_sessions": agent is not None and agent not in record_sessions,
            "record_is_exit_code_2_collision": record.get("status") == "error"
            and record.get("reason") == "Execution failed with returncode 2",
        }
        rows.append({
            "job_id": record["job_id"], "attempt": record["attempt"],
            "record": path.relative_to(ROOT).as_posix(), "record_sha256": digest(path),
            "record_status": record.get("status"), "record_reason": record.get("reason"),
            "event_log": recorded["path"], "event_log_size": len(data), "event_log_sha256": hashlib.sha256(data).hexdigest(),
            "event_log_agent_ids": agents, "event_log_run_ids": runs, "event_log_statuses": statuses,
            "event_log_error": next((e.get("message") for e in reversed(events) if e.get("type") == "status"
                                     and e.get("status") == "ERROR" and e.get("message")), None),
            "runner_log": slot.get("runner_log"), "checks": checks,
            "verdict": "launched; agent identified from surviving event log" if all(checks.values()) else "not established",
        })
    payload = {
        "amendment": "A1 (2026-09-28), rule 2",
        "method": "each record with session 'unknown' is compared with the SDK event log that survives in its slot "
                  "(read from WSL on the evaluation date, hashed, parsed); the records themselves are unchanged",
        "n_unknown_session_records": len(rows),
        "n_established": sum(r["verdict"].startswith("launched") for r in rows),
        "n_distinct_agents_all_slots": len(set(all_agents)), "n_agent_slots": len(all_agents),
        "records": rows,
    }
    EVALUATION.parent.mkdir(parents=True, exist_ok=True)
    EVALUATION.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "records"}, indent=2))
    return 0 if payload["n_established"] == len(rows) else 1


def amended_status():
    spec = verify_spec(ROOT)
    manifest = load_manifest(ROOT)
    frozen, _, _ = analysis_io.inspect(manifest, "primary", ROOT, spec)
    provenance = amended_provenance_for_job()
    evaluation = json.loads(EVALUATION.read_text("utf-8"))
    identified = {(r["job_id"], r["attempt"]): r for r in evaluation["records"]
                  if r["verdict"].startswith("launched") and digest(ROOT / r["record"]) == r["record_sha256"]}
    evidence = slot_evidence()
    errors, sessions, jobs = {}, [], panel_jobs(manifest, "primary")
    for job in jobs:
        try:
            provenance(job, ROOT, spec)
        except (ValueError, OSError, TypeError, KeyError) as exc:
            errors[job["job_id"]] = str(exc)
            continue
        for path in sorted((ROOT / "corrections_v2/execution" / job["job_id"]).glob("attempt-*.json")):
            record, key = read_json(path), (job["job_id"], int(path.stem.split("-")[1]))
            session = record["session_id"]
            if session.startswith("not_launched:"):
                continue
            if session == "unknown":
                if key not in identified:
                    errors[f"{job['job_id']}/attempt-{key[1]:02}"] = "unknown session not established by slot evidence"
                    continue
                session = identified[key]["event_log_agent_ids"][0]
            elif evidence[key].get("agent_ids") and evidence[key]["agent_ids"] != [session]:
                errors[f"{job['job_id']}/attempt-{key[1]:02}"] = "recorded session contradicts slot evidence"
            sessions.append(session)
    if len(sessions) != len(set(sessions)):
        errors["reused_session"] = "a session appears in more than one attempt"
    selected = {j["job_id"] for j in jobs}
    for path, record in execution_records():
        if path.parent.name not in selected and record.get("session_id") in sessions:
            errors["reused_session"] = "selected session reused by another panel/job"
    ready = not (errors or frozen["missing_jobs"] or frozen["invalid_outputs_or_packets"])
    return {
        "label": LABEL, "panel": "primary",
        "status": "ready_under_amendment_A1" if ready else "incomplete_under_amendment_A1",
        "max_attempts": MAX_ATTEMPTS, "sessions_checked": len(sessions), "distinct_sessions": len(set(sessions)),
        "unknown_session_records_resolved_by_evidence": len(identified),
        "amended_provenance_errors": errors,
        "frozen_protocol_status": frozen["status"],
        "frozen_protocol_provenance_errors": frozen["execution_provenance_errors"],
        "valid_schema_judgments": frozen["valid_schema_judgments"],
        "output_selection": "checkpoint-accepted output of every job (amendment rule 3)",
        "inference_launched": False,
    }


def run():
    out = ROOT / RESULTS
    if out.exists() and any(p.name != ".gitattributes" for p in out.iterdir()):
        raise SystemExit(f"{RESULTS} already contains results; they are written once")
    status = amended_status()
    if status["status"] != "ready_under_amendment_A1":
        print(json.dumps(status, indent=2))
        raise SystemExit("amended provenance incomplete; no results written")
    out.mkdir(parents=True, exist_ok=True)
    pa.compute(out, "2026-09-28", label=LABEL, results=RESULTS,
               names=("primary_accepted", "sensitivity_first_valid"), summary_name="sensitivity_summary.json",
               role="primary analysis under post-judgment amendment A1 (2026-09-28); specified after outputs and "
                    "provisional results were inspected; not preregistered",
               extra_meta={"amendment": f"{AMEND}/AMENDMENT_A1.md", "amended_status": status})
    (out / "amended_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(status, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["evaluate-collisions", "status", "run"])
    args = parser.parse_args()
    if args.command == "evaluate-collisions":
        return evaluate_collisions()
    if args.command == "status":
        status = amended_status()
        print(json.dumps(status, indent=2))
        return 0 if status["status"] == "ready_under_amendment_A1" else 1
    return run()


if __name__ == "__main__":
    sys.exit(main())
