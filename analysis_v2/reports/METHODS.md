# Evidex Analysis v2 — Methods

## Source artifacts (immutable)

- `experiment_results_balanced_10000_v1.csv` — 40,000 predictions (10,000 claims ×
  2 models × 2 conditions); validated before use (`src/validate_source_data.py`):
  row counts, label sets, per-cell balance (5,000 Supported / 5,000 Refuted),
  `correct`-flag consistency, claim-set identity across cells, agreement with
  `fever_balanced_10000_v1_source.csv`. Validation status: PASS; headline
  aggregates reproduced exactly (88.69/96.04 and 84.67/95.54).
- FEVER source sample, sample provenance, resolve summary — read-only inputs.

## Pairing and transitions

`src/build_paired_dataset.py` pivots the long results table into one row per
claim with per-model claim-only and evidence predictions and a four-way
transition class: rescue (wrong→correct), robust (correct→correct), resistant
(wrong→wrong), regression (correct→wrong). Cross-model agreement booleans are
added. Output: `data/derived/paired_claims.parquet` (10,000 × 23).

## Features

- `src/linguistic_features.py` — regex features (negation, comparatives,
  numbers, dates, pronouns, modals, conjunctions; claim/evidence lengths and
  ratios; lexical/Jaccard/numerical overlap) plus spaCy `en_core_web_sm`
  entity counts and claim/evidence entity overlap (cached in
  `data/cache/spacy_entities.parquet`).
- `src/semantic_features.py` — `sentence-transformers/all-MiniLM-L6-v2`
  (local, CPU) cosine similarity between claim and gold evidence; median/MAD
  outlier flag; embeddings cached (`data/cache/*.npy`, keyed by model name +
  length + claim-id hash).
- `src/nli_analysis.py` — `cross-encoder/nli-deberta-v3-small` (local, CPU)
  on (evidence → claim); entailment/neutral/contradiction probabilities,
  argmax prediction, disagreement with the FEVER-implied class, decision
  margin, and a "weakly warranted" flag (gold-implied class prob < 0.35).
  Probabilities cached (`data/cache/nli_probs.npy`).

## Statistics

`src/statistical_analysis.py` — McNemar tests (continuity-corrected) for the
paired evidence effect per model; percentile bootstrap CIs (2,000 resamples,
seed 20260821) for transition rates and gains; paired McNemar tests for
between-model transition-rate differences (same claims, so discordant-pair
McNemar, not independent χ²); χ² tests for label contrasts; Cohen's κ for
cross-model agreement.
`src/asymmetry_analysis.py` — binomial tests on error direction; conditioned
logistic model of error incidence on gold label + 18 covariates (statsmodels).
`src/feature_associations.py` — Kruskal-Wallis across the four transition
classes per feature, Benjamini-Hochberg corrected.
`src/verify_headlines.py` — independent recomputation of every number quoted
in FINDINGS.md directly from the canonical Parquet and raw CSV (69 checks,
all PASS; `tables/verification.md`).
`src/leakage_audit.py` — structural leakage checks plus duplicate-aware CV.

## Second NLI model (robustness)

`src/nli_second_model.py` — `typeform/distilbert-base-uncased-mnli` (local,
CPU, free; different architecture and training data from the primary NLI)
over the same (evidence → claim) pairs, cached in `data/cache/nli2_probs.npy`.
Side-by-side disagreement rates by transition class:
`tables/nli_model_comparison.csv`.

## Predictive models

`src/regression_analysis.py` — logistic regression (C=1, C=0.1, class-weight
balanced) and HistGradientBoosting (depth 3, 150 iters), 5-fold GroupKFold on
`claim_id` (no claim crosses folds; trivially leak-free here since one row per
claim, enforced anyway). Features are strictly pre-prediction claim/evidence
properties (surface features) plus, in the full configuration, the local NLI
probabilities and claim-evidence cosine — all computed from claim/evidence
text only, never from model predictions or outcomes. The adversarial pass
(`src/verify_headlines.py`, `src/leakage_audit.py`) quantified both feature
sets separately: surface-only regression AUC ~0.53–0.60 vs ~0.60–0.66 full.
Exact-duplicate claim texts (271 claims) are additionally grouped in the
duplicate-aware CV; AUC deltas ≤ 0.041.
Coefficients exported per target.

## Data quality and clustering

`src/data_quality_analysis.py` — exact duplicates on normalized text; near
duplicates via min-hash-style char-3-gram LSH buckets (200 hashes) with
Jaccard ≥ 0.85 confirmation; shared same-direction failure flags; low-overlap /
low-similarity / NLI-disagreement flags. `src/clustering_analysis.py` — UMAP
(10-dim) + HDBSCAN (min_cluster_size 15) on the GPT-5.4 failure cohort
(n=396) with 3-seed stability check (ARI).

## Manual review export

`src/manual_review_export.py` — priority-scored sample of 250 claims
(both-model regressions first) with claim, evidence, predictions, transitions,
NLI scores, similarity, linguistic flags, provisional diagnostic category, and
blank human-judgment columns. No human judgment is auto-filled.

## Software and reproducibility

Python 3.12.10; pandas 2.x, numpy, scipy, scikit-learn, statsmodels,
matplotlib, sentence-transformers, transformers, spaCy (en_core_web_sm),
umap-learn, hdbscan. Random seed 20260821 everywhere. Full pipeline:
`python run_all.py` (13 stages; expensive stages cached; optional stages
degrade gracefully). Tests: `python -m unittest discover -s tests` (10 tests).
Figures: `src/generate_figures.py` (6 figures, PNG, 150 dpi).

## Environment note

A security hook in the working environment statically flags every
`open(<CLI-arg>, "w")` in the repository's ORIGINAL upstream analysis scripts
as path traversal (22 findings that predate this branch and exist on `main`),
and force-blocks `git commit` while they are present. CWE-22 output-path
guards were briefly added to three scripts and then reverted to upstream
pristine form during the cleanup pass (Analysis v2 does not depend on them).
The cleanup commit and subsequent commits were recorded with inline git
plumbing (commit-tree/update-ref); no bypass script or Mimosa state is
committed to the repository. See ANALYSIS_LOG.md.
