# Methods — Claude residual Stage C panel

## Design

Narrow robustness test of the frozen Cursor/Grok Stage C residual
(Ambiguous/Unresolved; expected n = 231). Same blinded reconstructed
Stage C evidence and the same judge rubric as the Cursor panel. No new
retrieval. No cohort expansion.

Scientific target: persistence of residual ambiguity under a different
generative model family. This is not human adjudication.

## Model lock

- Required slug: `claude-opus-5-thinking-high`
- Cursor version recorded in `config.json`
- Auto, inherit, and substitution forbidden
- Web browse and external retrieval forbidden
- Temperature: provider default

If the locked model is unavailable, the protocol is to stop, not to
substitute.

## Isolation

Five isolated judges (`claude_judge_1`–`5`). Fresh Task subagent per
(judge, batch). Packet-only I/O. Judges see `item_id`, `claim`,
`evidence_sentences`, `page_titles`, `structured_evidence`, and the
shared rubric. Prohibited: Grok/Cursor/GLM verdicts, FEVER gold, GPT
transitions, NLI, cohort, residual-status language, and other judges.

Opaque IDs `CR-*` mapped to source `SA-*` IDs only in `data/id_map.csv`,
which judges do not receive.

## Residual reconstruction

Source: `cursor_panel/freezes/consensus_stage_C.parquet`. Keep items
with consensus in `{Ambiguous, Unresolved}`. Independently counted 231
(212 + 19). Seed `20260823` shuffles source IDs into CR order.

## Judging

- Batch size 77 (three batches of 77).
- Batches 01–02: first Cursor account, all five judges valid on first try.
- Batch 03: resumed under a **second Cursor account** because the first
  account exhausted its Claude usage allowance. Existing blinded packets,
  rubric, judge IDs, model slug, and inference settings were reused.
  Batches 01–02 were not rerun.
- Output schema: verdict, evidence_sufficiency, confidence 0–100,
  issue_flags, brief_reason.
- Schema retries: 0.

## Consensus and agreement

Raw five-judge consensus uses the same rules as the Cursor panel
(`high_consensus` if ≥4/5 Supported or Refuted; otherwise preserve
Ambiguous or Unresolved). Primary headlines use this raw consensus.
A same-family resolver was allowed as optional sensitivity analysis and
**was not run**.

Agreement is labeled **within-Claude-panel agreement**: pairwise
agreement, Fleiss' κ, Krippendorff's α (nominal), high-consensus rate,
Ambiguous/Unresolved rates, judge tendencies, confidence.

## Freeze-before-unblind

1. Validate 231/231 × 5 schema-complete judgments.
2. Freeze and hash raw judge files (`freezes/freeze_judgments.json`).
3. Compute consensus and agreement; hash those artifacts in
   `freezes/freeze_manifest.json`.
4. Only then join Cursor Stage C labels.
5. Only then unblind FEVER/GPT/NLI/cohort fields from
   `cursor_panel/freezes/silver_unblinded.parquet`.

Raw judgment files are append-only after freeze.

## Statistics

Percentile bootstrap, 2,000 resamples, seed 20260823. Primary family:
persistent ambiguity, Claude resolution, high-consensus resolution,
Grok-only ambiguity, Claude-internal disagreement, cross-family label
agreement, FEVER agreement among Claude-decisive items. Exploratory
family: cohort and shared/model-specific regression subgroups, Fisher
OR for residual regression vs residual resistant, Mann–Whitney
confidence contrast. BH adjustment on exploratory p-values.

## Reproduction

From `silver_adjudication_v1/claude_residual_panel/`:

```text
python src/run_judges.py verify
python src/consensus_agreement.py
python src/analyze.py freeze
python src/analyze.py unblind
python src/analyze.py stats
python src/verify_headlines.py
python src/figures.py
python -m unittest discover -s tests
```

Do not rerun judging. Frozen outputs are the record.
