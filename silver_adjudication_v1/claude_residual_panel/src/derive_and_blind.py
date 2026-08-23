"""Reconstruct the Cursor Stage C residual set and write a blinded Stage C file."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct_residual() -> pd.DataFrame:
    cons = pd.read_parquet(cfg.CURSOR_CONSENSUS_C)
    resid = cons.loc[cons["consensus"].isin(["Ambiguous", "Unresolved"])].copy()
    n = int(len(resid))
    if n != cfg.EXPECTED_RESIDUAL_N:
        raise SystemExit(
            f"residual count {n} != expected {cfg.EXPECTED_RESIDUAL_N}; "
            "investigate before judging"
        )
    return resid


def derive_and_blind() -> dict:
    cfg.load_lock()
    cfg.ensure_dirs()
    resid = reconstruct_residual()
    source_ids = sorted(resid["item_id"].tolist())

    blinded = {}
    for line in cfg.SHARED_STAGE_C.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        blinded[rec["item_id"]] = rec
    missing = [i for i in source_ids if i not in blinded]
    if missing:
        raise SystemExit(f"residual items missing from Stage C blinded file: {missing[:5]}")

    rng = np.random.default_rng(cfg.RANDOM_SEED)
    shuffled = source_ids.copy()
    rng.shuffle(shuffled)
    rows = []
    out_items = []
    for i, sa in enumerate(shuffled, start=1):
        cr = f"CR-{i:06d}"
        src = blinded[sa]
        item = {
            "item_id": cr,
            "claim": src["claim"],
            "evidence_sentences": src["evidence_sentences"],
            "page_titles": src.get("page_titles", []),
            "structured_evidence": src.get("structured_evidence", {}),
        }
        extra = set(item) - cfg.ALLOWED_ITEM_KEYS
        if extra:
            raise SystemExit(f"unexpected blinded keys: {extra}")
        out_items.append(item)
        rows.append({"claude_item_id": cr, "source_item_id": sa, "order": i})

    cfg.BLINDED_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_items),
        encoding="utf-8",
    )
    pd.DataFrame(rows).to_csv(cfg.ID_MAP_CSV, index=False)
    source = {
        "n": len(out_items),
        "expected_n": cfg.EXPECTED_RESIDUAL_N,
        "cursor_consensus_c": sha256(cfg.CURSOR_CONSENSUS_C),
        "shared_stage_c": sha256(cfg.SHARED_STAGE_C),
        "blinded_stage_c": sha256(cfg.BLINDED_JSONL),
        "seed": cfg.RANDOM_SEED,
        "selection": "Cursor Stage C consensus in {Ambiguous, Unresolved}",
        "source_item_ids_sorted": source_ids,
    }
    cfg.RESIDUAL_SOURCE.write_text(json.dumps(source, indent=2), encoding="utf-8")
    print(f"blinded residual n={len(out_items)} -> {cfg.BLINDED_JSONL}")
    return source


def leakage_errors(path: Path | None = None) -> list[str]:
    path = path or cfg.BLINDED_JSONL
    errors = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        rec = json.loads(line)
        extra = set(rec) - cfg.ALLOWED_ITEM_KEYS
        if extra:
            errors.append(f"line {i}: extra keys {sorted(extra)}")
        for k in rec:
            if k.lower() in {p.lower() for p in cfg.PROHIBITED_FIELDS}:
                errors.append(f"line {i}: prohibited key {k}")
        iid = str(rec.get("item_id", ""))
        if not iid.startswith("CR-"):
            errors.append(f"line {i}: item_id is not an opaque CR- id")
        if iid.startswith("SA-"):
            errors.append(f"line {i}: source SA- id leaked as item_id")
    return errors


def validate_blinding() -> None:
    errs = leakage_errors()
    if errs:
        raise SystemExit("LEAKAGE DETECTED:\n" + "\n".join(errs[:20]))
    print(f"blinding OK: {cfg.BLINDED_JSONL}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("derive", "all"):
        derive_and_blind()
    if cmd in ("validate", "all"):
        validate_blinding()
