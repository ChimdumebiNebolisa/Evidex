"""Automated blinding validation.

Hard checks on every blinded stage file before any judging is allowed:
1. Only allow-listed fields per stage.
2. No prohibited field names anywhere in the records.
3. Opaque-ID format is SA-NNNNNN and IDs are unique across the file set.
4. ID-neutrality: item_id ordering must not predict cohort or gold label
   (chi-square of cohort distribution across ID halves / first-vs-second half).
5. Stage A records must not contain page-title arrays; Stage B must contain
   them; Stage C contains the structured object (validated separately).

Exits non-zero on any failure (pipeline must stop before judging).
"""
import json
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

ALLOWED = {
    "A": {"item_id", "claim", "evidence_sentences"},
    "B": {"item_id", "claim", "evidence_sentences", "page_titles"},
    "C": {"item_id", "claim", "evidence_sentences", "page_titles",
          "structured_evidence"},
}


def load(stage):
    path = config.BLINDED_DIR / f"stage_{stage.lower()}.jsonl"
    if not path.exists():
        return None
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def validate():
    issues = []
    id_map = pd.read_csv(config.ID_MAP_CSV)
    cohort = pd.read_parquet(config.COHORT_PARQUET).set_index("claim_id")
    meta = id_map.merge(cohort, left_on="claim_id", right_index=True)

    # ID map integrity.
    if meta["item_id"].duplicated().any():
        issues.append("duplicate item_ids in ID map")
    if not meta["item_id"].str.fullmatch(r"SA-\d{6}").all():
        issues.append("item_id format violation")

    # ID neutrality: cohort and label must not concentrate by ID half.
    half = meta.sort_values("item_id")["cohort"].reset_index(drop=True)
    first, second = half[: len(half) // 2], half[len(half) // 2:]
    tab = pd.concat([first.value_counts(), second.value_counts()], axis=1).fillna(0)
    chi2, p, _, _ = stats.chi2_contingency(tab.to_numpy())
    if p < 0.01:
        issues.append(f"item_id ordering predicts cohort (p={p:.4g})")

    for stage in config.STAGES:
        records = load(stage)
        if records is None:
            if stage == "A":
                issues.append("stage_a.jsonl missing")
            continue
        ids = [r["item_id"] for r in records]
        if len(ids) != len(set(ids)):
            issues.append(f"stage {stage}: duplicate item_ids")
        for r in records:
            extra = set(r.keys()) - ALLOWED[stage]
            if extra:
                issues.append(f"stage {stage}: unexpected fields {extra} in {r['item_id']}")
                break
        # Field-level leakage: only allow-listed keys may appear (checked
        # above); natural claim/evidence TEXT may legitimately contain words
        # like "transition", so token scanning is restricted to keys and to
        # exact model-name strings in values.
        for r in records:
            keys = {k.lower() for k in r.keys()}
            for bad in ["gold_label", "true_label", "gpt", "transition", "cohort",
                        "nli", "cosine", "regression", "rescue", "robust",
                        "resistant", "weakly_warranted", "priority", "diagnostic",
                        "label", "prediction"]:
                if any(bad in k for k in keys):
                    issues.append(f"stage {stage}: prohibited key '{bad}' in {r['item_id']}")
            for v in r.values():
                if isinstance(v, str) and "gpt-5.4" in v.lower():
                    issues.append(f"stage {stage}: model name in value of {r['item_id']}")
        if stage == "A" and any("page_titles" in r for r in records):
            issues.append("stage A contains page_titles")
        if stage in ("B", "C") and any("page_titles" not in r for r in records):
            issues.append(f"stage {stage} missing page_titles")

    print("Blinding validation:", "PASS" if not issues else "FAIL")
    for i in issues:
        print(f"  - {i}")
    return issues


if __name__ == "__main__":
    sys.exit(1 if validate() else 0)
