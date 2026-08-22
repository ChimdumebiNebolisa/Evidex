"""Prepare, validate, and freeze GLM judge batches.

Batch files live in data/blinded/batches/ (identical across judges). Each
judge subagent (isolated GLM-5.3 context, driven by the orchestrator) reads
the rubric + its batch and writes judgments/stage_X/judge_N_batch_K.jsonl.

This module handles: batch preparation, completeness/schema validation of
written outputs, retry accounting, and per-stage freezing (append-only with
sha256 manifest). The actual subagent invocation is performed by the
orchestrating agent (see ADJUDICATION_LOG).
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

BATCH_DIR = config.BLINDED_DIR / "batches"
# Constant per-stage file locations (no caller-controlled path components).
# Judge subagents read item RANGES directly from the constant-named blinded
# file (batching is by line range, not by derived files).
STAGE_FILE = {"A": "stage_a.jsonl", "B": "stage_b.jsonl", "C": "stage_c.jsonl"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_items(stage: str):
    src = config.BLINDED_DIR / STAGE_FILE[stage]
    items = [json.loads(l)["item_id"]
             for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    pf = config.DERIVED_DIR / "provider_filtered.json"
    if pf.exists():
        excluded = set(json.loads(pf.read_text(encoding="utf-8"))["items"])
        items = [i for i in items if i not in excluded]
    return items


def valid_record(r, stage: str, judge: str) -> bool:
    if not isinstance(r, dict):
        return False
    if r.get("judge_id") != judge or r.get("stage") != stage:
        return False
    if r.get("verdict") not in config.VERDICTS:
        return False
    if r.get("evidence_sufficiency") not in config.SUFFICIENCY:
        return False
    c = r.get("confidence")
    if not isinstance(c, int) or not (0 <= c <= 100):
        return False
    flags = r.get("issue_flags")
    if not isinstance(flags, list) or not flags or \
            any(f not in config.ISSUE_FLAGS for f in flags):
        return False
    if not isinstance(r.get("brief_reason"), str) or not r["brief_reason"].strip():
        return False
    return True


def judge_status(stage: str, judge: str):
    """Return (done_item_ids, malformed_files) for a judge/stage."""
    expected = set(expected_items(stage))
    done = set()
    malformed = []
    outdir = config.JUDGMENTS_DIR / f"stage_{stage.lower()}"
    for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
        try:
            content = p.read_text(encoding="utf-8").strip()
            arr = json.loads(content) if content else []
        except ValueError:
            malformed.append(p.name)
            continue
        if not isinstance(arr, list):
            malformed.append(p.name)
            continue
        for r in arr:
            if valid_record(r, stage, judge):
                done.add(r["item_id"])
    return done & expected, malformed


def completeness_report(stage: str):
    rows = []
    for judge in config.JUDGES:
        done, malformed = judge_status(stage, judge)
        rows.append({"judge": judge, "n_valid": len(done),
                     "n_expected": len(expected_items(stage)),
                     "malformed_files": ";".join(malformed)})
        missing = sorted(set(expected_items(stage)) - done)
        (config.JUDGMENTS_DIR / f"stage_{stage.lower()}" / f"{judge}_missing.json").write_text(
            json.dumps(missing), encoding="utf-8")
    rep = pd.DataFrame(rows)
    rep.to_csv(config.TABLES_DIR / f"judgment_completeness_stage_{stage}.csv", index=False)
    print(rep.to_string(index=False))
    return rep


def freeze_stage(stage: str):
    """Freeze a stage: all judges complete + valid; write sha256 manifest."""
    outdir = config.JUDGMENTS_DIR / f"stage_{stage.lower()}"
    manifest_path = config.DERIVED_DIR / f"freeze_stage_{stage}.json"
    rep = completeness_report(stage)
    if (rep["n_valid"] != rep["n_expected"]).any() or (rep["malformed_files"] != "").any():
        raise SystemExit(f"Stage {stage} incomplete; not frozen")
    entries = {"blinded": sha256(config.BLINDED_DIR / f"stage_{stage.lower()}.jsonl"),
               "judges": {}}
    for judge in config.JUDGES:
        h = hashlib.sha256()
        for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
            h.update(p.read_bytes())
        entries["judges"][judge] = h.hexdigest()
    if manifest_path.exists():
        prev = json.loads(manifest_path.read_text(encoding="utf-8"))
        if prev != entries:
            raise SystemExit(f"Stage {stage} already frozen with different content; "
                             "frozen outputs are append-only")
        print(f"Stage {stage}: freeze verified (unchanged)")
    else:
        manifest_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        print(f"Stage {stage}: FROZEN -> {manifest_path}")
    return entries


def verify_frozen(stage: str):
    manifest_path = config.DERIVED_DIR / f"freeze_stage_{stage}.json"
    if not manifest_path.exists():
        raise SystemExit(f"Stage {stage} not frozen")
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    outdir = config.JUDGMENTS_DIR / f"stage_{stage.lower()}"
    if sha256(config.BLINDED_DIR / f"stage_{stage.lower()}.jsonl") != entries["blinded"]:
        raise SystemExit(f"Stage {stage} blinded file changed after freeze")
    for judge in config.JUDGES:
        h = hashlib.sha256()
        for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
            h.update(p.read_bytes())
        if h.hexdigest() != entries["judges"][judge]:
            raise SystemExit(f"Stage {stage} judge outputs changed after freeze ({judge})")
    print(f"Stage {stage}: freeze integrity verified")


if __name__ == "__main__":
    cmd = sys.argv[1]
    stage = sys.argv[2].upper() if len(sys.argv) > 2 else "A"
    if stage not in config.STAGES:
        raise SystemExit(f"invalid stage: {stage!r} (expected one of {config.STAGES})")
    if cmd == "status":
        completeness_report(stage)
    elif cmd == "freeze":
        freeze_stage(stage)
    elif cmd == "verify":
        verify_frozen(stage)
