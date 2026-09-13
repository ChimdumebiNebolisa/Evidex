"""Quarantine judge output whose model provenance cannot be established.

Cursor reports a substitution ("Switched to grok-4.6 after reaching Other Models
usage limit") at the end of a subagent run, so when that happens there is no way
to prove which model wrote the file -- it may have been produced wholly or partly
by the fallback model. The model lock forbids using it, and it must not be
silently dropped either, so it is moved out of the inbox unread, hashed, and
recorded with the reason.

Verdict content is never read or inspected here: the file is hashed as bytes and
moved. Quarantining is applied to whole `(judge, batch)` units, never to
individual items, so it cannot act as cherry-picking.

Usage:
    python src/quarantine.py <stage> <reason-tag> <judge_batch> [<judge_batch> ...]

where <judge_batch> is a stem such as ``claude_full_judge_2_batch_01``.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quarantine(stage: str, reason_tag: str, stems: list[str]) -> dict:
    dest = cfg.DISCARDED_DIR / f"{reason_tag}_stage_{stage.lower()}"
    dest.mkdir(parents=True, exist_ok=True)
    inbox = cfg.stage_inbox_dir(stage)
    records = []
    for stem in stems:
        src = inbox / f"{stem}.jsonl"
        if not src.exists():
            records.append({"file": stem, "status": "absent"})
            continue
        digest = sha256(src)
        shutil.move(str(src), str(dest / src.name))
        records.append({"file": src.name, "sha256": digest,
                        "bytes": (dest / src.name).stat().st_size,
                        "status": "quarantined"})
    manifest = {
        "stage": stage,
        "reason_tag": reason_tag,
        "quarantined_at": datetime.now(timezone.utc).isoformat(),
        "locked_model": cfg.LOCKED_MODEL,
        "reason": (
            "Cursor reported 'Other Models usage limit reached; switched to "
            "grok-4.6' for the subagent that produced this file. Model "
            "provenance cannot be established, and the panel model lock "
            "forbids any non-Claude judgment, so the whole (judge, batch) unit "
            "is discarded unread rather than ingested. Verdicts were not "
            "inspected before or after quarantine."
        ),
        "files": records,
    }
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=2),
                                        encoding="utf-8")
    print(f"stage {stage}: quarantined {sum(r['status'] == 'quarantined' for r in records)}"
          f" file(s) -> {dest}")
    return manifest


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    quarantine(sys.argv[1].upper(), sys.argv[2], sys.argv[3:])
