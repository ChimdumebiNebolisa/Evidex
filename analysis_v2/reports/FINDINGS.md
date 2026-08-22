# Evidex Analysis v2 — Findings

## Executive summary

We re-analyzed the existing 40,000-observation Evidex experiment (10,000 balanced
FEVER claims; GPT-5.4 and GPT-5.4-mini; claim-only vs claim+gold-evidence) with a
matched four-way transition decomposition, statistical testing, linguistic and
evidence-structure features, local semantic embeddings, a local NLI diagnostic,
and interpretable predictive models. The headline aggregates (evidence improves
accuracy by +7.35 / +10.87 pp) hide a small but sharply structured regression
cohort: 1.15% (GPT-5.4) and 1.51% (mini) of claims that were correct without
evidence become wrong with it. These regressions are not random noise — they
concentrate overwhelmingly in claims whose gold evidence an independent local NLI
model rates as weakly warranting the FEVER label.

## Strongest findings

Tags: **[C]** = confirmatory (pre-specified paired tests/CIs), **[E]** = exploratory
(conditioning, diagnostics, prediction; BH-corrected where noted).

1. **[C] Evidence-induced regressions are real but rare, and highly non-random.**
   GPT-5.4: 115/10,000 regressions (1.15%, bootstrap 95% CI [0.95, 1.36]);
   850 rescues (8.5%, CI [7.92, 9.04]); McNemar χ²=558.3, p≈2e-123.
   Mini: 151 regressions (1.51%, CI [1.28, 1.75]); 1,238 rescues (12.4%,
   CI [11.73, 13.00]); χ²=849.1, p≈1e-186. Rescue rates of claim-only errors:
   75.2% (GPT-5.4) and 80.8% (mini). Unique claims: 226 regress for at least
   one model, 40 for both, 186 for exactly one (see
   `tables/unique_claim_counts.csv`; counts are claims, never model-observations).

2. **[E] A local NLI diagnostic separates the regression cohort sharply — and a
   second, architecturally different NLI model replicates the pattern.**
   Disagreement between the primary local NLI model (nli-deberta-v3-small,
   diagnostic only) and the FEVER label: 22.6% among robust successes, 31.5%
   among GPT-5.4 rescues, 75.8% among evidence-resistant failures, and
   **74.8% among GPT-5.4 regressions (75.5% "weakly warranted")**; mini:
   76.8% / 75.5%. A second local model (distilbert-base-uncased-mnli; different
   architecture and training) reproduces the ordering: robust 26.2%,
   GPT-5.4 rescues 38.1%, resistant 74.4%, regressions 67.8% (GPT-5.4) and
   73.5% (mini). The two diagnostics agree on the disagreement flag for 84.3%
   of claims (overall disagreement 25.5% vs 29.0%). Weakly-warranted claims
   (n=2,462) also have lower claim-only accuracy (81.0% vs 88.7% for GPT-5.4),
   i.e., the NLI weakness signal marks genuinely hard claims, not model quirks.

3. **[E] Label asymmetry is model-dependent; the GPT-5.4 effect survives
   covariate conditioning.**
   Raw evidence-condition error directions: GPT-5.4 makes 238 Supported→Refuted
   vs 158 Refuted→Supported errors (binomial p=6.8e-5); mini reverses the
   direction (201 vs 245, p=0.042). GPT-5.4's Supported-skew persists in a
   logistic model of error incidence conditioned on 18 claim/evidence covariates
   (coef on Refuted −0.54, CI [−0.76, −0.31], p=3e-6); mini's reversed asymmetry
   is much weaker after conditioning (coef +0.14, p<1e-6 but with numerical
   instability in the CI). Regression counts by label: GPT-5.4 regresses on 88
   Supported vs 27 Refuted claims (χ²=31.7, p=1.8e-8); mini shows no regression
   asymmetry (74 vs 77, p=0.87).

4. **[C] Cross-model concordance is high, and evidence increases agreement.**
   Prediction agreement rises from 89.3% (κ=0.786) without evidence to 97.2%
   (κ=0.944) with it. 40 claims regress for both models; 186 regress for
   exactly one. 87.3% of claims share the same transition class. Model
   transition-rate differences (paired McNemar on discordant claims): rescue
   850 vs 1,238 (χ²=145.1, p=2.0e-33); regression 115 vs 151 (χ²=6.59, p=0.010);
   resistant 281 vs 295 (χ²=0.83, p=0.36).

