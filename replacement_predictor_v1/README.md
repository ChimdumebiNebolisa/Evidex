# Evidex replacement predictor experiment

**Recommendation: run three fresh repetitions on all 10,000 claims, after reviewing this package and approving the separate 12-call live smoke test.** The primary plan has 180,000 calls. Actual-prompt standard-price estimates are **$24.75** for stand-alone two-token labels, **$27.22** with 10% extra attempts, and **$85.14** if all responses hit the 32-token cap with that extra-attempt allowance. These are scenarios, not a guaranteed bill or an established budget. [Cost calculation and options](COST_ESTIMATE.md) cite current official pricing.

The historical study is preserved. This directory contains new preparation, implementation, tests and the prospective protocol. No paid inference or new judging was performed during construction. Public model listings were checked; this account's access remains unverified because no key is present in the process, Windows user environment or machine environment. That limitation is visible in [preflight.log](preflight.log) and the timestamped availability record. The runner fails closed before generation if metadata access fails.

Read [PROTOCOL.md](PROTOCOL.md), [RUN_MATRIX.csv](RUN_MATRIX.csv), [MESSAGE_EXAMPLES.json](MESSAGE_EXAMPLES.json), and [COST_ESTIMATE.json](COST_ESTIMATE.json). The exact source/data/plan fingerprints and UTC freeze time are in [protocol-freeze.json](protocol-freeze.json). This is locally prospective, not externally preregistered. The historical alias identifiers are used through the direct OpenAI global standard Chat Completions route; new calls do not recreate an undocumented historical snapshot. No silent fallback is implemented.

## What is ready

- Verified copy of the existing sample and selected evidence: 10,000 records, 11,137 directly checked sentence pointers; [input verification](prepared/input-verification.json).
- Exact A/B/C messages and fixed settings; [materialized examples](MESSAGE_EXAMPLES.json).
- Frozen randomized/interleaved plans for full3, smoke, and the separately priced hybrid3 alternative. Do not execute multiple plans and pool their results.
- A standard-library HTTP runner with full raw recording before strict parsing, exclusive files, atomic claims, OS locks, bounded explicit retries, ambiguous-transmission handling and recovery.
- Independent raw-response analysis, paired transitions, repeated-prompt variation, finite-repeat persistence, missing/invalid bounds, text-cluster intervals and separately labeled historical comparisons.
- [Unit tests](TEST_RESULTS.txt), [latest synthetic integration check](LATEST_MOCK_INTEGRATION.json), [historical preservation](PRESERVATION.json), and [release checks](RELEASE_CHECK.json).

## Environment and tests

Commands below use PowerShell from the repository root:

```powershell
Set-Location 'C:\Users\Chimdumebi\evidex'
$exp = Join-Path (Get-Location) 'replacement_predictor_v1'
python -B -m unittest discover -s "$exp\tests" -v
python -B "$exp\verify_release.py"
```

The live runner needs Python 3.12+ and its standard library. Analysis uses NumPy; token estimation uses tiktoken. Tested NumPy is 2.4.4 and the tokenizer is pinned to 0.12.0. The current machine already has NumPy; tiktoken was installed locally in `.deps/`, without changing global packages. On a clean environment, install the pinned requirements locally:

```powershell
python -m pip install --target "$exp\.deps" --no-compile -r "$exp\requirements.txt"
```

Do not re-prepare or modify a frozen experiment to obtain preferred results. Preparation already ran. `prepare.py` and `seal.py` are retained for reproduction of the construction; they refuse to replace prepared artifacts or redate a changed seal. An alternate design or parameter change requires a separately named and dated protocol revision. That is separate from simply resuming the frozen run.

## Read-only access check

Supply credentials only through the local shell environment. Do not paste a key into chat, scripts or version control. For a temporary PowerShell session, an interactive masked prompt avoids putting the literal key in command history:

```powershell
$keyInput = Read-Host 'OpenAI API key' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $keyInput).Password
python -B "$exp\runner.py" preflight
```

This performs only model metadata GETs, not completions. It checks both original aliases for this credential. A metadata success is not proof of generation quota, snapshot behavior or parameter acceptance. Each live worker repeats the check. Authentication, permission, model-route or parameter failures stop the runner; it never drops temperature or changes the model to make a request pass.

## Paid live smoke test — run only after review

