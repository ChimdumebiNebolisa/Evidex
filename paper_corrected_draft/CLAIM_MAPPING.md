# Old claim → corrected claim (2026-09-28)

"Old" is the pinned historical draft in `paper/` (unchanged). "Corrected" is this draft. Corrected
adjudication numbers come from the 70 accepted Stage C outputs under the dated post-judgment
amendment A1 (`corrections_v2/amendment_2026-09-28/`). The first-valid outputs are reported as
sensitivity. A1 is not preregistered, and the frozen protocol's own primary analysis remains
incomplete.

| # | Old claim (location) | Status | Corrected claim (location) |
|---|---|---|---|
| 1 | 10,000 claims, 40,000 predictions; 88.69→96.04% (+7.35 pp), 84.67→95.54% (+10.87 pp) (abstract, RQ1, Table 1) | Retained | Unchanged; `tab_accuracy.tex` reused from `paper/` |
| 2 | 115/151 regressions; 226 unique (40 both, 186 one; 75/111); McNemar χ²=6.59 (abstract, RQ2) | Retained | Unchanged; marked as observed outcomes, not repeat-run stability |
| 3 | NLI and feature characterization (RQ3 NLI block) | Retained | Unchanged; noted as independent of the corrected stage |
| 4 | Grok three-way split 50.0/11.9/38.1% (abstract, RQ3, Table `tab:mechanism-grok`, Fig. `fig:grok-tax`) | Withdrawn | Replaced by the v2 descriptive categories (Table `tab:diagnostic`): Grok 77/10/2/17/5/44/71. Old values are listed as withdrawn in Appendix `app:historical` |
| 5 | Claude three-way split 65.9/5.3/28.8%; +15.9 pp utilization (abstract, RQ4, Table `tab:cross-family`, Fig. `fig:by-family`) | Withdrawn | Replaced by Claude 106/3/3/14/5/54/41 accepted and 105/3/6/14/5/54/39 first-valid (Table `tab:diagnostic`) |
| 6 | "Utilization failure is largest in both panels"; the ordering replicates (RQ3, "What replicates", conclusion) | Withdrawn | The v2 taxonomy maps onto no legacy category. For Grok, sentence-only gold agreement (77) and final nondecisive (71) overlap; which category is largest depends on the family (Results "What depends on the judge family") |
| 7 | "Half or more … utilization failures"; "closer to a use failure" (discussion) | Replaced | Sentence-only gold agreement (34–47%) is compatible with an evidence-utilization explanation but does not establish it; not a prevalence of GPT failures (Discussion 2) |
| 8 | "Honest interval … 50–66%" (discussion) | Withdrawn | Two instruments do not define an interval; both panels are reported (Discussion 5) |
| 9 | Exact/broad agreement 74.3% (168/226), κ=0.537; 4-item overlap; directional confusion (RQ4, Table `tab:cross-family`, Fig. `fig:confusion`) | Replaced | v2 exact agreement 172/226 = 76.1%, κ=0.673 (accepted); 168/226 = 74.3%, κ=0.651 (first-valid). Stated as not comparable with the old 74.3%. The confusion figure is not reproduced |
| 10 | Stage-wise ambiguity 29.2/28.3/28.8 vs 45.6/42.0/38.1; McNemar p=7.8e-10, 3.4e-7, 7.5e-4 (RQ4, Fig. `fig:stage-amb`) | Partly retained | A/B rates retained (historical A/B judgments, unchanged inputs). C replaced: Grok 31.4%, Claude 18.1% (17.3%). BH-adjusted tests in Table `tab:stage` |
| 11 | Titles resolve 7.1%; structure alone 5.3% (RQ3) | Replaced | Titles 16 (7.1%) retained (A/B only). "5.3% by structure" withdrawn: Stage C resolution is 27/95 among B-nondecisive regressions, and C adds text for 41 regressions, so it is not a structure-only effect |
| 12 | "No decisive consensus is reversed" (RQ3, RQ4) | Retained, re-derived | Holds on the new Stage C in both panels (0 reversals). Losses of decisiveness are reported separately |
| 13 | Shared regressions "stickier" in both families (Table `tab:shared`: 60.0/33.3 Grok, 47.5/24.7 Claude) | Replaced | Final nondecisive 45.0/28.5 Grok (OR 2.05, p_BH=0.059, n.s.), 35.0/14.5 Claude (OR 3.17, p_BH=0.011) |
| 14 | Claude residual 134/231 (58.0%) persistent ambiguity (supporting checks) | Historical only | Appendix `app:historical`; inputs and selection depended on defective Stage C |
| 15 | GLM Stage A 0.862 / 0.831; ambiguity 0.223 vs 0.291 | Retained | Unchanged (Stage A inputs unaffected) |
| 16 | "Nested evidence representations"; Stage C = "reconstructed structured FEVER evidence" (study design) | Replaced | Stage C adds pointers, annotation boundaries and alternative evidence text; it can add information (149 claims, 41 regressions) |
| 17 | Three "diagnostic failure modes" rule taxonomy (introduction, design) | Replaced | Descriptive v2 taxonomy that keeps decisiveness and FEVER agreement separate; post hoc; coauthor review required |
| 18 | "Automated failure-mode prevalence depends partly on the adjudicating family" (abstract, conclusion) | Retained, reworded | Category proportions depend on the family. No failure-mode prevalence is claimed |
| 19 | Claude full panel "3,390 judgments" | Replaced | 2,260 retained A/B plus 1,130 new C judgments. The 3,390 historical judgments stay in the historical record |
| 20 | Contributions (iii)–(iv): decomposition; which parts "survive" | Replaced | (iii) descriptive adjudication on repaired evidence; (iv) family-dependence; (v) audit and execution deviations |
| — | Stage C amendment (new) | Added | Brief methods paragraph (Section 3.9), one limitations paragraph, and Appendix `app:amendment` with the first-valid sensitivity |

## Figures and tables

| Old | Status in the corrected draft |
|---|---|
| `tab_accuracy.tex` | reused unchanged from `paper/tables/` |
| `tab_mechanism.tex`, `tab_cross_family.tex` | withdrawn; replaced by `tables/tab_diagnostic_v2.tex` |
| `tab_shared.tex` | replaced by `tables/tab_shared_v2.tex` |
| — | new: `tables/tab_stage_v2.tex` |
| Fig. transitions, Fig. NLI (`analysis_v2/figures`) | reused unchanged |
| Fig. by-family, taxonomy distribution | replaced by `figures/fig_categories.pdf` (Fig. `fig:categories`) |
| Fig. stage ambiguity | replaced by `figures/fig_stage_nondecisive.pdf` (Fig. `fig:stage`) |
| Fig. confusion, resolution flow | withdrawn |
