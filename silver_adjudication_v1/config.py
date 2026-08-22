"""Central configuration for Evidex Silver Adjudication v1."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SV_ROOT = Path(__file__).resolve().parent

# Immutable Analysis v2 / experiment inputs (read-only).
A2 = REPO_ROOT / "analysis_v2"
PAIRED_ENRICHED = A2 / "data" / "derived" / "paired_enriched.parquet"
FEVER_SOURCE = REPO_ROOT / "fever_balanced_10000_v1_source.csv"

BLINDED_DIR = SV_ROOT / "data" / "blinded"
DERIVED_DIR = SV_ROOT / "data" / "derived"
CACHE_DIR = SV_ROOT / "data" / "cache"
JUDGMENTS_DIR = SV_ROOT / "judgments"
TABLES_DIR = SV_ROOT / "tables"
FIGURES_DIR = SV_ROOT / "figures"
REPORTS_DIR = SV_ROOT / "reports"
PROMPTS_DIR = SV_ROOT / "prompts"

COHORT_PARQUET = DERIVED_DIR / "cohort.parquet"
ID_MAP_CSV = DERIVED_DIR / "id_map.csv"
FREEZE_MANIFEST = DERIVED_DIR / "freeze_manifest.json"
UNBLINDED_PARQUET = DERIVED_DIR / "silver_unblinded.parquet"

MODELS = ["gpt-5.4", "gpt-5.4-mini"]
REGRESSION = "wrong_to_correct"  # placeholder names to avoid confusion
T_REGRESSION = "correct_to_wrong"
T_RESISTANT = "wrong_to_wrong"
T_RESCUE = "wrong_to_correct"
T_ROBUST = "correct_to_correct"

JUDGES = [f"judge_{i}" for i in range(1, 6)]  # 5 isolated GLM-5.3 judges
STAGES = ["A", "B", "C"]
BATCH_SIZE = 100
MAX_RETRIES = 2

VERDICTS = ["Supported", "Refuted", "Ambiguous"]
SUFFICIENCY = [
    "clearly_sufficient", "probably_sufficient", "partial_or_ambiguous",
    "probably_insufficient", "clearly_insufficient",
]
ISSUE_FLAGS = [
    "none", "possible_missing_title_context", "possible_coreference_or_entity_resolution",
    "possible_missing_surrounding_context", "multi_sentence_integration",
    "numerical_or_temporal_reasoning", "negation_or_scope", "entity_or_attribute_confusion",
    "partial_warrant", "apparent_internal_contradiction", "other",
]
RESOLVER_OUTCOMES = ["Supported", "Refuted", "Ambiguous", "Unresolved"]
RESOLVER_DISAGREEMENT_TYPES = [
    "judge_error", "partial_warrant", "representation_sensitive",
    "semantic_conflict", "unresolved",
]

# Cohort sizing (approved plan): all 226 regressions, resistant cohort,
# matched rescue/robust controls (~250 each). Target ~1,100 unique claims.
N_RESCUE_CONTROLS = 250
N_ROBUST_CONTROLS = 250

# Blinding: columns judges must NEVER see.
PROHIBITED_FIELDS = [
    "gold_label", "true_label", "gpt54_claim_only_pred", "gpt54_evidence_pred",
    "gpt54mini_claim_only_pred", "gpt54mini_evidence_pred",
    "gpt-5.4_claim_only_correct", "gpt-5.4_evidence_correct", "gpt-5.4_transition",
    "gpt-5.4-mini_claim_only_correct", "gpt-5.4-mini_evidence_correct",
    "gpt-5.4-mini_transition", "agree_co", "agree_ev", "agree_transition",
    "cohort", "cohort_type", "transition", "nli", "nli2", "cosine",
    "semantic_outlier", "weakly_warranted", "priority", "diagnostic",
]

RANDOM_SEED = 20260822
BOOTSTRAP_ITERS = 2000


def ensure_dirs():
    for d in (BLINDED_DIR, DERIVED_DIR, CACHE_DIR, TABLES_DIR, FIGURES_DIR,
              REPORTS_DIR, *[JUDGMENTS_DIR / f"stage_{s.lower()}" for s in STAGES],
              JUDGMENTS_DIR / "resolver"):
        d.mkdir(parents=True, exist_ok=True)
