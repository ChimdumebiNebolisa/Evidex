# Limitations — Claude full-regression A→B→C panel

## What this panel is not

- **Not human validation.** Every judgment here is a model judgment.
  `claude-opus-5-thinking-high` agreeing with `cursor-grok-4.6-high-fast` does
  not establish human ground truth. Two model families can share the same
  blind spots, especially on claim/evidence pairs whose difficulty comes from
  annotation conventions rather than from language understanding.
- **Not a test of FEVER correctness.** Where the panel calls an item Ambiguous
  and FEVER assigns a decisive label, that is a disagreement between a model
  panel and an annotation, not evidence that the annotation is wrong.
- **Not a window into GPT reasoning.** The panel judges whether the supplied
  evidence warrants the claim. It says nothing about why a GPT model changed its
  answer. "Evidence-utilization failure" is a label for *"a blinded panel finds
  this warrant clear"*, not a mechanism observed inside GPT.
- **Not a new cohort.** The 226 regressions are the same claims the Cursor/Grok
  panel judged, so the two panels are paired by construction. That makes the
  comparison sensitive but means both inherit any cohort-construction bias in
  Analysis v2.

## Within-panel dependence

The five judges are five isolated contexts of the *same* model. Within-Claude
agreement (pairwise, Fleiss κ, Krippendorff α) measures reproducibility of one
family, not independent consensus, and will overstate how much genuinely
separate raters would agree. It is reported as **within-Claude-panel
agreement** throughout.

## Selection and paired-design caveats

- The cohort is conditioned on GPT behaviour, so it is not a random sample of
  FEVER. Rates here should not be read as population rates.
- Claude and Grok judged the same items, so their agreement is measured on a
  paired sample. Paired discordance tests (McNemar) are appropriate; unpaired
  comparisons of the two panels' marginal rates would understate precision.
- Subgroup splits (shared vs single-model regressions; the finer taxonomy
  buckets) have small cells. They are reported as exploratory with counts, and
  no significance is claimed where n does not support it.

## Taxonomy caveats

- The taxonomy is a **rule**, not a ground truth. It assigns each regression to
  the first matching branch of an ordered rule set, so the labels are only as
  meaningful as those rules.
- Rule order is load-bearing and was deliberately not changed: an item that is
  ambiguous at Stage A and decisive at Stage C is classified
  `structured_evidence_sensitive` even when page titles already resolved it.
  This is why the finer `title_context_sensitive` bucket can be empty for a
  panel, and it means "representation-sensitive" is dominated by the
  structure branch by construction.
- `residual ambiguity` is defined by the panel's own Stage C consensus. A panel
  that is more willing to answer Ambiguous will produce a larger residual share
  without anything changing about the claims. Cross-panel differences in this
  bucket are therefore partly a judge-disposition effect and partly a property
  of the warrants; this panel cannot separate the two.
- No case was hand-classified, and no rule was altered after results were seen.

## Protocol caveats

- **No resolver.** The Cursor/Grok panel ran a same-family resolver over
  non-high-consensus items; this panel, like the Claude residual panel, reports
  raw five-judge consensus. Consensus labels — the taxonomy's only input — are
  computed identically in both panels, so the comparison is like-for-like, but
  the Grok panel had an extra adjudication layer available for other analyses.
- **Stage C evidence is reconstructed, not retrieved.** It reuses the frozen
  reconstruction from the official FEVER wiki archive, including the two
  pointer-only alternative-set sentences that the archive could not supply. No
  browsing or new retrieval happened in this panel.
- **Judge identity is stable across stages but contexts are fresh.** A judge
  cannot see its own earlier verdict, so a stage-to-stage "change" is a change
  in the panel's answer under more evidence, not a revision by a judge who
  remembers its previous answer. This matches the original protocol.
- **A discarded first wave.** The initial Stage A batch-01 wave was launched
  with judge-facing paths that contained the panel directory name, which names
  the cohort selection criterion. Those five files were quarantined unread and
  the batch rerun under neutral paths (see `ADJUDICATION_LOG.md`). The frozen
  Claude residual panel retains the analogous exposure and was not modified.

## Capacity

The panel is bounded by Cursor Claude usage. If capacity is exhausted the
protocol is to stop, preserve all valid judgments, and emit an exact
missing-work manifest — never to substitute another model. Any incompleteness
is recorded in `freezes/missing_work_manifest.json`.
