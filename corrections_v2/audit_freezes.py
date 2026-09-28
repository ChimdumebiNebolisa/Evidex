"""Explain residual-panel raw/LF/CRLF hashes without rewriting any manifest."""
import hashlib
import json
from pathlib import Path
from provenance import verify_historical, write_json

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "silver_adjudication_v1/claude_residual_panel"


def variants(parts):
    lf = [b.replace(b"\r\n", b"\n") for b in parts]
    return {"raw": hashlib.sha256(b"".join(parts)).hexdigest(),
            "lf": hashlib.sha256(b"".join(lf)).hexdigest(),
            "crlf": hashlib.sha256(b"".join(b.replace(b"\n", b"\r\n") for b in lf)).hexdigest()}


def audit():
    verify_historical(ROOT)
    raw = json.loads((PANEL / "freezes/freeze_judgments.json").read_text())
    manifest = json.loads((PANEL / "freezes/freeze_manifest.json").read_text())
    entries = [("blinded", raw["blinded"], [PANEL / "data/blinded_stage_c.jsonl"])]
    for judge, expect in raw["judges"].items():
        entries.append((judge, expect, sorted((PANEL / "judgments" / judge).glob("*_batch_*.jsonl"))))
    paths = {p.name: p for folder in ("data", "freezes", "tables") for p in (PANEL / folder).iterdir() if p.is_file()}
    paths["freeze_judgments"] = PANEL / "freezes/freeze_judgments.json"
    entries.extend((key, expected, [paths[key]]) for key, expected in manifest.items())
    result = []
    for key, expected, files in entries:
        hashes = variants([p.read_bytes() for p in files])
        # Binary parquet must match exact bytes, never EOL folding.
        matching = [mode for mode, h in hashes.items() if h == expected]
        if any(p.suffix == ".parquet" for p in files):
            matching = [m for m in matching if m == "raw"]
        result.append({"key": key, "status": "exact_recorded_bytes" if "raw" in matching else "eol_only_equivalent",
                       "files": [p.relative_to(ROOT).as_posix() for p in files],
                       "frozen_sha256": expected, "computed_sha256": hashes, "matching_encodings": matching})
        if not matching:
            raise ValueError(f"unexplained hash mismatch: {key}")
    output = ROOT / "corrections_v2/generated/freeze_eol_audit.json"
    write_json(output, result)
    print(f"{len(result)} entries: all accounted for; {sum('lf' not in r['matching_encodings'] and not r['key'].endswith('.parquet') for r in result)} text hashes differ under LF-only checkout")


if __name__ == "__main__":
    audit()
