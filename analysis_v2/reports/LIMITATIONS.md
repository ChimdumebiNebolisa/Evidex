# Evidex Analysis v2 — Limitations

- **FEVER's age and characteristics**: Wikipedia-based, 2017-era claims,
  entity-centric, written from evidence; not representative of modern
  misinformation. The binary Supported/Refuted design excludes NOT ENOUGH
  INFO, removing exactly the cases where evidence insufficiency is the label.
- **Sentence-only gold evidence**: the prompt-ready evidence is concatenated
  resolved sentences; page titles, sentence indices, and alternative evidence
  sets are dropped by the original resolver. Title-loss and multi-set effects
  can be flagged but not isolated post hoc without reruns.
- **No new controlled reruns**: everything is secondary analysis of one
  fixed set of 40,000 predictions. Mechanism claims cannot be tested
  experimentally here.
- **No original token probabilities / confidences**: the runs returned labels
  only. Model confidence, calibration, and abstention behavior cannot be
  reconstructed, and we did not fabricate any.
- **Shared model family**: both models are GPT-5.4 variants; cross-model
  concordance may reflect family-correlated errors, not independent evidence.
- **Local NLI diagnostic**: nli-deberta-v3-small is itself imperfect on
  multi-sentence Wikipedia evidence (25.5% overall disagreement with FEVER).
  It is used as an independent signal, never as ground truth; NLI-based flags
  mark candidates for review, not mislabeling.
- **Small outcome classes**: regressions (115/151) limit power for conditioned
  models; the mini conditioned-logit CI showed numerical instability
  (separation), reported as-is.
- **Exploratory multiplicity**: many feature × transition × model tests were
  run (BH correction applied in `feature_associations.csv`); uncorrected
  p-values elsewhere should be read accordingly. The analysis log records
  what was tried to reduce cherry-picking.
- **Clustering**: stable by ARI but 53% noise and no semantic validation;
  treated as uninformative rather than forced into a narrative.
- **Generalizability**: findings are about two specific models on one
  benchmark; no claim extends to other models, domains, or retrievers.
- **Observational associations only**: no causal language is warranted for
  any feature-outcome relationship reported here.
