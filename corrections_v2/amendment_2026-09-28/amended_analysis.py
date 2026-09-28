"""Post-judgment amendment A1 (2026-09-28) to the correction-v2 Stage C analysis.

Written after all 70 required Stage C outputs existed and after provisional results had been
inspected; see AMENDMENT_A1.md. It changes three execution rules and nothing else:

  1. up to 9 attempt records per job (frozen protocol: 3);
  2. a collision record -- a failed-attempt record with session `unknown` and exit code 2,
     written by a duplicate runner invocation that stopped before launching -- is not the record
     of the slot's launched attempt. The slot counts once, through the agent named by the SDK
     event log that survives in it, provided the shared runner log shows both the duplicate's
     exit-code-2 failure and a separate outcome for that slot consistent with the event log;
  3. the analysed output of every job is its checkpoint-accepted output (explicit selection);
     first-schema-valid alternatives are sensitivity analyses only.

Session uniqueness is checked on the agents of the launched slots (one per slot), not on record
fields. The provenance check is the frozen analysis_io.provenance_for_job with the single constant
3 -> 9 substituted in its source; all other frozen checks run unchanged. The analysis is the frozen
analysis code, called through deviation_review/provisional_analysis.compute.

  python corrections_v2/amendment_2026-09-28/amended_analysis.py evaluate-sessions   (needs WSL; one-time)
  python corrections_v2/amendment_2026-09-28/amended_analysis.py status
  python corrections_v2/amendment_2026-09-28/amended_analysis.py run
  python corrections_v2/amendment_2026-09-28/amended_analysis.py verify
"""
import argparse
import hashlib
import inspect as pyinspect
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "corrections_v2"))
sys.path.insert(0, str(ROOT / "corrections_v2/deviation_review"))

import analysis_io  # noqa: E402
from analysis_io import digest, load_manifest, panel_jobs, read_json, verify_spec  # noqa: E402
import provisional_analysis as pa  # noqa: E402

AMEND = "corrections_v2/amendment_2026-09-28"
RESULTS = f"{AMEND}/results"
SESSION_EVIDENCE = ROOT / AMEND / "session_evidence.json"
EVIDENCE = ROOT / "corrections_v2/deviation_review/evidence/attempt_evidence.json"
INVENTORY = ROOT / "corrections_v2/deviation_review/evidence/wsl_inventory.json"
RUNNER_LOG = ROOT / "corrections_v2/sdk_execution/wsl/remaining_jobs.log"
LABEL = "AMENDMENT_A1_2026-09-28__POST_JUDGMENT_NOT_PREREGISTERED"
MAX_ATTEMPTS = 9
FROZEN_CAP_LINE = "if len(paths) > 3:"
COLLISION_REASON = "Execution failed with returncode 2"
# Exit-code-2 runner events that left no unknown-session record, with the reason established from
# the runner code and the execution session transcript.
OTHER_EXIT_2 = {
    ("p02_C_j2_b02", 3): "collision record written, then deleted during execution so the running "
                         "attempt could checkpoint (DEVIATION_ASSESSMENT_2026-09-28.md, item 4)",
    ("p01_C_j3_b10", 2): "not a collision: the first runner's wrapper script had CRLF line endings and bash "
                         "exited 2 before creating a workspace; its error logger then failed, so no record "
                         "was written; a restarted runner launched attempt 2 (accepted)",
}


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


def slot_key(path):
    return path.parent.name, int(re.fullmatch(r"attempt-(\d+)\.json", path.name).group(1))


def runner_events():
    """(job, attempt) -> START/ATTEMPT_FAILED/CHECKPOINT_FAILED line numbers from the shared runner log."""
    events = defaultdict(lambda: defaultdict(list))
    for number, line in enumerate(RUNNER_LOG.read_text("utf-8").splitlines(), 1):
        if m := re.match(r"START (\S+) panel=\S+ attempt=(\d+)", line):
            events[(m[1], int(m[2]))]["start"].append(number)
        elif m := re.match(r"ATTEMPT_FAILED (\S+) attempt=(\d+) code=(\d+)", line):
            events[(m[1], int(m[2]))][f"exit_{m[3]}"].append(number)
        elif m := re.match(r"CHECKPOINT_FAILED (\S+) attempt=(\d+)", line):
            events[(m[1], int(m[2]))]["checkpoint_failed"].append(number)
    return events


