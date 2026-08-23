"""Validate, packetize, and freeze Claude residual judgments."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_batch_file(path: Path) -> list:
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


def expected_items() -> list[str]:
    return [json.loads(l)["item_id"]
            for l in cfg.BLINDED_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]


def valid_record(r, judge: str) -> bool:
    if not isinstance(r, dict):
        return False
    if r.get("judge_id") != judge or r.get("stage") != cfg.STAGE:
        return False
    if r.get("verdict") not in cfg.VERDICTS:
        return False
    if r.get("evidence_sufficiency") not in cfg.SUFFICIENCY:
        return False
    c = r.get("confidence")
    if not isinstance(c, int) or not (0 <= c <= 100):
        return False
    flags = r.get("issue_flags")
    if not isinstance(flags, list) or not flags or any(f not in cfg.ISSUE_FLAGS for f in flags):
        return False
    if not isinstance(r.get("brief_reason"), str) or not r["brief_reason"].strip():
        return False
    return True


def judge_status(judge: str):
    expected = set(expected_items())
    done, malformed = set(), []
    outdir = cfg.JUDGMENTS_DIR / judge
    for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
        try:
            arr = load_batch_file(p)
        except ValueError:
            malformed.append(p.name)
            continue
        for r in arr:
            if valid_record(r, judge):
                done.add(r["item_id"])
    return done & expected, malformed


def completeness_report():
    rows = []
    for judge in cfg.JUDGES:
        done, malformed = judge_status(judge)
        rows.append({"judge": judge, "n_valid": len(done),
                     "n_expected": len(expected_items()),
                     "malformed_files": ";".join(malformed)})
        missing = sorted(set(expected_items()) - done)
        (cfg.JUDGMENTS_DIR / judge / f"{judge}_missing.json").write_text(
            json.dumps(missing), encoding="utf-8")
    rep = pd.DataFrame(rows)
    cfg.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    rep.to_csv(cfg.TABLES_DIR / "judgment_completeness.csv", index=False)
    print(rep.to_string(index=False))
    return rep


def write_packets():
    cfg.load_lock()
    cfg.require_locked_model(cfg.LOCKED_MODEL)
    cfg.ensure_dirs()
    items = [json.loads(l) for l in cfg.BLINDED_JSONL.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    rubric = (cfg.PROMPTS_DIR / "judge_rubric.md").read_text(encoding="utf-8")
    written = []
    for judge in cfg.JUDGES:
        done, _ = judge_status(judge)
        missing = [it for it in items if it["item_id"] not in done]
        for i, start in enumerate(range(0, len(missing), cfg.BATCH_SIZE), start=1):
            chunk = missing[start:start + cfg.BATCH_SIZE]
            name = f"{judge}_batch_{i:02d}"
            out_rel = f"silver_adjudication_v1/claude_residual_panel/judgments/{judge}/{name}.jsonl"
            packet = {
                "judge_id": judge,
                "stage": cfg.STAGE,
                "model": cfg.LOCKED_MODEL,
                "output_path": out_rel,
                "n_items": len(chunk),
                "item_ids": [c["item_id"] for c in chunk],
                "items": chunk,
                "rubric": rubric,
                "disclosure_note": (
                    "This is Stage C. Use only the fields in each item. "
                    "Do not browse, look up facts, or read other repository files."
                ),
            }
            path = cfg.PACKETS_DIR / f"{name}.json"
            path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
            written.append({"judge": judge, "batch": name, "n": len(chunk)})
            print(f"{name} n={len(chunk)}")
    (cfg.CACHE_DIR / "queue.json").write_text(json.dumps(written, indent=2), encoding="utf-8")
    print(f"wrote {len(written)} packets")
    return written


def freeze_judgments():
    cfg.require_locked_model(cfg.LOCKED_MODEL)
    if not cfg.BLINDED_JSONL.exists():
        raise SystemExit("blinded cohort missing")
    rep = completeness_report()
    if (rep["n_valid"] != rep["n_expected"]).any() or (rep["malformed_files"] != "").any():
        raise SystemExit("Claude panel incomplete; not frozen")
    entries = {"blinded": sha256(cfg.BLINDED_JSONL), "judges": {},
               "model": cfg.LOCKED_MODEL, "n_items": len(expected_items())}
    for judge in cfg.JUDGES:
        h = hashlib.sha256()
        for p in sorted((cfg.JUDGMENTS_DIR / judge).glob(f"{judge}_batch_*.jsonl")):
            h.update(p.read_bytes())
        entries["judges"][judge] = h.hexdigest()
    if cfg.FREEZE_JUDGES.exists():
        prev = json.loads(cfg.FREEZE_JUDGES.read_text(encoding="utf-8"))
        if prev != entries:
            raise SystemExit("judge freeze mismatch; frozen outputs are append-only")
        print("judge freeze verified (unchanged)")
    else:
        cfg.FREEZE_JUDGES.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        print(f"judge freeze -> {cfg.FREEZE_JUDGES}")
    return entries


def verify_frozen():
    if not cfg.FREEZE_JUDGES.exists():
        raise SystemExit("Claude judgments not frozen")
    entries = json.loads(cfg.FREEZE_JUDGES.read_text(encoding="utf-8"))
    if sha256(cfg.BLINDED_JSONL) != entries["blinded"]:
        raise SystemExit("blinded file changed after freeze")
    if entries.get("model") != cfg.LOCKED_MODEL:
        raise SystemExit("frozen model lock drifted")
    for judge in cfg.JUDGES:
        h = hashlib.sha256()
        for p in sorted((cfg.JUDGMENTS_DIR / judge).glob(f"{judge}_batch_*.jsonl")):
            h.update(p.read_bytes())
        if h.hexdigest() != entries["judges"][judge]:
            raise SystemExit(f"judge outputs changed after freeze ({judge})")
    print("Claude judgment freeze integrity verified")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "packets":
        write_packets()
    elif cmd == "status":
        completeness_report()
    elif cmd == "freeze":
        freeze_judgments()
    elif cmd == "verify":
        verify_frozen()
    else:
        raise SystemExit("usage: run_judges.py packets|status|freeze|verify")
