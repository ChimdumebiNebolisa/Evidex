# Evidex replacement predictor protocol v1

Local date: October 16, 2026, America/Chicago. **Prospective local protocol; not externally preregistered.** The exact UTC freeze time and SHA-256 file map are in `protocol-freeze.json`. No new predictor outcomes were collected during development. Mocked test fixtures are synthetic and are not experiment data.

## Purpose and source record

The replacement measures (1) adding selected evidence with classification instructions held fixed, (2) the additional evidence-only restriction, and (3) variation under identical repeated messages. Original results are historical recorded labels, not outcomes to repair or overwrite. This protocol uses no automated adjudication, NLI inference, new sample extraction, retrieval or structured Stage C machinery.

Historical checkout: `codex/methodology-correction-v2`, SHA `6f57f49337acb68635c87544ee9e29be13ff5e35`. User-supplied AGENTS.md agreements apply; no additional on-disk instructions were found in the repository or searched ancestors. Stage 1 and Stage 2 reports inform the recording, instruction and repetition changes. They are not used as scientific ground truth.

Reuse the existing 10,000 FEVER records, 5,000 Supported and 5,000 Refuted. `prepared/input-verification.json` pins source hashes and records verification. All 40,000 accepted historical rows must agree on claim, gold label, selected evidence ID and evidence string. Recompute the selected set's historical ID from its annotation index and NFC-normalized ordered pointers, require a unique match, and compare each selected sentence with the archive's second tab field at that pointer. The prepared copy retains the exact existing sentence text and joining format. No choice of alternative set, replacement text, exclusion or imputation is permitted if verification fails. Preparation verified 11,137 pointers across the 10,000 records. The frozen input copy is used thereafter.

Records are the target units, not necessarily distinct texts: 9,855 normalized text clusters occur among 10,000 records. Claims sharing a casefolded, whitespace-normalized text are one resampling cluster even when their evidence or reference labels differ. Do not infer independence from distinct FEVER IDs.

## Exact complete messages and settings

Each call contains exactly one user message, with UTF-8 strings and the literal line breaks below. There is no system/developer message, prior conversation, tool definition, response-format schema, retrieval or appended run identifier in model-visible content. Braced fields are substituted without modifying their text. `MESSAGE_EXAMPLES.json` contains complete materialized messages and request bodies for the first prepared claim, for both models and all three conditions; every job pins its exact request-body hash.

**A — original claim-only instruction**

```text
Classify the claim as Supported or Refuted.
Output only one word: Supported or Refuted.

Claim: {claim_text}
```

**B — identical classification instruction, selected evidence added**

```text
Classify the claim as Supported or Refuted.
Output only one word: Supported or Refuted.

Claim: {claim_text}
Evidence: {gold_evidence}
```

**C — original evidence prompt, including evidence-only restriction**

```text
Classify the claim as Supported or Refuted based only on the evidence provided.
Output only one word: Supported or Refuted.

Claim: {claim_text}
Evidence: {gold_evidence}
```

A↔B changes the evidence field/content; the classification instruction stays identical. B↔C changes only the restriction in the first sentence. C↔A is the original combined contrast, reported as secondary. Evidence length and tokens necessarily increase in B/C. There is no empty evidence placeholder in A, preserving the original message.

Route: direct OpenAI global standard `POST https://api.openai.com/v1/chat/completions`. Requested model identifiers stay `gpt-5.4` and `gpt-5.4-mini`, matching the old script. Public model pages currently list these aliases and documented snapshots `gpt-5.4-2026-03-05` / `gpt-5.4-mini-2026-03-17`. Public listing is verified; account access is not yet verified because this process has no API key. The read-only `preflight` checks model metadata before execution, and every live worker repeats that check. Only a paid smoke test can establish completion access, parameter acceptance and actual returned model on this account. Stop on failure; never substitute.