def evaluate_sessions():
    """Re-read every slot's SDK event log from WSL and classify every attempt record against it."""
    if SESSION_EVIDENCE.exists():
        raise SystemExit(f"{SESSION_EVIDENCE.relative_to(ROOT)} exists; it is written once")
    inventory = {}
    for item in json.loads(INVENTORY.read_text("utf-8")):
        if m := re.fullmatch(r"/home/evidex/records/([^/]+)/attempt-(\d+)/attempt-\d+\.sdk-events\.jsonl", item["path"]):
            inventory[(m[1], int(m[2]))] = item
    parsed_before = {(j["job_id"], a["attempt"]): a.get("agent_ids") or []
                     for j in json.loads(EVIDENCE.read_text("utf-8")) for a in j["attempts"]}
    runner = runner_events()
    rows = []
    for path, record in execution_records():
        key = slot_key(path)
        session = record.get("session_id", "")
        log_item = inventory.get(key)
        agents, runs, statuses = [], [], []
        if log_item:
            data = subprocess.run(["wsl", "-u", "root", "-e", "cat", log_item["path"]],
                                  capture_output=True, check=True).stdout
            if hashlib.sha256(data).hexdigest() != log_item["sha256"] or len(data) != log_item["size"]:
                raise SystemExit(f"event log differs from the recorded inventory: {log_item['path']}")
            events = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
            agents = sorted({e["agent_id"] for e in events if e.get("agent_id")})
            runs = sorted({e["run_id"] for e in events if e.get("run_id")})
            statuses = [e["status"] for e in events if e.get("type") == "status"]
        if session.startswith("not_launched:"):
            kind = "not_launched"
        elif session == "unknown" and record.get("status") == "error" and record.get("reason") == COLLISION_REASON:
            kind = "collision_record"
        else:
            kind = "own_record"
        log = {k: v for k, v in runner.get(key, {}).items()}
        final = statuses[-1] if statuses else None
        checks = {}
        if kind == "not_launched":
            checks["no_event_log_or_empty"] = not agents
        else:
            checks["event_log_names_exactly_one_agent"] = len(agents) == 1
        if kind == "own_record":
            checks["record_session_equals_event_log_agent"] = agents == [session]
        if kind == "collision_record":
            outcome = "checkpoint_failed" if log.get("checkpoint_failed") else "exit_1" if log.get("exit_1") else None
            checks["duplicate_exit_2_logged"] = bool(log.get("exit_2"))
            checks["two_invocations_started_for_slot"] = len(log.get("start", [])) >= 2
            checks["launched_run_outcome_logged"] = outcome is not None
            checks["outcome_consistent_with_event_log"] = (outcome, final) in {("checkpoint_failed", "FINISHED"),
                                                                               ("exit_1", "ERROR")}
        rows.append({
            "job_id": key[0], "attempt": key[1], "record": path.relative_to(ROOT).as_posix(),
            "record_sha256": digest(path), "record_status": record.get("status"), "record_session": session,
            "record_reason": record.get("reason"), "classification": kind,
            "slot_event_log": log_item["path"] if log_item else None,
            "slot_event_log_sha256": log_item["sha256"] if log_item else None,
            "slot_agent": agents[0] if len(agents) == 1 else None, "slot_runs": runs, "slot_final_status": final,
            "agent_parsed_in_attempt_evidence": parsed_before.get(key) == agents and bool(agents),
            "runner_log_lines": log, "checks": checks,
        })
    launched = [r["slot_agent"] for r in rows if r["classification"] != "not_launched"]
    for r in rows:
        if r["classification"] != "not_launched":
            r["checks"]["slot_agent_unique"] = r["slot_agent"] is not None and launched.count(r["slot_agent"]) == 1
        r["established"] = all(r["checks"].values())
    unexplained, other_exit_2 = [], {}
    for key, log in sorted(runner.items()):
        if not log.get("exit_2"):
            continue
        row = next((r for r in rows if (r["job_id"], r["attempt"]) == key), None)
        if row and row["classification"] == "collision_record":
            continue
        if row and row["classification"] == "own_record" and log.get("exit_1") and min(log["exit_1"]) < min(log["exit_2"]):
            other_exit_2[f"{key[0]}/attempt-{key[1]:02}"] = ("duplicate invocation exited 2 after the launched run had "
                                                            "already written its own record; no second record")
        elif key in OTHER_EXIT_2:
            other_exit_2[f"{key[0]}/attempt-{key[1]:02}"] = OTHER_EXIT_2[key]
        else:
            unexplained.append(f"{key[0]}/attempt-{key[1]:02}")
    summary = {
        "attempt_records": len(rows),
        "by_classification": {k: sum(r["classification"] == k for r in rows)
                              for k in ("own_record", "collision_record", "not_launched")},
        "launched_attempt_slots": len(launched),
        "distinct_slot_agents": len(set(launched)),
        "slot_agents_parsed_in_attempt_evidence": sum(r["agent_parsed_in_attempt_evidence"] for r in rows),
        "slot_agents_missing_from_attempt_evidence": [
            {"slot": f"{r['job_id']}/attempt-{r['attempt']:02}", "agent": r["slot_agent"],
             "reason": "slot had no local staging copy; build_attempt_evidence.py parsed staging copies only"}
            for r in rows if r["classification"] != "not_launched" and not r["agent_parsed_in_attempt_evidence"]],
        "runner_exit_2_events": sum(len(v.get("exit_2", [])) for v in runner.values()),
        "exit_2_events_without_collision_record": other_exit_2,
        "unexplained_exit_2_events": unexplained,
        "all_records_established": all(r["established"] for r in rows),
    }
    payload = {
        "amendment": "A1 (2026-09-28), rule 2",
        "method": "every attempt record is compared with the SDK event log that survives in its slot (read from WSL "
                  "on the evaluation date and checked against the recorded inventory hash) and with the shared "
                  "runner log; records are unchanged. An exit-2 invocation stops in run_required_job.sh before a "
                  "workspace or agent exists, so it never launched a model.",
        "summary": summary, "records": rows,
    }
    SESSION_EVIDENCE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["all_records_established"] and not unexplained else 1


