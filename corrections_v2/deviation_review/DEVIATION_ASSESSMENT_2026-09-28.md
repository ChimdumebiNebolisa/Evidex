# Correction-v2 Stage C: execution deviation assessment (2026-09-28)

Status: written after all 70 required judgment outputs existed. This is a post-judgment
assessment. It does not amend, replace or re-date the frozen protocol
(`corrections_v2/protocol/analysis_spec_2026-09-27.md`, freeze
`analysis_spec_2026-09-27.freeze.json`), which verifies unchanged.

## Frozen-protocol result

`python corrections_v2/analysis_pipeline.py status --panel primary` returns `incomplete`:
6,430/6,430 judgments are schema-valid, but execution provenance fails for six jobs with
more than three attempt records (`p01_C_j4_b08`, `p01_C_j4_b09`, `p02_C_j2_b03`,
`p02_C_j3_b01`, `p02_C_j3_b02`, `p02_C_j3_b03`) and on a reused session ID (13 records
whose session is `unknown`). Under the frozen protocol, no primary analysis may be produced.
That outcome stands. No accepted output, failed-attempt record, cap or session value was
changed to make validation pass.

## Evidence base

- `evidence/wsl_inventory.json`: size, SHA-256 and mtime of every file under
  `/home/evidex/records` and `/home/evidex/isolated` (721 files).
- `evidence/attempt_evidence.json`: per-slot reconstruction for all 70 jobs from execution
  records, staging archives, the WSL inventory and surviving runner logs.
- `evidence/unstaged_failed_outputs.json`: output files that failed attempts left in WSL.
- `attempt_table.md`: chronological attempt table for the six flagged jobs plus two
  further affected jobs.

Checks across all 70 jobs: every job has exactly one accepted attempt. The 99 slots with
agent evidence have 99 distinct agent IDs, so no session was reused. (Addendum,
2026-09-28: 99 is the parser's coverage, not the number of launched slots. Two launched
slots, `p01_C_j1_b01` attempt 2 and `p01_C_j1_b02` attempt 1, had no local staging copy,
and `tools/build_attempt_evidence.py` parsed staging copies only. Their WSL event logs
name two further distinct agents that match their records, giving 101 launched slots
with 101 distinct agents; see `../amendment_2026-09-28/session_evidence.json`.) Every staging file
matches its WSL original by hash. No archived record names a session that contradicts
the evidence in its slot.

## Deviations found

1. **Retry cap exceeded (six jobs).** The operator authorized redoing attempts that failed
   on quota errors, and the operational cap was raised to 9. Every extra attempt for
   `p01_C_j4_b08`/`b09` followed a provider `[resource_exhausted]` or account
   out-of-usage error. For the four Claude jobs, the extra slots arose from the
   concurrency failure below.
2. **Concurrent runners (01:39–01:57 UTC).** Up to three runner processes ran at once,
   including orphaned processes that kept running after their wrapper was stopped. Their
   console logs were never captured. When two runners claimed the same attempt number,
   the loser exited with code 2 ("workspace or record dir already exists") and wrote an
   error record with session `unknown`. Those 13 records describe the losing
   invocation, not the agent that actually ran in that slot. Every one of those slots
   contains a real launch by another runner (see the table). The records are kept
   verbatim.
3. **First-schema-valid rule not followed (three jobs).**
   - `p02_C_j2_b02`: slots 1 and 2 finished with schema-valid outputs and slot 3 was
     accepted. Slot 1's checkpoint was refused because a collision record already
     occupied the slot.
   - `p02_C_j2_b03`: slots 1–3 finished with schema-valid outputs and slot 4 was
     accepted, for the same reason.
   - `p01_C_j5_b09`: slot 1 wrote a complete schema-valid output, then the run ended with
     `[resource_exhausted]`. The runner treated that as a failure and slot 2 was accepted.
     Whether an unfinished run counts as a "response" is debatable.

   In all three cases, the earlier slot is also first by start time and by completion
   time, so "first" is unambiguous.
4. **Deleted record.** During execution, the coordinating agent deleted a collision
   record for `p02_C_j2_b02` slot 3 (`attempt-03.json`, `attempt-03.routing.txt`) so
   the running slot-3 attempt could checkpoint. The session transcript documents this.
   The files do not survive.
5. **Template text in error records.** `record_error_attempt.py` writes fixed lines that
   are not evidence: `sandbox_initialized: true`, `hooks_loaded: true`,
   `observed_tool_names: read`, "stream stalled … designated output was never created",
   and a recording-time timestamp when the start time was unknown. These lines are false
   in specific cases: `p01_C_j4_b08` slot 1 left a truncated output file, and
   `p01_C_j5_b09` slot 1 left a complete one.
6. **Evidence line endings.** The recorder hashed text with LF line endings but Windows
   wrote CRLF, so all 29 failed-attempt `routing.txt` files mismatched their recorded
   hashes. On 2026-09-28, each file was rewritten to LF, and only where the LF bytes
   reproduced the recorded SHA-256 exactly. Content is otherwise identical and no record
   was edited. The recorder now writes exact bytes.

