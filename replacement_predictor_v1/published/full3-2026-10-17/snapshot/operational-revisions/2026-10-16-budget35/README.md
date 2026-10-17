# Full3 supervised launch with a $35 forecast stop — 2026-10-16

The user authorized full3 with added funding, the selected operator600 configuration, the existing full3 directory and twenty workers. The amount added is not inferred. The user requires a progress report after 1,000 completed jobs and pausing admissions if projected full3 cost exceeds $35 or an existing defined halt occurs. Prior seals and configurations remain unchanged.

`budget_supervisor.py` wraps the existing sealed launcher. It does not replace or edit the launcher, coordinator, worker, scientific requests/settings, retry rules, parsing, response recording, queue or recovery code. It verifies the original seal chain, the operator600 configuration seal and this independent supervision seal, then uses the existing model-metadata preflight and launches twenty workers in `runs/full3` with the exact preserved operator600 configuration and cumulative admission cap of 540,000. Metadata preflight is not a smoke test or generation benchmark.

The supervisor checks every two seconds, plus computation time. It writes append-only snapshots at least every ten seconds and saves `first-1000-completed.json` on the first observation of 1,000 or more completed jobs. Existing launcher progress continues to show jobs, failures, successful calls per minute, available usage, provider budgets and ETA. Files are under `runs/full3/supervision/<timestamp>/`; `finished.json` captures usage and cost after draining. Existing `runs/full3/launches/` progress and every per-attempt request/response remain intact.

## Cost rule

The forecast uses the same prepared-message local token estimate as the frozen cost calculation (`o200k_base`, content tokens plus seven estimated framing tokens). No requests are changed. All future jobs are included in remaining demand.

1. Sum actual reported input/output usage for every attempt, including invalid and failed results when usage is returned. Use frozen standard rates, checked again against official pricing before launch: GPT-5.4 $2.50/$15 input/output per million; mini $0.75/$4.50. Completion usage already includes reasoning tokens. Assume no cache discount.
2. Reserve conservative input-byte-based admission tokens and the full 32-token output allowance for attempts with unreported usage, uncertain transmissions and active calls. They are not treated as free. An active attempt's job is removed from remaining normal demand to avoid charging both a full reservation and another forecasted call for the same active request.
3. Forecast remaining prompt usage by scaling the exact remaining prepared token estimates with observed actual/local input ratios per model. Forecast remaining output using observed completion means per model. Include the preserved six smoke calls per model as initial observations and add all complete live HTTP-200 usage, including terminal invalid outputs. Use observed finished attempts per distinct attempted job, with the same prior observations, to account for retries. Known failed-attempt costs remain in the spent/reserved total.
4. If the sum of known usage cost, unreported/in-flight reservation and remaining forecast is **strictly greater than $35**, write the existing shared `stop_requested` flag. Do not increase the threshold or wait for 1,000 completions. Existing workers stop taking admissions and admitted requests finish recording under the original draining/recovery behavior. Existing global halts are preserved. Monitor errors also request a stop and signal the launcher's existing coordinated interruption handler.

The initial full3 usage forecast is $29.678725, reproduced from the preserved smoke without new calls. The forecast is an estimate, not an independently reconciled invoice or a guarantee about unobserved future usage. It excludes the earlier smoke charge of $0.0021275, taxes and unrelated account usage. Sampling, throttling, delays and in-flight activity may alter the eventual bill or runtime. Snapshot fields separate known reported cost from conservative reservations.

No defined halt is automatically cleared. Resume requires inspection and `--resume`; a forecast still exceeding $35 cannot be resumed through this supervisor. Previously completed/invalid/uncertain jobs are never restarted. Monitor startup waits for the new launcher owner so a reviewed previous operational stop cannot make the new monitor exit prematurely.

## Commands

Only use this supervised entry point for this authorization so the cost stop remains active:

```powershell
$exp = 'C:\Users\Chimdumebi\evidex\replacement_predictor_v1'
python -B "$exp\budget_supervisor.py" --live
# After inspection of an operational stop, continuing the same authorized run:
python -B "$exp\budget_supervisor.py" --live --resume

# Request coordinated stop without changing the run or responses:
python -B "$exp\launcher.py" stop --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --workers 20 --limits "$exp\operational-revisions\2026-10-16-operator600\limits-operator600.json"
```

The launch process must receive the API key only through its local environment. Do not put credentials in command arguments, logs, chat, source files or version control. A hidden background process can run this supervised entry point while Codex reports from the persisted snapshots. The monitor is inside that process; it continues independently of chat polling. If the supervisor process exits unexpectedly, the existing workers detect loss of their launcher parent and stop further admissions, retaining uncertain transmissions for the existing recovery rules.

The selected target remains 600 RPM aggregate, gradually ramped, with 600,000 reserved TPM shared across both models and confirmed per-model caps preserved. Provider aggregate capacity remains unverified. Observed lower limits, Retry-After, reset/remaining budgets, cooldowns and adaptive throttling remain authoritative. Five-to-six hours remains conditional.

## Evidence

`BASELINE.json` records user authorization and prior hashes. `TEST_RESULTS.txt` records fresh mocked tests and regression checks. `revision.json` seals the added supervisor, tests and documentation without modifying previous seals or frozen implementation. Launch/access/monitoring evidence is written separately after sealing. [Official OpenAI standard pricing](https://developers.openai.com/api/docs/pricing) was fetched for the rate check.

All **78 tests passed in 146.877 seconds**, including ten new supervision tests, the existing scientific/runner tests and operational tests. New tests cover the baseline forecast, known and missing usage, in-flight reservations, retry charges, invalid terminal outputs, strict $35 comparison, preservation of stops, safe in-flight recording after a budget stop, monitoring failure, resume startup and the 1,000-job checkpoint. No paid calls are used in these tests.
