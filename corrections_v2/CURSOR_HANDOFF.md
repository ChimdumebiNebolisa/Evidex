# Cursor execution handoff — correction v2

No inference has been run by this package. **Model availability and actual routing
are unverified.** This is an operator handoff, not a claim that a named Cursor
feature/API presently exists or that these model slugs are callable.

## Operator-only material

Keep this document, protocol, manifests, mappings, audit, labels, results and
historical judgments OUT of judge contexts. Use the repository copy containing
the frozen protocol and verified prepared packets. Dependencies for offline
analysis: Python, pandas, NumPy, SciPy, pyarrow and matplotlib (pytest for legacy
tests). The packet itself contains the entire judge rubric and required schema.

Read `protocol/analysis_spec_2026-09-27.md` and its `.freeze.json`; this is a post
hoc correction, not original-study preregistration. Review the proposed taxonomy
and A/B retention limitation before dispatch. Changes require an explicit dated
amendment before fresh data, not editing the frozen files.

## 1. Availability, identity and isolation gate (manual)

Required historical locks, no substitutions:

| Panel | Slug | Jobs / judgments |
|---|---|---:|
| p01 Grok C | `cursor-grok-4.6-high-fast` | 55 / 5,300 |
| p02 Claude full C | `claude-opus-5-thinking-high` | 15 / 1,130 |
| p03 optional fixed historical cohort | `claude-opus-5-thinking-high` | 15 / 1,155 |
| p04 newly selected cohort, prepared later | `claude-opus-5-thinking-high` | result-dependent |
| p05 separate resolver, prepared later | `cursor-grok-4.6-high-fast` | result-dependent |

Before judging, and again for each job:

- Confirm the exact slug is offered by the actual execution environment. Record
  account/availability interruptions. A selected dropdown label alone does not
  establish the route actually used.
- Inspect actual request/session routing metadata or an auditable execution log;
  confirm requested AND resolved model. Save the evidence, not just a typed claim.
  Record provider model/version/snapshot ID if exposed, request/session ID,
  timestamp, Cursor/app version and any fallback or routing warning. If version
  is not exposed, explicitly record that limitation and what was inspected.
- Disable Auto/inherit routing, browsing and external retrieval. Keep provider-
  default temperature and the reasoning setting embodied by the historical slug;
  do not silently choose a different reasoning variant or temperature.
- Use a new context for EACH job and EACH retry. No inherited conversation,
  parent audit, project instructions, previous stage/judge messages, repository
  index, memories or tool-accessible historical files. Do not simulate five judges
  in one context. A/B and new C are independent contexts, not continuations.
- Enforce a packet-only environment using filesystem permissions or an isolated
  sandbox/workspace with no parent-repository access, no network and no repository
  tools. Prompt instructions alone are NOT access control. Allow read access only
  to that designated packet and write access only to its designated output path.
  If the execution surface cannot enforce/verify this isolation, stop and record
  the block; do not use a broadly privileged agent as an equivalent setup.
- A human reviewer checks captured routing and isolation evidence. The offline
  validator checks the record/hash completeness; it cannot independently prove
  what a provider actually executed.

If exact routing cannot be verified, the model is unavailable, settings differ,
or unexpected fallback occurs: mark the attempt `blocked`/`error`, record why and
STOP that panel. No replacement may be described as the historical model. A new
model requires a separately named replication and fresh full A/B/C trajectories.

## 2. Verify and export one job (no inference)

From the repository root, preparation must already be finalized:

```powershell
python corrections_v2/verify_outputs.py
python corrections_v2/analysis_pipeline.py freeze-spec
python corrections_v2/analysis_pipeline.py export-handoff
python corrections_v2/analysis_pipeline.py show-job --panel grok --job p01_C_j1_b01
python corrections_v2/analysis_pipeline.py export-job --panel grok --job p01_C_j1_b01
```

All exit 0 on success. Repeating `freeze-spec` verifies the same freeze; it never
replaces it. `export-job` creates `handoff_jobs/<job_id>.zip` containing exactly
ONE packet at its original relative path, with the rubric embedded. It prints
the exact `launch_prompt`, locked model and hashes. It does NOT create a sandbox
or launch a model. Do not pass the output metadata or this handoff to a judge.

`export-handoff` packages all 85 one-packet ZIPs plus a separate `OPERATOR_ONLY`
folder containing this handoff, frozen protocol, execution template and exact
manifest, at `handoff/cursor_handoff_2026-09-27.zip`. The 70 primary jobs are
required; the 15 p03 jobs remain optional. No other repository material is needed
by a judge. Return outputs/provenance to the original verified repository for
offline validation/analysis; do not expose that repository to judge contexts.

Extract only that ZIP into the isolated execution root. Provision the designated
output directory with write permission; no other input files or network tools.
Verify the extracted packet SHA-256 equals the manifest. Dispatch a fresh Cursor
Task/context using `job.model` and exactly `job.launch_prompt`; no extra explanation
of the claim cohort or audit. This is an orchestration instruction, NOT an invented
Cursor CLI command. Use a verified route exposed by the operator's environment.

Enumerate required jobs from `generated/rerun_manifest.json`, panels `grok` and
`claude_full`; dispatch each exact job ID once. Do not launch p03 as a prerequisite
for primary completion. No judge may see the manifest or source-ID mappings.

## 3. Raw output and execution record

