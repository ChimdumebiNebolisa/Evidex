# Amendment A1 to the correction-v2 Stage C analysis (2026-09-28)

**Post-judgment amendment. Not preregistered.** Written after all 70 required Stage C
outputs existed and after provisional results from those outputs had been inspected
(`corrections_v2/deviation_review/`). The frozen protocol
(`corrections_v2/protocol/analysis_spec_2026-09-27.md`, freeze
`analysis_spec_2026-09-27.freeze.json`) is unchanged and still reports the primary panel
as `incomplete`. A1 is a separately named analysis rule set; its results live only under
`results/` in this directory.

## Rule changes

| Frozen rule (2026-09-27) | A1 rule |
|---|---|
| At most 3 attempt records per job | At most 9 attempt records per job |
| Every attempt record must carry a distinct session ID | A record whose session is `unknown` counts as a launched attempt when the SDK event log that survives in its slot names exactly one agent, that agent appears in no other slot or record, and the log's bytes match the recorded evidence hash; that agent ID then enters the uniqueness check |
| Accept the first schema-valid response; an earlier schema-valid response may not be discarded | The analysed output of each job is its checkpoint-accepted output, selected explicitly; first-schema-valid alternatives are analysed as sensitivity |

Everything else is unchanged: packets, models, taxonomy, statistics, the remaining frozen
provenance checks (routing to the locked model, isolation flags, input/output hashes, raw
output equals delivered output, timestamps after the freeze, one accepted attempt that is
the last record), and the frozen analysis code. `amended_analysis.py` applies the frozen
`provenance_for_job` with only the constant 3 replaced by 9.

## Why

- **Cap.** Six jobs used 4 to 7 attempts. The extra attempts followed provider
  `resource_exhausted` errors and account usage limits (two Grok jobs), and slot
  collisions from concurrently running runner processes (four Claude jobs). The operator
  authorized the redo during execution; A1 records that decision as a rule. No retry was
  triggered by verdict content: runners never read outputs.
- **Unknown sessions.** The 13 `unknown`-session records were written by runner
  processes that lost a race for an attempt slot and exited with code 2. They describe
  the losing invocation, not the agent that ran in the slot.
  `collision_evaluation.json` re-read each slot's SDK event log from the execution host on
  2026-09-28. All 13 logs match their recorded hashes, and each names exactly one agent.
  The 99 agents found in slot evidence are all distinct. Of the 102 attempt records, 101
  describe launched sessions and one is an explicit `not_launched`. With the 13 resolved,
  those 101 sessions are all distinct. All 13 records are established as launched
  attempts, and no session was reused.
- **Selection.** For `p02_C_j2_b02` and `p02_C_j2_b03`, earlier finished runs with
  schema-valid outputs were never checkpointed because a collision record already occupied
  the slot. For `p01_C_j5_b09`, the first run wrote a complete output and then ended in a
  provider error. The accepted outputs are the ones the execution procedure checkpointed.
  A1 selects them because they are the delivered, hash-attested outputs. The first-valid
  alternatives are kept, byte-verified and analysed as sensitivity.

## Result of applying A1

`python corrections_v2/amendment_2026-09-28/amended_analysis.py status` gives
`ready_under_amendment_A1`: 70/70 jobs, 6,430 schema-valid judgments, no amended
provenance error. `run` wrote `results/primary_accepted/`,
`results/sensitivity_first_valid/`, `results/sensitivity_summary.json` and
`results/amended_status.json`.

The result tables and figures are byte-identical to the provisional results produced
under the same selections before A1 was written. A1 changes the status of the analysis,
not any estimate.

## Disclosure required wherever A1 results are reported

1. A1 was specified after the outputs and provisional results were seen. It is not
   preregistered, and the frozen-protocol primary analysis remains incomplete.
2. The cap was raised because of capacity failures during execution.
3. For three jobs the analysed output is not the first schema-valid output. First-valid
   selection changes 6 of 226 Claude Stage C consensus labels and 1 of 1,060 Grok labels
   (a non-regression claim). No significance decision changes.
4. Launch facts for the 13 `unknown` records come from slot evidence, not from the records.
5. One collision record (`p02_C_j2_b02`, slot 3) was deleted during execution and does not
   survive.
6. Provenance rests on operator records and hashed evidence, not provider attestation.
