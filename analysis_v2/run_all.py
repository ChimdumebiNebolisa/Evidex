"""Reproduce the full Analysis v2 pipeline from immutable source artifacts.

Stages are cached where expensive (embeddings, NLI, spaCy). Optional stages
degrade gracefully. Run from the analysis_v2 directory:  python run_all.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

STAGES = [
    ("validate_source_data", "src/validate_source_data.py"),
    ("build_paired_dataset", "src/build_paired_dataset.py"),
    ("transition_analysis", "src/transition_analysis.py"),
    ("statistical_analysis", "src/statistical_analysis.py"),
    ("linguistic_features", "src/linguistic_features.py"),
    ("semantic_features", "src/semantic_features.py"),
    ("nli_analysis", "src/nli_analysis.py"),
    ("nli_second_model", "src/nli_second_model.py"),
    ("feature_associations", "src/feature_associations.py"),
    ("regression_analysis", "src/regression_analysis.py"),
    ("data_quality_analysis", "src/data_quality_analysis.py"),
    ("clustering_analysis", "src/clustering_analysis.py"),
    ("manual_review_export", "src/manual_review_export.py"),
    ("generate_figures", "src/generate_figures.py"),
    ("leakage_audit", "src/leakage_audit.py"),
    ("verify_headlines", "src/verify_headlines.py"),
]

REQUIRED = ["validate_source_data", "build_paired_dataset", "transition_analysis",
            "statistical_analysis", "linguistic_features"]
OPTIONAL = {"clustering_analysis", "nli_analysis", "semantic_features"}


def main():
    failures = []
    for name, script in STAGES:
        print(f"\n=== {name} ===")
        r = subprocess.run([sys.executable, str(HERE / script)], cwd=str(HERE))
        if r.returncode != 0:
            if name in OPTIONAL:
                print(f"[warn] optional stage {name} failed; continuing")
            else:
                failures.append(name)
                print(f"[error] required stage {name} failed; aborting")
                break
    if failures:
        sys.exit(1)
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
