"""Aggregate frozen judge outputs into consensus labels (per stage).

Consensus rules (panel of 5):
- high_consensus verdict: >=4/5 judges agree on Supported or Refuted.
- Ambiguous: modal verdict is Ambiguous, OR no decisive majority AND >=3/5
  sufficiency ratings in {partial_or_ambiguous, probably_insufficient,
  clearly_insufficient}.
- Unresolved: everything else (substantial split without ambiguity signal).

Runs ONLY after the stage is frozen (verifies the freeze manifest first).
Writes tables/consensus_stage_<X>.csv and data/derived/consensus_stage_<X>.parquet.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import run_judges  # noqa: E402

WEAK_SUFF = {"partial_or_ambiguous", "probably_insufficient", "clearly_insufficient"}


def load_judgments(stage: str):
    run_judges.verify_frozen(stage)
    rows = []
    outdir = config.JUDGMENTS_DIR / f"stage_{stage.lower()}"
    for judge in config.JUDGES:
        for p in sorted(outdir.glob(f"{judge}_batch_*.jsonl")):
            arr = json.loads(p.read_text(encoding="utf-8").strip() or "[]")
            for r in arr:
                if run_judges.valid_record(r, stage, judge):
                    rows.append({"item_id": r["item_id"], "judge": judge,
                                 "verdict": r["verdict"],
                                 "sufficiency": r["evidence_sufficiency"],
                                 "confidence": r["confidence"],
                                 "issue_flags": ";".join(r["issue_flags"])})
    df = pd.DataFrame(rows)
    # Batch splitting can produce duplicate (item, judge) records; keep first.
    df = df.drop_duplicates(subset=["item_id", "judge"], keep="first")
    return df


def consensus_for_item(sub: pd.DataFrame):
    verdicts = list(sub["verdict"])
    counts = Counter(verdicts)
    modal, modal_n = counts.most_common(1)[0]
    decisive = counts.get("Supported", 0), counts.get("Refuted", 0)
    max_decisive = max(decisive)
    weak_suff = sub["sufficiency"].isin(WEAK_SUFF).sum()

    if max_decisive >= 4:
        label = "Supported" if decisive[0] > decisive[1] else "Refuted"
        return label, "high_consensus", modal_n
    if modal == "Ambiguous" and modal_n >= 2 and max_decisive <= 3:
        return "Ambiguous", "ambiguous_majority", modal_n
    if max_decisive <= 3 and weak_suff >= 3:
        return "Ambiguous", "ambiguous_weak_sufficiency", weak_suff
    return "Unresolved", "unresolved", modal_n


def aggregate(stage: str):
    df = load_judgments(stage)
    rows = []
    for item_id, sub in df.groupby("item_id"):
        label, rule, support = consensus_for_item(sub)
        v = Counter(sub["verdict"])
        rows.append({
            "item_id": item_id, "consensus": label, "rule": rule,
            "n_supported": v.get("Supported", 0), "n_refuted": v.get("Refuted", 0),
            "n_ambiguous": v.get("Ambiguous", 0),
            "mean_confidence": sub["confidence"].mean(),
            "sd_confidence": sub["confidence"].std(ddof=0),
            "modal_sufficiency": Counter(sub["sufficiency"]).most_common(1)[0][0],
        })
    res = pd.DataFrame(rows)
    res.to_parquet(config.DERIVED_DIR / f"consensus_stage_{stage}.parquet", index=False)
    dist = res["consensus"].value_counts().rename("n").reset_index()
    dist.to_csv(config.TABLES_DIR / f"consensus_stage_{stage}.csv", index=False)
    print(f"Stage {stage} consensus:")
    print(dist.to_string(index=False))
    return res


if __name__ == "__main__":
    aggregate(sys.argv[1].upper() if len(sys.argv) > 1 else "A")
