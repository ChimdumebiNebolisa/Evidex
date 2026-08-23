# Limitations — Claude residual Stage C panel

- **Not human ground truth.** Five Claude Opus judges are still automated
  generative judges. Cross-family agreement is stronger than same-family
  agreement, not a substitute for expert adjudication.
- **Two families, not a survey of models.** Cursor/Grok and Claude Opus
  do not exhaust the space of judge models. Persistence here does not
  prove that every model family would remain ambiguous.
- **Residual-conditioned sample.** The 231 items are Grok Stage C
  leftovers. Rates do not describe the full 1,060-item Cursor panel.
  Claude was not asked to re-judge items Grok already found decisive.
- **Same evidence reconstruction.** Both panels use the same reconstructed
  FEVER wiki structure, including the same archive gaps. Shared ambiguity
  can reflect shared missing context as well as intrinsic warrant
  difficulty.
- **Blinding hides labels, not world knowledge.** Packets omit FEVER gold,
  GPT, NLI, and cohort tags. They cannot hide facts the model already
  knows.
- **No resolver.** Primary results are raw consensus. A same-family
  resolver might move some Unresolved/Ambiguous items; it was not run
  and would not be an independent family.
- **FEVER is not an error oracle.** Claude-decisive items that disagree
  with FEVER (35/97) are not automatically benchmark mislabels.
- **Small subgroups.** Shared regressions (n=24), rescue (n=24), and
  robust (n=9) CIs are wide. Exploratory tests are BH-adjusted and should
  not be over-read.
- **Account change is operational, not scientific.** Batch 03 used a
  second Cursor account after a usage-limit stop. The locked model and
  packets did not change. That does not create a new experimental arm.
- **No causal claim about GPT.** Persistence or resolution under Claude
  does not explain why GPT-5.4 or GPT-5.4-mini transitioned.
- **Issue flags are not a taxonomy gold.** `partial_warrant` is the most
  common persistent flag; it is a judge annotation, not a human warrant
  review.
