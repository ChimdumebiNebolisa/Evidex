# Cost estimate — October 16, 2026

Prepared-prompt estimate for direct OpenAI global standard Chat Completions. Currency: USD. No paid requests have been made.

| Design | Planned calls | Two-token label scenario | With 10% extra attempts | 32-token cap + 10% extra attempts | Three-attempt cap scenario |
|---|---:|---:|---:|---:|---:|
| full1 | 60,000 | $8.2485 | $9.0734 | $28.3784 | $77.3956 |
| full3 | 180,000 | $24.7456 | $27.2201 | $85.1351 | $232.1867 |
| full5 | 300,000 | $41.2426 | $45.3669 | $141.8919 | $386.9778 |
| hybrid3 | 84,000 | $11.5200 | $12.6720 | $39.6990 | $108.2700 |
| hybrid5 | 108,000 | $14.7915 | $16.2706 | $51.0196 | $139.1444 |
| hybrid3-historical | 86,280 | $11.8424 | $13.0267 | $40.7873 | $111.2380 |
| smoke | 12 | $0.0018 | $0.0020 | $0.0058 | $0.0159 |

The recommended full3 plan costs about **$24.75** when replies are stand-alone labels, or **$27.22** in the 10% extra-attempt scenario. These are estimates, not an approved budget or a billing guarantee. A 32-token output cap is not an assertion that 32 tokens will be generated. Retry scenarios are allowances, not measured service-failure probabilities. The 12-call smoke adds about $0.0018 under the two-token scenario; it remains paid inference.

## Verified rates and route

[Official OpenAI pricing](https://developers.openai.com/api/docs/pricing), standard text-token table, checked October 16, 2026: GPT-5.4 input $2.50 / output $15.00 per million; GPT-5.4-mini input $0.75 / output $4.50. No Batch, caching, regional, priority, tool or subscription discount is used. The plan requests global standard service. No browsing/tools are configured. Taxes and account credits are not estimated.

[GPT-5.4 model documentation](https://developers.openai.com/api/docs/models/gpt-5.4) and [GPT-5.4-mini documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini) list the original aliases, none reasoning effort and Chat Completions support. Actual account entitlement and completion parameter acceptance are pending. No key was available at build time.

## Token calculation

`tiktoken==0.12.0`, `o200k_base`, counts each complete substituted message content. Totals per one model and one full pass: A 331,901; B 788,053; C 848,053 content tokens. Add an estimated seven framing/role/priming tokens per single-user request: 2,178,007 estimated input tokens for 30,000 calls per model. Stand-alone Supported/Refuted labels require at most two local tokens, so the label scenario charges two output tokens on every call. The price calculation uses every actual subset message too; it does not multiply an unrelated average length.

Formula per model: `(estimated input tokens × input rate + calls × output tokens × output rate) / 1,000,000`. The full3 input estimate is 6,534,021 per model, and 90,000 completions per model.

Actual service-side token framing, cache behavior and usage can differ. The runner explicitly requests none reasoning, and `max_completion_tokens=32` caps visible plus reasoning tokens where supported. Any reported reasoning tokens are billed at the output rate and retained. The smoke test must calibrate actual usage and verify settings before the full run. The maximum-attempt cost column assumes every logical job incurs all three attempts and each attempt is charged the estimated input plus the full output cap; this is a conservative scenario, not a guaranteed upper bill. All attempts and missing usage remain visible.

## Precision tradeoff

At an assumed 1% rate, a 2,000-record repeated subset contains about 20 events, with a planning Wilson interval about 0.65–1.54%. At 10,000 records, about 100 events gives 0.82–1.21%. Neither replication counts nor conditional repeated pairs create additional independent claims. Under an illustrative paired discordance q=0.02, 95% half-widths are approximately 0.62 pp versus 0.28 pp. These approximations do not establish power and do not include all clustering/provider uncertainty.

**Recommendation:** three fresh repetitions across all 10,000 claims (full3), after an approved 12-call smoke test. The $13.23 difference from hybrid3 buys repeat measurements on the full target sample and avoids a much less precise rare-regression repeat estimate. Five repetitions cost more without expanding the number of claim clusters.
