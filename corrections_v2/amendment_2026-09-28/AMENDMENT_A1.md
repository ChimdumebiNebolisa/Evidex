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
| Every attempt record must carry a distinct session ID | Uniqueness is checked on the agent of each launched attempt slot, read from the SDK event log that survives in the slot (bytes must match the recorded inventory hash; exactly one agent). A record the slot's own run wrote must name that agent. A *collision record* (status `error`, exit code 2, session `unknown`) was written by a duplicate runner invocation that stopped before launching; it is not the slot's attempt record and is never counted as a launched model attempt. Its slot is accepted only if the shared runner log shows the duplicate's exit-code-2 failure, at least two starts for the slot, and a separate outcome for the launched run that agrees with its event log |
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
  invocations that lost a race for an attempt slot. `run_required_job.sh` exits with
  code 2 at its "workspace or record dir already exists" check, before a workspace or
  agent exists, so these invocations launched nothing. Each slot's launched attempt
  belongs to the winning invocation, whose agent is named by the slot's event log.
  `session_evidence.json` (`amended_analysis.py evaluate-sessions`) re-read all 101 slot
  event logs from the execution host on 2026-09-28 and compared every one of the 102
  records with its slot and with `sdk_execution/wsl/remaining_jobs.log`:
  - 88 records were written by the slot's own run and name the event-log agent;
  - 13 are collision records. In each slot, the runner log shows two starts, the
    duplicate's `code=2` failure, and the winner's outcome: `CHECKPOINT_FAILED` for five
    `p02_C_j2_*` slots whose event logs end `FINISHED`, or `code=1` for eight `p02_C_j3_*`
    slots whose event logs end `ERROR` (usage limit);
  - 1 is an explicit `not_launched` record with no event log.

  That gives 101 launched slots and 101 distinct agents. The deviation review's earlier
  count of 99 was the parser's coverage. `tools/build_attempt_evidence.py` read events
  only from staging copies, and `p01_C_j1_b01` attempt 2 and `p01_C_j1_b02` attempt 1
  had none; their WSL logs name agents that match their records. The runner log has
  16 exit-code-2 events: the 13 collision records, one duplicate that lost after the
  winner had written its own record (`p02_C_j3_b01` attempt 2), the deleted record below,
  and a wrapper-script failure (CRLF line endings) in `p01_C_j3_b10` attempt 2 that
  stopped before launch and left no record.
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
4. In 13 slots the only record describes a duplicate invocation that never launched; the
   slot's launched agent is known from its surviving event log and the runner log, not
   from an attempt record.
5. One collision record (`p02_C_j2_b02`, slot 3) was deleted during execution and does not
   survive.
6. Provenance rests on operator records and hashed evidence, not provider attestation.
