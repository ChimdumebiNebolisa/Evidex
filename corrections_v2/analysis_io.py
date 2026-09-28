"""Offline ingestion, provenance gates and append-only freezes for correction v2."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from provenance import (ROOT, digest, lf_bytes, sha256, verify_historical,
                        verify_implementation, verify_output_inventory, verify_snapshot, write_json)
from rerun import validate_job, validate_packet, validate_rows

SPEC = "corrections_v2/protocol/analysis_spec_2026-09-27.md"
SPEC_FREEZE = "corrections_v2/protocol/analysis_spec_2026-09-27.freeze.json"
MANIFEST = "corrections_v2/generated/rerun_manifest.json"
MODELS = {"grok": "cursor-grok-4.6-high-fast", "claude_full": "claude-opus-5-thinking-high",
          "claude_historical_residual_optional": "claude-opus-5-thinking-high",
          "new_residual": "claude-opus-5-thinking-high", "resolver": "cursor-grok-4.6-high-fast"}
PANEL_ROOTS = {"grok": "silver_adjudication_v1/cursor_panel",
               "claude_full": "silver_adjudication_v1/claude_full_regression_panel"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if text.lstrip().startswith("[") else [json.loads(x) for x in text.splitlines() if x.strip()]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def safe_path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path outside repository: {name}")
    return path


def version_name(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value):
        raise ValueError("version must be 1-64 lowercase letters, digits, underscores or hyphens")
    return value


def write_once(path, value):
    """Never overwrite a frozen object; identical repeat is a verification."""
    if path.exists():
        if read_json(path) != value:
            raise ValueError(f"immutable file differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))


def preparation_gate(root=ROOT):
    historical = verify_historical(root)
    verify_snapshot(root / "corrections_v2/inputs/historical_pages.json", root)
    verify_output_inventory(root)
    verify_implementation(root)
    return historical


def spec_files(root):
    names = [SPEC, MANIFEST, "corrections_v2/baseline/historical_inputs.json",
             "corrections_v2/.gitattributes",
             "corrections_v2/CURSOR_HANDOFF.md", "corrections_v2/protocol/execution.template.json",
             "corrections_v2/baseline/page_snapshot.json", "corrections_v2/rerun.py",
             "corrections_v2/provenance.py", "silver_adjudication_v1/src/taxonomy_v2.py",
             "silver_adjudication_v1/prompts/judge_rubric.md",
             "silver_adjudication_v1/prompts/resolver_rubric.md"]
    names += [p.relative_to(root).as_posix() for p in sorted((root / "corrections_v2").glob("analysis_*.py"))]
    names += [f"silver_adjudication_v1/{p}/config.json" for p in
              ("cursor_panel", "claude_full_regression_panel", "claude_residual_panel")]
    return {n: sha256(lf_bytes((root / n).read_bytes())) for n in sorted(names)}


def freeze_spec(root=ROOT):
    preparation_gate(root)
    path = root / SPEC_FREEZE
    files = spec_files(root)
    if path.exists():
        verify_spec(root)
        return read_json(path)
    if any((root / "corrections_v2/blind_io").rglob("*.output.json")) or any((root / "corrections_v2/execution").rglob("attempt-*.json")):
        raise ValueError("cannot label a new specification pre-inference after outputs/execution records exist")
    value = {"protocol": "post_hoc_correction_v2_2026-09-27", "frozen_at_utc": stamp(),
             "description": "Post hoc correction protocol; NOT preregistration of the original study",
             "judgment_outputs_present_at_freeze": False,
             "hash_policy": "CRLF-to-LF only for frozen code/spec text; packets separately exact-byte frozen",
             "files": files}
    write_once(path, value)
    return value


def verify_spec(root=ROOT):
    value = read_json(root / SPEC_FREEZE)
    if value["files"] != spec_files(root):
        raise ValueError("analysis specification/code changed after freeze; explicit dated amendment required")
    return value


def verify_file_map(root, files):
    for name, expected in files.items():
        if digest(safe_path(root, name)) != expected:
            raise ValueError(f"frozen bytes changed: {name}")


def result_manifest(root, parent):
    path = root / f"corrections_v2/results/{version_name(parent)}/artifact_manifest.json"
    manifest = read_json(path)
    verify_file_map(root, manifest["files"])
    frozen = read_json(root / manifest["judgment_freeze"])
    verify_file_map(root, frozen["files"])
    if manifest.get("parent"):
        result_manifest(root, manifest["parent"])
    if manifest["spec_sha256"] != digest(root / SPEC_FREEZE):
        raise ValueError("parent analysis belongs to a different protocol freeze")
    return manifest


def load_manifest(root=ROOT, parent=None):
    if parent:
        result_manifest(root, parent)
        return read_json(root / f"corrections_v2/results/{parent}/followup_manifest.json")
    return read_json(root / MANIFEST)


def panel_jobs(manifest, panel):
    names = {"grok", "claude_full"} if panel == "primary" else {panel}
    jobs = [j for j in manifest["jobs"] if j["panel"] in names]
    if any(j["model"] != MODELS[j["panel"]] for j in jobs):
        raise ValueError("model substitution in manifest")
    if len({j["job_id"] for j in jobs}) != len(jobs):
        raise ValueError("duplicate job ID")
    selected = [p for p in manifest["panels"] if p["panel"] in names]
    if {p["panel"] for p in selected} != names:
        raise ValueError("panel absent from manifest")
    for p in selected:
        counts = {}
        for j in jobs:
            if j["panel"] == p["panel"]:
                if j["n_judgments"] != len(j["item_ids"]):
                    raise ValueError("incorrect judgment count")
                for iid in j["item_ids"]:
                    counts.setdefault(iid, []).append(j["judge_id"])
        expected_judges = ["resolver"] if p["panel"] == "resolver" else [f"judge_{i}" for i in range(1, 6)]
        if set(counts) != set(p["item_ids"]) or any(sorted(x) != expected_judges for x in counts.values()):
            raise ValueError("manifest has missing/duplicate judge slots")
        if len(p["item_ids"]) != len(set(p["item_ids"])) or len(p["source_ids"]) != len(set(p["source_ids"])):
            raise ValueError("duplicate panel mapping")
        if len(p["source_ids"]) != len(p["item_ids"]):
            raise ValueError("incomplete source mapping")
    return jobs


def validate_resolver(job, root):
    validate_packet(job, root)
    path = safe_path(root, job["output"])
    if not path.exists():
        return "missing"
    rows = read_json(path)
    return validate_resolver_rows(job, rows)


def validate_resolver_rows(job, rows):
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows) or [r.get("item_id") for r in rows] != job["item_ids"]:
        raise ValueError("resolver output items/order differ")
    for r in rows:
        if (r.get("stage") != "C" or r.get("resolver_outcome") not in {"Supported", "Refuted", "Ambiguous", "Unresolved"}
                or r.get("disagreement_type") not in {"judge_error", "partial_warrant", "representation_sensitive", "semantic_conflict", "unresolved"}
                or type(r.get("confidence")) is not int or not 0 <= r["confidence"] <= 100
                or not isinstance(r.get("brief_reason"), str) or not r["brief_reason"].strip()):
            raise ValueError("invalid resolver output")
    return "valid"


def raw_records(path):
    raw = path.read_text(encoding="utf-8").strip()
    if raw.startswith("```json\n") and raw.endswith("```"):
        raw = raw[len("```json\n"):-3].strip()
    return json.loads(raw)


def provenance_for_job(job, root, spec):
    directory = root / "corrections_v2/execution" / job["job_id"]
    paths = sorted(directory.glob("attempt-*.json"))
    if not paths:
        raise ValueError("missing execution record; output presence is not execution proof")
    if len(paths) > 3:
        raise ValueError("retry limit exceeded")
    files, accepted, sessions = {}, [], []
    for i, path in enumerate(paths, 1):
        record = read_json(path)
        if path.name != f"attempt-{i:02}.json" or record.get("attempt") != i or record.get("job_id") != job["job_id"]:
            raise ValueError("attempts must be contiguous and job-specific")
        files[path.relative_to(root).as_posix()] = digest(path)
        if record.get("status") != "accepted":
            if record.get("status") not in {"invalid", "error", "blocked"} or not record.get("reason"):
                raise ValueError("failed attempt requires status/reason")
            if not isinstance(record.get("session_id"), str) or not record["session_id"]:
                raise ValueError("failed attempt requires session ID or explicit not_launched:<reason>")
            if not record["session_id"].startswith("not_launched:"):
                sessions.append(record["session_id"])
            if not record.get("raw_response") and (record["status"] == "invalid" or not record.get("raw_response_unavailable_reason")):
                raise ValueError("retain failed raw response or explicitly explain its absence")
            refs = ("raw_response", "routing_evidence")
            for key in refs:
                if record.get(key):
                    ref = record[key]
                    p = safe_path(root, ref["path"])
                    if digest(p) != ref["sha256"]:
                        raise ValueError("failed attempt evidence changed")
                    files[ref["path"]] = ref["sha256"]
            if record.get("raw_response"):
                schema_valid = False
                try:
                    failed_rows = raw_records(root / record["raw_response"]["path"])
                    check = validate_resolver_rows if job["panel"] == "resolver" else validate_rows
                    schema_valid = check(job, failed_rows) == "valid"
                except (ValueError, TypeError, KeyError):
                    pass
                if schema_valid:
                    raise ValueError("schema-valid earlier response cannot be discarded/retried")
            continue
        accepted.append(record)
        if i != len(paths):
            raise ValueError("accepted output followed by another attempt; no cherry-picking")
        if record.get("requested_model") != job["model"] or record.get("resolved_model") != job["model"]:
            raise ValueError("actual routing not attested to the locked model")
        for flag, expected in {"fresh_context": True, "inherited_context": False,
                               "auto": False, "inherit": False, "web_browse": False, "external_retrieval": False}.items():
            if record.get(flag) is not expected:
                raise ValueError(f"invalid execution setting: {flag}")
        if record.get("temperature") != "provider_default" or record.get("visible_input_files") != [job["packet"]]:
            raise ValueError("temperature or input isolation does not match protocol")
        for key in ("session_id", "cursor_version", "operator", "reviewer"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError(f"missing provenance: {key}")
        sessions.append(record["session_id"])
        if record.get("routing_and_isolation_reviewed") is not True:
            raise ValueError("manual routing/isolation review required")
        start, end = [datetime.fromisoformat(record[k]) for k in ("started_at_utc", "completed_at_utc")]
        frozen = datetime.fromisoformat(spec["frozen_at_utc"])
        if start.tzinfo is None or end.tzinfo is None or not frozen <= start <= end:
            raise ValueError("execution dates missing timezone or preceding frozen protocol")
        version = record.get("provider_model_version")
        if record.get("version_metadata_status") == "available":
            if not isinstance(version, str) or not version.strip():
                raise ValueError("available model version must be recorded")
        elif record.get("version_metadata_status") != "not_exposed" or version is not None or not record.get("version_metadata_note"):
            raise ValueError("record available version metadata or explicit not-exposed limitation")
        if record.get("packet_sha256") != job["packet_sha256"] or record.get("output_sha256") != digest(root / job["output"]):
            raise ValueError("execution input/output hash mismatch")
        for key in ("raw_response", "routing_evidence"):
            ref = record[key]
            p = safe_path(root, ref["path"])
            if not p.is_relative_to((root / "corrections_v2/execution").resolve()) or digest(p) != ref["sha256"]:
                raise ValueError("provenance attachment missing/changed/outside execution archive")
            files[ref["path"]] = ref["sha256"]
        if raw_records(root / record["raw_response"]["path"]) != read_json(root / job["output"]):
            raise ValueError("delivered records differ from raw response; record edits prohibited")
    if len(accepted) != 1:
        raise ValueError("exactly one accepted attempt required")
    return files, sessions


def inspect(manifest, panel, root=ROOT, spec=None):
    jobs = panel_jobs(manifest, panel)
    files, rows, missing, invalid, provenance_errors, sessions = {}, [], [], {}, {}, []
    for job in jobs:
        try:
            safe_path(root, job["packet"])
            safe_path(root, job["output"])
            validator = validate_resolver if job["panel"] == "resolver" else validate_job
            if validator(job, root) == "missing":
                missing.append(job["job_id"])
                continue
            rows += [dict(r, panel=job["panel"], job_id=job["job_id"]) for r in read_json(root / job["output"])]
            files[job["packet"]] = job["packet_sha256"]
            files[job["output"]] = digest(root / job["output"])
        except (ValueError, OSError, TypeError, KeyError) as exc:
            invalid[job["job_id"]] = str(exc)
            continue
        try:
            extra, context_ids = provenance_for_job(job, root, spec)
            files.update(extra)
            sessions += context_ids
        except (ValueError, OSError, TypeError, KeyError) as exc:
            provenance_errors[job["job_id"]] = str(exc)
    if len(sessions) != len(set(sessions)):
        provenance_errors["reused_session"] = "each job/attempt needs a fresh isolated session"
    selected_ids = {j["job_id"] for j in jobs}
    for path in (root / "corrections_v2/execution").glob("*/attempt-*.json"):
        if path.parent.name not in selected_ids:
            try:
                other = read_json(path)
            except (ValueError, OSError):
                continue  # Unrelated malformed outputs do not block this scope.
            if other.get("session_id") in sessions:
                provenance_errors["reused_session"] = "selected session reused by another panel/job"
    ready = not (missing or invalid or provenance_errors)
    status = {"panel": panel, "status": "ready_to_freeze" if ready else "incomplete",
              "expected_jobs": len(jobs), "expected_judgments": sum(j["n_judgments"] for j in jobs),
              "valid_schema_judgments": len(rows), "missing_jobs": missing,
              "invalid_outputs_or_packets": invalid, "execution_provenance_errors": provenance_errors,
              "provenance_basis": "operator records plus hashed evidence and human review; not independent provider attestation",
              "scientific_estimates": "not_computed", "inference_launched": False}
    return status, rows, files


def freeze_path(root, panel, parent=None):
    suffix = "_" + version_name(parent) if parent else ""
    return root / f"corrections_v2/freezes_v2/{panel}{suffix}.json"


def freeze_judgments(manifest, panel, root=ROOT, parent=None):
    spec = verify_spec(root)
    status, _, files = inspect(manifest, panel, root, spec)
    if status["status"] != "ready_to_freeze":
        return status
    path = freeze_path(root, panel, parent)
    payload = {"panel": panel, "parent": parent, "files": dict(sorted(files.items())),
               "spec_sha256": digest(root / SPEC_FREEZE), "job_ids": [j["job_id"] for j in panel_jobs(manifest, panel)],
               "manifest_identity": sha256(json.dumps(manifest, sort_keys=True).encode()),
               "n_judgments": status["expected_judgments"]}
    if path.exists():
        prior = read_json(path)
        payload["frozen_at_utc"] = prior["frozen_at_utc"]
    else:
        payload["frozen_at_utc"] = stamp()
    write_once(path, payload)
    return dict(status, status="frozen", freeze=path.relative_to(root).as_posix())


def frozen_rows(manifest, panel, root=ROOT, parent=None):
    status, rows, files = inspect(manifest, panel, root, verify_spec(root))
    path = freeze_path(root, panel, parent)
    if status["status"] != "ready_to_freeze" or not path.exists():
        return dict(status, status="pending", freeze_present=path.exists()), None
    frozen = read_json(path)
    if (frozen["files"] != files or frozen["spec_sha256"] != digest(root / SPEC_FREEZE)
            or frozen["manifest_identity"] != sha256(json.dumps(manifest, sort_keys=True).encode())):
        raise ValueError("judgment freeze mismatch; do not overwrite or analyze")
    verify_file_map(root, frozen["files"])
    return dict(status, status="frozen"), rows
