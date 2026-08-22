**Verdict: PASS** (structural checks)
# Leakage audit

1. One row per claim_id: PASS
2. Outcome-derived predictor features: none (PASS)
3. Exact-duplicate claims: 126 groups, 271 claims (2.7% of sample).
   Claims in duplicate groups sharing an identical gold label: 269/271.

## Duplicate-aware CV (surface features only, logreg)
```
       model     target  n_pos  auc_claim_id_grouped  auc_duplicate_aware  delta
     gpt-5.4     rescue    850                 0.653                0.654  0.001
     gpt-5.4 regression    115                 0.604                0.645  0.041
     gpt-5.4  resistant    281                 0.551                0.561  0.011
gpt-5.4-mini     rescue   1238                 0.638                0.639  0.001
gpt-5.4-mini regression    151                 0.563                0.569  0.006
gpt-5.4-mini  resistant    295                 0.550                0.569  0.020
```

4. NLI and embedding features are computed from claim text and gold evidence text only (src/semantic_features.py, src/nli_analysis.py); no model prediction or correctness flag enters them. PASS by construction.