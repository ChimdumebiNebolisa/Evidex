"""Packetize, validate, and freeze Claude full-regression judgments.

Same conventions as the Cursor/Grok panel (``silver_adjudication_v1/src/
run_judges.py``) and the Claude residual panel:

- one packet per ``(judge, batch, stage)``; a fresh Task subagent per packet
- schema validation with the shared verdict / sufficiency / issue-flag vocabulary
- progressive-disclosure gate: Stage B packets cannot be written until Stage A
  is frozen, Stage C until Stage B is frozen
- per-stage sha256 freeze; frozen judgment files are append-only
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import panel_config as cfg  # noqa: E402
from eolhash import path_digest_matches, paths_digest_matches  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_batch_file(path: Path) -> list:
    """Read a judge batch file. Canonical container is a JSON array; the
    line-per-object variant is also accepted (same convention as the Cursor and
    Claude residual panels)."""
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    try:
        arr = json.loads(content)
    except ValueError:
        arr = [json.loads(l) for l in content.splitlines() if l.strip()]
    if not isinstance(arr, list):
        raise ValueError(f"{path.name}: top-level JSON is not a list")
    return arr


def expected_items(stage: str) -> list[str]:
    return [json.loads(l)["item_id"]
            for l in cfg.stage_blinded(stage).read_text(encoding="utf-8").splitlines()
            if l.strip()]


def valid_record(r, stage: str, judge: str) -> bool:
    if not isinstance(r, dict):
        return False
    if r.get("judge_id") != judge or r.get("stage") != stage:
        return False
    if r.get("verdict") not in cfg.VERDICTS:
        return False
    if r.get("evidence_sufficiency") not in cfg.SUFFICIENCY:
        return False
    c = r.get("confidence")
    if not isinstance(c, int) or isinstance(c, bool) or not (0 <= c <= 100):
        return False
    flags = r.get("issue_flags")
    if not isinstance(flags, list) or not flags or any(f not in cfg.ISSUE_FLAGS for f in flags):
        return False
    if not isinstance(r.get("brief_reason"), str) or not r["brief_reason"].strip():
        return False
    return True


def judge_status(stage: str, judge: str):
    expected = set(expected_items(stage))
    done, malformed = set(), []
    outdir = cfg.stage_judgments_dir(stage)
    for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
        try:
            arr = load_batch_file(p)
        except ValueError:
            malformed.append(p.name)
            continue
        for r in arr:
            if valid_record(r, stage, judge):
                done.add(r["item_id"])
            elif isinstance(r, dict) and r.get("item_id") in expected:
                malformed.append(f"{p.name}:{r.get('item_id')}")
    return done & expected, malformed


def completeness_report(stage: str) -> pd.DataFrame:
    cfg.ensure_dirs()
    expected = expected_items(stage)
    rows = []
    for judge in cfg.JUDGES:
        done, malformed = judge_status(stage, judge)
        rows.append({"stage": stage, "judge": judge, "n_valid": len(done),
                     "n_expected": len(expected),
                     "malformed_files": ";".join(malformed)})
        (cfg.stage_judgments_dir(stage) / f"{judge}_missing.json").write_text(
            json.dumps(sorted(set(expected) - done)), encoding="utf-8")
    rep = pd.DataFrame(rows)
    rep.to_csv(cfg.TABLES_DIR / f"judgment_completeness_stage_{stage}.csv", index=False)
    print(rep.to_string(index=False))
    return rep


def _require_predecessor_frozen(stage: str) -> None:
    pred = cfg.STAGE_PREDECESSOR.get(stage)
    if pred:
        if not cfg.stage_freeze(pred).exists():
            raise SystemExit(f"Stage {pred} must be frozen before Stage {stage}")
        verify_frozen(pred)


def write_packets(stage: str):
    cfg.load_lock()
    cfg.require_locked_model(cfg.LOCKED_MODEL)
    cfg.ensure_dirs()
    _require_predecessor_frozen(stage)
    items = [json.loads(l) for l in
             cfg.stage_blinded(stage).read_text(encoding="utf-8").splitlines() if l.strip()]
    rubric = (cfg.PROMPTS_DIR / "judge_rubric.md").read_text(encoding="utf-8")
    outdir = cfg.stage_packets_dir(stage)
    written = []
    for judge in cfg.JUDGES:
        done, _ = judge_status(stage, judge)
        missing = [it for it in items if it["item_id"] not in done]
        for i, start in enumerate(range(0, len(missing), cfg.BATCH_SIZE), start=1):
            chunk = missing[start:start + cfg.BATCH_SIZE]
            name = f"{judge}_batch_{i:02d}"
            out_rel = ("silver_adjudication_v1/claude_full_regression_panel/judgments/"
                       f"stage_{stage.lower()}/{name}.jsonl")
            packet = {
                "judge_id": judge,
                "stage": stage,
                "model": cfg.LOCKED_MODEL,
                "output_path": out_rel,
                "n_items": len(chunk),
                "item_ids": [c["item_id"] for c in chunk],
                "items": chunk,
                "rubric": rubric,
                "disclosure_note": (
                    f"This is Stage {stage}. Use only the fields in each item. "
                    "Do not browse, look up facts, or read other repository files."
                ),
            }
            path = outdir / f"{name}.json"
            path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
            written.append({"judge": judge, "batch": name, "stage": stage,
                            "n": len(chunk), "packet": path.as_posix(),
                            "output": out_rel})
            print(f"stage {stage} {name} n={len(chunk)}")
    (cfg.CACHE_DIR / f"queue_stage_{stage}.json").write_text(
        json.dumps(written, indent=2), encoding="utf-8")
    print(f"stage {stage}: wrote {len(written)} packets -> {outdir}")
    return written


def freeze_stage(stage: str):
    cfg.require_locked_model(cfg.LOCKED_MODEL)
    _require_predecessor_frozen(stage)
    rep = completeness_report(stage)
    if (rep["n_valid"] != rep["n_expected"]).any() or (rep["malformed_files"] != "").any():
        raise SystemExit(f"Stage {stage} incomplete or malformed; not frozen")
    if int(rep["n_valid"].sum()) != cfg.EXPECTED_PER_STAGE:
        raise SystemExit(f"Stage {stage} judgment total {int(rep['n_valid'].sum())} "
                         f"!= expected {cfg.EXPECTED_PER_STAGE}")
    entries = {"stage": stage, "model": cfg.LOCKED_MODEL,
               "n_items": len(expected_items(stage)),
               "n_judgments": int(rep["n_valid"].sum()),
               "blinded": sha256(cfg.stage_blinded(stage)), "judges": {}}
    outdir = cfg.stage_judgments_dir(stage)
    for judge in cfg.JUDGES:
        h = hashlib.sha256()
        for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
            h.update(p.read_bytes())
        entries["judges"][judge] = h.hexdigest()
    path = cfg.stage_freeze(stage)
    if path.exists():
        prev = json.loads(path.read_text(encoding="utf-8"))
        if prev != entries:
            verify_frozen(stage)
            return prev
        print(f"Stage {stage} freeze verified (unchanged)")
        return prev
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"Stage {stage}: FROZEN -> {path}")
    return entries


def verify_frozen(stage: str) -> dict:
    path = cfg.stage_freeze(stage)
    if not path.exists():
        raise SystemExit(f"Stage {stage} not frozen")
    entries = json.loads(path.read_text(encoding="utf-8"))
    if entries.get("model") != cfg.LOCKED_MODEL:
        raise SystemExit(f"Stage {stage} frozen model lock drifted")
    if entries.get("n_judgments") != cfg.EXPECTED_PER_STAGE:
        raise SystemExit(f"Stage {stage} frozen judgment count is not "
                         f"{cfg.EXPECTED_PER_STAGE}")
    if not path_digest_matches(entries["blinded"], cfg.stage_blinded(stage)):
        raise SystemExit(f"Stage {stage} blinded file changed after freeze")
    outdir = cfg.stage_judgments_dir(stage)
    for judge in cfg.JUDGES:
        parts = sorted(outdir.glob(f"{judge}_batch_*.jsonl"))
        if not paths_digest_matches(entries["judges"][judge], parts):
            raise SystemExit(f"Stage {stage} judge outputs changed after freeze ({judge})")
    print(f"Stage {stage}: freeze integrity verified")
    return entries


def missing_work_manifest() -> dict:
    """Exact remaining-work manifest, for a capacity-limited stop."""
    out = {"model_lock": cfg.LOCKED_MODEL, "expected_total": cfg.EXPECTED_TOTAL, "stages": {}}
    total_valid = 0
    for stage in cfg.STAGES:
        expected = expected_items(stage)
        stage_rec = {"frozen": cfg.stage_freeze(stage).exists(), "judges": {}}
        for judge in cfg.JUDGES:
            done, malformed = judge_status(stage, judge)
            total_valid += len(done)
            missing = sorted(set(expected) - done)
            stage_rec["judges"][judge] = {
                "n_valid": len(done), "n_missing": len(missing),
                "missing_item_ids": missing, "malformed": malformed,
            }
        stage_rec["n_valid"] = sum(j["n_valid"] for j in stage_rec["judges"].values())
        stage_rec["n_missing"] = cfg.EXPECTED_PER_STAGE - stage_rec["n_valid"]
        out["stages"][stage] = stage_rec
    out["n_valid_total"] = total_valid
    out["n_missing_total"] = cfg.EXPECTED_TOTAL - total_valid
    out["complete"] = out["n_missing_total"] == 0
    path = cfg.FREEZES_DIR / "missing_work_manifest.json"
    cfg.ensure_dirs()
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"valid {total_valid}/{cfg.EXPECTED_TOTAL}; missing "
          f"{out['n_missing_total']} -> {path.name}")
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    stage_arg = sys.argv[2].upper() if len(sys.argv) > 2 else None
    if cmd == "packets":
        write_packets(stage_arg or "A")
    elif cmd == "status":
        for s in ([stage_arg] if stage_arg else cfg.STAGES):
            completeness_report(s)
    elif cmd == "freeze":
        freeze_stage(stage_arg or "A")
    elif cmd == "verify":
        for s in ([stage_arg] if stage_arg else cfg.STAGES):
            verify_frozen(s)
    elif cmd == "missing":
        missing_work_manifest()
    else:
        raise SystemExit("usage: run_judges.py packets|status|freeze|verify|missing [STAGE]")