All conditions/models request: `temperature=0`, `reasoning_effort="none"`, `max_completion_tokens=32`, `n=1`, `stream=false`, `store=false`, `service_tier="default"`. There is no seed or sampling-setting variation between repeats. Explicit none reasoning and output/storage/service controls reduce uncontrolled defaults but do not retrospectively establish the old defaults. No instruction is added to ask for reasoning. Temperature zero does not imply deterministic outputs. Allowed returned identifiers are the requested alias or the corresponding documented snapshot; an unexpected identifier or missing returned model quarantines that response and halts the run. Provider changes behind a permitted identifier may still be unobserved; retain fingerprints and response metadata.

## Run matrix and chosen repeat design

**Recommended primary design: three fresh calls in each model/claim/condition cell over all 10,000 records.** That is 10,000 × 2 × 3 × 3 = **180,000 planned calls**, not 60,000 independent claims. Repetition indices identify new requests, not copied outputs or SDK choices from one request. `prepared/full3/jobs.jsonl` assigns a unique stable job ID and a pre-shuffled global order to all calls. Every repeat has the same message/settings hash as its own cell's other repeats.

The schedule is shuffled jointly across claims, models, conditions and repetition indices using local RNG seed 20261016. Jobs are claimed in that order. Multiple local workers may finish in another order; start/completion times are recorded, and allocation is still interleaved. Each request is stateless with a fresh message array. Each worker issues at most one request at a time and spaces attempts by at least one second; retries have additional 2/4-second backoff. Increase throughput by additional workers only within account limits, retaining this schedule and requests. This affects timing and must be recorded, not model content. No response-level cache is used by the runner. Provider prompt caching is not proof that generation was reused; cached-token usage is retained.

| Design option | Full-sample repetitions | Representative subset total repetitions | Planned calls |
|---|---:|---:|---:|
| full1 |1|1|60,000|
| full3, recommended |3|3|180,000|
| full5 |5|5|300,000|
| hybrid3 |1|3 on 2,000 records|84,000|
| hybrid5 |1|5 on 2,000 records|108,000|
| hybrid3-historical, optional comparison |1|3 on 2,000 plus all 226 historical regression records|86,280 for this seeded selection|
| smoke, validation only |1 on two records|none|12|

The representative repeat subset is fixed before new outcomes: use seed 20261016 to draw 1,000 IDs without replacement within each gold-label stratum, from sorted existing IDs; no historical prediction or regression status enters that draw. The selected 2,000 records contain 1,993 text clusters. The optional historical extension adds repeats for the 190 historically regressing records outside that subset. These cases are selected by historical outcomes, so report them separately and never weight them as a representative sample. The default recommended design repeats everybody and requires neither enrichment nor weighting for that enrichment. Prepared `hybrid3` remains an explicitly alternative plan, not an additional run to combine with `full3`.

The smoke plan has the first sorted Supported and Refuted records, both models, all three conditions once. Its outcomes are validation-only and must not be imported into primary data. The main run makes fresh calls even for those two IDs. Do not optimize settings after viewing smoke labels; check acceptance, request identity, usage, parsing, rate limits and returned metadata. Parameter or model changes require a separately dated protocol revision before further new outcomes; retain the failed smoke run.

## Precision basis and why three full repetitions

A 1% record-level event rate corresponds to about 100 cases in 10,000 records or 20 in 2,000. Under an illustrative independent Bernoulli approximation, a Wilson 95% interval is about 0.82–1.21% for 100/10,000, and 0.65–1.54% for 20/2,000. Actual claims have clustered texts and repeated calls; these are planning benchmarks, not power claims or guaranteed achieved intervals.

For a paired difference in rare event indicators, an illustrative discordance probability q=0.02 gives normal-approximation 95% half-width 1.96√(q/n), about 0.28 percentage points at n=10,000 versus 0.62 at n=2,000. q is an assumption, not an observed new result. If a comparison really needs half-width approximately 0.3 pp under that assumption, about 8,537 independent claims are needed; a nearly full repeat subset saves little while adding a second sampling scheme. Three full repetitions are the smallest of the proposed fully repeated designs that show more than a two-way consistency split. Five improves within-claim descriptions but does not multiply the independent claim count. This experiment does not guarantee adequate power for a very small excess loss or rare subgroup. It measures finite-repeat persistence, never stable individual causal effects.

## Recording, acceptance, failure and stopping rules

