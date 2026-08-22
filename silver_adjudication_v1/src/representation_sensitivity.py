"""Representation sensitivity: verdict/sufficiency/confidence/flag changes
across progressive-disclosure stages, per judge and at consensus level.

All comparisons are within-item (each claim is its own control under the
controlled disclosure design). No causal language beyond that design.

Requires all three stages frozen. Writes:
tables/stage_transition_counts.csv, tables/representation_sensitivity.csv,
data/derived/verdict_changes.parquet.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from aggregate_consensus import load_judgments  # noqa: E402


def per_judge_changes():
    frames = {s: load_judgments(s).set_index(["item_id", "judge"]) for s in config.STAGES}
    rows = []
    for item_id, judge in frames["A"].index:
        try:
            a = frames["A"].loc[(item_id, judge)]
            b = frames["B"].loc[(item_id, judge)]
            c = frames["C"].loc[(item_id, judge)]
        except KeyError:
            continue
        rows.append({
            "item_id": item_id, "judge": judge,
            "verdict_A": a["verdict"], "verdict_B": b["verdict"], "verdict_C": c["verdict"],
            "change_A_to_B": a["verdict"] != b["verdict"],
            "change_B_to_C": b["verdict"] != c["verdict"],
            "change_A_to_C": a["verdict"] != c["verdict"],
            "ambiguous_to_decisive_A_to_C": a["verdict"] == "Ambiguous" and c["verdict"] != "Ambiguous",
            "decisive_to_ambiguous_A_to_C": a["verdict"] != "Ambiguous" and c["verdict"] == "Ambiguous",
            "conf_delta_A_to_C": c["confidence"] - a["confidence"],
            "suff_A": a["sufficiency"], "suff_C": c["sufficiency"],
            "suff_improved_A_to_C": (
                config.SUFFICIENCY.index(c["sufficiency"]) <
                config.SUFFICIENCY.index(a["sufficiency"])),
            "flags_A": a["issue_flags"], "flags_C": c["issue_flags"],
        })
    df = pd.DataFrame(rows)
    df.to_parquet(config.DERIVED_DIR / "verdict_changes.parquet", index=False)

    counts = pd.DataFrame({
        "A_to_B": [df["change_A_to_B"].mean()],
        "B_to_C": [df["change_B_to_C"].mean()],
        "A_to_C": [df["change_A_to_C"].mean()],
        "amb_to_decisive_A_to_C": [df["ambiguous_to_decisive_A_to_C"].mean()],
        "decisive_to_amb_A_to_C": [df["decisive_to_ambiguous_A_to_C"].mean()],
        "mean_conf_delta_A_to_C": [df["conf_delta_A_to_C"].mean()],
        "suff_improved_A_to_C": [df["suff_improved_A_to_C"].mean()],
    })
    counts.to_csv(config.TABLES_DIR / "stage_transition_counts.csv", index=False)
    print(counts.T.to_string())
    return df


def consensus_sensitivity():
    """Consensus-level resolution/reversal rates (run before unblinding
    module but requires consensus for all stages)."""
    cons = {s: pd.read_parquet(config.DERIVED_DIR / f"consensus_stage_{s}.parquet")
            .set_index("item_id") for s in config.STAGES}
    rows = []
    for item_id in cons["A"].index:
        a, b, c = cons["A"].loc[item_id, "consensus"], cons["B"].loc[item_id, "consensus"], \
            cons["C"].loc[item_id, "consensus"]
        rows.append({
            "item_id": item_id, "consensus_A": a, "consensus_B": b, "consensus_C": c,
            "resolved_by_titles": a in ("Ambiguous", "Unresolved") and b in ("Supported", "Refuted"),
            "resolved_only_by_structure": (b in ("Ambiguous", "Unresolved"))
            and (c in ("Supported", "Refuted")),
            "still_ambiguous_after_C": c in ("Ambiguous", "Unresolved"),
            "reversed_after_titles": a in ("Supported", "Refuted") and b in ("Supported", "Refuted") and a != b,
            "reversed_after_structure": b in ("Supported", "Refuted") and c in ("Supported", "Refuted") and b != c,
        })
    df = pd.DataFrame(rows)
    df.to_parquet(config.DERIVED_DIR / "consensus_changes.parquet", index=False)

    summary = pd.DataFrame([{
        "pct_resolved_by_titles": df["resolved_by_titles"].mean() * 100,
        "pct_resolved_only_by_structure": df["resolved_only_by_structure"].mean() * 100,
        "pct_still_ambiguous_after_C": df["still_ambiguous_after_C"].mean() * 100,
        "pct_reversed_after_titles": df["reversed_after_titles"].mean() * 100,
        "pct_reversed_after_structure": df["reversed_after_structure"].mean() * 100,
    }])
    summary.to_csv(config.TABLES_DIR / "representation_sensitivity.csv", index=False)
    print(summary.T.to_string())
    return df


if __name__ == "__main__":
    per_judge_changes()
    consensus_sensitivity()
