"""Local configuration for the Claude residual Stage C panel."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SV_ROOT = ROOT.parent
REPO_ROOT = SV_ROOT.parent
CURSOR_ROOT = SV_ROOT / "cursor_panel"
PROMPTS_DIR = SV_ROOT / "prompts"

DATA_DIR = ROOT / "data"
JUDGMENTS_DIR = ROOT / "judgments"
FREEZES_DIR = ROOT / "freezes"
TABLES_DIR = ROOT / "tables"
FIGURES_DIR = ROOT / "figures"
REPORTS_DIR = ROOT / "reports"
CACHE_DIR = ROOT / "cache"
PACKETS_DIR = CACHE_DIR / "packets"

BLINDED_JSONL = DATA_DIR / "blinded_stage_c.jsonl"
ID_MAP_CSV = DATA_DIR / "id_map.csv"
RESIDUAL_SOURCE = DATA_DIR / "residual_source.json"
FREEZE_JUDGES = FREEZES_DIR / "freeze_judgments.json"
FREEZE_MANIFEST = FREEZES_DIR / "freeze_manifest.json"
UNBLINDED_PARQUET = FREEZES_DIR / "claude_unblinded.parquet"

CURSOR_CONSENSUS_C = CURSOR_ROOT / "freezes" / "consensus_stage_C.parquet"
CURSOR_UNBLINDED = CURSOR_ROOT / "freezes" / "silver_unblinded.parquet"
SHARED_STAGE_C = SV_ROOT / "data" / "blinded" / "stage_c.jsonl"
COHORT_PARQUET = SV_ROOT / "data" / "derived" / "cohort.parquet"
ID_MAP_SHARED = SV_ROOT / "data" / "derived" / "id_map.csv"
PAIRED_ENRICHED = REPO_ROOT / "analysis_v2" / "data" / "derived" / "paired_enriched.parquet"

LOCKED_MODEL = "claude-opus-5-thinking-high"
EXPECTED_RESIDUAL_N = 231
BATCH_SIZE = 77
RANDOM_SEED = 20260823
BOOTSTRAP_ITERS = 2000
STAGE = "C"
JUDGES = [f"claude_judge_{i}" for i in range(1, 6)]
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
ALLOWED_ITEM_KEYS = {
    "item_id", "claim", "evidence_sentences", "page_titles", "structured_evidence",
}
PROHIBITED_FIELDS = [
    "gold_label", "true_label", "gpt54_claim_only_pred", "gpt54_evidence_pred",
    "gpt54mini_claim_only_pred", "gpt54mini_evidence_pred",
    "gpt-5.4_claim_only_correct", "gpt-5.4_evidence_correct", "gpt-5.4_transition",
    "gpt-5.4-mini_claim_only_correct", "gpt-5.4-mini_evidence_correct",
    "gpt-5.4-mini_transition", "agree_co", "agree_ev", "agree_transition",
    "cohort", "cohort_type", "transition", "nli", "nli2", "cosine",
    "semantic_outlier", "weakly_warranted", "priority", "diagnostic",
    "cursor", "grok", "glm", "residual", "silver_taxonomy", "consensus",
    "unresolved", "regression", "resistant", "rescue", "robust",
]
PROHIBITED_TEXT = [
    "cursor", "grok", "glm", "residual", "silver_taxonomy", "fever gold",
    "gpt-5.4", "gpt-5.4-mini", "regression", "resistant", "rescue", "robust",
    "nli", "difficult subset", "prior judge",
]
WEAK_SUFF = {"partial_or_ambiguous", "probably_insufficient", "clearly_insufficient"}
AGREEMENT_FAMILY_LABEL = "within-Claude-panel"


def load_lock() -> dict:
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    if cfg.get("model") != LOCKED_MODEL or cfg.get("required_model") != LOCKED_MODEL:
        raise SystemExit("Claude model lock mismatch; stop, do not substitute")
    inf = cfg.get("inference", {})
    if inf.get("auto") or inf.get("inherit"):
        raise SystemExit("Claude panel forbids Auto/inherit")
    return cfg


def require_locked_model(claimed: str) -> None:
    if claimed != LOCKED_MODEL:
        raise SystemExit(
            f"model substitution forbidden: claimed={claimed!r} locked={LOCKED_MODEL!r}"
        )


def ensure_dirs() -> None:
    for d in (DATA_DIR, FREEZES_DIR, TABLES_DIR, FIGURES_DIR, REPORTS_DIR,
              CACHE_DIR, PACKETS_DIR, JUDGMENTS_DIR / "resolver",
              *[JUDGMENTS_DIR / j for j in JUDGES]):
        d.mkdir(parents=True, exist_ok=True)
