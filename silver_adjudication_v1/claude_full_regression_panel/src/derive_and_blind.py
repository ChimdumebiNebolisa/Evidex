"""Independently derive the 226-regression cohort and write blinded A/B/C files.

Regression definition (unchanged from Evidex): a claim that the GPT model got
*correct without evidence* and *incorrect after* receiving the designated FEVER
evidence, i.e. transition ``correct_to_wrong``. The cohort is the union across
``gpt-5.4`` and ``gpt-5.4-mini``.

The count is recomputed from ``analysis_v2/data/derived/paired_enriched.parquet``
(the canonical source) and cross-checked against the frozen shared cohort
manifest. Any mismatch, or any count other than 226, is a hard stop.

Blinded stage files reuse the *existing* Stage A/B/C evidence representations
built by ``silver_adjudication_v1/src/{blind_cohort,reconstruct_evidence}.py``.
No new evidence is retrieved. Fresh opaque IDs ``CF-000001..CF-000226`` are
assigned by a seeded shuffle; the CF -> SA -> claim_id mapping stays private in
``data/id_map.csv`` and is never shown to a judge.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402

T_REGRESSION = "correct_to_wrong"
MODEL_COLS = {"gpt-5.4": "gpt-5.4_transition", "gpt-5.4-mini": "gpt-5.4-mini_transition"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive_regression_claim_ids() -> tuple[list[int], dict]:
    """Recompute the regression cohort from paired_enriched; fail loudly on drift."""
    enriched = pd.read_parquet(cfg.PAIRED_ENRICHED)
    is_reg = {m: enriched[c] == T_REGRESSION for m, c in MODEL_COLS.items()}
    union = is_reg["gpt-5.4"] | is_reg["gpt-5.4-mini"]
    claim_ids = sorted(int(c) for c in enriched.loc[union, "claim_id"])

    n = len(claim_ids)
    if n != cfg.EXPECTED_COHORT_N:
        raise SystemExit(
            f"FAIL: independent regression count is {n}, expected "
            f"{cfg.EXPECTED_COHORT_N}. Refusing to build the cohort."
        )
    if len(set(claim_ids)) != n:
        raise SystemExit("FAIL: duplicate claim_ids in the regression union")

    cohort = pd.read_parquet(cfg.COHORT_PARQUET)
    frozen = sorted(int(c) for c in cohort.loc[cohort["cohort"] == "regression", "claim_id"])
    if frozen != claim_ids:
        raise SystemExit(
            "FAIL: independently derived regressions differ from the frozen shared "
            f"cohort manifest (derived {len(claim_ids)}, manifest {len(frozen)})"
        )

    both = int((is_reg["gpt-5.4"] & is_reg["gpt-5.4-mini"]).sum())
    only54 = int((is_reg["gpt-5.4"] & ~is_reg["gpt-5.4-mini"]).sum())
    onlymini = int((~is_reg["gpt-5.4"] & is_reg["gpt-5.4-mini"]).sum())
    if both + only54 + onlymini != n:
        raise SystemExit("FAIL: regression_type partition does not sum to the cohort")
    audit = {
        "definition": "transition == 'correct_to_wrong' (correct without evidence, "
                      "incorrect with designated FEVER evidence)",
        "union_across": list(MODEL_COLS),
        "source": str(cfg.PAIRED_ENRICHED.relative_to(cfg.REPO_ROOT).as_posix()),
        "n_total_claims_scanned": int(len(enriched)),
        "n_regressions": n,
        "n_both_models": both,
        "n_gpt54_only": only54,
        "n_mini_only": onlymini,
        "cross_check_shared_cohort_manifest": "identical",
    }
    print(f"independent regression cohort: n={n} "
          f"(both {both} / gpt-5.4 only {only54} / mini only {onlymini})")
    return claim_ids, audit


def _load_shared_blinded(stage: str) -> dict:
    out = {}
    for line in cfg.SHARED_BLINDED[stage].read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["item_id"]] = rec
    return out


def derive_and_blind() -> dict:
    cfg.load_lock()
    cfg.ensure_dirs()
    claim_ids, audit = derive_regression_claim_ids()

    shared_map = pd.read_csv(cfg.ID_MAP_SHARED)
    cid_to_sa = dict(zip(shared_map["claim_id"].astype(int), shared_map["item_id"]))
    source_ids = [cid_to_sa[c] for c in claim_ids]
    if len(set(source_ids)) != len(source_ids):
        raise SystemExit("FAIL: duplicate source item ids")

    filtered = set(json.loads(cfg.PROVIDER_FILTERED.read_text(encoding="utf-8"))["items"])
    overlap = sorted(set(source_ids) & filtered)
    if overlap:
        raise SystemExit(
            f"FAIL: provider-filtered items inside the regression cohort: {overlap}. "
            "Stop and decide handling explicitly before judging."
        )

    blinded = {s: _load_shared_blinded(s) for s in cfg.STAGES}
    for s in cfg.STAGES:
        missing = [i for i in source_ids if i not in blinded[s]]
        if missing:
            raise SystemExit(f"FAIL: Stage {s} blinded records missing for {missing[:5]}")

    rng = np.random.default_rng(cfg.RANDOM_SEED)
    shuffled = list(source_ids)
    rng.shuffle(shuffled)
    sa_to_cid = {sa: cid for cid, sa in zip(claim_ids, source_ids)}

    rows = []
    per_stage_items = {s: [] for s in cfg.STAGES}
    for i, sa in enumerate(shuffled, start=1):
        cf = f"CF-{i:06d}"
        rows.append({"claude_item_id": cf, "source_item_id": sa,
                     "claim_id": sa_to_cid[sa], "order": i})
        for s in cfg.STAGES:
            src = blinded[s][sa]
            item = {"item_id": cf, "claim": src["claim"],
                    "evidence_sentences": src["evidence_sentences"]}
            if s in ("B", "C"):
                item["page_titles"] = src.get("page_titles", [])
            if s == "C":
                item["structured_evidence"] = src.get("structured_evidence", {})
            extra = set(item) - cfg.ALLOWED_ITEM_KEYS[s]
            if extra:
                raise SystemExit(f"FAIL: unexpected Stage {s} blinded keys: {sorted(extra)}")
            per_stage_items[s].append(item)

    for s in cfg.STAGES:
        cfg.stage_blinded(s).write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in per_stage_items[s]),
            encoding="utf-8")
    pd.DataFrame(rows).to_csv(cfg.ID_MAP_CSV, index=False)

    source = {
        "n": len(rows),
        "expected_n": cfg.EXPECTED_COHORT_N,
        "seed": cfg.RANDOM_SEED,
        "model_lock": cfg.LOCKED_MODEL,
        "stages": cfg.STAGES,
        "cohort_audit": audit,
        "inputs": {
            "paired_enriched": sha256(cfg.PAIRED_ENRICHED),
            "shared_cohort": sha256(cfg.COHORT_PARQUET),
            "shared_id_map": sha256(cfg.ID_MAP_SHARED),
            **{f"shared_blinded_stage_{s.lower()}": sha256(cfg.SHARED_BLINDED[s])
               for s in cfg.STAGES},
        },
        "outputs": {
            **{f"blinded_stage_{s.lower()}": sha256(cfg.stage_blinded(s)) for s in cfg.STAGES},
            "id_map": sha256(cfg.ID_MAP_CSV),
        },
        "source_item_ids_sorted": sorted(source_ids),
        "note": "Judges receive only the blinded stage files. They are not told the "
                "items are regressions, which GPT model regressed, or that any prior "
                "panel judged them.",
    }
    cfg.COHORT_SOURCE.write_text(json.dumps(source, indent=2), encoding="utf-8")
    for s in cfg.STAGES:
        print(f"Stage {s} blinded: {len(per_stage_items[s])} items -> {cfg.stage_blinded(s).name}")
    return source


def leakage_errors(stage: str) -> list[str]:
    path = cfg.stage_blinded(stage)
    errors = []
    allowed = cfg.ALLOWED_ITEM_KEYS[stage]
    prohibited_keys = {p.lower() for p in cfg.PROHIBITED_FIELDS}
    seen = set()
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        rec = json.loads(line)
        extra = set(rec) - allowed
        if extra:
            errors.append(f"stage {stage} line {i}: extra keys {sorted(extra)}")
        for k in rec:
            if k.lower() in prohibited_keys:
                errors.append(f"stage {stage} line {i}: prohibited key {k}")
        iid = str(rec.get("item_id", ""))
        if not iid.startswith("CF-"):
            errors.append(f"stage {stage} line {i}: item_id is not an opaque CF- id")
        if iid in seen:
            errors.append(f"stage {stage} line {i}: duplicate item_id {iid}")
        seen.add(iid)
    if len(seen) != cfg.EXPECTED_COHORT_N:
        errors.append(f"stage {stage}: {len(seen)} items, expected {cfg.EXPECTED_COHORT_N}")
    return errors


def id_neutrality_errors() -> list[str]:
    """CF order must not encode which GPT model regressed."""
    idmap = pd.read_csv(cfg.ID_MAP_CSV)
    cohort = pd.read_parquet(cfg.COHORT_PARQUET).set_index("claim_id")
    types = cohort.loc[idmap["claim_id"], "regression_type"].to_numpy()
    half = len(types) // 2
    first = pd.Series(types[:half]).value_counts(normalize=True)
    second = pd.Series(types[half:]).value_counts(normalize=True)
    errors = []
    for t in set(first.index) | set(second.index):
        if abs(float(first.get(t, 0)) - float(second.get(t, 0))) > 0.20:
            errors.append(f"id order may encode regression_type ({t}): "
                          f"{first.get(t, 0):.2f} vs {second.get(t, 0):.2f}")
    return errors


def validate_blinding() -> None:
    errs = []
    for s in cfg.STAGES:
        errs.extend(leakage_errors(s))
    errs.extend(id_neutrality_errors())
    if errs:
        raise SystemExit("LEAKAGE DETECTED:\n" + "\n".join(errs[:20]))
    print("blinding OK for stages " + ", ".join(cfg.STAGES))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("derive", "all"):
        derive_and_blind()
    if cmd in ("validate", "all"):
        validate_blinding()
