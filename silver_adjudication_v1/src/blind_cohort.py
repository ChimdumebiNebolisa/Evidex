"""Create the blinded Stage A dataset and the opaque-ID map.

- Opaque IDs: SA-000001..SA-XXXXXX assigned after a seeded shuffle of
  claim_ids (seed 20260822). IDs carry no cohort/label signal; the mapping
  lives only in data/derived/id_map.csv and never in blinded files.
- Stage A fields: item_id, claim, evidence_sentences (the exact gold_evidence
  text the GPT models saw). Nothing else.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def build_stage_a():
    config.ensure_dirs()
    cohort = pd.read_parquet(config.COHORT_PARQUET)

    ids = cohort["claim_id"].to_numpy().copy()
    rng = np.random.default_rng(config.RANDOM_SEED)
    rng.shuffle(ids)
    mapping = {"SA-{:06d}".format(i + 1): int(cid) for i, cid in enumerate(ids)}
    pd.DataFrame({"item_id": mapping.keys(), "claim_id": mapping.values()}
                 ).to_csv(config.ID_MAP_CSV, index=False)

    by_cid = cohort.set_index("claim_id")
    out = config.BLINDED_DIR / "stage_a.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for item_id, cid in mapping.items():
            row = by_cid.loc[cid]
            f.write(json.dumps({
                "item_id": item_id,
                "claim": row["claim_text"],
                "evidence_sentences": row["gold_evidence"],
            }, ensure_ascii=False) + "\n")
    print(f"Stage A blinded file: {len(mapping)} items -> {out}")
    return mapping


if __name__ == "__main__":
    build_stage_a()
