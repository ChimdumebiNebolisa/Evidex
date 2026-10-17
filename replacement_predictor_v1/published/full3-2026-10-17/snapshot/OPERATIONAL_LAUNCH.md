# Twenty-worker operational launch — October 16, 2026

The scientific design remains full3: all 10,000 claims, both original models, conditions A/B/C, three repetitions, 180,000 logical jobs. Prompts, API request settings, strict parsing, selected evidence, analysis and the three-request retry ceiling are unchanged. No paid inference was performed to build this revision.

The [original seal](protocol-freeze.json) is retained byte for byte. The [operational revision](operational-revisions/2026-10-16-workers20/revision.json) separately seals the changed runtime and new operational tools. [Change record](operational-revisions/2026-10-16-workers20/CHANGE_RECORD.md). Original runner/common bytes are archived in that revision's `original/` directory. The original inventory, release reports and construction logs remain historical records.

## Queue, limits and stopping

`launcher.py` starts exactly 20 Python processes using Windows-compatible spawn, monitors their exit codes, and owns an OS launcher lock. Every process uses the same run directory, `jobs.sqlite`, randomized queue, atomic claims and per-job OS locks. The parent initializes/verifies the plan once. Children never select a new sample, change payloads or replace invalid responses.

SQLite admission transactions reserve one request and a conservative token allowance in every applicable model and shared bucket. Tokens use UTF-8 content bytes plus 32 framing and the existing 32 output cap, rather than billing usage; this deliberately overestimates local token counts. Reservations are never refunded after errors or uncertainty. Rolling minute/day budgets and request/token pacing apply before a request file is created. Daily limits are supported through `rpd`/`tpd` where supplied.

The initial [limits file](operational-revisions/2026-10-16-workers20/limits.json) imposes a shared 60 RPM/60,000 TPM ceiling plus separate ceilings for both models. These are conservative local defaults, **not verified account entitlements**. They do not guarantee absence of 429s. Twenty processes overlap latency; at 60 shared RPM, 180,000 calls still require at least 50 hours before jitter, retries and cooldowns. The added 10–200 ms admission jitter contributes roughly 5.25 hours if that request ceiling dominates.

Response headers impose additional, tighter budgets for each model/header group, including remaining requests/tokens and reset times. Exposed project/organization request/token headers apply across both models. Out-of-order replies cannot replenish an active budget early; outstanding reservations are conservatively subtracted. Header caps also impose rolling minute limits/pacing, so a short reset cannot bypass a lower RPM/TPM cap. Provider limits cannot automatically raise the configured ceilings.

Use the account's [Organization Limits page](https://platform.openai.com/settings/organization/limits) to confirm RPM/TPM and any RPD/TPD or shared model-family limits. Those family memberships are not reliably discoverable from the standard response headers or model metadata. If two models share a family, assign the same `header_groups` value and add its shared bucket. Copy the initial file to an ignored path, for example `runs/account-limits.json`, enter the verified values/source/date, and pass `--limits` to every command. Each launch records the full configuration and revision fingerprint. Retain every previous launch record; never edit a live configuration or queue. External traffic sharing the account remains outside this local queue; response headers and cooldowns handle exposed reductions.

`Retry-After` supports seconds and HTTP dates. Reset headers support compound durations such as `6m0s` or `250ms`. Temporary 429/502/503/504 failures publish a shared cooldown before requeueing, with a per-job not-before time and positive jitter. Admissions remain serialized and paced after cooldown. The existing retry eligibility is unchanged: at most three request-bearing attempts, only 502/503/504 or 429 `rate_limit_exceeded`. A different 429 code does not gain a new retry. A header never makes quota, authentication or parameter errors retryable.

Authentication, access, parameter, quota/billing or unexpected-model errors set a sticky shared halt. Workers waiting to send stop; requests already admitted/in flight can finish recording. A worker crash or explicit stop requests a coordinated operational stop without respawning workers. Ctrl+C asks workers to drain; their SIGINT handler lets submitted calls finish. After the 120-second transport timeout, the launcher allows up to 160 seconds before terminating remaining workers and recovering. Killing the launcher causes children to stop on parent loss; a new launcher changes the owner token so earlier workers cannot admit more work.

Recovery preserves exact request/raw-response/receipt files. An active OS lock is skipped. A saved complete receipt is interpreted without an API call; a request without a complete receipt stays uncertain and is never automatically resent. A crash before request creation can be rescheduled using a new ordinal without increasing service retry eligibility. Transient retry records, exhausted failures, invalids and uncertain transmissions remain visible. No overwrite is permitted. Normal resumption uses the same plan and directory; the existing registration rejects a second directory for the same plan.

