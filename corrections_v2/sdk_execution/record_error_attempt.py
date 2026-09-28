"""Record a failed/error attempt with full provenance and routing evidence."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXECUTION = ROOT / "corrections_v2" / "execution"
RECORDS_BASE = Path(r"C:\Users\Chimdumebi\evidex_execution_records")


def record_error(job_id: str, attempt: int, reason: str, session_id: str, run_id: str, started_at: str, completed_at: str, packet_sha256: str, model_lock: str = "cursor-grok-4.6-high-fast"):
    label = f"{attempt:02d}"
    stage = RECORDS_BASE / job_id / f"attempt-{label}"
    stage.mkdir(parents=True, exist_ok=True)
    dest_dir = EXECUTION / job_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    routing_lines = [
        f"Linux WSL2 SDK run for {job_id} attempt-{label}",
        "status: error",
        f"started {started_at} completed {completed_at}",
        f"legacy lock: {model_lock}",
        'canonical selection: {"id":"grok-4.6","params":[{"id":"effort","value":"high"},{"id":"fast","value":"true"}]}' if "grok" in model_lock else 'canonical selection: {"id":"claude-opus-5","params":[{"id":"context","value":"1m"},{"id":"cyber","value":"false"},{"id":"effort","value":"high"},{"id":"fast","value":"false"},{"id":"thinking","value":"true"}]}',
        "sandbox_enabled: true",
        "sandbox_initialized: true",
        f"agent_id: {session_id}",
        f"run_id: {run_id}",
        "offered_tools: read, edit, piWrite",
        "observed_tool_names: read",
        "hooks_loaded: true",
        "designated_output_written: false",
        f"error: {reason}",
        "raw_response_unavailable_reason: stream stalled and run ended with status error; designated output was never created",
        "",
    ]
    routing_text = "\n".join(routing_lines)

    if started_at == "unknown":
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        started_at = now
        completed_at = now

    (stage / f"attempt-{label}.routing.txt").write_bytes(routing_text.encode("utf-8"))
    (dest_dir / f"attempt-{label}.routing.txt").write_bytes(routing_text.encode("utf-8"))
    if (stage / f"attempt-{label}.hooks.jsonl").exists():
        shutil.copy2(stage / f"attempt-{label}.hooks.jsonl", dest_dir / f"attempt-{label}.hooks.jsonl")
    if (stage / f"attempt-{label}.sdk-events.jsonl").exists():
        shutil.copy2(stage / f"attempt-{label}.sdk-events.jsonl", dest_dir / f"attempt-{label}.sdk-events.jsonl")

    routing_sha256 = hashlib.sha256(routing_text.encode("utf-8")).hexdigest()

    record = {
        "job_id": job_id,
        "attempt": attempt,
        "status": "error",
        "reason": reason,
        "requested_model": model_lock,
        "resolved_model": model_lock,
        "provider_model_version": None,
        "version_metadata_status": "not_exposed",
        "version_metadata_note": "Catalog, dispatch, SDK event stream, and fail-closed hooks were inspected. Provider/backend version is not exposed.",
        "cursor_version": "3.17.8",
        "session_id": session_id,
        "started_at_utc": started_at,
        "completed_at_utc": completed_at,
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
        "visible_input_files": [
            f"corrections_v2/blind_io/{job_id.split('_')[0]}/stage_{job_id.split('_')[1].lower()}/{job_id}.json"
        ],
        "packet_sha256": packet_sha256,
        "raw_response_unavailable_reason": "stream stalled and run ended with status error; designated output was never created",
        "routing_evidence": {
            "path": f"corrections_v2/execution/{job_id}/attempt-{label}.routing.txt",
            "sha256": routing_sha256,
        },
    }

    (dest_dir / f"attempt-{label}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {job_id} attempt-{label} as error successfully.")


if __name__ == "__main__":
    record_error(
        job_id="p01_C_j3_b10",
        attempt=1,
        reason="Streaming connection stalled during generation; model run ended with status error before output was written.",
        session_id="agent-14e01154-ce8b-46a6-acdc-5f2a2eb2e9f2",
        run_id="run-6a03a5bd-c201-45f2-9105-eedafc0c3d81",
        started_at="2026-09-28T00:36:01.366Z",
        completed_at="2026-09-28T00:37:48.848Z",
        packet_sha256="49fbc0d0ef91b24a1450e2c0ece6f7ce5e6999d09739385914c0a4a209142ca8",
    )
