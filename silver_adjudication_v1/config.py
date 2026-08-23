"""Central configuration for Evidex Silver Adjudication v1.

Default paths are the GLM panel. Pass ``--panel cursor`` or set
``SILVER_PANEL=cursor`` to remap outputs into ``cursor_panel/`` without
touching frozen GLM judgments. Blinded inputs and the cohort stay shared.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SV_ROOT = Path(__file__).resolve().parent
CURSOR_PANEL_ROOT = SV_ROOT / "cursor_panel"

# Immutable Analysis v2 / experiment inputs (read-only).
A2 = REPO_ROOT / "analysis_v2"
PAIRED_ENRICHED = A2 / "data" / "derived" / "paired_enriched.parquet"
FEVER_SOURCE = REPO_ROOT / "fever_balanced_10000_v1_source.csv"

# Shared across panels (never remapped).
BLINDED_DIR = SV_ROOT / "data" / "blinded"
SHARED_DERIVED_DIR = SV_ROOT / "data" / "derived"
CACHE_DIR = SV_ROOT / "data" / "cache"
PROMPTS_DIR = SV_ROOT / "prompts"
COHORT_PARQUET = SHARED_DERIVED_DIR / "cohort.parquet"
ID_MAP_CSV = SHARED_DERIVED_DIR / "id_map.csv"
PROVIDER_FILTERED = SHARED_DERIVED_DIR / "provider_filtered.json"
GLM_JUDGMENTS_DIR = SV_ROOT / "judgments"
GLM_DERIVED_DIR = SHARED_DERIVED_DIR

MODELS = ["gpt-5.4", "gpt-5.4-mini"]
REGRESSION = "wrong_to_correct"  # placeholder names to avoid confusion
T_REGRESSION = "correct_to_wrong"
T_RESISTANT = "wrong_to_wrong"
T_RESCUE = "wrong_to_correct"
T_ROBUST = "correct_to_correct"

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

N_RESCUE_CONTROLS = 250
N_ROBUST_CONTROLS = 250

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

CURSOR_LOCKED_MODEL = "cursor-grok-4.6-high-fast"

# Panel-specific (defaults = GLM). Mutated by apply_panel().
PANEL = "glm"
DERIVED_DIR = SHARED_DERIVED_DIR
JUDGMENTS_DIR = SV_ROOT / "judgments"
TABLES_DIR = SV_ROOT / "tables"
FIGURES_DIR = SV_ROOT / "figures"
REPORTS_DIR = SV_ROOT / "reports"
FREEZE_MANIFEST = DERIVED_DIR / "freeze_manifest.json"
UNBLINDED_PARQUET = DERIVED_DIR / "silver_unblinded.parquet"
JUDGES = [f"judge_{i}" for i in range(1, 6)]
PANEL_MODEL = "GLM-5.3"
LOCKED_MODEL = None
AGREEMENT_FAMILY_LABEL = "within-GLM-family"


def _glm_defaults():
    return {
        "PANEL": "glm",
        "DERIVED_DIR": SHARED_DERIVED_DIR,
        "JUDGMENTS_DIR": SV_ROOT / "judgments",
        "TABLES_DIR": SV_ROOT / "tables",
        "FIGURES_DIR": SV_ROOT / "figures",
        "REPORTS_DIR": SV_ROOT / "reports",
        "JUDGES": [f"judge_{i}" for i in range(1, 6)],
        "PANEL_MODEL": "GLM-5.3",
        "LOCKED_MODEL": None,
        "AGREEMENT_FAMILY_LABEL": "within-GLM-family",
    }


def load_cursor_lock():
    path = CURSOR_PANEL_ROOT / "config.json"
    if not path.exists():
        raise SystemExit("cursor_panel/config.json missing; refuse to run Cursor panel")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    model = cfg.get("model")
    required = cfg.get("required_model", CURSOR_LOCKED_MODEL)
    if model != required or model != CURSOR_LOCKED_MODEL:
        raise SystemExit(
            f"Cursor model lock mismatch: config model={model!r} "
            f"required={required!r} locked={CURSOR_LOCKED_MODEL!r}; stop, do not substitute"
        )
    if cfg.get("inference", {}).get("auto") or cfg.get("inference", {}).get("inherit"):
        raise SystemExit("Cursor panel forbids Auto/inherit model routing")
    return cfg


def apply_panel(name: str):
    """Remap panel-specific output paths. Shared blinded/cohort paths stay put."""
    global PANEL, DERIVED_DIR, JUDGMENTS_DIR, TABLES_DIR, FIGURES_DIR, REPORTS_DIR
    global FREEZE_MANIFEST, UNBLINDED_PARQUET, JUDGES, PANEL_MODEL, LOCKED_MODEL
    global AGREEMENT_FAMILY_LABEL
    name = (name or "glm").lower()
    if name not in ("glm", "cursor"):
        raise ValueError(f"unknown panel: {name}")
    if name == "cursor":
        lock = load_cursor_lock()
        root = CURSOR_PANEL_ROOT
        PANEL = "cursor"
        DERIVED_DIR = root / "freezes"
        JUDGMENTS_DIR = root / "judgments"
        TABLES_DIR = root / "tables"
        FIGURES_DIR = root / "figures"
        REPORTS_DIR = root / "reports"
        JUDGES = list(lock.get("judges") or [f"cursor_judge_{i}" for i in range(1, 6)])
        PANEL_MODEL = lock["model"]
        LOCKED_MODEL = lock["model"]
        AGREEMENT_FAMILY_LABEL = "within-Cursor-panel"
    else:
        d = _glm_defaults()
        PANEL = d["PANEL"]
        DERIVED_DIR = d["DERIVED_DIR"]
        JUDGMENTS_DIR = d["JUDGMENTS_DIR"]
        TABLES_DIR = d["TABLES_DIR"]
        FIGURES_DIR = d["FIGURES_DIR"]
        REPORTS_DIR = d["REPORTS_DIR"]
        JUDGES = d["JUDGES"]
        PANEL_MODEL = d["PANEL_MODEL"]
        LOCKED_MODEL = d["LOCKED_MODEL"]
        AGREEMENT_FAMILY_LABEL = d["AGREEMENT_FAMILY_LABEL"]
    FREEZE_MANIFEST = DERIVED_DIR / "freeze_manifest.json"
    UNBLINDED_PARQUET = DERIVED_DIR / "silver_unblinded.parquet"
    return PANEL


def strip_panel_argv(argv=None):
    """Return (panel_name, argv_without_panel_flags)."""
    argv = list(sys.argv if argv is None else argv)
    panel = os.environ.get("SILVER_PANEL", "glm")
    out = []
    i = 0
    while i < len(argv):
        if argv[i] == "--panel" and i + 1 < len(argv):
            panel = argv[i + 1]
            i += 2
            continue
        if argv[i].startswith("--panel="):
            panel = argv[i].split("=", 1)[1]
            i += 1
            continue
        out.append(argv[i])
        i += 1
    return panel, out


def apply_panel_from_argv(argv=None):
    panel, stripped = strip_panel_argv(argv)
    if argv is None:
        sys.argv = stripped
    apply_panel(panel)
    return panel


def require_locked_model(claimed: str):
    """Refuse a mid-experiment model substitution on the Cursor panel."""
    if PANEL != "cursor":
        return
    if claimed != LOCKED_MODEL or claimed != CURSOR_LOCKED_MODEL:
        raise SystemExit(
            f"model substitution forbidden: claimed={claimed!r} "
            f"locked={LOCKED_MODEL!r}; stop rather than substituting"
        )


def ensure_dirs():
    for d in (BLINDED_DIR, DERIVED_DIR, CACHE_DIR, TABLES_DIR, FIGURES_DIR,
              REPORTS_DIR, *[JUDGMENTS_DIR / f"stage_{s.lower()}" for s in STAGES],
              JUDGMENTS_DIR / "resolver"):
        d.mkdir(parents=True, exist_ok=True)
    if PANEL == "cursor":
        for extra in (CURSOR_PANEL_ROOT / "cache", CURSOR_PANEL_ROOT / "cache" / "packets"):
            extra.mkdir(parents=True, exist_ok=True)


apply_panel_from_argv()