Save the exact provider response (including fences if present) under
`corrections_v2/execution/<job_id>/attempt-01.raw.txt`. Preserve transport metadata
separately if applicable. Save routing/isolation evidence in the same directory;
text, screenshot or exported log is acceptable as archived evidence. Avoid secrets.
Save the returned JSON array to `job.output`, preserving record order and values.
Only surrounding `json` code fences/outer whitespace may be removed; no record
repair, invented explanations or edited judgments. The offline pipeline checks
JSON equality to the archived raw response. Retain rejected raw responses too.

Fill `protocol/execution.template.json` into
`execution/<job_id>/attempt-01.json` using ACTUAL observed values, never placeholders
or inferred provider versions. Hash files with:

```powershell
(Get-FileHash -Algorithm SHA256 -LiteralPath 'EXACT_FILE_PATH').Hash.ToLowerInvariant()
```

Capture UTC times, unique session ID, operator/reviewer, requested/resolved model,
version availability, settings, packet/output hashes, raw-response and routing-
evidence path/hash. Do not copy the template's booleans as if verification occurred.
No output is scientifically accepted on schema validity alone.

## 4. Validate, retry and resume

```powershell
python corrections_v2/rerun.py validate --scope required
python corrections_v2/analysis_pipeline.py status --panel primary
```

The first checks schema/preparation; the second additionally checks execution
records/evidence and context uniqueness. Exit 0 means the selected scope is
ready; exit 1 means pending/incomplete, with job-level reasons. Infrastructure
or immutable-integrity violations exit 2 from `analysis_pipeline.py`.

Resume only missing jobs or documented invalid/interrupted attempts. Up to two
retries (three attempts total) per job, each a new isolated context. Store failed
attempt records with `job_id`, contiguous `attempt`, `status` in
`invalid/error/blocked`, `reason`, `session_id`, and raw/routing attachments when
available. If no session launched, use `not_launched:<reason>`. Keep actual received
failed raw responses; do not erase them. Subsequent record names are
`attempt-02.json` and `attempt-03.json`. The accepted attempt must be the last;
never rerun a schema-valid response because of its verdict or confidence. Do not
overwrite archived attempts. Stop if the retry budget is exhausted.
If no raw response was received, include `raw_response_unavailable_reason`;
`invalid` requires the actual rejected response. A schema-valid earlier response
cannot be relabeled invalid and retried. Session IDs are checked against other
archived panels too, not just jobs in the selected scope.

Missing provenance is a manual recovery task, not permission to fabricate it.
Never regenerate preparation or alter a packet after dispatch. `reproduce.py`
refuses existing primary delivered outputs; archived evidence and freeze checks
also protect later stages. Reuse the existing hashes and verify on resume.

## 5. Freeze before analysis, then run offline

After all 70 required jobs and provenance are complete:

```powershell
python corrections_v2/analysis_pipeline.py freeze --panel primary
python corrections_v2/analysis_pipeline.py analyze --panel primary --version run001
python corrections_v2/analysis_pipeline.py verify-result --version run001
```

Each exits 0 on success. `freeze` is append-only/idempotent for identical bytes;
changed raw outputs or provenance block. `analyze` refuses partial data, joins
retained A/B with provenance only after the new freeze, and writes a new result
version. No estimate directory is produced while judgments/freezes are pending.
Completed versions are never overwritten. Only final verified artifact manifests
count as completion; hidden `.incomplete` directories are failed/interrupted work.

Grok-only may be frozen/analyzed with `--panel grok --version run001` when complete,
without waiting for Claude. Cross-family results remain explicitly pending. If
using this route, choose a NEW version (e.g. run002) for later primary analysis.

## 6. Newly selected residual and separate resolver

The completed Grok-containing result creates `followup_manifest.json`, private
source mapping and packet-only p04/p05 jobs under neutral opaque paths. Selection
uses corrected raw Grok C, never the historical 231 or resolver outcomes.

For an exact p04 job ID from `results/run001/followup_manifest.json`:

```powershell
python corrections_v2/analysis_pipeline.py show-job --panel new_residual --parent run001 --job EXACT_JOB_ID
python corrections_v2/analysis_pipeline.py export-job --panel new_residual --parent run001 --job EXACT_JOB_ID
python corrections_v2/analysis_pipeline.py status --panel new_residual --parent run001
python corrections_v2/analysis_pipeline.py freeze --panel new_residual --parent run001
python corrections_v2/analysis_pipeline.py analyze --panel new_residual --parent run001 --version run003
```

Repeat the same routing/isolation/raw/provenance procedures. Analyze only after
complete 5R judgments. Empty R produces no jobs and no conditional rate estimate.
For the independent p05 secondary branch, substitute `--panel resolver` and a
different result version. A resolver sees only its designated packet, which
intentionally includes anonymous ratings, not any other judgments or hidden data.
Resolver outcomes never overwrite primary C consensus/taxonomy.

Optional p03 fixed-historical sensitivity uses
`freeze --panel claude_historical_residual_optional`, then
`analyze --panel claude_historical_residual_optional --parent run001 --version run004`.
Its selection remains historical and must not be described as the new residual.

## Completion checklist

Verify every result with `verify-result`; review routing limitations, ties,
denominators, undefined statistics and representative-case selection. Preserve
all historical files/tag and new raw/provenance freezes. Seek coauthor review of
taxonomy and post hoc interpretation. Do not update manuscripts, push, merge or
publish without separate authorization. Passing offline tests alone establishes
neither fresh inference nor corrected scientific conclusions.
