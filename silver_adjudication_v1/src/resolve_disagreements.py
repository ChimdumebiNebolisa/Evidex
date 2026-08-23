"""Disagreement resolver orchestration.

Builds resolver input files (claim + stage evidence + ANONYMIZED judge
outputs for non-high-consensus items only), validates resolver outputs, and
freezes them. The resolver itself is a separate GLM-5.3 subagent driven by
the orchestrator; it never sees FEVER labels, GPT predictions, transitions,
cohort types, NLI outputs, or similarity scores.

Judge anonymization: judge ids are replaced by r1..r5 in a per-item shuffled
order so the resolver cannot track individual judges across items.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import run_judges  # noqa: E402
from aggregate_consensus import load_judgments  # noqa: E402

RESOLVER_INPUT = config.DERIVED_DIR / "resolver_inputs.jsonl"


def build_resolver_inputs(stage: str):
    cons = pd.read_parquet(config.DERIVED_DIR / f"consensus_stage_{stage}.parquet")
    # Resolver runs on items whose consensus is not a high-consensus verdict.
    need = set(cons.loc[cons["rule"] != "high_consensus", "item_id"])

    df = load_judgments(stage)
    stage_file = config.BLINDED_DIR / f"stage_{stage.lower()}.jsonl"
    evidence = {json.loads(l)["item_id"]: json.loads(l)
                for l in stage_file.read_text(encoding="utf-8").splitlines() if l.strip()}

    rng = np.random.default_rng(config.RANDOM_SEED + 7)
    records = []
    for item_id in sorted(need):
        sub = df[df["item_id"] == item_id]
        judges = sorted(sub["judge"].unique().tolist())
        shuffled = judges.copy()
        rng.shuffle(shuffled)
        anon = {j: f"r{i+1}" for i, j in enumerate(shuffled)}
        rec = {
            "item_id": item_id, "stage": stage,
            "claim": evidence[item_id]["claim"],
            "evidence": {k: v for k, v in evidence[item_id].items()
                         if k not in ("item_id", "claim")},
            "judgments": [
                {"judge": anon[r["judge"]], "verdict": r["verdict"],
                 "evidence_sufficiency": r["sufficiency"],
                 "confidence": r["confidence"],
                 "issue_flags": r["issue_flags"].split(";"),
                 "brief_reason": ""}  # reasons withheld to keep inputs compact
                for _, r in sub.iterrows()
            ],
        }
        records.append(rec)
    out = config.DERIVED_DIR / f"resolver_inputs_stage_{stage}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Stage {stage}: {len(records)} resolver inputs -> {out}")
    return out


def validate_resolver_outputs(stage: str):
    expected = {json.loads(l)["item_id"]
                for l in (config.DERIVED_DIR / f"resolver_inputs_stage_{stage}.jsonl")
                .read_text(encoding="utf-8").splitlines() if l.strip()}
    outdir = config.JUDGMENTS_DIR / "resolver"
    got, bad = set(), []
    for p in sorted(outdir.glob(f"resolver_stage_{stage}_*.jsonl")):
        try:
            arr = run_judges.load_batch_file(p)
        except ValueError:
            bad.append(p.name)
            continue
        for r in arr:
            if (isinstance(r, dict) and r.get("stage") == stage
                    and r.get("resolver_outcome") in config.RESOLVER_OUTCOMES
                    and r.get("disagreement_type") in config.RESOLVER_DISAGREEMENT_TYPES
                    and isinstance(r.get("confidence"), int) and 0 <= r["confidence"] <= 100
                    and isinstance(r.get("brief_reason"), str)):
                got.add(r["item_id"])
            else:
                bad.append(p.name)
    missing = expected - got
    print(f"Stage {stage} resolver: {len(got & expected)}/{len(expected)} valid; "
          f"missing {len(missing)}; malformed {len(set(bad))}")
    return missing, sorted(set(bad))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "inputs":
        for s in config.STAGES:
            if (config.DERIVED_DIR / f"consensus_stage_{s}.parquet").exists():
                build_resolver_inputs(s)
    elif cmd == "validate":
        ok = True
        for s in config.STAGES:
            if (config.DERIVED_DIR / f"resolver_inputs_stage_{s}.jsonl").exists():
                missing, bad = validate_resolver_outputs(s)
                ok = ok and not missing and not bad
        if not ok:
            raise SystemExit("resolver outputs incomplete or malformed")
    else:
        raise SystemExit(f"usage: {sys.argv[0]} inputs|validate")