5. **[E] Failure structure is predictable — but the predictability comes mostly
   from the local NLI features, not surface features.**
   With NLI probability and cosine features included, claim-level GroupKFold
   ROC-AUC is 0.60–0.72 for rescue/regression and 0.84 for resistant (shallow
   tree). With surface features only (lengths, overlap, counts, structure),
   regression AUC drops to ~0.53–0.60 across models. PR-AUCs remain low for the
   rare classes (regression PR-AUC ≤ 0.07). Interpretation: what predicts
   regressions is the semantic warrant of the claim-evidence pair, not its
   surface form — consistent with finding 2. A duplicate-aware regrouping
   (grouping exact-duplicate claim texts so identical claims cannot straddle
   folds) changes AUCs by at most 0.041 (`tables/leakage_duplicate_aware_cv.csv`),
   so duplicate leakage does not explain these results.

6. **Evidence-resistant failures share structure with regressions.**
   Both wrong-with-evidence cohorts (resistant and regression) show ~75% NLI
   disagreement vs ~23% for robust, ~13% multi-sentence evidence vs ~9%
   (BH-corrected Kruskal-Wallis p<0.05 for evidence-set size, sentence and page
   counts, lengths, claim numbers/dates, entity counts, numerical overlap,
   lexical overlap, and all NLI scores).

## Data-quality diagnostics

- 271 claims (126 groups) are exact text duplicates of another claim in the
  balanced sample; 0 near-duplicate pairs (Jaccard ≥ 0.85) beyond those.
- 561 unique claims are failed by at least one model with evidence; 281 by both
  (same number as shared same-direction failures, since both models only ever
  err by flipping to the opposite label); 281 is a claim count, not an
  observation count.
- 421 claims are semantic outliers (low claim–evidence cosine similarity).

## Verification and audit trail (adversarial pass)

- `tables/verification.md`: every headline number recomputed independently
  from the canonical paired Parquet and raw results CSV — 69/69 checks PASS.
- `tables/leakage_audit.md`: one row per claim; no outcome-derived predictors;
  duplicate-aware CV changes AUCs by ≤ 0.041.
- `tables/transition_four_way_tables.csv`: complete 2×2 transition tables with
  margins, overall and by gold label, for both models.
- `tables/unique_claim_counts.csv`: unique-claim cohort sizes (no
  claim/observation mixing).
- Model-comparison p-values were corrected from independent-samples χ² to
  paired McNemar during the adversarial pass (conclusions unchanged; see
  ANALYSIS_LOG.md).

## Negative / null findings

- **Semantic similarity barely separates regressions**: mean cosine 0.589
  (regressions) vs 0.613 (all); low-similarity (<0.35) rate is 9.6% vs 7.5%
  baseline. Semantic similarity is a weak diagnostic for regressions.
- **Evidence-set structure effects are small and inconsistent in direction**
  across models (set size, sentence count, page count significant only for
  mini after BH correction).
- **Numerical/comparative and date features** differ across transition classes
  overall (claim_numbers, claim_dates: BH p<1e-30 for mini) but with small
  effect sizes; they do not specifically mark regressions.
- **Clustering** of the GPT-5.4 failure-cohort embeddings produced 4 stable
  clusters (mean ARI 1.0 across seeds) but with 53% noise; we treat the
  cluster structure as only weakly informative and do not interpret it as
  failure subtypes.

## What these results do NOT establish

- No causal claim: all feature associations are observational.
- The NLI model is not ground truth; "weakly warranted" flags candidate
  ambiguity, not annotation error. No FEVER label is declared wrong.
- Regressions cannot be attributed to specific model internals — the original
  runs recorded labels only, so confidence/calibration cannot be reconstructed.
- The model-vs-representation-vs-benchmark decomposition is supported only as
  a hypothesis generator: the NLI concentration suggests a large share of
  regressions involve claim-evidence relationships that are semantically
  contestable (representation/benchmark side), but human review of the
  exported 250-claim cohort is required.

## Robustness labels

- Confirmatory **[C]** (pre-specified in the master protocol): transition
  counts, McNemar tests, bootstrap CIs, label asymmetry contrasts, kappa,
  paired model-difference McNemar.
- Exploratory **[E]**: NLI diagnostics (both models), feature associations,
  conditioned logistic models, predictive models, clustering (BH correction
  applied where noted). All exploratory findings should be treated as
  hypothesis-generating; only the tagged confirmatory family was pre-specified.
