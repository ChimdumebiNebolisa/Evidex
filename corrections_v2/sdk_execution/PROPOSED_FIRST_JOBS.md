# Proposed first-job commands

These commands are prepared but not authorized by setup validation. Run neither
block until the operator explicitly authorizes that named experimental job.
Each block launches exactly one fresh SDK agent and has no loop.

Run from `C:\Users\Chimdumebi\evidex` in Windows PowerShell.

## Grok — `p01_C_j1_b01`

```powershell
$workspace = 'C:\Users\Chimdumebi\evidex_isolated\p01_C_j1_b01\attempt-01\workspace'
$recordsParent = 'C:\Users\Chimdumebi\evidex_execution_records\p01_C_j1_b01'
$recordDir = Join-Path $recordsParent 'attempt-01'

python corrections_v2/analysis_pipeline.py export-job --panel grok --job p01_C_j1_b01
if ($LASTEXITCODE -ne 0) { throw 'export-job failed' }
New-Item -ItemType Directory -Path $workspace -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $recordsParent -Force -ErrorAction Stop | Out-Null
Expand-Archive -LiteralPath 'corrections_v2\handoff_jobs\p01_C_j1_b01.zip' -DestinationPath $workspace -ErrorAction Stop

$env:EVIDEX_EXECUTION_AUTHORIZATION = 'p01_C_j1_b01'
try {
  node corrections_v2\sdk_execution\run-proposed-job.mjs `
    --job p01_C_j1_b01 `
    --workspace $workspace `
    --record-dir $recordDir
  if ($LASTEXITCODE -ne 0) { throw 'SDK job failed' }
} finally {
  Remove-Item Env:EVIDEX_EXECUTION_AUTHORIZATION -ErrorAction SilentlyContinue
}
```

## Claude — `p02_C_j1_b01`

```powershell
$workspace = 'C:\Users\Chimdumebi\evidex_isolated\p02_C_j1_b01\attempt-01\workspace'
$recordsParent = 'C:\Users\Chimdumebi\evidex_execution_records\p02_C_j1_b01'
$recordDir = Join-Path $recordsParent 'attempt-01'

python corrections_v2/analysis_pipeline.py export-job --panel claude_full --job p02_C_j1_b01
if ($LASTEXITCODE -ne 0) { throw 'export-job failed' }
New-Item -ItemType Directory -Path $workspace -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $recordsParent -Force -ErrorAction Stop | Out-Null
Expand-Archive -LiteralPath 'corrections_v2\handoff_jobs\p02_C_j1_b01.zip' -DestinationPath $workspace -ErrorAction Stop

$env:EVIDEX_EXECUTION_AUTHORIZATION = 'p02_C_j1_b01'
try {
  node corrections_v2\sdk_execution\run-proposed-job.mjs `
    --job p02_C_j1_b01 `
    --workspace $workspace `
    --record-dir $recordDir
  if ($LASTEXITCODE -ne 0) { throw 'SDK job failed' }
} finally {
  Remove-Item Env:EVIDEX_EXECUTION_AUTHORIZATION -ErrorAction SilentlyContinue
}
```

## Recording and acceptance

The runner records, outside the judge workspace:

- complete SDK event stream;
- fail-closed hook audit;
- exact generated output bytes as `attempt-01.raw.txt`;
- requested legacy lock and canonical SDK selection;
- account-catalog match, agent/run/request IDs, init/run/result model records;
- packet/output/raw hashes, timestamps, tool events, token usage, and billed usage
  when exposed.

It leaves status as `pending_human_review`. A human must inspect the routing,
isolation, raw response, and output before copying anything into
`corrections_v2/execution/<job_id>/` or the manifest output path and before
creating `attempt-01.json` from the frozen template. Do not label an attempt
accepted when a model/configuration differs, a non-allowlisted access succeeded,
the output differs from the raw bytes, or required provenance is absent.
