# Methods — Claude full-regression A→B→C panel

## Design

Independent cross-family replication of the complete Evidex progressive-
disclosure adjudication on **all 226 unique GPT regressions**. The original
mechanism decomposition (evidence-utilization failure / representation-
sensitive / residual ambiguity) came from a single judge family
(`cursor-grok-4.6-high-fast`). The existing Claude experiment covered only the
231 Grok Stage C residuals, so it could not test whether the full
decomposition survives a change of judge family. This panel runs the entire
A→B→C protocol from scratch with Claude, freezes the judgments while fully
blinded, and only then compares.

This is **cross-family silver validation, not human validation**. Agreement
between Claude and Grok does not establish ground truth, and disagreement with
FEVER does not establish FEVER annotation error.

## Cohort

Regression definition, unchanged from Evidex: a claim the model answered
**correctly without evidence** and **incorrectly after** receiving the
designated FEVER evidence (`transition == "correct_to_wrong"`). The cohort is
the union across `gpt-5.4` and `gpt-5.4-mini`.

`src/derive_and_blind.py` recomputes this directly from
`analysis_v2/data/derived/paired_enriched.parquet` and hard-stops unless the
count is exactly **226** and the claim-id set is identical to the frozen shared
cohort manifest. Independently recounted composition: 40 both models, 75
`gpt-5.4` only, 111 `gpt-5.4-mini` only. No cohort item is on the
provider-filtered list (`SA-000352` is not a regression), so all 226 are
judged.

## Blinding

Fresh opaque IDs `CF-000001`–`CF-000226`, assigned by a seeded shuffle
(seed 20260913) of the source items. The `CF-* → SA-* → claim_id` map lives
only in `data/id_map.csv` and is never shown to a judge.

Judges never see: that the items are regressions; which GPT model regressed;
whether one or both regressed; GPT predictions; FEVER labels; NLI results;
Grok or GLM judgments; the existing taxonomy labels; or the previous Claude
residual judgments. `src/derive_and_blind.py` machine-validates the allowed key
set per stage, opaque-ID form, uniqueness, and that CF order does not encode
`regression_type`.

Judge-facing packets, wrapper prompts, and the raw output inbox live under
`silver_adjudication_v1/blind_io/`, a deliberately neutral directory, because a
path containing the panel name would itself reveal the selection criterion.
Packet metadata and wrapper prompts are scanned for prohibited tokens before
any launch.

## Progressive disclosure

Stage evidence representations are **reused verbatim** from the existing
pipeline (`src/blind_cohort.py`, `src/reconstruct_evidence.py`); a unit test
asserts field-by-field equality with the shared blinded stage files. No new
retrieval, no browsing, no external facts.

- **Stage A** — `claim`, `evidence_sentences` (the exact gold-evidence text the
  GPT models saw)
- **Stage B** — Stage A plus `page_titles`
- **Stage C** — Stage B plus `structured_evidence`: chosen set with per-sentence
  page/line and text, alternative complete annotation sets, and the archive
  availability flag

Disclosure is strictly nested (`keys(A) ⊂ keys(B) ⊂ keys(C)`), enforced by test.

## Model lock

- Required slug: `claude-opus-5-thinking-high` for every judgment
- Auto, inherit, and any substitution are refused in code
  (`panel_config.require_locked_model`), including the Grok and GLM slugs
- Web browse and external retrieval forbidden; temperature provider default
- If the locked model becomes unavailable the protocol is to **stop** and emit a
  missing-work manifest, never to substitute

## Isolation

Five judges (`claude_full_judge_1`–`5`). A fresh Cursor Task subagent per
`(judge, batch, stage)`, packet-only I/O, batch size 77 (three batches per
judge per stage), matching the batching convention of the existing Claude
panel. Judges do not see other judges' outputs, downstream analysis,
previous-family judgments, or unblinded metadata. No context is asked to
simulate multiple judges.

Judge identity is stable across stages (`claude_full_judge_1` judges the same
items at A, B and C), but each stage runs in fresh contexts, matching the
Cursor/Grok panel: a judge's Stage A answer is frozen before Stage B evidence
exists, and later information never rewrites a stored earlier answer.

## Schema

