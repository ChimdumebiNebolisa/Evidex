# Evidex Analysis v2 — Novelty Boundaries

## Not novel (established in prior literature)

That retrieval/gold evidence helps on average; that context can sometimes
hurt; robustness to irrelevant or conflicting context; parametric-vs-context
knowledge conflicts; context length and position effects; perturbation
robustness in fact verification; fine-grained claim-evidence support; oracle
evidence utilization. Our aggregate results (+7.35/+10.87 pp) sit squarely
inside these known findings and are not claimed as contributions.

## What this analysis adds that appears more distinctive

1. **A matched decomposition of natural regressions under designated gold
   evidence** on a large (10k-claim, two-model) fixed-prediction corpus:
   rare (1.15–1.51%) but sharply structured, and separable from generic
   evidence-condition error by construction (correct-without-evidence is a
   within-claim control).
2. **An independent local NLI signal that marks ~75% of both regression and
   resistant-failure cohorts vs ~23% of robust successes**, while semantic
   similarity does not. The diagnostic asymmetry (NLI separates, embeddings
   do not) is, to our knowledge, not the standard reporting in
   retrieval-hurts papers, which typically manipulate context quality
   experimentally rather than characterize natural failures.
3. **Model-dependent reversal of label asymmetry** (GPT-5.4 Supported-skew
   surviving covariate conditioning; mini reversed), showing the
   Supported/Refuted error balance is a model property, not a dataset
   property.

## Boundary statement

We do not claim absolute novelty: NLI-vs-label disagreement as an ambiguity
signal is related to known label-noise work on FEVER, and regression cohorts
under oracle evidence relate to known knowledge-conflict findings. The
contribution is the specific, statistically tested decomposition on natural
(not perturbed) failures with a within-claim control, not any single
component. No literature search was performed within this task; novelty
claims are bounded accordingly and require a related-work pass before
publication.
