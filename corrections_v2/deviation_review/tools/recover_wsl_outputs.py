"""One-time recovery of output files that failed attempts left in the operator's WSL workspaces.

Requires the original WSL distribution. Copies exact bytes into
evidence/recovered_wsl_outputs/ and writes a manifest only after each copy matches the size and
SHA-256 recorded in evidence/unstaged_failed_outputs.json and evidence/wsl_inventory.json.
Contents are never repaired. Refuses to overwrite an existing copy.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = REVIEW.parents[1]
sys.path.insert(0, str(ROOT / "corrections_v2"))
from rerun import validate_rows  # noqa: E402

EVIDENCE = REVIEW / "evidence"
TARGET = EVIDENCE / "recovered_wsl_outputs"


def parse_status(job, data):
    try:
        rows = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        return {"parse": f"invalid JSON: {exc}", "schema_valid": False, "n_rows": None}
    try:
        valid = validate_rows(job, rows) == "valid"
        error = None
    except (ValueError, TypeError, KeyError) as exc:
        valid, error = False, str(exc)
    return {"parse": "ok", "schema_valid": valid, "schema_error": error,
            "n_rows": len(rows) if isinstance(rows, list) else None}


def main():
    recorded = json.loads((EVIDENCE / "unstaged_failed_outputs.json").read_text(encoding="utf-8"))
    inventory = {i["path"]: i for i in json.loads((EVIDENCE / "wsl_inventory.json").read_text(encoding="utf-8"))}
    manifest = json.loads((ROOT / "corrections_v2/generated/rerun_manifest.json").read_text(encoding="utf-8"))
    jobs = {j["job_id"]: j for j in manifest["jobs"]}
    entries = []
    for item in recorded:
        job = jobs[item["job_id"]]
        source = item["wsl_path"]
        if source != f"/home/evidex/isolated/{job['job_id']}/attempt-{item['attempt']:02d}/workspace/{job['output']}":
            raise SystemExit(f"unexpected source path: {source}")
        inv = inventory.get(source)
        if not inv or inv["sha256"] != item["sha256"] or inv["size"] != item["size"]:
            raise SystemExit(f"recorded hash/size disagree with WSL inventory: {source}")
        result = subprocess.run(["wsl", "-u", "root", "-e", "cat", source], capture_output=True)
        if result.returncode != 0:
            print(f"MISSING {source}: {result.stderr.decode(errors='replace').strip()}")
            entries.append({"job_id": item["job_id"], "attempt": item["attempt"], "source_wsl_path": source,
                            "status": "missing_at_recovery"})
            continue
        data = result.stdout
        digest = hashlib.sha256(data).hexdigest()
        status = parse_status(job, data)
        if len(data) != item["size"] or digest != item["sha256"] or status["schema_valid"] != item["schema_valid"]:
            raise SystemExit(f"bytes differ from the recorded file; not accepted: {source}")
        dest = TARGET / item["job_id"] / f"attempt-{item['attempt']:02d}.workspace.output.json"
        if dest.exists():
            if dest.read_bytes() != data:
                raise SystemExit(f"existing recovered copy differs; not overwritten: {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        entries.append({"job_id": item["job_id"], "attempt": item["attempt"], "source_wsl_path": source,
                        "source_mtime_utc": inv["mtime_utc"],
                        "path": dest.relative_to(ROOT).as_posix(), "size": len(data), "sha256": digest,
                        **status, "status": "recovered_exact_bytes", "contents_repaired": False})
    out = EVIDENCE / "recovered_wsl_outputs" / "manifest.json"
    out.write_text(json.dumps({"policy": "exact bytes copied from WSL; never repaired", "files": entries},
                              indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(entries, indent=2))


if __name__ == "__main__":
    main()
