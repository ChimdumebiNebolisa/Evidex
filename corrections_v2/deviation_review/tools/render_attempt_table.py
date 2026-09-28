"""Render the chronological attempt table for flagged jobs from attempt_evidence.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "corrections_v2/deviation_review/evidence"
JOBS = ["p01_C_j4_b08", "p01_C_j4_b09", "p02_C_j2_b03", "p02_C_j3_b01", "p02_C_j3_b02", "p02_C_j3_b03",
        "p02_C_j2_b02", "p01_C_j5_b09"]

SELECTION = {
    "p01_C_j4_b08": "Slots 1-5 each ended with a provider `[resource_exhausted]` ERROR status. Slot 1 streamed for a "
                    "while and left a truncated, invalid output file in its WSL workspace (never archived; its error "
                    "record wrongly says the output was never created); slots 2-5 produced nothing. Slot 6 is the "
                    "first run that finished with an output; checkpoint accepted it as the first schema-valid response. "
                    "Slots 4-6 exceed the frozen three-attempt cap (operator-authorized quota redo).",
    "p01_C_j4_b09": "Slots 1-3 ended `[resource_exhausted]`, slots 4-6 ended with the account out-of-usage error; none "
                    "produced output. Slot 7 is the first run that finished with an output and was accepted. Slots 4-7 "
                    "exceed the frozen three-attempt cap (operator-authorized quota redo).",
    "p02_C_j2_b03": "Slots 1, 2 and 3 each contain a finished run with a schema-valid output, but those runs were never "
                    "checkpointed: a duplicate runner had already written an exit-code-2 collision record into each slot, "
                    "so checkpointing refused (`archive already contains attempt-NN.routing.txt`, logged for slot 2). "
                    "Slot 4 was the first run whose checkpoint succeeded. The accepted output is therefore NOT the first "
                    "schema-valid response, and slot 4 exceeds the three-attempt cap.",
    "p02_C_j3_b01": "Slots 1-3 all launched agents that ended with the account out-of-usage ERROR without output. Slot 4 is the first run with an output and was accepted, consistent with "
                    "first-valid acceptance, but it exceeds the three-attempt cap and records 1 and 3 do not describe the "
                    "launched run in their slot.",
    "p02_C_j3_b02": "Slots 1-3 each launched an agent that immediately ended with the account out-of-usage error; no output. "
                    "Slot 4 is the first run with an output and was accepted, consistent with first-valid acceptance, but "
                    "it exceeds the three-attempt cap and records 1-3 do not describe the launched run in their slot.",
    "p02_C_j3_b03": "Same pattern as p02_C_j3_b02: slots 1-3 out-of-usage with no output; slot 4 first output, accepted; "
                    "exceeds the three-attempt cap; records 1-3 do not describe the launched run in their slot.",
    "p02_C_j2_b02": "Not flagged by the retry cap (three records). Slots 1 and 2 each contain a finished run with a "
                    "schema-valid output; slot 1's checkpoint was refused because a collision record already occupied the "
                    "slot (logged). Slot 3 was accepted. The accepted output is NOT the first schema-valid response. "
                    "While slot 3 was still running, the coordinating agent deleted a collision record already written "
                    "for slot 3 (`attempt-03.json` and `attempt-03.routing.txt`) so the run could checkpoint; the "
                    "deletion is recorded in the session transcript and the deleted files do not survive.",
    "p01_C_j5_b09": "Not flagged by the retry cap (two records). Slot 1 wrote a complete schema-valid 100-row output "
                    "file, then the SDK run ended with `[resource_exhausted]`; the runner treated the non-finished run "
                    "status as failure, never archived the file (it remains only in the WSL workspace), and its error "
                    "record wrongly says the output was never created. Slot 2 was accepted. Whether slot 1 counts as a "
                    "'response' under the first-valid rule is a judgment call, because the run did not finish.",
}


def short(value, n=12):
    return value[:n] if isinstance(value, str) else value


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def when(row):
    if row["routing"] and row["routing"].get("started_at_utc"):
        return row["routing"]["started_at_utc"]
    events = row["wsl_record_files"].get(f"attempt-{row['attempt']:02d}.sdk-events.jsonl")
    if events:
        return events["mtime_utc"]
    return (row["execution_record"] or {}).get("started_at_utc") or ""


def main():
    data = {j["job_id"]: j for j in json.loads((EVIDENCE / "attempt_evidence.json").read_text(encoding="utf-8"))}
    unstaged = {(u["job_id"], u["attempt"]): u for u in
                json.loads((EVIDENCE / "unstaged_failed_outputs.json").read_text(encoding="utf-8"))}
    out = ["# Attempt evidence for flagged jobs", "",
           "Generated by `render_attempt_table.py` from `evidence/attempt_evidence.json`. Rows are ordered by the "
           "best available time: run start from `routing.json` for finished runs, otherwise the last write of the "
           "slot's SDK event log in WSL. \"Slot evidence\" columns come from the WSL record directory and its staging "
           "copy (hash-identical for every slot); \"Execution record\" is the archived `attempt-NN.json`, unchanged. "
           "`unknown` means no surviving artifact establishes the fact.", ""]
    for job_id in JOBS:
        job = data[job_id]
        out += [f"## {job_id} ({job['panel']}, {job['n_judgments']} judgments)", "",
                "| Slot | Time (UTC) | Execution record | Agent created | send() | Stream events | Model output | "
                "Failure reason (evidence) | Runner log |",
                "|---|---|---|---|---|---|---|---|---|"]
        for row in sorted(job["attempts"], key=when):
            rec = row["execution_record"] or {}
            record = f"{rec.get('status')}; session `{short(rec.get('session_id'), 20)}`; {rec.get('reason') or ''}"
            agent = row["agent_created"] + (f" (`{short(row['agent_ids'][0], 20)}`)" if row["agent_ids"] else "")
            ev = row["events"]
            if ev and ev["n_events"]:
                types = ", ".join(f"{k} {v}" for k, v in sorted(ev["types"].items()))
                stream = f"{ev['n_events']} events ({types}); final status {ev['statuses'][-1] if ev['statuses'] else 'none'}"
            elif ev is not None:
                stream = "event log exists but is empty"
            else:
                stream = "unknown (no event log)"
            mo = row["model_output"]
            if mo:
                output = (f"{'schema-valid' if mo['schema_valid'] else 'not schema-valid'} {mo.get('n_rows')} rows, "
                          f"sha `{short(mo['sha256'])}`" + ("; = accepted output" if row["output_is_accepted_output"] else ""))
            elif (job_id, row["attempt"]) in unstaged:
                u = unstaged[(job_id, row["attempt"])]
                output = (f"unarchived file left in WSL workspace: "
                          f"{'schema-valid ' + str(u.get('n_rows')) + ' rows' if u['schema_valid'] else u['parse']}, "
                          f"{u['size']} bytes, sha `{short(u['sha256'])}`")
            else:
                output = "none found"
            if ev and ev.get("error_message"):
                reason = ev["error_message"]
            elif row["dispatch_error"]:
                reason = f"{row['dispatch_error']['stage']}: {row['dispatch_error']['message']}"
            elif mo and mo["schema_valid"] and (rec.get("status") != "accepted"):
                reason = "run finished; output never checkpointed (slot already held a collision record)"
            elif rec.get("status") == "accepted":
                reason = "none (accepted)"
            else:
                reason = "unknown"
            log = "; ".join(
                f"{e['log'].removesuffix('.txt')}:{e['line']} {e['event']}"
                + (f" code={e['code']}" if "code" in e else "")
                + (f" \"{e['text']}\"" if e.get("text") else "")
                for e in row["runner_log"]) or "no surviving log line"
            out.append("| " + " | ".join(cell(x) for x in (
                row["attempt"], when(row)[:19], record, agent, row["send_occurred"], stream, output, reason, log)) + " |")
        out += ["", f"**Why the accepted attempt was selected:** {SELECTION[job_id]}", ""]
    (ROOT / "corrections_v2/deviation_review/attempt_table.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
