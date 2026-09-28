"""Run remaining required correction-v2 jobs on Linux WSL2. No optional jobs."""
from __future__ import annotations

import atexit
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "corrections_v2" / "generated" / "rerun_manifest.json"
EXECUTION = ROOT / "corrections_v2" / "execution"
LOG = ROOT / "corrections_v2" / "sdk_execution" / "wsl" / "remaining_jobs.log"
CURSOR_VERSION = "3.17.8"
WSL_SCRIPT = "/home/evidex/sdk_execution/run_required_job.sh"
MAX_ATTEMPT = 9
LOCK = ROOT / "corrections_v2" / "sdk_execution" / "wsl" / "runner.lock"
USAGE_LIMIT_MARKERS = ("out of usage", "increase your limit")


def pid_alive(pid: int) -> bool:
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
    return str(pid) in out


def acquire_lock() -> None:
    for _ in range(2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                holder = int(LOCK.read_text(encoding="utf-8").strip() or 0)
            except (OSError, ValueError):
                holder = 0
            if holder and pid_alive(holder):
                raise SystemExit(f"another runner holds {LOCK} (pid {holder})")
            LOCK.unlink(missing_ok=True)
            continue
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        atexit.register(lambda: LOCK.unlink(missing_ok=True))
        return
    raise SystemExit(f"could not acquire {LOCK}")


def load_required_jobs():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    optional = {panel["panel"] for panel in manifest["panels"] if panel.get("optional")}
    return [job for job in manifest["jobs"] if job["panel"] not in optional]


def next_attempt(job_id: str) -> int:
    directory = EXECUTION / job_id
    if not directory.exists():
        return 1
    n = 0
    for path in directory.glob("attempt-*.json"):
        if path.name.count(".") != 1:
            continue
        n += 1
    return n + 1


def accepted(job_id: str) -> bool:
    directory = EXECUTION / job_id
    if not directory.exists():
        return False
    for path in directory.glob("attempt-*.json"):
        if path.name.count(".") != 1:
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("job_id") == job_id and record.get("status") == "accepted":
            return True
    return False


def retry_exhausted(job_id: str) -> bool:
    return next_attempt(job_id) > MAX_ATTEMPT


def last_error_reason(job_id: str) -> str:
    directory = EXECUTION / job_id
    if not directory.exists():
        return ""
    records = []
    for path in directory.glob("attempt-*.json"):
        if path.name.count(".") != 1:
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        records.append((record.get("attempt", 0), str(record.get("reason") or "")))
    if not records:
        return ""
    records.sort()
    return records[-1][1]


def run(command, cwd=ROOT) -> None:
    completed = subprocess.run(command, cwd=cwd)
    if completed.returncode != 0:
        raise SystemExit(f"command failed ({completed.returncode}): {command}")


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")
    print(message, flush=True)


def main() -> None:
    acquire_lock()
    only = set()
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        only = {item.strip() for item in sys.argv[idx + 1].split(",") if item.strip()}
    jobs = load_required_jobs()
    if only:
        jobs = [job for job in jobs if job["job_id"] in only]
        log(f"required={len(jobs)} only={','.join(sorted(only))}")
        if any("resource_exhausted" in last_error_reason(job["job_id"]).lower() for job in jobs if not accepted(job["job_id"])):
            log("QUOTA_COOLDOWN 600s before grok redo")
            subprocess.run(["powershell", "-Command", "Start-Sleep -Seconds 600"], cwd=ROOT)
    else:
        log(f"required={len(jobs)}")
    last_panel_failure = None
    if not only:
        for job in jobs:
            if retry_exhausted(job["job_id"]) and "resource_exhausted" in last_error_reason(job["job_id"]).lower():
                last_panel_failure = job["panel"]
                break
    while True:
        pending = [job for job in jobs if not accepted(job["job_id"]) and not retry_exhausted(job["job_id"])]
        exhausted = [job["job_id"] for job in jobs if not accepted(job["job_id"]) and retry_exhausted(job["job_id"])]
        if not pending:
            if exhausted:
                raise SystemExit(f"retry budget exhausted for {', '.join(exhausted)}")
            break
        if last_panel_failure:
            other = [job for job in pending if job["panel"] != last_panel_failure]
            job = other[0] if other else pending[0]
        else:
            job = pending[0]
        job_id = job["job_id"]
        panel = job["panel"]
        attempt = next_attempt(job_id)
        if attempt > MAX_ATTEMPT:
            log(f"SKIPPED_RETRY_BUDGET {job_id}")
            continue
        label = f"{attempt:02d}"
        log(f"START {job_id} panel={panel} attempt={attempt} (remaining pending={len(pending)})")
        run([
            sys.executable,
            str(ROOT / "corrections_v2" / "analysis_pipeline.py"),
            "export-job",
            "--panel",
            panel,
            "--job",
            job_id,
        ])

        proc = subprocess.run([
            "wsl",
            "-e",
            "env",
            "HOME=/root",
            "PATH=/usr/bin:/bin:/usr/sbin",
            "bash",
            WSL_SCRIPT,
            job_id,
            str(attempt),
        ], cwd=ROOT)

        staging = Path(rf"C:\Users\Chimdumebi\evidex_execution_records\{job_id}\attempt-{label}")
        routing_json = staging / f"attempt-{label}.routing.json"

        if proc.returncode != 0 or not routing_json.exists():
            log(f"ATTEMPT_FAILED {job_id} attempt={attempt} code={proc.returncode}")
            dest_dir = EXECUTION / job_id
            attempt_json = dest_dir / f"attempt-{label}.json"
            if not attempt_json.exists():
                sys.path.insert(0, str(ROOT / "corrections_v2" / "sdk_execution"))
                from record_error_attempt import record_error
                session_id = "unknown"
                run_id = "unknown"
                reason = f"Execution failed with returncode {proc.returncode}"
                events_file = staging / f"attempt-{label}.sdk-events.jsonl"
                if events_file.exists():
                    lines = events_file.read_text(encoding="utf-8", errors="replace").strip().splitlines()
                    for line in reversed(lines[-25:]):
                        try:
                            ev = json.loads(line)
                            if "agent_id" in ev and session_id == "unknown":
                                session_id = ev["agent_id"]
                            if "run_id" in ev and run_id == "unknown":
                                run_id = ev["run_id"]
                            if ev.get("status") == "ERROR":
                                reason = ev.get("message", reason)
                        except Exception:
                            pass
                record_error(
                    job_id=job_id,
                    attempt=attempt,
                    reason=reason,
                    session_id=session_id,
                    run_id=run_id,
                    started_at="unknown",
                    completed_at="unknown",
                    packet_sha256=job["packet_sha256"],
                    model_lock=job["model"],
                )
            latest = last_error_reason(job_id).lower()
            if any(marker in latest for marker in USAGE_LIMIT_MARKERS):
                raise SystemExit(f"USAGE_LIMIT_REACHED at {job_id} attempt {attempt}; stopping to preserve retries")
            if "resource_exhausted" in latest:
                last_panel_failure = panel
                log(f"RESOURCE_EXHAUSTED {job_id} panel={panel}; backing off 600s")
                subprocess.run(["powershell", "-Command", "Start-Sleep -Seconds 600"], cwd=ROOT)
            continue

        chk = subprocess.run([
            sys.executable,
            str(ROOT / "corrections_v2" / "sdk_execution" / "checkpoint_job.py"),
            "--job",
            job_id,
            "--attempt",
            str(attempt),
            "--staging",
            str(staging),
            "--cursor-version",
            CURSOR_VERSION,
        ], cwd=ROOT)

        if chk.returncode != 0:
            log(f"CHECKPOINT_FAILED {job_id} attempt={attempt} code={chk.returncode}")
            continue

        if panel == last_panel_failure:
            last_panel_failure = None
        log(f"ACCEPTED {job_id}")
    log("ALL_REQUIRED_COMPLETE")


if __name__ == "__main__":
    main()
