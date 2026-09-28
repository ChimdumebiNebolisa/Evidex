"""One-time migration from fixed Git objects; never from current input bytes.

Not part of reproduction. Refuses to replace an established baseline.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "corrections_v2"))
from provenance import lf_bytes, sha256, write_json, TEXT_SUFFIXES

REVIEWED = "0cc36f04ce8bbfd2a62848760c71550242be78c4"
SOURCE = "776d09b40e9161800bf87238eb2cac4fe102df8e"
ARTIFACT = "29102c39427fac01ff46c77c28365feb91f6397b"


def blob(ref, name):
    return subprocess.check_output(["git", "show", f"{ref}:{name}"], cwd=ROOT)


def main():
    target = ROOT / "corrections_v2/baseline/historical_inputs.json"
    if target.exists():
        raise SystemExit("Baseline already exists; refusing to refresh it")
    recorded = json.loads(blob(REVIEWED, "corrections_v2/generated/input_hashes.json"))
    files = {}
    # Batch Git reads avoid starting hundreds of processes on Windows.
    names = sorted(n for n in recorded if not n.startswith("corrections_v2/"))
    request = "".join(f"{SOURCE}:{n}\n" for n in names).encode()
    packed = subprocess.check_output(["git", "cat-file", "--batch"], input=request, cwd=ROOT)
    offset = 0
    for name in names:
        end = packed.index(b"\n", offset)
        size = int(packed[offset:end].split()[-1])
        data = packed[end + 1:end + 1 + size]
        offset = end + 2 + size
        text = Path(name).suffix in TEXT_SUFFIXES
        variants = {sha256(data)}
        if text:
            variants.update((sha256(lf_bytes(data)), sha256(lf_bytes(data).replace(b"\n", b"\r\n"))))
        if recorded[name] not in variants:
            raise ValueError(f"reviewed raw hash not explained by pinned blob/EOL: {name}")
        files[name] = {"kind": "text" if text else "binary", "recorded_raw_sha256": recorded[name],
                       "baseline_blob_sha256": sha256(data),
                       "lf_sha256": sha256(lf_bytes(data)) if text else None}
    write_json(target, {"scientific_artifact_commit": ARTIFACT,
                       "scientific_artifact_tag_object": subprocess.check_output(["git", "rev-parse", "evidex-artifact-v1"], cwd=ROOT, text=True).strip(),
                       "source_baseline_commit": SOURCE, "reviewed_correction_commit": REVIEWED, "files": files})
    name = "corrections_v2/generated/historical_pages_used.json"
    data = blob(REVIEWED, name)
    write_json(ROOT / "corrections_v2/baseline/page_snapshot.json", {
        "source_commit": REVIEWED, "source_path": name, "source_git_blob_sha256": sha256(data),
        "original_acquisition_raw_sha256": json.loads(blob(REVIEWED, "corrections_v2/generated/archive_provenance.json"))["exported_page_snapshot_sha256"],
        "lf_sha256": sha256(lf_bytes(data))})
    inputs = ROOT / "corrections_v2/inputs"
    inputs.mkdir(exist_ok=True)
    (inputs / "historical_pages.json").write_bytes(lf_bytes(data))
    (inputs / "archive_provenance.json").write_bytes(lf_bytes(blob(REVIEWED, "corrections_v2/generated/archive_provenance.json")))
    print(f"Imported {len(files)} immutable historical identities from pinned Git objects")


if __name__ == "__main__":
    main()
