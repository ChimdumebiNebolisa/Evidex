# Evidex: authorized twelve-call smoke report

Completed October 16, 2026. **The smoke passed. The 180,000-call full3 experiment was not started.**

## Execution and preservation

The original and operational seals verified before execution and again afterward. Account metadata access verified both original aliases. The existing smoke plan ran through the sealed 20-process launcher, same queue and unchanged conservative limits. All 20 processes exited successfully. There were exactly 12 unique requests and 12 distinct provider response IDs, no duplicate submissions, no retries and no overwritten responses. Every raw response, request, receipt and interpretation is retained under `replacement_predictor_v1/runs/smoke/attempts/`; their byte sizes and SHA-256 fingerprints are in [RESPONSE_INVENTORY.json](RESPONSE_INVENTORY.json).

| Planned | Attempted | Completed | Valid | Invalid | Failed | Uncertain | Retried |
|---:|---:|---:|---:|---:|---:|---:|---:|
|12|12|12|12|0|0|0|0|

All responses were exact standalone labels, finished with `stop`, reported service tier `default`, matched the allowed snapshots, and passed an independent strict reparse. Saved request bodies match every prepared request hash and all frozen settings. No prompts, models, settings or acceptance rules were changed.

## Model identifiers, reported usage and cost

| Returned model | Calls | Input tokens | Output tokens | Total tokens | Usage-derived USD |
|---|---:|---:|---:|---:|---:|
|gpt-5.4-2026-03-05|6|476|27|503|0.0015950|
|gpt-5.4-mini-2026-03-17|6|476|39|515|0.0005325|
|**Total**|**12**|**952**|**66**|**1,018**|**0.0021275**|

No cached input or reasoning tokens were reported. These costs use API-reported usage and [checked standard prices](https://developers.openai.com/api/docs/pricing), rather than local visible-label token counts or a billing-invoice reconciliation. Output usage averaged 4.5 tokens for GPT-5.4 and 6.5 for mini, above the earlier two-token planning assumption; the projection uses the reported counts. Mean recorded request-to-receipt latency was 1.415 seconds and 0.903 seconds respectively. The smoke's request window was 14.04 seconds; peak recorded overlap was 2 requests. This is a smoke test, not a twenty-simultaneous-request stress test.

## Updated full3 projection and launch requirements

Using measured smoke usage and latency, the existing prepared full3 token estimates and the unchanged account/local limit configuration:

- Full3 cost scenario: **$29.68**; with 10% additional attempts: **$32.65**. These are projections, not a guaranteed upper bill. Six calls per model cannot establish the full output distribution, cache behavior, retries or future prices.
- Runtime under the unchanged conservative 60 shared RPM/60,000 TPM ceiling and admission jitter: approximately **55.28 hours**, before additional cooldowns/interruptions. Twenty processes overlap latency but do not bypass the limiter.
- Observed provider headers: both models 5,000 RPM; GPT-5.4 1,000,000 TPM; mini 2,000,000 TPM. Shared family/project/day limits were not established by these headers. The higher provider figures were recorded without raising the local ceilings.
- No model, parameter, format, parsing or worker error blocked the smoke. Full3 still requires separate authorization and sufficient budget: the stated $5 funding is below the roughly $30 projection. A faster limit configuration would need a separate review of shared/account ceilings and a recorded configuration; this report does not modify it.

All 180,000 full3 jobs remain pending, with zero request artifacts. The temporary Windows user API-key variable was removed as promised; a future authorized run needs local credentials configured again. No credential was printed, written into research artifacts or committed to Git.

The full structured report is [SMOKE_REPORT.json](SMOKE_REPORT.json). The unchanged scientific smoke analysis is retained in `runs/smoke/analysis-01/`; the operational projection is `runs/smoke/operational-projection-01.json`.

- **What changed:** executed only the prepared smoke and generated post-run reports.
- **Files changed:** new local smoke artifacts, availability checks, analysis, projection and this report/inventory; frozen implementation and scientific files unchanged.
- **Verification run:** both seals; account/model metadata; prepared payload hashes/settings; raw-response SHA-256; independent strict parsing; unique job/response IDs; available usage and cost reconciliation; all worker exit codes; full3 unstarted check.
- **Result:** 12/12 valid, zero failed/invalid/uncertain/retried calls; usage-derived cost $0.0021275; full experiment unstarted.
- **Remaining uncertainty:** two-claim smoke extrapolation, sustained concurrency, shared/daily account limits and actual future billing; full3 budget and authorization remain outstanding.
