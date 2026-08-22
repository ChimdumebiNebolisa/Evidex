"""Central configuration for Evidex Analysis v2."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
A2_ROOT = Path(__file__).resolve().parent

DATASET_TAG = "balanced_10000_v1"

# Immutable source artifacts (never written to).
SOURCE_RESULTS = REPO_ROOT / f"experiment_results_{DATASET_TAG}.csv"
SOURCE_RUNS = REPO_ROOT / f"experiment_runs_{DATASET_TAG}.csv"
SOURCE_FEVER = REPO_ROOT / f"fever_{DATASET_TAG}_source.csv"
SOURCE_PROVENANCE = REPO_ROOT / f"sample_provenance_{DATASET_TAG}.csv"
SOURCE_RESOLVE_SUMMARY = REPO_ROOT / f"resolve_summary_{DATASET_TAG}.json"

# Derived outputs.
DERIVED_DIR = A2_ROOT / "data" / "derived"
CACHE_DIR = A2_ROOT / "data" / "cache"
TABLES_DIR = A2_ROOT / "tables"
FIGURES_DIR = A2_ROOT / "figures"
REPORTS_DIR = A2_ROOT / "reports"

PAIRED_PARQUET = DERIVED_DIR / "paired_claims.parquet"
ENRICHED_PARQUET = DERIVED_DIR / "paired_enriched.parquet"
MANUAL_REVIEW_CSV = DERIVED_DIR / "manual_review_cohort.csv"

MODELS = ["gpt-5.4", "gpt-5.4-mini"]
CONDITIONS = ["claim_only", "claim_plus_evidence"]
LABELS = ["Supported", "Refuted"]

# Four-way transition classes between claim_only -> claim_plus_evidence.
TRANSITION_RESCUE = "wrong_to_correct"          # evidence rescue
TRANSITION_ROBUST = "correct_to_correct"        # robust success
TRANSITION_RESISTANT = "wrong_to_wrong"         # evidence-resistant failure
TRANSITION_REGRESSION = "correct_to_wrong"      # evidence-induced regression

RANDOM_SEED = 20260821
BOOTSTRAP_ITERS = 2000

# Local model choices (CPU-friendly).
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
SPACY_MODEL = "en_core_web_sm"


def ensure_dirs():
    for d in (DERIVED_DIR, CACHE_DIR, TABLES_DIR, FIGURES_DIR, REPORTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
