# Evidex Analysis v2 — Next Experiments (ranked)

Ranked by scientific value × directness of mechanism test; inference needs noted.

## 1. Human adjudication + controlled representation rerun of the regression cohort
**(driven by the strongest v2 pattern: ~75% of regressions are NLI-weakly-warranted)**

- Step 1 (no inference cost): expert-annotate the exported 250-claim manual
  review cohort (`data/derived/manual_review_cohort.csv`) into the provisional
  taxonomy (model-utilization vs representation vs benchmark ambiguity).
- Step 2 (paid API, small): rerun only the ~266 regression/resistant claims
  under 3 evidence serializations — sentence-only (current), sentences +
  page titles, full evidence set (not just shortest complete set) — predicting
  label + confidence + evidence-quote requirement.
- Directly tests whether the sentence-only, shortest-set representation
  contributes to regressions, separating representation failure from model
  failure. Cost: a few hundred paid calls, three arms.
- Decisive because v2 shows regressions concentrate in weakly-warranted
  claim-evidence pairs; if titles/full sets fix a large share, representation
  is implicated; if not, model utilization.

## 2. NLI-guided relabeling audit of the weakly-warranted cohort (local, free)

Have annotators blind-rate the 2,462 weakly-warranted claims (local NLI
already computed) against FEVER labels; estimate the ambiguity rate of the
benchmark conditional on NLI weakness. No inference cost; quantifies the
benchmark-ambiguity share of the decomposition.

## 3. Confidence-logged rerun of transitions (paid API, medium)

Rerun both conditions on a 2,000-claim stratified sample with logprobs/verbalized
confidence to test whether regressions are low-confidence flips (stochastic)
or high-confidence overrides (evidence-induced belief change). Cannot be done
locally; original runs stored labels only.

## 4. Model-family diversity check (paid API, medium)

One non-GPT model (e.g., a strong open model via local inference, or another
API family) on the same 2,000-claim sample to test whether the Supported-skew
asymmetry and the 40 shared regressions are family artifacts. Partially
feasible locally with an open-weights model of comparable strength.

## 5. Causal context-position/length perturbations (paid API or local)

Standard robustness battery on the regression cohort (evidence order
shuffling, sentence truncation, title injection) — lower priority: overlaps
heavily with established literature (see NOVELTY_BOUNDARIES.md).
