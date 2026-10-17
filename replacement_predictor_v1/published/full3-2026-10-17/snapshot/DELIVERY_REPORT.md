# Replacement predictor experiment: delivery

**Local construction and verification are complete. Paid inference has not started.** The account-access check reports `credential_unavailable`, not success. A metadata-only check and the separately approved paid smoke must precede the main run.

- [Protocol and analysis definitions](PROTOCOL.md)
- [Run commands and operational details](README.md)
- [Verified-source pricing and actual-prompt estimates](COST_ESTIMATE.md)
- [Runner](runner.py) and [independent raw-response analysis](analyze.py)
- [Unit-test output](TEST_RESULTS.txt), [latest end-to-end synthetic integration](LATEST_MOCK_INTEGRATION.json), [release checks](RELEASE_CHECK.json)
- [Protocol freeze](protocol-freeze.json), [historical preservation](PRESERVATION.json), [created-file inventory](FILE_INVENTORY.json)

The freeze was written at `2026-10-16T07:40:30.383240+00:00` on October 16, 2026, America/Chicago. Its SHA-256 is `2dcd6ee8877201c7c96d3413768ac6db9718403cadbda4410a56267e859af676`. It pins 22 protocol, input, plan, implementation and test files. It is a local prospective record, not external preregistration.

| Full-sample repetitions | Calls | Two-token label estimate | With 10% extra attempts |
|---|---:|---:|---:|
|1|60,000|$8.25|$9.07|
|3|180,000|$24.75|$27.22|
|5|300,000|$41.24|$45.37|

A full pass plus three total repeats on the seeded representative 2,000-record subset costs about $11.52 ($12.67 with the same allowance), for 84,000 calls. Its rare-regression repeat estimate is much less precise. Other scenarios and conservative output/retry caps are in the cost document. In particular, the recommended plan's 32-token-cap plus 10% scenario is about $85.14; $27.22 is not a guaranteed budget. Prices are standard API rates, not a ChatGPT subscription allowance.

All 10,000 existing inputs and 11,137 selected sentence pointers verify. All 24 unit tests pass, and the synthetic end-to-end run produces 34 valid jobs, one invalid response and one intentionally missing job with the expected analysis. Two processes cannot claim the same job; a plan cannot accidentally start again in a second run directory. The pending full3 database contains exactly 180,000 jobs and the smoke database 12, with no generation request artifacts.

One analysis edge case was first reproduced in `retry-edge-before.txt`: a pending transient retry was mislabeled a final service failure. The corrected analysis distinguishes unfinished retries, and the regression test now passes. A test spy was updated to accept the explicit request-count argument. A preparation helper also had a syntax error before execution; it was corrected without creating inference records. None of these development checks modified historical artifacts or involved paid model calls.

- **What changed:** added a separate prospective predictor experiment with verified reusable inputs, exact messages, recording, scheduling, recovery, independent analysis and pricing.
- **Files changed:** only files under `replacement_predictor_v1/`; all 2,632 inventoried historical files remain byte-identical, with unchanged branch and commit. Local dependencies, initialized pending databases and synthetic fixtures are ignored by the new directory's own `.gitignore`.
- **Verification run:** exact-message and input hashes, archival selected-pointer validation, randomized matrix checks, 24 unit tests, synthetic end-to-end execution/analysis, protocol hashes, credential handling checks and historical preservation.
- **Result:** runnable local package prepared and frozen; zero paid inference or judging calls.
- **Remaining uncertainty:** account generation access, accepted settings and actual usage await the approved live smoke; new calls cannot recover the old raw responses or recreate undocumented historical snapshots.

**Recommendation:** approve the 12-call smoke first, then use the frozen full3 plan—three fresh repetitions on every claim—if the route, settings, recording and usage checks pass.
