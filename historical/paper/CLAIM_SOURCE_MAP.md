# Claim–source map

Authority order: frozen artifacts → freezes/configs → `HEADLINES.json` → verifiers → analysis tables → `CROSS_FAMILY_SYNTHESIS.md` → findings/methods → other Markdown.

All numeric claims below were checked against `analysis_v2/tables/verification.md` (69/69) and/or panel `HEADLINES.json` files at `evidex-artifact-v1` (`29102c3`).

| Section | Claim | Value | Denominator | Source | Figure/table | Verification | Placement | Caveat |
|---|---|---|---|---|---|---|---|---|
| 4.1 | GPT-5.4 acc. claim-only → evidence | 88.69% → 96.04%, +7.35 pp | 10,000 claims | `verification.md`; `experiment_summary_balanced_10000_v1.csv` | Table 1 | verify_headlines 69/69 | main | paired, same claims |
| 4.1 | Mini acc. | 84.67% → 95.54%, +10.87 pp | 10,000 claims | same | Table 1 | same | main | |
| 4.1 | Predictions | 40,000 | 2 models × 2 conditions × 10,000 | `source_validation.md` | Design | source validation | main | |
| 4.1 | McNemar GPT-5.4 | χ²=558.3, p≈2e-123 | 10,000 paired | `verification.md`; FINDINGS | text | 69/69 | main | confirmatory |
| 4.1 | McNemar mini | χ²=849.1, p≈1e-186 | 10,000 | same | text | 69/69 | main | |
| 4.2 | GPT-5.4 regressions | 115 (1.15%, CI 0.95–1.36) | 10,000 | FINDINGS; verification | Table 1 | 69/69 | main | |
| 4.2 | Mini regressions | 151 (1.51%, CI 1.28–1.75) | 10,000 | same | Table 1 | 69/69 | main | |
| 4.2 | GPT-5.4 rescues | 850 (8.5%, CI 7.92–9.04) | 10,000 | same | Table 1 | 69/69 | main | |
| 4.2 | Mini rescues | 1,238 (12.4%, CI 11.73–13.00) | 10,000 | same | Table 1 | 69/69 | main | |
| 4.2 | Unique regressions | 226 (40 both, 186 exactly one) | claims, not model-obs. | `unique_claim_counts.csv` | Table 1 | 69/69 | main | 75 GPT-5.4-only + 111 mini-only = 186 |
| 4.2 | Model-obs. regressions | 115 vs 151; χ²=6.59, p=0.010 | paired claims | FINDINGS | text | FINDINGS [C] | main | |
| 4.2 | Transition agreement | 87.3% same class; pred. agree 89.3%→97.2%; κ 0.786→0.944 | 10,000 | verification | text | 69/69 | main | |
| 4.3 | NLI-1 disagree robust / regression | 22.6% / 74.8% | GPT-5.4 transitions | verification; fig6 | Fig. 2 | 69/69 | main | local NLI, not GT |
| 4.3 | NLI-1 mini regression | 76.8% | mini regressions | verification | text | 69/69 | main | |
| 4.3 | NLI-2 ordering | robust 26.2%, rescue 38.1%, resistant 74.4%, regr. 67.8% | GPT-5.4 | verification | app. | 69/69 | appendix/main brief | different architecture |
| 4.3 | Weakly warranted n | 2,462; claim-only acc. 81.0% vs 88.7% | claims | FINDINGS | text | 69/69 | main | 88.7 is rounded 88.69 |
| 4.3 | GPT-5.4 regr. by label | 88 Supported vs 27 Refuted; p=1.8e-8 | 115 regressions | verification | text | 69/69 | main | mini 74 vs 77, p=0.87 |
| 4.3 | Surface vs NLI prediction | regression AUC ~0.53 surface, 0.61 full | CV | verification last row | text | 69/69 | appendix | exploratory |
| 3.6 | Diagnostic cohort | 1,061 = 226+335+250+250 | unique claims | Cursor HEADLINES | Design | 33/33 | main | |
| 3.6 | Judged N | 1,060; SA-000352 filtered | 1,061 | Cursor HEADLINES; LIMITATIONS | Design | 33/33 | main | |
| 4.4 | Grok split | 50.0 / 11.9 / 38.1 (113 / 27 / 86) | 226 regressions | Cursor HEADLINES; synthesis | Tables 2–3; Fig. 3 | 33/33 and 21/21 | main | one family |
| 4.4 | Grok util. CI | 43.5–56.5 | 226 | CROSS_FAMILY_SYNTHESIS | text | synthesis | main | not in HEADLINES.json |
| 4.4 | Grok Stage A/C amb. (regr.) | 45.6% / 38.1% | 226 | full HEADLINES | Fig. 4 | 21/21 | main | |
| 4.4 | Titles / structure resolve | 7.1% / 5.3% | 226 Grok | Cursor HEADLINES | Table 2 | 33/33 | main | |
| 4.4 | No reversal after disclosure | 0.0% both families | 226 | synthesis stage table | text | synthesis | main | |
| 4.5 | GLM Stage A modal / consensus / GLM amb. | 0.862 / 0.831 / 0.223 | 1,060 | CROSS_PANEL; verify_glm | text | GLM verifier | supporting | Stage A only |
| 4.5 | Cursor Stage A amb. | 0.291 | 1,060 | CROSS_PANEL | text | HEADLINES 29.1% | supporting | |
| 4.5 | Residual persistent / resolved | 58.0% = 134/231; 42.0% = 97/231 | 231 leftovers | residual HEADLINES | text | 38/38 | supporting | not 226 regressions |
| 4.5 | Residual judgments | 1,155 | 231×5 | residual HEADLINES | Methods | 38/38 | methods | |
| 4.6 | Claude judgments | 3,390 | 226×5×3 | full HEADLINES | Methods | 21/21 | main | |
| 4.6 | Claude split | 65.9 / 5.3 / 28.8 (149 / 12 / 65) | 226 | full HEADLINES; synthesis | Table 3; Fig. 3 | 21/21 | main | family-sensitive |
| 4.6 | Claude util. CI | 59.5–71.8 | 226 | CLAUDE_FINDINGS / synthesis | text | HEADLINES n + synthesis CI | main | |
| 4.6 | Agreement / κ | 74.3% exact and broad (168/226); κ=0.537 | 226 paired | synthesis; HEADLINES 74.3% | Table 3 | 21/21; κ from synthesis | main | κ not in HEADLINES.json |
| 4.6 | Confusion | 107/20/22 directional to util. | 226 | synthesis matrix | Fig. app. | synthesis | main/app | |
| 4.6 | Shared vs specific residual amb. | Grok 60.0% vs 33.3%; Claude 47.5% vs 24.7% | 40 / 186 | synthesis | Table 4 | synthesis | main | |
| 4.6 | Stage amb. Grok vs Claude | 45.6/42.0/38.1 vs 29.2/28.3/28.8 | 226 | synthesis; HEADLINES | Fig. 4 | 21/21 | main | McNemar p in synthesis |
| 3.8 | Path leak quarantined | 385 unread | 5×77 Stage A batch 01 | ADJUDICATION_LOG | Methods/app | log + REASON | methods | |
| 3.8 | Composition 40/75/111 | 226 | derive_and_blind / METHODS | Design | METHODS | main | |

**Do not confuse:** 10,000 claims ≠ 40,000 predictions ≠ 1,061 cohort ≠ 1,060 judged ≠ 226 regressions ≠ 231 residuals ≠ 1,155 residual judgments ≠ 3,390 Claude-full judgments.
