"""Read-only inventory of root files and Python scripts, with their contracts and movability.

python scripts/repository_inventory.py [--json OUT]

For each tracked root file and each .py file under scripts/, analysis_v2/, silver_adjudication_v1/
and corrections_v2/ it reports: hash contracts (historical 774-file inventory, correction code
fingerprint, spec freeze, output inventory), Python importers, references from tracked documents
(and whether any referencing document is itself pinned), whether it is a command-line entry point,
and a movability verdict. Nothing is moved or written unless --json is given.
"""
import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AREAS = ("scripts", "analysis_v2", "silver_adjudication_v1", "corrections_v2")
TEXT = (".py", ".md", ".sh", ".ps1", ".txt", ".tex", ".cff", ".yml", ".yaml", ".toml", ".mjs", ".js", ".json")
APPEND_ONLY = ("corrections_v2/execution/", "corrections_v2/blind_io/")
HISTORICAL_CODE = ("analysis_v2/", "silver_adjudication_v1/", "archive_old_pipeline/")
EXECUTION_TOOLING = ("corrections_v2/sdk_execution/",)


def load(rel, key=None):
    data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    return data[key] if key else data


def contracts():
    return {
        "historical_774": set(load("corrections_v2/baseline/historical_inputs.json", "files")),
        "code_fingerprint": set(load("corrections_v2/generated/code_hashes.json")),
        "spec_freeze": set(load("corrections_v2/protocol/analysis_spec_2026-09-27.freeze.json", "files")),
        "output_inventory": set(load("corrections_v2/generated/output_hashes.json", "files")),
    }


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def verdict(path, pins, importers, pinned_refs, pinned_importers):
    if pins:
        return "immovable", "hash contract: " + ", ".join(pins)
    if path.startswith(APPEND_ONLY):
        return "immovable", "append-only execution evidence"
    if pinned_importers:
        return "post-submission", "imported by pinned code: " + ", ".join(pinned_importers[:3])
    if pinned_refs:
        return "post-submission", "invoked or named by pinned documents: " + ", ".join(pinned_refs[:3])
    if path.startswith(HISTORICAL_CODE):
        return "leave", "historical study pipeline that produced pinned outputs; moving would be cosmetic"
    if path.startswith(EXECUTION_TOOLING):
        return "leave", "execution-time tooling that produced the accepted outputs; kept as the operational record"
    if importers:
        return "movable-with-importers", "update importers: " + ", ".join(importers[:3])
    return "movable", "post-judgment utility with no contract, importer or pinned reference"


def build():
    files = tracked()
    pins_by = contracts()
    pinned_any = set().union(*pins_by.values())
    texts = {}
    for p in files:
        if p.endswith(TEXT) and (ROOT / p).is_file() and (ROOT / p).stat().st_size < 2_000_000:
            texts[p] = (ROOT / p).read_text(encoding="utf-8", errors="replace")
    root_files = [p for p in files if "/" not in p]
    scripts = [p for p in files if p.endswith(".py") and p.split("/")[0] in AREAS]
    entries = []
    for p in sorted(set(root_files) | set(scripts)):
        pins = [name for name, s in pins_by.items() if p in s]
        name = p.rsplit("/", 1)[-1]
        importers, refs = [], []
        if p.endswith(".py"):
            mod = name[:-3]
            pattern = re.compile(rf"^\s*(from\s+{mod}\s+import|import\s+{mod}\b)", re.M)
            importers = sorted(q for q, t in texts.items() if q != p and q.endswith(".py") and pattern.search(t))
        mention = re.compile(rf"(?<![\w.-]){re.escape(name)}\b")
        refs = sorted(q for q, t in texts.items() if q != p and not q.endswith(".py") and (p in t or mention.search(t)))
        pinned_refs = [q for q in refs if q in pinned_any]
        pinned_importers = [q for q in importers if q in pinned_any]
        text = texts.get(p, "")
        movability, reason = verdict(p, pins, importers, pinned_refs, pinned_importers)
        entries.append({"path": p, "area": p.split("/")[0] if "/" in p else "<root>", "pins": pins,
                        "entry_point": p.endswith(".py") and "__main__" in text,
                        "importers": importers, "doc_references": len(refs), "pinned_doc_references": pinned_refs,
                        "movability": movability, "reason": reason})
    summary = {
        "tracked_files": len(files),
        "root_files": len(root_files),
        "root_py": sum(1 for p in root_files if p.endswith(".py")),
        "root_by_movability": dict(collections.Counter(e["movability"] for e in entries if e["area"] == "<root>")),
        "py_by_area": {a: dict(collections.Counter(e["movability"] for e in entries
                                                   if e["area"] == a and e["path"].endswith(".py"))) for a in AREAS},
    }
    return {"summary": summary, "files": entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    args = parser.parse_args()
    inventory = build()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(inventory["summary"], indent=2))
    for e in inventory["files"]:
        if e["area"] == "<root>" and e["path"].endswith(".py") or e["movability"] in ("movable", "movable-with-importers"):
            print(f"{e['movability']:<24} {e['path']}  ({e['reason']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
