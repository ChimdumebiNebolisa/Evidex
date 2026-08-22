"""Validate immutable source artifacts before any derived analysis.

Checks row counts, model/condition coverage, label balance, pairing
completeness, and duplicate claim_ids. Writes analysis_v2/tables/source_validation.md.
"""
import json
import sys

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def validate():
    config.ensure_dirs()
    issues = []
    df = pd.read_csv(config.SOURCE_RESULTS, dtype={"claim_id": int})
    n = len(df)
    lines = [f"# Source data validation ({config.DATASET_TAG})", "", f"Rows: {n}", ""]

    # Expected 2 models x 2 conditions x 10000 claims = 40000.
    if n != 40000:
        issues.append(f"Expected 40000 rows, found {n}")

    counts = df.groupby(["model", "condition"]).size()
    lines.append("## Rows by model x condition")
    lines.append("```")
    lines.append(counts.to_string())
    lines.append("```")
    for m in config.MODELS:
        for c in config.CONDITIONS:
            got = counts.get((m, c), 0)
            if got != 10000:
                issues.append(f"{m}/{c}: expected 10000, found {got}")

    # Label values.
    bad_labels = set(df["gold_label"].unique()) - set(config.LABELS)
    if bad_labels:
        issues.append(f"Unexpected gold labels: {bad_labels}")
    bad_pred = set(df["model_output"].unique()) - set(config.LABELS)
    if bad_pred:
        issues.append(f"Unexpected model outputs: {bad_pred}")

    # Claim balance per cell.
    lines.append("\n## Gold label balance per model x condition")
    bal = df.groupby(["model", "condition", "gold_label"]).size().unstack(fill_value=0)
    lines.append("```")
    lines.append(bal.to_string())
    lines.append("```")

    # Same claim set across all four cells.
    sets = {c: set(df[df["condition"] == c]["claim_id"]) for c in config.CONDITIONS}
    if sets[config.CONDITIONS[0]] != sets[config.CONDITIONS[1]]:
        issues.append("claim_id sets differ between conditions")
    dup = df.duplicated(subset=["claim_id", "model", "condition"]).sum()
    if dup:
        issues.append(f"{dup} duplicate (claim_id, model, condition) rows")

    # correct flag consistency.
    recon = (df["model_output"] == df["gold_label"]).astype(int)
    mism = (recon != (df["correct"] == "Yes")).sum()
    if mism:
        issues.append(f"{mism} rows where 'correct' disagrees with output==label")

    # Evidence present in evidence condition.
    ev = df[df["condition"] == "claim_plus_evidence"]
    empty_ev = ev["gold_evidence"].isna().sum() + (ev["gold_evidence"].astype(str).str.len() == 0).sum()
    if empty_ev:
        issues.append(f"{empty_ev} evidence-condition rows with empty gold_evidence")

    # Unique claims.
    lines.append(f"\nUnique claims: {df['claim_id'].nunique()}")

    # Cross-check with FEVER source.
    fever = pd.read_csv(config.SOURCE_FEVER, dtype={"claim_id": int})
    lines.append(f"FEVER source rows: {len(fever)}")
    if set(fever["claim_id"]) != sets[config.CONDITIONS[0]]:
        issues.append("claim_id set differs between results and FEVER source")
    lbl = fever.set_index("claim_id")["gold_label"]
    res_lbl = df.drop_duplicates("claim_id").set_index("claim_id")["gold_label"]
    if not lbl.reindex(res_lbl.index).equals(res_lbl):
        issues.append("gold_label mismatch between results and FEVER source")

    # Reproduce headline aggregates.
    acc = (df["model_output"] == df["gold_label"]).groupby([df["model"], df["condition"]]).mean()
    lines.append("\n## Reproduced aggregate accuracy")
    lines.append("```")
    lines.append((acc * 100).round(2).to_string())
    lines.append("```")

    status = "PASS" if not issues else "FAIL"
    lines.append(f"\n**Status: {status}**")
    if issues:
        lines.append("\n## Issues")
        lines.extend(f"- {i}" for i in issues)

    (config.TABLES_DIR / "source_validation.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Source validation: {status}")
    for i in issues:
        print(f"  - {i}")
    return issues


if __name__ == "__main__":
    sys.exit(1 if validate() else 0)
