# Adjudication Log (silver v1)

Running record of panel setup, execution, retries, deviations, and null
findings — anti-cherry-picking documentation.

## Panel setup (2026-08-22)

- 5 isolated GLM-5.3 judge subagents (judge_1..judge_5), each a FRESH agent
  context per batch; no judge sees another judge's output, consensus,
  FEVER labels, GPT predictions, transitions, NLI outputs, similarity, or
  cohort type. Judges read only `prompts/judge_rubric.md` + their item range
  of the stage's blinded JSONL.
- Model: GLM-5.3 (environment general-purpose subagent; same family for ALL
  judges — within-family agreement only).
- Rubric version: `prompts/judge_rubric.md` v1 (2026-08-22), unchanged
  across judges and stages.
- Batch size: 100 items (11 batches/stage; batch 11 = 61 items).
- Item IDs: SA-000001..SA-001061, seeded shuffle (seed 20260822) of cohort
  claim_ids; ID-neutrality validated (chi-square across ID halves, p>0.01).

## Execution environment notes

- Background subagent concurrency limit observed: ~2-3 simultaneous agents;
  launches beyond the limit fail immediately ("user concurrency limit
  exceeded") without consuming judge state. Failed launches are relaunched
  with identical blinded inputs (this is launch retry, not judgment retry).
- One transient "Model request failed" on judge_1 batch 01; relaunched,
  completed. Recorded as retry #1 for judge_1.

## Judgment retries (schema failures requiring re-prompt)

(none so far)

## Stage freezes

- (pending)

## Deviations from protocol

- None. Stage C structured evidence reconstructed from the official FEVER
  wiki archive (fever.ai, https-only, host-validated) per user decision;
  alternative-set sentence text recovered for 506/508 referenced sentences
  (2 pointer-only due to missing pages in the archive).

## Null findings / notes

- (pending)

## Judging session 2 (Stage A continuation)

- judge_2 batch_06 (SA-000501..0600): OK, 100 valid.
- judge_1 batch_06 (SA-000501..0600): OK, 100 valid.
- judge_3 batch_04 (SA-000401..0500): FAILED (provider "Model request failed", empty response). Retry 1 launched with same blinded range + two-part write guidance.
- judge_4 batch_04 (SA-000401..0500): launched.
- judge_5 batch_04 (SA-000401..0500): launched.
