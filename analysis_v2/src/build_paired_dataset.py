"""Build the canonical claim-level paired dataset (one row per claim).

Pairs claim_only and claim_plus_evidence predictions per model, computes the
four-way transition class per model, and cross-model agreement features.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def transition_class(correct_only: bool, correct_ev: bool) -> str:
    if not correct_only and correct_ev:
        return config.TRANSITION_RESCUE
    if correct_only and correct_ev:
        return config.TRANSITION_ROBUST
    if not correct_only and not correct_ev:
        return config.TRANSITION_RESISTANT
    return config.TRANSITION_REGRESSION


def build_paired() -> pd.DataFrame:
    config.ensure_dirs()
    df = pd.read_csv(config.SOURCE_RESULTS, dtype={"claim_id": int})

    # One claim-level base row (claim/evidence metadata identical across cells).
    base_cols = [
        "claim_id", "claim_text", "gold_label", "gold_evidence",
        "evidence_sentences_json", "evidence_pages_json",
        "evidence_set_size", "evidence_set_id",
    ]
    base = df.drop_duplicates("claim_id")[base_cols].sort_values("claim_id").reset_index(drop=True)

    # Parse evidence metadata.
    def safe_json(x):
        try:
            return json.loads(x) if isinstance(x, str) and x else []
        except (ValueError, TypeError):
            return []

    base["evidence_pages"] = base["evidence_pages_json"].map(safe_json)
    base["n_evidence_sentences"] = base["evidence_sentences_json"].map(lambda x: len(safe_json(x)))
    base["n_evidence_pages"] = base["evidence_pages"].map(len)

    # Pivot predictions per model/condition.
    pred = df.pivot_table(
        index="claim_id", columns=["model", "condition"], values="model_output", aggfunc="first"
    )
    pred.columns = [f"{m}__{c}" for m, c in pred.columns]
    out = base.merge(pred, left_on="claim_id", right_index=True, how="left", validate="1:1")

    for m in config.MODELS:
        co = out[f"{m}__claim_only"] == out["gold_label"]
        ev = out[f"{m}__claim_plus_evidence"] == out["gold_label"]
        out[f"{m}_claim_only_correct"] = co
        out[f"{m}_evidence_correct"] = ev
        out[f"{m}_transition"] = [
            transition_class(a, b) for a, b in zip(co, ev)
        ]

    # Cross-model agreement features.
    for cond, tag in [("claim_only", "co"), ("claim_plus_evidence", "ev")]:
        out[f"agree_{tag}"] = out[f"{config.MODELS[0]}__{cond}"] == out[f"{config.MODELS[1]}__{cond}"]
    out["agree_transition"] = out[f"{config.MODELS[0]}_transition"] == out[f"{config.MODELS[1]}_transition"]

    out = out.rename(columns={
        "gpt-5.4__claim_only": "gpt54_claim_only_pred",
        "gpt-5.4__claim_plus_evidence": "gpt54_evidence_pred",
        "gpt-5.4-mini__claim_only": "gpt54mini_claim_only_pred",
        "gpt-5.4-mini__claim_plus_evidence": "gpt54mini_evidence_pred",
    })
    out = out.drop(columns=["evidence_pages"])

    out.to_parquet(config.PAIRED_PARQUET, index=False)
    print(f"Paired dataset: {len(out)} claims -> {config.PAIRED_PARQUET}")
    return out


if __name__ == "__main__":
    build_paired()