For every claimed attempt create an exclusive directory keyed by claim/model/condition/repetition and attempt number. Persist a complete `request.json` with stable IDs, endpoint, exact JSON body/settings and start timestamp, without authorization headers. Use environment-only `OPENAI_API_KEY`; do not read arbitrary credential files or print credentials. API traffic is restricted to the fixed HTTPS host, with redirects disabled.

Save complete raw body bytes as `response.bin`, flush them, then save HTTP status, response headers excluding credential-bearing headers, receive timestamp and raw SHA-256 in `receipt.json`. Only then parse or normalize. Retain all choices, refusals, finish reasons, returned model, response ID, usage including cached/reasoning tokens when exposed, fingerprint, service tier and errors in the raw response; derived result fields also expose the main metadata. Error bodies that echo full or masked API keys are explicitly redacted before persistence; receipts flag this exception to byte-exact recording. Request headers are never saved. Files are exclusively created, never overwritten.

**Exact parsing:** accept only a string whose leading/trailing whitespace can be removed to yield exactly `Supported` or `Refuted`, case-sensitive, with one choice, a known returned model, `finish_reason="stop"` and no refusal. Do not remove quotes or punctuation, search within prose, guess an answer, or rerun an invalid/refused/truncated answer. The first HTTP-successful substantive response is terminal even if invalid. Save invalids and failures in the denominator and analysis.

**Retries:** at most three attempts per logical job, only for received HTTP 502/503/504 service errors or HTTP 429 with explicit code/type `rate_limit_exceeded`; backoff 2 then 4 seconds. Do not retry 429 `insufficient_quota`, authentication/access/model/parameter errors, malformed answers, refusals, truncations or unexpected models. Halt all pending work on request/access/quota errors or a model mismatch. Three failed transient attempts yield a terminal service failure. Other HTTP failures remain visible, terminal service failures. There are no SDK retries; the runner uses one explicit HTTP request per attempt.

The three-attempt limit counts durable request records that may have been submitted. A recovered crash before any request file exists consumes an identifier but does not consume the service-retry allowance; its recovery record remains. Ordinal identifiers can therefore exceed three after prelaunch recovery, while at most three request-bearing attempts occur. A request file without a complete receipt is uncertain and is never retried, even if transmission may not actually have begun. The analysis distinguishes a pending transient retry from three exhausted requests, rather than treating unfinished work as a final service failure.

**Uncertain transmission:** network loss or timeout can occur after the provider generated an answer. Mark it uncertain and never automatically resend that job. Exactly-once provider execution cannot be guaranteed across an unknown network outcome; local scheduling and durable recovery must not pretend otherwise. Include uncertain jobs as missing/nonresponses in analysis. Lost successful replies cannot be recovered by requesting a replacement label.

**Concurrency and recovery:** SQLite immediate transactions claim pending jobs atomically; an OS file lock acquired inside the transaction remains held throughout the attempt. Recovery skips a live locked job. On process death, an OS lock releases without a time-based lease. Recovery can derive a result from saved body+receipt without making a call, or reschedule a claim when no request file was ever created. If request bytes exist but a complete receipt does not, mark uncertain and retain the artifact. Damaged artifacts remain uncertain; never overwrite them. An intentional global halt is sticky; do not edit the database to erase errors or make a blocked protocol continue. A separately documented continuation/revision is needed if settings, model routing or an access/quota stop must be changed.

Each prepared plan hash is also bound, through exclusive registration, to one canonical local run directory. Starting that same plan in a second directory is rejected. This prevents an accidental second full experiment from bypassing the first directory's completed-job records. Separate protocol revisions have separate hashes; the smoke plan has its own identity. Partial bytes from interrupted HTTP reads, when available, are retained without being accepted or retried.

**Stopping:** complete the frozen schedule or stop for the specified infrastructure/provenance errors, explicit operator interruption, or the explicit CLI attempt cap. There is no significance-, accuracy- or label-dependent stopping, exclusion, retry or sample expansion. An unfinished run remains unfinished. Concurrent workers and resumption use the same run directory; never initialize a second directory to redo “bad” outcomes. The paid smoke and primary run use different directories and purposes.

## Estimands and independent analysis

