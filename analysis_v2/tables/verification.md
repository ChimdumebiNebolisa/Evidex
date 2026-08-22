# Headline verification (independent recomputation)

Total checks: 69; PASS: 69; FAIL: 0

| check | reported | recomputed | status |
|---|---|---|---|
| GPT-5.4 claim_only acc % | 88.69 | 88.69 | PASS |
| GPT-5.4 evidence acc % | 96.04 | 96.04 | PASS |
| mini claim_only acc % | 84.67 | 84.67 | PASS |
| mini evidence acc % | 95.54 | 95.54 | PASS |
| GPT-5.4 robust | 8754 | 8754 | PASS |
| GPT-5.4 rescue | 850 | 850 | PASS |
| GPT-5.4 resistant | 281 | 281 | PASS |
| GPT-5.4 regression | 115 | 115 | PASS |
| mini robust | 8316 | 8316 | PASS |
| mini rescue | 1238 | 1238 | PASS |
| mini resistant | 295 | 295 | PASS |
| mini regression | 151 | 151 | PASS |
| GPT-5.4 regression rate % | 1.15 | 1.15 | PASS |
| mini regression rate % | 1.51 | 1.51 | PASS |
| GPT-5.4 rescue % | 8.5 | 8.5 | PASS |
| mini rescue % | 12.4 | 12.4 | PASS |
| rescue rate of co-errors GPT-5.4 % | 75.2 | 75.2 | PASS |
| rescue rate of co-errors mini % | 80.8 | 80.8 | PASS |
| gpt-5.4 McNemar chi2 | 558.3 | 558.3 | PASS |
| gpt-5.4 McNemar p ~ 1e- | -123 | -123 | PASS |
| gpt-5.4-mini McNemar chi2 | 849.1 | 849.1 | PASS |
| gpt-5.4-mini McNemar p ~ 1e- | -186 | -186 | PASS |
| GPT-5.4 regression CI low | 0.95 | 0.95 | PASS |
| GPT-5.4 regression CI high | 1.36 | 1.36 | PASS |
| mini regression CI low | 1.28 | 1.28 | PASS |
| mini regression CI high | 1.75 | 1.75 | PASS |
| GPT-5.4 rescue CI low | 7.92 | 7.92 | PASS |
| GPT-5.4 rescue CI high | 9.04 | 9.04 | PASS |
| mini rescue CI low | 11.73 | 11.73 | PASS |
| mini rescue CI high | 13.0 | 13.0 | PASS |
| gpt-5.4 gain pp | 7.35 | 7.35 | PASS |
| gpt-5.4-mini gain pp | 10.87 | 10.87 | PASS |
| gpt-5.4 Sup->Ref errors | 238 | 238 | PASS |
| gpt-5.4 Ref->Sup errors | 158 | 158 | PASS |
| gpt-5.4-mini Sup->Ref errors | 201 | 201 | PASS |
| gpt-5.4-mini Ref->Sup errors | 245 | 245 | PASS |
| gpt-5.4 regressions on Supported | 88 | 88 | PASS |
| gpt-5.4 regressions on Refuted | 27 | 27 | PASS |
| gpt-5.4-mini regressions on Supported | 74 | 74 | PASS |
| gpt-5.4-mini regressions on Refuted | 77 | 77 | PASS |
| gpt-5.4 regression label contrast p | 1.8e-08 | 1.8286090140762365e-08 | PASS |
| gpt-5.4-mini regression label contrast p | 0.87 | 0.8697306666099708 | PASS |
| both regress | 40 | 40 | PASS |
| exactly one regress | 186 | 186 | PASS |
| agree transition % | 87.3 | 87.3 | PASS |
| agree co pred % | 89.3 | 89.3 | PASS |
| agree ev pred % | 97.2 | 97.2 | PASS |
| kappa claim_only | 0.786 | 0.786 | PASS |
| kappa evidence | 0.944 | 0.944 | PASS |
| nli1 disagree gpt-5.4 correct_to_correct % | 22.6 | 22.6 | PASS |
| nli2 disagree gpt-5.4 correct_to_correct % | 26.2 | 26.2 | PASS |
| nli1 disagree gpt-5.4 wrong_to_correct % | 31.5 | 31.5 | PASS |
| nli2 disagree gpt-5.4 wrong_to_correct % | 38.1 | 38.1 | PASS |
| nli1 disagree gpt-5.4 wrong_to_wrong % | 75.8 | 75.8 | PASS |
| nli2 disagree gpt-5.4 wrong_to_wrong % | 74.4 | 74.4 | PASS |
| nli1 disagree gpt-5.4 correct_to_wrong % | 74.8 | 74.8 | PASS |
| nli2 disagree gpt-5.4 correct_to_wrong % | 67.8 | 67.8 | PASS |
| nli1 disagree gpt-5.4-mini correct_to_wrong % | 76.8 | 76.8 | PASS |
| nli2 disagree gpt-5.4-mini correct_to_wrong % | 73.5 | 73.5 | PASS |
| weakly warranted n | 2462 | 2462 | PASS |
| weakly warranted co acc % | 81.0 | 81.0 | PASS |
| regression mean cosine GPT-5.4 | 0.589 | 0.5889999866485596 | PASS |
| overall mean cosine | 0.613 | 0.6129999756813049 | PASS |
| semantic outliers | 421 | 421 | PASS |
| exact duplicate groups | 126 | 126 | PASS |
| exact duplicate groups | 126 | 126 | PASS |
| claims in duplicate groups | 271 | 271 | PASS |
| shared same-direction failures | 281 | 281 | PASS |
| regression logreg AUC, surface-only vs full (reported full) | 0.60-0.72 (full) | surface=0.53, full=0.61 | PASS |

Unique-claim counts: regression_gpt54=115, regression_mini=151, regression_either=226, regression_both=40, regression_exactly_one=186, evidence_failure_gpt54=396, evidence_failure_mini=446, evidence_failure_either=561, evidence_failure_both=281