"""Local configuration for the Claude full-regression A->B->C panel.

Mirrors ``claude_residual_panel/src/panel_config.py``; the differences are the
cohort (all 226 unique GPT regressions instead of the 231 Grok Stage C
residuals) and the fact that all three disclosure stages are run.

Shared, immutable inputs (cohort manifest, blinded stage files, rubric) are
read from ``silver_adjudication_v1/`` and never written.
"""
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
DISCARDED_DIR = CACHE_DIR / "discarded"

# Judge-facing I/O lives under a neutrally-named directory. Judges are given
# only paths inside it, so no path component can hint that the cohort is a
# regression set (the panel directory name would otherwise leak that).
BLIND_IO = SV_ROOT / "blind_io"
BLIND_IO_REL = "silver_adjudication_v1/blind_io"

STAGES = ["A", "B", "C"]
STAGE_PREDECESSOR = {"B": "A", "C": "B"}

ID_MAP_CSV = DATA_DIR / "id_map.csv"
COHORT_SOURCE = DATA_DIR / "cohort_source.json"
UNBLINDED_PARQUET = FREEZES_DIR / "claude_full_unblinded.parquet"
FREEZE_MANIFEST = FREEZES_DIR / "freeze_manifest.json"

# Shared immutable inputs (read-only).
COHORT_PARQUET = SV_ROOT / "data" / "derived" / "cohort.parquet"
ID_MAP_SHARED = SV_ROOT / "data" / "derived" / "id_map.csv"
PROVIDER_FILTERED = SV_ROOT / "data" / "derived" / "provider_filtered.json"
SHARED_BLINDED = {s: SV_ROOT / "data" / "blinded" / f"stage_{s.lower()}.jsonl" for s in STAGES}
CURSOR_UNBLINDED = CURSOR_ROOT / "freezes" / "silver_unblinded.parquet"
CURSOR_CONSENSUS = {s: CURSOR_ROOT / "freezes" / f"consensus_stage_{s}.parquet" for s in STAGES}
PAIRED_ENRICHED = REPO_ROOT / "analysis_v2" / "data" / "derived" / "paired_enriched.parquet"

LOCKED_MODEL = "claude-opus-5-thinking-high"
FORBIDDEN_FALLBACK_MODELS = [
    "cursor-grok-4.6-high-fast", "grok-4.6", "GLM-5.3", "auto", "inherit",
]
EXPECTED_COHORT_N = 226
EXPECTED_PER_STAGE = 1130          # 226 items x 5 judges
EXPECTED_TOTAL = 3390              # x 3 stages
BATCH_SIZE = 77                    # same batch size as the Claude residual panel
RANDOM_SEED = 20260913
BOOTSTRAP_ITERS = 2000
JUDGES = [f"claude_full_judge_{i}" for i in range(1, 6)]

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
WEAK_SUFF = {"partial_or_ambiguous", "probably_insufficient", "clearly_insufficient"}

# Progressive disclosure: exactly the fields the Cursor/Grok panel showed.
ALLOWED_ITEM_KEYS = {
    "A": {"item_id", "claim", "evidence_sentences"},
    "B": {"item_id", "claim", "evidence_sentences", "page_titles"},
    "C": {"item_id", "claim", "evidence_sentences", "page_titles", "structured_evidence"},
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
    "unresolved", "regression", "regression_type", "resistant", "rescue", "robust",
    "claim_id", "source_item_id",
]
PROHIBITED_TEXT = [
    "cursor", "grok", "glm", "residual", "silver_taxonomy", "fever gold",
    "gpt-5.4", "gpt-5.4-mini", "regression", "resistant", "rescue", "robust",
    "nli", "difficult subset", "prior judge", "utilization failure",
]
AGREEMENT_FAMILY_LABEL = "within-Claude-panel"


def load_lock() -> dict:
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    if cfg.get("model") != LOCKED_MODEL or cfg.get("required_model") != LOCKED_MODEL:
        raise SystemExit("Claude model lock mismatch; stop, do not substitute")
    inf = cfg.get("inference", {})
    if inf.get("auto") or inf.get("inherit"):
        raise SystemExit("Claude panel forbids Auto/inherit routing")
    if inf.get("web_browse") or inf.get("external_retrieval"):
        raise SystemExit("Claude panel forbids browsing/external retrieval")
    if cfg.get("expected_cohort_n") != EXPECTED_COHORT_N:
        raise SystemExit("config expected_cohort_n disagrees with panel_config")
    return cfg


def require_locked_model(claimed: str) -> None:
    if claimed in FORBIDDEN_FALLBACK_MODELS or claimed != LOCKED_MODEL:
        raise SystemExit(
            f"model substitution forbidden: claimed={claimed!r} locked={LOCKED_MODEL!r}; "
            "stop rather than substituting"
        )


def stage_blinded(stage: str) -> Path:
    return DATA_DIR / f"blinded_stage_{stage.lower()}.jsonl"


def stage_judgments_dir(stage: str) -> Path:
    return JUDGMENTS_DIR / f"stage_{stage.lower()}"


def stage_packets_dir(stage: str) -> Path:
    """Judge-facing packet directory (neutral path)."""
    return BLIND_IO / "packets" / f"stage_{stage.lower()}"


def stage_inbox_dir(stage: str) -> Path:
    """Judge-facing output directory (neutral path); ingested into judgments/."""
    return BLIND_IO / "inbox" / f"stage_{stage.lower()}"


def stage_packets_rel(stage: str) -> str:
    return f"{BLIND_IO_REL}/packets/stage_{stage.lower()}"


def stage_inbox_rel(stage: str) -> str:
    return f"{BLIND_IO_REL}/inbox/stage_{stage.lower()}"


def stage_freeze(stage: str) -> Path:
    return FREEZES_DIR / f"freeze_stage_{stage}.json"


def consensus_path(stage: str) -> Path:
    return FREEZES_DIR / f"consensus_stage_{stage}.parquet"


def ensure_dirs() -> None:
    for d in (DATA_DIR, FREEZES_DIR, TABLES_DIR, FIGURES_DIR, REPORTS_DIR,
              CACHE_DIR,
              *[stage_judgments_dir(s) for s in STAGES],
              *[stage_packets_dir(s) for s in STAGES],
              *[stage_inbox_dir(s) for s in STAGES]):
        d.mkdir(parents=True, exist_ok=True)


def blinding_text_errors(text: str) -> list[str]:
    """Tokens that must never appear in judge-facing metadata."""
    low = text.lower()
    return [t for t in PROHIBITED_TEXT if t in low]