def amended_status():
    spec = verify_spec(ROOT)
    manifest = load_manifest(ROOT)
    frozen, _, _ = analysis_io.inspect(manifest, "primary", ROOT, spec)
    provenance = amended_provenance_for_job()
    evidence = json.loads(SESSION_EVIDENCE.read_text("utf-8"))
    slots = {(r["job_id"], r["attempt"]): r for r in evidence["records"]}
    errors, agents, jobs = {}, [], panel_jobs(manifest, "primary")
    counts = defaultdict(int)
    for job in jobs:
        try:
            provenance(job, ROOT, spec)
        except (ValueError, OSError, TypeError, KeyError) as exc:
            errors[job["job_id"]] = str(exc)
            continue
        for path in sorted((ROOT / "corrections_v2/execution" / job["job_id"]).glob("attempt-*.json")):
            key, name = slot_key(path), f"{job['job_id']}/{path.stem}"
            row = slots.get(key)
            if row is None or row["record_sha256"] != digest(path):
                errors[name] = "record missing from, or changed since, the session evaluation"
                continue
            if not row["established"]:
                errors[name] = f"{row['classification']} not established: {row['checks']}"
                continue
            counts[row["classification"]] += 1
            if row["classification"] != "not_launched":
                agents.append(row["slot_agent"])
    if len(agents) != len(set(agents)):
        errors["reused_session"] = "an agent appears in more than one launched attempt slot"
    selected = {j["job_id"] for j in jobs}
    for path, record in execution_records():
        if path.parent.name not in selected and record.get("session_id") in agents:
            errors["reused_session"] = "selected session reused by another panel/job"
    ready = not (errors or frozen["missing_jobs"] or frozen["invalid_outputs_or_packets"])
    return {
        "label": LABEL, "panel": "primary",
        "status": "ready_under_amendment_A1" if ready else "incomplete_under_amendment_A1",
        "max_attempts": MAX_ATTEMPTS,
        "attempt_records": sum(counts.values()),
        "records_by_classification": dict(sorted(counts.items())),
        "launched_attempt_slots": len(agents), "distinct_slot_agents": len(set(agents)),
        "amended_provenance_errors": errors,
        "frozen_protocol_status": frozen["status"],
        "frozen_protocol_provenance_errors": frozen["execution_provenance_errors"],
        "valid_schema_judgments": frozen["valid_schema_judgments"],
        "output_selection": "checkpoint-accepted output of every job (amendment rule 3)",
        "inference_launched": False,
    }