The smoke sends 12 fresh calls, two records × two models × three conditions. It is paid inference; it was **not run** during this task. It costs approximately $0.0018 in the two-token scenario, or about $0.00584 at the cap plus 10% extra attempts. Those amounts can differ in actual usage. Keep its data separate from primary inference:

```powershell
python -B "$exp\runner.py" run --live --plan "$exp\prepared\smoke" --run-dir "$exp\runs\smoke" --max-attempts 36
python -B "$exp\runner.py" status --plan "$exp\prepared\smoke" --run-dir "$exp\runs\smoke"
python -B "$exp\analyze.py" --plan "$exp\prepared\smoke" --run-dir "$exp\runs\smoke" --output "$exp\runs\smoke\analysis-01"
```

Review all smoke raw responses, returned identifiers, finish reasons, usage and parsing statuses; confirm the messages match their frozen hashes. Analysis `summary.json` includes available usage accounting; missing usage is not zero cost. Check the price estimate against those usage counts. Do not select prompts/models from their accuracy. Unexpected identifiers/settings or a needed protocol change require a separate revision before the full run. Missing/invalid smoke results should not be silently replaced until valid.

## Primary full run — only after smoke and cost review

```powershell
python -B "$exp\runner.py" run --live --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --max-attempts 540000
python -B "$exp\runner.py" status --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3"
python -B "$exp\analyze.py" --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --output "$exp\runs\full3\analysis-01"
```

180,000 logical jobs allow at most three request-bearing attempts each. The explicit 540,000 CLI cap is a maximum scheduling-attempt allowance, not a request to make 540,000 successful calls. Valid and invalid terminal jobs are never resent. Ordinal attempt IDs consumed before a request exists do not consume a service retry; no request with uncertain acceptance is automatically resent.

One worker spaces attempts by at least one second, so 180,000 calls take at least 50 hours on one worker, with additional latency possible. Independent local workers may run the same command against the **same directory** to share pending jobs, if account rate limits allow. Worker IDs/PIDs and timestamps are retained. Do not start another directory to repeat completed calls: plan-to-run registration rejects that accidental second execution. Never introduce another response from the same request as a fresh repetition.

After an interruption, perform offline recovery before resuming the same run:

```powershell
python -B "$exp\runner.py" recover --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3"
python -B "$exp\runner.py" run --live --plan "$exp\prepared\full3" --run-dir "$exp\runs\full3" --max-attempts 540000
```

Recovery skips active workers, reconstructs results from saved receipts without inference, and marks uncertain transmissions without reissuing them. A sticky access/quota/model/parameter halt is not cleared by recovery; inspect the retained record and document a continuation/revision rather than editing the SQLite file or discarding errors. Repeated analysis needs a new output name (`analysis-02`, etc.); reports are not overwritten.

Remove the temporary key when finished:

```powershell
Remove-Item Env:\OPENAI_API_KEY
```

## Record and analysis layout

`runs/<plan>/run.json` binds the protocol and plan hashes. `jobs.sqlite` manages scheduling, not scientific truth. Each `attempts/<claim_model_condition_repetition>/attempt-NN/` holds exact request data, raw response bytes, a receipt with HTTP/metadata and SHA-256, and a derived result. Partial/transport failures and recovery records remain in place. Credentials are excluded; a response echoing a key is explicitly redacted and flagged. Run directories, local dependencies and synthetic test artifacts are Git-ignored by this directory's own `.gitignore`.

The independent analysis reconstructs outputs from request/receipt/raw files, ignoring execution parser labels. It reports primary first-pass A→B and B→C paired outcomes, secondary A→C, full joint correctness counts, operational and valid-only accuracy, unknown-transition bounds, repeated identical-prompt disagreement, per-claim persistence, excess observed losses over repeated-left-prompt variation, historical-label comparisons and available usage. Repetitions are reduced within claims; 2,000 bootstrap draws resample text clusters jointly across models/conditions. An incomplete run is explicitly labeled incomplete. Historically selected cases are reported separately and never treated as representative population prevalence.

The result can establish new average prompt sensitivity and finite-repeat persistence under the recorded provider route. It cannot recover the original raw responses, establish the old snapshots' behavior, prove internal reasoning, or label a single observed transition a stable causal effect. No judging is included in this initial replacement.
