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

1. **Evidence-induced regressions are real but rare, and highly non-random.**
   GPT-5.4: 115/10,000 regressions (1.15%, bootstrap 95% CI [0.95, 1.36]);
   850 rescues (8.5%, CI [7.92, 9.04]); McNemar χ²=558.3, p≈2e-123.
   Mini: 151 regressions (1.51%, CI [1.28, 1.75]); 1,238 rescues (12.4%,
   CI [11.73, 13.00]); χ²=849.1, p≈1e-186. Rescue rates of claim-only errors:
   75.2% (GPT-5.4) and 80.8% (mini).

2. **A local NLI diagnostic separates the regression cohort sharply.**
   The share of claims where the local NLI model (nli-deberta-v3-small, run
   locally, diagnostic only) disagrees with the FEVER label is 22.6% among robust
   successes, 31.5% among rescues, 75.8% among evidence-resistant failures, and
   **74.8% among GPT-5.4 regressions (75.5% "weakly warranted", i.e., the NLI
   probability of the gold-implied class < 0.35)**. The same pattern holds for
   mini (76.8% / 75.5%). Weakly-warranted claims (n=2,462) also have lower
   claim-only accuracy (81.0% vs 88.7% for GPT-5.4), i.e., the NLI weakness
   signal marks genuinely hard claims, not model quirks.

3. **Label asymmetry is model-dependent and survives covariate conditioning
   for GPT-5.4 only.**
   Raw evidence-condition error directions: GPT-5.4 makes 238 Supported→Refuted
   vs 158 Refuted→Supported errors (binomial p=6.8e-5); mini reverses the
   direction (201 vs 245, p=0.042). GPT-5.4's Supported-skew persists in a
   logistic model of error incidence conditioned on 18 claim/evidence covariates
   (coef on Refuted −0.54, CI [−0.76, −0.31], p=3e-6); mini's reversed asymmetry
   is much weaker after conditioning (coef +0.14, p<1e-6 but with numerical
   instability in the CI). Regression counts by label: GPT-5.4 regresses on 88
   Supported vs 27 Refuted claims (χ²=31.7, p=1.8e-8); mini shows no regression
   asymmetry (74 vs 77, p=0.87).

4. **Cross-model concordance is high, and evidence increases agreement.**
   Prediction agreement rises from 89.3% (κ=0.786) without evidence to 97.2%
   (κ=0.944) with it. 40 claims regress for both models; 186 regress for
   exactly one. 79.8% of claims share the same transition class.

5. **Failure structure is predictable from pre-prediction features, modestly.**
   GroupKFold (claim-level) out-of-sample ROC-AUC for predicting transitions:
   rescue 0.67–0.72; regression 0.60–0.71; resistant 0.59 (logistic) but 0.84
   (shallow gradient-boosted tree) for both models. PR-AUCs remain low for the
   rare classes (regression PR-AUC ≤ 0.07), so these are not deployable
   classifiers — the signal exists but is weak.

6. **Evidence-resistant failures share structure with regressions.**
   Both wrong-with-evidence cohorts (resistant and regression) show ~75% NLI
   disagreement vs ~23% for robust, ~13% multi-sentence evidence vs ~9%
   (BH-corrected Kruskal-Wallis p<0.05 for evidence-set size, sentence and page
   counts, lengths, claim numbers/dates, entity counts, numerical overlap,
   lexical overlap, and all NLI scores).

## Data-quality diagnostics

- 271 claims (126 groups) are exact text duplicates of another claim in the
  balanced sample; 0 near-duplicate pairs (Jaccard ≥ 0.85) beyond those.
- 281 claims are failed by both models in the same direction with evidence —
  a benchmark-ambiguity candidate cohort, not proof of annotation error.
- 421 claims are semantic outliers (low claim–evidence cosine similarity).

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

- Confirmatory (pre-specified in the master protocol): transition counts,
  McNemar tests, bootstrap CIs, label asymmetry contrasts, kappa.
- Exploratory: feature associations, conditioned logistic models, predictive
  models, clustering, NLI diagnostics (BH correction applied where noted).
