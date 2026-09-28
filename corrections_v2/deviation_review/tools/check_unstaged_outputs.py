"""Validate output files left in WSL workspaces by failed attempts (read-only). Requires the operator's WSL."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "corrections_v2"))
from rerun import validate_rows  # noqa: E402

TARGETS = [("p01_C_j1_b02", 1), ("p01_C_j4_b08", 1), ("p01_C_j5_b09", 1)]
manifest = json.loads((ROOT / "corrections_v2/generated/rerun_manifest.json").read_text(encoding="utf-8"))
jobs = {j["job_id"]: j for j in manifest["jobs"]}
results = []
for job_id, slot in TARGETS:
    job = jobs[job_id]
    path = f"/home/evidex/isolated/{job_id}/attempt-{slot:02d}/workspace/{job['output']}"
    data = subprocess.run(["wsl", "-u", "root", "-e", "cat", path], capture_output=True, check=True).stdout
    entry = {"job_id": job_id, "attempt": slot, "wsl_path": path, "size": len(data),
             "sha256": hashlib.sha256(data).hexdigest()}
    try:
        rows = json.loads(data.decode("utf-8"))
        entry["parse"] = "ok"
        entry["n_rows"] = len(rows) if isinstance(rows, list) else None
        try:
            entry["schema_valid"] = validate_rows(job, rows) == "valid"
        except (ValueError, TypeError, KeyError) as exc:
            entry["schema_valid"], entry["schema_error"] = False, str(exc)
    except (ValueError, UnicodeDecodeError) as exc:
        entry["parse"], entry["schema_valid"] = f"invalid JSON: {exc}", False
        entry["tail"] = data[-120:].decode("utf-8", errors="replace")
    results.append(entry)
out = ROOT / "corrections_v2/deviation_review/evidence/unstaged_failed_outputs.json"
out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