No deviation was triggered by verdict content. The runners never read outputs; accept or
retry depended only on exit codes, run status and checkpoint file collisions. Deviations
2–4 are operator/infrastructure failures, not model behavior.

## Provisional analysis (not the frozen-protocol primary analysis)

`provisional_analysis.py` imports the frozen analysis code unchanged. It writes only
under `provisional_results/`, with no judgment freeze, no follow-up packets and nothing in
`corrections_v2/results/`. Every output is labeled
`PROVISIONAL_DEVIATION_ANALYSIS__NOT_FROZEN_PROTOCOL_PRIMARY`.

| Selection | Claude C Supported/Refuted/Ambiguous | Claude nondecisive C | Grok nondecisive C | Cross-family exact taxonomy agreement | Kappa |
|---|---|---|---|---|---|
| Accepted as delivered (`accepted70_2026-09-28`) | 78 / 107 / 41 | 41/226 (18.1%) | 220/1060 | 172/226, 76.1% (70.4–81.4) | 0.673 |
| First schema-valid (`sensitivity_first_valid_2026-09-28`) | 80 / 107 / 39 | 39/226 (17.3%) | 220/1060 | 168/226, 74.3% (68.6–80.1) | 0.651 |

Across all 12 combinations of the completed runs for `p02_C_j2_b02` × `p02_C_j2_b03`,
Claude C consensus differs from the accepted selection on 0–6 of 226 claims, and the
Ambiguous count ranges from 37 to 42. The Grok substitution for `p01_C_j5_b09` changes 1
of 1,060 claims (SA-000834, Ambiguous to Unresolved) and leaves the nondecisive count
unchanged. All 16 cross-family and subgroup tests keep their BH significance
status, and every significant test keeps its direction. For example, Claude C
nondecisive is lower than Grok by 13.3 pp (accepted) or 14.2 pp (first-valid), with BH
p < 1e-7 in both, and the Claude shared-vs-specific odds ratio is 3.17 or 3.47. The only
sign change is in a non-significant test (`resolved_at_C`: −1.3 pp to 0.0 pp).

## Is a dated deviation analysis defensible?

Yes, as a separately named, post-judgment deviation analysis reported alongside the
statement that the frozen-protocol primary analysis is incomplete. It is not defensible
as the pre-specified primary analysis, and it must not be described as pre-registered or
as preceding the data. The case rests on:

- the deviations are mechanical and outcome-blind;
- every launched run survives with hash-verified SDK event logs, and every alternative
  completed output survives, so the effect of selection can be measured rather than
  assumed;
- the measured effect is small and changes no qualitative conclusion.

The protocol-closest estimate is the **first schema-valid selection**. A deviation analysis
should treat it as its main estimate, and report accepted-as-delivered plus the full
combination range as sensitivity. The dated amendment must be written now and marked as
post-judgment. It should state the selection rule (first schema-valid output by slot
order, which equals chronological order here) and how the retry-cap exceedances are
treated, before any further outcome is examined.

## Uncertainty that must be disclosed

1. The frozen-protocol primary analysis is incomplete, and the deviation analysis was
   specified after all outputs, and the provisional results reported here, had been seen.
2. Six jobs exceeded the three-attempt cap. The cap increase was authorized during
   execution in response to capacity errors, not written in advance.
3. For three jobs, the accepted output was not the first schema-valid output. The
   accepted-vs-first-valid difference is 6 Claude claims and 1 Grok claim; the
   combination range is 0–6 Claude claims.
4. Whether `p01_C_j5_b09` slot 1, a complete output from a run that ended in error,
   counts as a response is a judgment call.
5. Launch facts for the 13 `unknown`-session records rest on slot artifacts: SDK event
   logs, hooks and staging copies. The records themselves do not establish them. The
   runner logs for the orphaned processes are lost, so which process launched some slots
   cannot be established.
6. One collision record (`p02_C_j2_b02` slot 3) was deleted during execution, and its
   contents are known only from the transcript.
7. Error-record routing text contains template assertions that are not evidence. Two of
   them are false: the claims that no output was written for `p01_C_j4_b08` slot 1 and
   `p01_C_j5_b09` slot 1. Recorded start times for error attempts are recording times.
8. 29 evidence files were rewritten from CRLF to LF after the fact. Their hash
   equivalence to the recorded values is verified, but the rewrite is still an operator
   touch on archived evidence.
9. Several runs ended early from account or provider capacity. It is unknown whether
   those limits would have affected other runs in ways not visible in the artifacts.
10. As in the frozen protocol: execution provenance is operator records plus hashed
    evidence, not independent provider attestation; the provider model version is not
    exposed; and the taxonomy is a proposed v2 requiring coauthor review, descriptive and
    not causal.