def compute(base, status):
    pa.compute(base, "2026-09-28", label=LABEL, results=RESULTS,
               names=("primary_accepted", "sensitivity_first_valid"), summary_name="sensitivity_summary.json",
               role="primary analysis under post-judgment amendment A1 (2026-09-28); specified after outputs and "
                    "provisional results were inspected; not preregistered",
               extra_meta={"amendment": f"{AMEND}/AMENDMENT_A1.md", "amended_status": status})
    (base / "amended_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8", newline="\n")


def ready_status():
    status = amended_status()
    if status["status"] != "ready_under_amendment_A1":
        print(json.dumps(status, indent=2))
        raise SystemExit("amended provenance incomplete; no results written")
    return status


def run():
    out = ROOT / RESULTS
    if out.exists() and any(p.name != ".gitattributes" for p in out.iterdir()):
        raise SystemExit(f"{RESULTS} already contains results; they are written once")
    status = ready_status()
    out.mkdir(parents=True, exist_ok=True)
    compute(out, status)
    print(json.dumps(status, indent=2))
    return 0


def verify():
    """Recompute into a temporary directory; compare with the committed results, ignoring only timestamps."""
    committed = ROOT / RESULTS
    status = ready_status()
    problems = []
    with tempfile.TemporaryDirectory(prefix="evidex_amended_verify_") as tmp:
        new = Path(tmp)
        compute(new, status)
        new_files = {p.relative_to(new).as_posix() for p in new.rglob("*") if p.is_file()}
        old_files = {p.relative_to(committed).as_posix() for p in committed.rglob("*")
                     if p.is_file() and p.name != ".gitattributes"}
        if new_files != old_files:
            problems.append(f"file sets differ: +{sorted(new_files - old_files)} -{sorted(old_files - new_files)}")
        for rel in sorted(new_files & old_files):
            a, b = (new / rel).read_bytes(), (committed / rel).read_bytes()
            if rel.endswith("/status.json"):
                a, b = json.loads(a), json.loads(b)
                a.pop("created_at_utc"), b.pop("created_at_utc")
            elif rel.endswith("provisional_file_hashes.json"):
                a, b = json.loads(a), json.loads(b)
                for j in (a, b):
                    j["files"] = {k: v for k, v in j["files"].items() if not k.endswith("/status.json")}
            if a != b:
                problems.append(f"{rel} differs")
    report = {"label": LABEL, "status": status["status"], "compared_files": len(new_files),
              "differences": problems, "result": "PASS" if not problems else "FAIL"}
    print(json.dumps(report, indent=2))
    return 0 if not problems else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["evaluate-sessions", "status", "run", "verify"])
    args = parser.parse_args()
    if args.command == "evaluate-sessions":
        return evaluate_sessions()
    if args.command == "status":
        status = amended_status()
        print(json.dumps(status, indent=2))
        return 0 if status["status"] == "ready_under_amendment_A1" else 1
    return verify() if args.command == "verify" else run()


if __name__ == "__main__":
    sys.exit(main())