The analysis reads the planned jobs and raw request/response artifacts and independently parses labels. It does not trust the execution SQLite state or `result.json` labels. Verify request-body hashes, response hashes and expected model/condition/repetition identities. Report assigned calls, all attempt counts, invalids, service failures, uncertainties, model mismatches and missing cells before any accuracy claim.

Primary group: all assigned 10,000 records, repetition 1, separately per predictor. Primary contrasts are A→B and B→C. A→C is secondary. For each contrast report the full joint correctness table where both labels are valid, known rescues and regressions, unknown transition counts and actual denominators. Report known-event fractions over all assigned pairs as lower bounds, alongside complete-valid-pair conditional fractions and identification upper bounds that allow each unclassified pair to be an event. Operational accuracy uses correct valid classifications / all assigned calls; invalids/nonresponses count as operational errors, not invented Supported/Refuted labels. Also report accuracy among valid outputs and bounds allowing nonresponses to be correct. Net operational accuracy differences preserve pairing and remain separate from known label transitions.

Repeated analysis: average matched repetition transitions within each claim before aggregation. Report identical-prompt label disagreement across every unordered pair of repeated outputs, but summarize those pair comparisons within claim first. Report the fraction of matched repetitions showing correct→wrong, the count that recur on every recorded repetition, and ordered identical-left-prompt correct→wrong transitions. For A/B and B/C, report the per-claim difference between matched between-condition loss frequency and ordered identical-left-condition loss frequency. This compares the observed loss probability with a repeat-variation baseline, not the fraction of stable causal failures. Complete-repeat analysis explicitly reports how many claims have every assigned output valid; incomplete claims stay visible, with no silent imputation. Differences in outcomes after changing model-visible instructions/evidence can support average sensitivity under this controlled, interleaved new protocol, not access to internal knowledge or historical snapshot reconstruction.

Uncertainty: 2,000 seeded nonparametric bootstrap draws of normalized claim-text clusters, using identical cluster weights across models, conditions, repetitions and endpoints. Reduce repetitions within claims; never treat 180,000 calls as 180,000 independent claims. Within each draw retain observed gold-label-stratum proportions (50/50 in the full and representative samples; actual proportions in historically selected cohorts). A cluster spanning conflicting gold labels receives the same weight in both strata. Bootstrap percentile intervals condition on this provider execution/configuration; they do not integrate unknown future model versions. For missing outputs, confidence intervals for observed lower-bound/operational quantities are separate from identification bounds for unobserved labels. Descriptive intervals are not simultaneous tests. No isolated “p<0.05” declarations or equivalence claims are primary; do not add post hoc significance claims to the two model/two contrast families without a separately specified multiplicity rule.

Always report representative repeats separately from any historically selected cases. Historical A/C label agreement and accuracy comparisons are descriptive, paired by matching ID; B has no old counterpart. New calls cannot establish what an unavailable historical model snapshot would have done, whether an old raw response was misparsed, or why a historical predictor answered as it did. Old data stay unchanged regardless of new results.

No downstream judging or manuscript rewrite is part of this initial experiment. Whether judging adds value depends on the new predictor findings and a separately stated measurement question.

## Price and launch gate

`COST_ESTIMATE.json` and `COST_ESTIMATE.md` use all actual prepared messages, local tokenizer counts and official standard rates checked October 16. They distinguish a two-output-token label scenario, a 10% extra-attempt scenario, the 32-output-token cap scenario, and a conservative three-attempt envelope. Input message framing is an estimate; no cache discount, free quota, tax estimate or total-budget guarantee is asserted. Reasoning tokens, if returned, are output-priced and included in the completion cap. No paid inference is authorized by local implementation or this freeze.

The user must review the concrete protocol and cost before paid smoke testing. The 12-call smoke is also paid inference, so it was not run during this task. A missing credential, metadata access failure or unaccepted parameter is an explicit readiness limitation. The exact commands are in `README.md`; the runner requires `--live` and an explicit positive attempt cap. A successful metadata GET is not itself evidence that generation/quota/settings work. Calibrate billing/token estimates against smoke usage before approving the full run; retain any new cost calibration separately rather than modifying this prospective protocol.