These header names, shared-family behavior and retry guidance were checked against [official OpenAI rate-limit documentation](https://developers.openai.com/api/docs/guides/rate-limits). This implementation uses the existing direct HTTP client; no SDK retries are added.

## Prepare and check access — no generation

Run in PowerShell from `C:\Users\Chimdumebi\evidex`:

```powershell
$exp = Join-Path (Get-Location) 'replacement_predictor_v1'
$limits = Join-Path $exp 'operational-revisions\2026-10-16-workers20\limits.json'
python -B "$exp\launcher.py" prepare --plan "$exp\prepared\smoke" --run-dir "$exp\runs\smoke" --workers 20 --limits "$limits"
python -B "$exp\launcher.py" prepare --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits"
```

Metadata access checking found no `OPENAI_API_KEY` in the process, Windows User or Machine environment during preparation. No credential was printed. Set a temporary credential locally using a masked prompt:

```powershell
$keyInput = Read-Host 'OpenAI API key' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $keyInput).Password
python -B "$exp\runner.py" preflight
```

This sends model-metadata GET requests only. Both original model aliases must verify for the account. Metadata access does not establish generation quota, parameter acceptance or rate limits. The live launcher repeats this check once before starting workers. It inherits the local environment and never writes credentials to launch records.

## Twelve-call smoke — paid, not started

After review and authorization, this uses the **existing** two-claim, two-model, three-condition smoke plan, with all workers sharing its one queue. It does not add repetitions or jobs:

```powershell
python -B "$exp\launcher.py" run --live --plan "$exp\prepared\smoke" --run-dir "$exp\runs\smoke" --workers 20 --limits "$limits" --max-attempts 36
python -B "$exp\launcher.py" status --plan "$exp\prepared\smoke" --run-dir "$exp\runs\smoke" --limits "$limits"
python -B "$exp\analyze.py" --plan "$exp\prepared\smoke" --run-dir "$exp\runs\smoke" --output "$exp\runs\smoke\analysis-01"
python -B "$exp\smoke_projection.py" --smoke-run "$exp\runs\smoke" --limits "$limits" --output "$exp\runs\smoke\operational-projection-01.json"
```

Review every smoke raw response and receipt for route, exact settings, returned model, finish reason, parsing, usage, latency, headers and errors. Do not rerun invalid or uncertain jobs to improve the smoke summary. The unchanged scientific analysis and operational projection both retain incomplete outcomes. A protocol/settings change requires a separate revision; do not edit the existing seal.

The projection tool uses measured latency/usage, actual prepared full3 reservations, token-estimate scaling, configured account limits and observed provider headers. It estimates full3 cost at the frozen standard rates and a runtime constrained by latency at 20 workers, pacing and exposed limits. It refuses a numeric projection for unresolved/invalid jobs or missing usage. The small smoke does not establish steady-state throughput; changing account traffic, rate limits, retries and latency tails remain uncertain. Recheck pricing at launch. No measured runtime or updated cost is claimed before smoke results exist.

## Full run — exact command, not started

After the smoke, rate/usage/runtime/cost review and explicit authorization:

```powershell
python -B "$exp\launcher.py" run --live --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000
```

The cap is cumulative operational admissions, including conservative reservations made before a crash. It does not permit more than three request-bearing attempts for any job. A pre-send crash can therefore stop at the operational cap early; it cannot enlarge the retry policy. The full plan remains 180,000 jobs.

Progress is printed every ten seconds and retained as immutable JSON snapshots under `runs/<plan>/launches/<timestamp-session>/`: completed jobs, terminal failures, HTTP-200 calls/minute, available token usage, known usage cost, provider budgets and provisional ETA. Invalid 200 responses count as HTTP successes and remain terminal failures in job statistics. Missing usage and uncertain acceptance never imply zero billing. ETA uses recent terminal-job rate, includes failures, and is null when stopped or when there is no observed throughput.

To stop from another terminal, recover offline, then resume after inspection:

```powershell
python -B "$exp\launcher.py" stop --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --limits "$limits"
python -B "$exp\launcher.py" recover --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --limits "$limits"
python -B "$exp\launcher.py" run --live --resume --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$limits" --max-attempts 540000
```

`--resume` clears only an operational stop, retaining the reason in the previous launch's records. It never clears a sticky request/access/quota/model halt. Keep the same directory and all artifacts. Run analysis to a fresh output directory. Remove the temporary key when finished:

```powershell
Remove-Item Env:\OPENAI_API_KEY
```