Unchanged from the shared rubric (`../prompts/judge_rubric.md`, reused
byte-identically): `item_id`, `judge_id`, `stage`, `verdict`,
`evidence_sufficiency`, `confidence`, `issue_flags`, `brief_reason`. Verdicts
are `Supported | Refuted | Ambiguous`; sufficiency and issue-flag vocabularies
are asserted equal to `silver_adjudication_v1/config.py`. Validation rejects
non-integer or out-of-range confidence, empty or unknown flags, empty reasons,
and mismatched judge/stage stamps. The rubric was not modified at any point.

## Stage gating and freezing

`run_judges.freeze_stage` refuses to freeze Stage B before Stage A is frozen
and verified, and Stage C before Stage B. A stage freezes only when all five
judges have exactly 226 valid records (1,130 per stage) with no malformed
records, and records the locked model plus the judgment count. Frozen judgment
files are append-only; a byte change fails verification.

## Consensus

Existing Evidex panel-of-five rules, reused unchanged and asserted equal to
`silver_adjudication_v1/src/aggregate_consensus.py` over all 3^5 × 3^2 verdict
and sufficiency configurations:

- `high_consensus` decisive verdict when ≥4/5 judges agree on Supported or Refuted
- `Ambiguous` when the modal verdict is Ambiguous without a decisive 4/5, or
  when there is no decisive 4/5 and ≥3/5 sufficiency ratings are weak
- `Unresolved` otherwise

No resolver was run; the primary result is raw five-judge consensus, matching
the Claude residual panel's convention. Grok consensus plays no part in
computing Claude consensus.

## Transition variables

Definitions copied from `src/representation_sensitivity.py`: per-stage
ambiguity (Ambiguous ∪ Unresolved), `resolved_by_titles`,
`resolved_only_by_structure`, `still_ambiguous_after_C`,
`reversed_after_titles`, `reversed_after_structure`, plus per-judge verdict
change, ambiguity direction, confidence delta and sufficiency improvement.

## Freeze before unblinding

1. Verify all three stage freezes and the 3,390 total.
2. Compute consensus, agreement and transitions from frozen files only.
3. Hash blinded stages, id map, cohort audit, stage freezes, consensus,
   agreement, completeness and transition artifacts into
   `freezes/freeze_manifest.json`, together with the locked model, cohort size,
   judge count and the git commit.
4. Only then does `analyze.py unblind` reveal that the cohort is the regression
   set, apply the taxonomy, and join Grok/FEVER/GPT metadata.

`analyze.unblind` calls `verify_manifest()` first and raises if the manifest is
absent or any hash drifted. Grok results were not inspected during judging.

## Taxonomy

The existing Evidex rules from `src/join_analysis_v2.py`, applied
mechanically to the Claude A/B/C consensus with `cohort = "regression"`:

| rule order | label | broad category |
| --- | --- | --- |
| 1 | `silver_partial_or_ambiguous_warrant` (still ambiguous after C) | residual ambiguity |
| 2 | `silver_structured_evidence_sensitive` | representation-sensitive |
| 3 | `silver_title_context_sensitive` | representation-sensitive |
| 4 | `silver_clear_evidence_utilization_failure` | utilization failure |
| 5 | `silver_unresolved` | other |

Rule order is load-bearing and was not changed: an item that is ambiguous at A
and decisive at C is `structured_evidence_sensitive` even if titles already
resolved it, which is why the finer `title_context_sensitive` bucket can be
empty. A unit test asserts this implementation reproduces the frozen Grok
`silver_taxonomy` labels for all 226 regressions from Grok consensus alone, so
Claude and Grok are classified by provably identical code. No case was
classified by hand and no definition was altered after seeing results.

## Statistics

Wilson intervals for proportions; exact McNemar (binomial) tests for paired
Claude-vs-Grok discordance; percentile bootstrap (2,000 resamples, seed
20260913) for rate CIs; Fisher exact odds ratio for the shared vs
model-specific subgroup. Subgroup analyses are exploratory and reported with
counts; no significance is claimed where n is small.

## Verification

`tests/test_claude_full_regression.py` covers cohort size, blinding,
progressive nesting, evidence reuse, model lock and substitution refusal,
schema validation, consensus-rule and taxonomy equivalence with the shared
implementation, per-stage and total judgment counts, duplicate detection,
vocabulary validity, freeze integrity, the unblinding gate, and non-mutation of
the frozen Cursor/Grok, GLM and Claude-residual artifacts.
`src/verify_headlines.py` independently recomputes every quoted headline from
raw frozen files along a separate code path and checks it appears in a report.
