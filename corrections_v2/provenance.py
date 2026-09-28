"""Task-local provenance and serialization. Never refresh historical baselines."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "corrections_v2/baseline/historical_inputs.json"
OUTPUT_MANIFEST = "corrections_v2/generated/output_hashes.json"
TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".tex"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def lf_bytes(data):
    """The ONLY historical equivalence: CRLF -> LF. Preserve lone CR, spaces,
    tabs, Unicode, record order, values, BOMs and final-newline presence.
    """
    return data.replace(b"\r\n", b"\n")


def digest(path):
    return sha256(path.read_bytes())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False,
                                allow_nan=False) + "\n").encode("utf-8"))


def compare_historical(data, entry):
    raw = sha256(data)
    if raw == entry["recorded_raw_sha256"]:
        status = "exact_recorded_bytes"
    elif entry["kind"] == "text" and sha256(lf_bytes(data)) == entry["lf_sha256"]:
        status = "eol_only_equivalent"
    else:
        raise ValueError("substantive historical drift (not CRLF/LF equivalence)")
    return {"status": status, "observed_raw_sha256": raw,
            "recorded_raw_sha256": entry["recorded_raw_sha256"],
            "baseline_blob_sha256": entry["baseline_blob_sha256"]}


def verify_historical(root=ROOT, *, check_tag=True):
    manifest = json.loads((root / BASELINE).read_text(encoding="utf-8"))
    reports = {}
    for name, entry in manifest["files"].items():
        if name.startswith("corrections_v2/"):
            raise ValueError(f"correction output in historical inventory: {name}")
        try:
            reports[name] = compare_historical((root / name).read_bytes(), entry)
        except (OSError, ValueError) as exc:
            raise ValueError(f"historical input failed: {name}: {exc}") from exc
    if check_tag:
        commit = subprocess.check_output(["git", "rev-parse", "evidex-artifact-v1^{}"], cwd=root, text=True).strip()
        tag = subprocess.check_output(["git", "rev-parse", "evidex-artifact-v1"], cwd=root, text=True).strip()
        if commit != manifest["scientific_artifact_commit"] or tag != manifest["scientific_artifact_tag_object"]:
            raise ValueError("scientific artifact tag changed")
    return {"scientific_artifact_commit": manifest["scientific_artifact_commit"],
            "source_baseline_commit": manifest["source_baseline_commit"],
            "files": reports,
            "exact_recorded_bytes": sum(r["status"] == "exact_recorded_bytes" for r in reports.values()),
            "eol_only_equivalent": sum(r["status"] == "eol_only_equivalent" for r in reports.values())}


def verify_snapshot(path, root=ROOT):
    entry = json.loads((root / "corrections_v2/baseline/page_snapshot.json").read_text(encoding="utf-8"))
    data = path.read_bytes()
    if sha256(lf_bytes(data)) != entry["lf_sha256"]:
        raise ValueError("historical page snapshot changed beyond CRLF/LF; no outputs written")
    return {"source_commit": entry["source_commit"], "source_path": entry["source_path"],
            "observed_raw_sha256": sha256(data), "lf_sha256": entry["lf_sha256"],
            "status": "exact_lf_bytes" if sha256(data) == entry["lf_sha256"] else "eol_only_equivalent"}


def implementation_files(root=ROOT):
    names = {"fever_evidence.py", "resolve_gold_evidence.py",
             "silver_adjudication_v1/src/reconstruct_evidence.py",
             "silver_adjudication_v1/src/join_analysis_v2.py",
             "silver_adjudication_v1/src/taxonomy_legacy_v1.py",
             "silver_adjudication_v1/src/taxonomy_v2.py",
             "silver_adjudication_v1/claude_full_regression_panel/src/analyze.py"}
    package = root / "corrections_v2"
    for pattern in ("*.py", "*.md", "tests/*.py", "baseline/*", "inputs/*.json", "protocol/*.md", "protocol/*.template.json", ".gitattributes", ".gitignore"):
        names.update(p.relative_to(root).as_posix() for p in package.glob(pattern) if p.is_file())
    return sorted(names)


def implementation_inventory(root=ROOT):
    # Code identity ignores ONLY checkout EOL conversion, like historical text.
    return {name: sha256(lf_bytes((root / name).read_bytes())) for name in implementation_files(root)}


def output_paths(root=ROOT):
    paths = list((root / "corrections_v2/generated").glob("*.json"))
    paths += list((root / "corrections_v2/generated").glob("*.jsonl"))
    paths += list((root / "corrections_v2/generated").glob("*.csv"))
    paths += [p for p in (root / "corrections_v2/blind_io").rglob("*.json") if not p.name.endswith(".output.json")]
    return sorted(p for p in paths if p != root / OUTPUT_MANIFEST)


def seal_outputs(root=ROOT):
    # Called only after ALL generated reports, revisions and packets are written.
    write_json(root / OUTPUT_MANIFEST, {
        "policy": "exact UTF-8 bytes, LF newlines; this inventory excludes itself and future judgment outputs",
        "files": {p.relative_to(root).as_posix(): digest(p) for p in output_paths(root)}})


def verify_output_inventory(root=ROOT):
    expected = json.loads((root / OUTPUT_MANIFEST).read_text(encoding="utf-8"))["files"]
    actual = {p.relative_to(root).as_posix() for p in output_paths(root)}
    if set(expected) != actual or OUTPUT_MANIFEST in expected:
        raise ValueError("output inventory membership changed or self-reference")
    for name, value in expected.items():
        data = (root / name).read_bytes()
        if b"\r\n" in data or sha256(data) != value:
            raise ValueError(f"generated bytes changed: {name}; regenerate with reproduce.py")


def verify_implementation(root=ROOT):
    expected = json.loads((root / "corrections_v2/generated/code_hashes.json").read_text(encoding="utf-8"))
    if expected != implementation_inventory(root):
        raise ValueError("correction implementation changed; regenerate outputs")
