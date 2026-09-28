"""Verify the organized tree against the preserved 2026-09-28 scientific record.

The original correction verifier remains executable at SOURCE_COMMIT through
run_frozen.py. This verifier checks the relocated files without rewriting that
verifier, its historical inventory, or the frozen protocol.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "33121b773ecbd438fc4c473d5b3cd3a06f8961fd"
MIGRATION = ROOT / "docs/post_judgment/ROOT_LAYOUT_MIGRATION_2026-09-28.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    migration = json.loads(MIGRATION.read_text(encoding="utf-8"))
    if migration["source_commit"] != SOURCE_COMMIT:
        fail("source commit changed")
    entries = migration["entries"]
    mapping = {e["old_path"]: e["new_path"] for e in entries}
    if len(mapping) != len(entries) or len(set(mapping.values())) != len(entries):
        fail("duplicate migration path")
    for entry in entries:
        old, new = entry["old_path"], entry["new_path"]
        if not new.startswith(("historical/", "docs/")) or (
            (ROOT / old).exists() and old not in {"README.md", "REPRODUCING.md"}
        ):
            fail(f"invalid or unmoved path: {old}")
        target = ROOT / new
        if not target.is_file():
            fail(f"missing moved file: {new}")
        current = target.read_bytes()
        if entry["kind"] == "text":
            current = lf(current)
        elif entry["kind"] != "binary":
            fail(f"unknown file kind: {new}")
        if digest(current) != entry["sha256"]:
            fail(f"moved file changed: {new}")
        original = subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:{old}"], cwd=ROOT
        )
        if entry["kind"] == "text":
            original = lf(original)
        if digest(original) != digest(current):
            fail(f"source commit differs from moved file: {old}")

    baseline = json.loads((ROOT / "corrections_v2/baseline/historical_inputs.json").read_text())
    for old, entry in baseline["files"].items():
        path = ROOT / mapping.get(old, old)
        if not path.is_file():
            fail(f"missing historical file: {old}")
        data = path.read_bytes()
        observed = digest(lf(data)) if entry["kind"] == "text" else digest(data)
        expected = entry["lf_sha256"] if entry["kind"] == "text" else entry["recorded_raw_sha256"]
        if observed != expected:
            fail(f"historical input changed: {old}")

    code = json.loads((ROOT / "corrections_v2/generated/code_hashes.json").read_text())
    for old, expected in code.items():
        path = ROOT / mapping.get(old, old)
        if not path.is_file() or digest(lf(path.read_bytes())) != expected:
            fail(f"correction implementation changed: {old}")

    sys.path.insert(0, str(ROOT / "corrections_v2"))
    from provenance import verify_output_inventory, verify_snapshot
    from analysis_io import verify_spec

    verify_snapshot(ROOT / "corrections_v2/inputs/historical_pages.json", ROOT)
    verify_output_inventory(ROOT)
    verify_spec(ROOT)
    tag = subprocess.check_output(
        ["git", "rev-parse", "evidex-artifact-v1^{}"], cwd=ROOT, text=True
    ).strip()
    if tag != baseline["scientific_artifact_commit"]:
        fail("original scientific artifact tag changed")
    print(
        f"PASS: {len(entries)} content-preserved moves; {len(baseline['files'])} historical "
        f"inputs; {len(code)} implementation files; output inventory, spec, and tag",
        flush=True,
    )


if __name__ == "__main__":
    main()
