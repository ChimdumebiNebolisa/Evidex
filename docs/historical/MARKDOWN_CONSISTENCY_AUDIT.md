# Markdown consistency audit

**Audit target:** commit `7129bd5` (`7129bd5db2f2f4c98797aa58b700755e741b5cdc`)  
**Branch at audit:** `docs/publication-artifact-audit-v1`  
**Scope:** all git-tracked `*.md` files (43). Read-only inspection of Markdown against frozen artifacts, freeze manifests, `HEADLINES.json`, verifiers, analysis tables, and the current final synthesis.  
**This file is the only document created in this pass.** No other files were edited, moved, renamed, deleted, or regenerated. No model inference was run.

**Source-of-truth order used here:** frozen/raw experimental artifacts → freeze manifests / panel configs → committed `HEADLINES.json` registries → independent verifiers / `analysis_v2/tables/verification.md` → canonical analysis tables → `silver_adjudication_v1/claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md` → experiment-specific findings/methods → other Markdown.

Repeated incorrect statements are marked in every file that makes them. Historical truth that is still true for its original experiment is not treated as a defect. Iterative research history is not a defect.

---

## 1. Executive verdict

The **current manuscript-facing layer is scientifically aligned** with the frozen record. Root `README.md`, `REPRODUCING.md`, `docs/STUDY_OVERVIEW.md`, `docs/LIMITATIONS.md`, `silver_adjudication_v1/README.md`, Analysis v2 findings/tables, Cursor `SILVER_FINDINGS.md` (except one historical heading), GLM Stage A report, Claude full `CLAUDE_FINDINGS.md` / `CROSS_FAMILY_SYNTHESIS.md` / `METHODS.md` / `LIMITATIONS.md`, and the Claude residual findings/methods (when read inside that folder) match the headline registries.

The remaining problem is **navigation and chronology, not a second set of scientific numbers**. A reader who starts at the current root README will get the right hierarchy, denominators, and caveats. A reader who lands in three older or supporting files can still be told, in present tense, that the residual Claude panel closed the study, that a “final” synthesis is the residual write-up, or that the next experiment has not been run.

**Do not freeze the public documentation layer until the two critical items below are bannered or pointed.** Do not rewrite historical scientific content to match later results. Smallest truthful patches are enough.

**Counts (this audit):** 43 Markdown files; **2 critical**, **10 major**, **18 minor** discrepancies. Cosmetic issues are listed but not counted in the 18.

---

## 2. Markdown inventory

`git ls-files "*.md"` at `7129bd5` returns **43** files.

| Area | Count | Paths |
|---|---|---|
| Root | 5 | `README.md`, `REPRODUCING.md`, `PUBLICATION_ARTIFACT_AUDIT.md`, `professor_update.md`, `presentation_dossier_comprehensive.md` |
| `docs/` | 5 | `STUDY_OVERVIEW.md`, `DATA_PROVENANCE.md`, `ADJUDICATION_PROTOCOL.md`, `LIMITATIONS.md`, `historical/README.md` |
| `analysis_v2/` | 10 | README; FINDINGS, METHODS, LIMITATIONS, NEXT_EXPERIMENTS, NOVELTY_BOUNDARIES, ANALYSIS_LOG; `tables/verification.md`, `source_validation.md`, `leakage_audit.md` |
| Silver shared | 5 | `silver_adjudication_v1/README.md`, `reports/ADJUDICATION_LOG.md`, three `prompts/*.md` |
| Cursor/Grok | 4 | panel README; SILVER_FINDINGS, LIMITATIONS, CROSS_PANEL_STAGE_A_REPLICATION |
| Claude residual | 7 | panel README; ADJUDICATION_LOG, CLAUDE_FINDINGS, CROSS_FAMILY_SYNTHESIS, FINAL_EVIDEX_STRENGTHENING, LIMITATIONS, METHODS |
| Claude full | 6 | panel README; ADJUDICATION_LOG, CLAUDE_FINDINGS, CROSS_FAMILY_SYNTHESIS, LIMITATIONS, METHODS |
| Provenance note | 1 | `claude_full_regression_panel/cache/discarded/.../REASON.md` |

Relative Markdown links: **45 resolve; 0 broken** (checked by resolving every `[text](target)` that is not `http(s)` / `mailto`). Filename collisions, not missing files, are the link risk.

---

## 3. Canonical-document map

| Role | Canonical file | Status |
|---|---|---|
| Study entry / headline table | `README.md` | Current. Matches verification + full-panel synthesis. |
| Reproduction | `REPRODUCING.md` | Current. Level 1 matches `scripts/verify_all_headlines.py` at this commit. |
| Architecture walkthrough | `docs/STUDY_OVERVIEW.md` | Current supporting map. Defers to root README for numbers. |
| Final scientific synthesis | `silver_adjudication_v1/claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md` | **The only current final synthesis.** |
| Claude full findings | `.../claude_full_regression_panel/reports/CLAUDE_FINDINGS.md` | Current for Claude A→B→C on 226. |
| Cursor/Grok findings | `.../cursor_panel/reports/SILVER_FINDINGS.md` | Current for Grok A→B→C on judged N = 1,060 / 226 regressions. One section is historical. |
| GLM Stage A | `.../cursor_panel/reports/CROSS_PANEL_STAGE_A_REPLICATION.md` | Current supporting. Stage A only. |
| Claude residual findings | `.../claude_residual_panel/reports/CLAUDE_FINDINGS.md` | Current for the 231-item residual question only. |
| Intermediate residual synthesis | `.../claude_residual_panel/reports/FINAL_EVIDEX_STRENGTHENING.md` | Historically valid residual write-up; **bannered as intermediate**. Body still speaks as if the study closed. |
| Residual-only comparison | `.../claude_residual_panel/reports/CROSS_FAMILY_SYNTHESIS.md` | Correct science, **same filename** as the canonical final synthesis. |
| Analysis v2 science | `analysis_v2/reports/FINDINGS.md` + `tables/verification.md` | Current for the 10K / 40K layer. |
| Study-level limits | `docs/LIMITATIONS.md` | Current. Layer lists remain authoritative. |
| Protocol (do not edit) | `silver_adjudication_v1/prompts/*.md` | Frozen protocol, not results. |
| Prior packaging audit | `PUBLICATION_ARTIFACT_AUDIT.md` | Snapshot of `9a4ee4e`, not of `7129bd5`. |

---

## 4. File-by-file classification table

Primary status is exactly one of: `canonical-current`, `supporting-current`, `historical-clearly-marked`, `historical-not-clearly-marked`, `planning/superseded`, `redundant-current`, `contradictory`, `needs-manual-review`.

| Path | Role | Status | Defer to | Edit recommended? |
|---|---|---|---|---|
| `README.md` | Study entry, hierarchy, headlines, Level 1 commands | canonical-current | verification.md; Cursor/Claude/residual HEADLINES.json; full CROSS_FAMILY_SYNTHESIS | No (optional: “Grok-only” wording, §8) |
| `REPRODUCING.md` | Level 1/2/3 reproduction | canonical-current | `scripts/verify_all_headlines.py`, `verify_glm_stage_a.py` | No |
| `docs/STUDY_OVERVIEW.md` | Architecture + layer table | canonical-current | Root README; full CROSS_FAMILY_SYNTHESIS | No |
| `docs/DATA_PROVENANCE.md` | License / FEVER / wiki provenance | canonical-current | Committed sample + experiment files | No |
| `docs/ADJUDICATION_PROTOCOL.md` | Pointers to frozen protocol | canonical-current | `prompts/*.md` | No |
| `docs/LIMITATIONS.md` | Study-level limits | canonical-current | Layer LIMITATIONS + full synthesis | Optional “validation” → “replication” |
| `docs/historical/README.md` | Index of pre-completion docs | historical-clearly-marked | Root README | Optional: add PUBLICATION_ARTIFACT_AUDIT and shared ADJUDICATION_LOG |
| `analysis_v2/README.md` | v2 layout + Level 2 run | supporting-current | FINDINGS, REPRODUCING | Should: mark NEXT_EXPERIMENTS as historical |
| `analysis_v2/reports/FINDINGS.md` | v2 scientific findings | canonical-current | `tables/verification.md` | Optional: one pointer that silver panels later exist |
| `analysis_v2/reports/METHODS.md` | v2 methods | canonical-current | v2 source + verification | No |
| `analysis_v2/reports/LIMITATIONS.md` | v2 limits | canonical-current | FINDINGS | No |
| `analysis_v2/reports/NOVELTY_BOUNDARIES.md` | v2 novelty claims | supporting-current | FINDINGS | No |
| `analysis_v2/reports/ANALYSIS_LOG.md` | v2 anti-cherry-pick log | supporting-current | FINDINGS / verification | No (rounding 88.7) |
| `analysis_v2/reports/NEXT_EXPERIMENTS.md` | Pre-silver wishlist | planning/superseded | historical/README; later panel reports | **Yes — banner only** |
| `analysis_v2/tables/verification.md` | 69/69 headline checks | canonical-current | paired CSVs / verifier | No |
| `analysis_v2/tables/source_validation.md` | 40K source invariants | canonical-current | experiment CSVs | No |
| `analysis_v2/tables/leakage_audit.md` | Leakage checks | supporting-current | leakage script | No |
| `silver_adjudication_v1/README.md` | Four-artifact map + Level 1 | canonical-current | panel reports | No |
| `silver_adjudication_v1/reports/ADJUDICATION_LOG.md` | Shared silver execution log | contradictory | Cursor log + residual log + **full-panel ADJUDICATION_LOG** | **Yes — banner + one line that Claude full followed** |
| `silver_adjudication_v1/prompts/judge_rubric.md` | Frozen judge rubric | canonical-current | (protocol) | Leave untouched |
| `silver_adjudication_v1/prompts/progressive_disclosure_protocol.md` | Frozen A→B→C protocol | canonical-current | (protocol) | Leave untouched |
| `silver_adjudication_v1/prompts/resolver_rubric.md` | Frozen Cursor resolver rubric | canonical-current | (protocol) | Leave untouched |
| `silver_adjudication_v1/cursor_panel/README.md` | Primary Grok panel entry | supporting-current | SILVER_FINDINGS | **Yes — fix Reproduce paths** |
| `silver_adjudication_v1/cursor_panel/reports/SILVER_FINDINGS.md` | Grok A→B→C findings | canonical-current | `cursor_panel/reports/HEADLINES.json` | Should: retitle historical section |
| `silver_adjudication_v1/cursor_panel/reports/LIMITATIONS.md` | Grok limits | supporting-current | SILVER_FINDINGS | No |
| `silver_adjudication_v1/cursor_panel/reports/CROSS_PANEL_STAGE_A_REPLICATION.md` | GLM vs Cursor Stage A | supporting-current | HEADLINES + freeze Stage A | No |
| `silver_adjudication_v1/claude_residual_panel/README.md` | Residual panel entry | contradictory | residual CLAUDE_FINDINGS; full CROSS_FAMILY_SYNTHESIS for study-level final | **Yes — role + start-here** |
| `silver_adjudication_v1/claude_residual_panel/reports/CLAUDE_FINDINGS.md` | Residual findings | supporting-current | residual HEADLINES.json | Optional “validation” wording |
| `silver_adjudication_v1/claude_residual_panel/reports/CROSS_FAMILY_SYNTHESIS.md` | Residual-only comparison | redundant-current | residual HEADLINES; **not** the study-level final | Should: filename/title note in header |
| `silver_adjudication_v1/claude_residual_panel/reports/FINAL_EVIDEX_STRENGTHENING.md` | Intermediate residual synthesis | historical-clearly-marked | Banner already points to full synthesis | Should: one sentence in “What is finished” |
| `silver_adjudication_v1/claude_residual_panel/reports/METHODS.md` | Residual methods | supporting-current | residual config / HEADLINES | Optional “validation” wording |
| `silver_adjudication_v1/claude_residual_panel/reports/LIMITATIONS.md` | Residual limits | supporting-current | residual FINDINGS | No |
| `silver_adjudication_v1/claude_residual_panel/reports/ADJUDICATION_LOG.md` | Residual execution log | supporting-current | residual freezes | No |
| `silver_adjudication_v1/claude_full_regression_panel/README.md` | Main Claude replication entry | supporting-current | full HEADLINES + CROSS_FAMILY_SYNTHESIS | Should: κ 0.537; lead Reproduce with verifier |
| `silver_adjudication_v1/claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md` | Final synthesis | canonical-current | full HEADLINES.json + comparison tables | No |
| `silver_adjudication_v1/claude_full_regression_panel/reports/CLAUDE_FINDINGS.md` | Claude A→B→C findings | canonical-current | full HEADLINES.json | No |
| `silver_adjudication_v1/claude_full_regression_panel/reports/METHODS.md` | Claude full methods | canonical-current | protocol + HEADLINES | Optional “silver validation” wording |
| `silver_adjudication_v1/claude_full_regression_panel/reports/LIMITATIONS.md` | Claude full limits | canonical-current | CROSS_FAMILY_SYNTHESIS | No |
| `silver_adjudication_v1/claude_full_regression_panel/reports/ADJUDICATION_LOG.md` | Claude full execution log | supporting-current | freezes / REASON.md | No |
| `.../cache/discarded/.../REASON.md` | Duplicate Stage B provenance | historical-clearly-marked | full ADJUDICATION_LOG | Leave untouched |
| `professor_update.md` | April 2026 1K status | historical-clearly-marked | Root README | Leave scientific body untouched |
| `presentation_dossier_comprehensive.md` | 10K behavioral talk dossier | historical-clearly-marked | Root README; verification.md | Leave scientific body untouched |
| `PUBLICATION_ARTIFACT_AUDIT.md` | Packaging audit of `9a4ee4e` | historical-not-clearly-marked | This file + current README | **Yes — snapshot banner only** |

---

## 5. Critical contradictions

These would let a reasonable reader treat a **supporting or incomplete chronology** as the current scientific close of Evidex.

### C1. Shared silver log closes the study before Claude full

| Field | Detail |
|---|---|
| File | `silver_adjudication_v1/reports/ADJUDICATION_LOG.md` |
| Location | “Cursor consensus, resolver, unblind” and “Claude residual Stage C” (approx. lines 155–171) |
| Current wording | “One next experiment recommended, not run.” / “Evidex strengthening experiment sequence is complete; no further family is planned.” |
| Why problematic | This is the parent-level silver log. It has **no superseded banner**. Claude full A→B→C (226 regressions, 3,390 judgments) is absent. Present-tense closure is false at `7129bd5`. |
| Canonical evidence | `claude_full_regression_panel/reports/ADJUDICATION_LOG.md`; `freezes/missing_work_manifest.json` completeness; `reports/HEADLINES.json` (`judgments_total` 3390); full `CROSS_FAMILY_SYNTHESIS.md`. |
| Smallest fix | Add a top banner: this log ends at the residual panel; the later Claude full panel is recorded in `claude_full_regression_panel/reports/ADJUDICATION_LOG.md`. Do **not** rewrite the 2026-08-22/23 entries. |
| Severity | `critical` |

### C2. Residual panel README still presents the intermediate “final” as the start

| Field | Detail |
|---|---|
| File | `silver_adjudication_v1/claude_residual_panel/README.md` |
| Location | Title sentence and last paragraph |
| Current wording | “Cross-family validation of the Cursor/Grok Stage C residual…” / “Start with `reports/CLAUDE_FINDINGS.md` and `reports/FINAL_EVIDEX_STRENGTHENING.md`.” |
| Why problematic | The file is a **current** folder entry with no banner. It never mentions the later 226-item A→B→C panel or the canonical synthesis. Combined with `FINAL_EVIDEX_STRENGTHENING.md`’s title and leftover “last planned” body, a reader who enters `claude_residual_panel/` can take residual 58.0/42.0 as the study-level cross-family result. “Validation” overstates what family agreement is. |
| Canonical evidence | Root README layers 5 vs 6; residual HEADLINES (`residual_n` 231, not 226); full HEADLINES (`cohort_n` 226, `judgments_total` 3390); full CROSS_FAMILY_SYNTHESIS. |
| Smallest fix | One sentence: supporting Stage C test on 231 Grok leftovers, not the main Claude replication. Start with residual `CLAUDE_FINDINGS.md`. Study-level final synthesis is the full-panel `CROSS_FAMILY_SYNTHESIS.md`. Keep FINAL as optional historical write-up. |
| Severity | `critical` |

---

## 6. Stale but historically valid statements

These were true when written. They become misleading only if read as **current project status**.

| File | Location | Current wording | Why stale now | Marking today | Severity |
|---|---|---|---|---|---|
| `FINAL_EVIDEX_STRENGTHENING.md` | Banner (good) vs “What is finished” | “This was the last planned strengthening experiment. No further model family… is required” | Claude full A→B→C was later run | Banner present; **body still closes the study** | major |
| `FINAL_EVIDEX_STRENGTHENING.md` | “Final mechanism assessment” | “Those full-panel shares are unchanged; Claude does not re-open them.” | True for the *residual* design (Claude never saw the 113+27 already-decisive Grok regressions). False as a claim about later Claude full. | Banner helps; sentence lacks “in this residual experiment” | major |
| `FINAL_EVIDEX_STRENGTHENING.md` | H1 / § “Final mechanism assessment” | Title still “Final …” | Historically the residual close-out title | Banner says intermediate | minor |
| `SILVER_FINDINGS.md` | `## One next experiment (not run)` | Heading plus original residual-panel proposal | Residual and full Claude panels were run | Blockquote historical note is present; **heading still reads current** | major |
| `silver_adjudication_v1/reports/ADJUDICATION_LOG.md` | Cursor unblind / residual close | See C1 | See C1 | None | critical (already counted) |
| `analysis_v2/reports/NEXT_EXPERIMENTS.md` | Whole file, especially item 1 | Ranked “next” human + representation rerun | Grok/Claude A→B→C later implemented the representation-disclosure test with **silver** judges, not humans | Indexed in `docs/historical/README.md` only; **file itself unmarked** | major |
| `PUBLICATION_ARTIFACT_AUDIT.md` | §1 | “The repository is **not yet publication-ready**.” Root README “scientifically stale.” | Describes `9a4ee4e`. Later commits (`eca7b38`, `7129bd5`) implemented the navigation layer it asked for. | Header has audit date + commit, but present tense after that | major |
| `professor_update.md` | Body | 1,000-claim wiki-shard blocker | 10K run completed | Banner present | leave untouched |
| `presentation_dossier_comprehensive.md` | Body | 10K-only “main finding”; “Final balanced sample” | Stops before analysis_v2 and silver | Banner present | leave untouched |
| `REASON.md` | Whole file | Duplicate Stage B quarantine | Correct provenance | Path + title mark it superseded | leave untouched |

Do **not** rewrite the historical scientific numbers in these files to match Claude full. Preserve provenance.

---

## 7. Numeric discrepancies

Headline numbers in the **current** layer match the registries. Conflicts are rounding, omitted κ in `HEADLINES.json`, or stale closure language—not a second 50.0/65.9 science.

### 7.1 Exact agreement with canonical artifacts

Checked against `analysis_v2/tables/verification.md` (69/69), `cursor_panel/reports/HEADLINES.json`, `claude_residual_panel/reports/HEADLINES.json`, `claude_full_regression_panel/reports/HEADLINES.json`, and `CROSS_PANEL_STAGE_A_REPLICATION.md`.

| Claim | Canonical | Current Markdown that matches |
|---|---|---|
| GPT-5.4 88.69% → 96.04%, +7.35 pp | verification.md | README, FINDINGS, REPRODUCING |
| Mini 84.67% → 95.54%, +10.87 pp | verification.md | README, FINDINGS |
| 226 unique / 40 both / 186 exactly one | verification.md | README, FINDINGS, Claude full README |
| 40,000 predictions / 10,000 claims | source_validation / verification | README, analysis README, STUDY_OVERVIEW |
| Grok 50.0 / 11.9 / 38.1 (113 / 27 / 86) | Cursor + full HEADLINES | README, SILVER_FINDINGS, full README, synthesis |
| Claude 65.9 / 5.3 / 28.8 (149 / 12 / 65) | full HEADLINES | README, CLAUDE_FINDINGS, synthesis |
| Exact and broad taxonomy agreement 74.3% (168/226) | full HEADLINES | README, synthesis |
| Residual 58.0% = 134/231; 42.0% = 97/231 | residual HEADLINES | README, residual FINDINGS/synthesis/FINAL |
| GLM n=1060; modal 0.862; consensus 0.831; GLM amb. 0.223 | CROSS_PANEL + Cursor HEADLINES | README, REPRODUCING, SILVER_FINDINGS, CROSS_PANEL |
| 3,390 Claude full judgments | full HEADLINES | README, Claude full README/METHODS |
| 1,061 cohort / 1,060 judged | Cursor HEADLINES | SILVER_FINDINGS, STUDY_OVERVIEW, FINAL §5 |
| Cursor pairwise 89.8 / 95.3 / 95.4; Fleiss A 0.846 | Cursor HEADLINES | SILVER_FINDINGS, shared log |
| Residual 1,155 judgments; 87.9%; Fleiss 0.802; 56.3% label agree | residual HEADLINES | residual FINDINGS |
| Presentation overall 86.68% → 95.79% (+9.11 pp) | mean of the two models’ verification accuracies | `presentation_dossier_comprehensive.md` (bannered; **overall**, not per-model) |

Cohen’s κ **0.537** is stated in full `CROSS_FAMILY_SYNTHESIS.md` and root README. It is **not** a `HEADLINES.json` field. Independent verifiers at this commit check 74.3% agreement, not κ. Treat 0.537 as synthesis-canonical, not registry-canonical.

### 7.2 Rounding-only (not contradictions)

| File | Location | Wording | Canonical | Severity |
|---|---|---|---|---|
| `claude_full_regression_panel/README.md` | Result paragraph | “κ = 0.54” | 0.537 in CROSS_FAMILY_SYNTHESIS | minor |
| `analysis_v2/reports/FINDINGS.md` | Finding 2 | “88.7% for GPT-5.4” claim-only on weakly-warranted contrast | 88.69 in verification.md | minor |
| `analysis_v2/reports/ANALYSIS_LOG.md` | Chronology item 7 | “81.0% vs 88.7%” | same | minor |

### 7.3 Same digit string, different legitimate denominator

Do **not** treat these as contradictions when the document labels the denominator.

| Digit | Meaning A | Meaning B |
|---|---|---|
| 38.1% | Grok residual-ambiguity share of **226 regressions** | NLI-2 disagreement among GPT-5.4 **rescues** (`verification.md` / FINDINGS) |
| 5.3% | Claude representation-sensitive share of 226 | Grok “resolved only by structure” share of 226 (`reg_resolved_only_by_structure_pct`) |
| 42.0% | Residual Claude-resolved / “Grok-only” 97/231 | Residual high-consensus rate (same 97/231) |
| 0.54 | Claude full README rounded κ | FINDINGS logistic coef on Refuted (−0.54), different analysis |

### 7.4 Stale numeric *status* (numbers themselves still valid)

Grok 50.0/11.9/38.1 in FINAL and SILVER_FINDINGS remains correct for Cursor/Grok. Residual 58.0/42.0 remains correct for 231 leftovers. The error is **role**, not arithmetic.

### 7.5 Stage B overall 24.7%

`FINAL_EVIDEX_STRENGTHENING.md` §5: “Ambiguity falls 29.1% → 24.7% → 21.8% overall.”  
29.1% and 21.8% are in Cursor HEADLINES. 24.7% is Stage B (241 Ambiguous + 21 Unresolved) / 1,060 = 24.717%. Consistent with SILVER_FINDINGS consensus table; not a HEADLINES field. **No discrepancy.**

---

## 8. Denominator / cohort ambiguities

No current manuscript-facing file equates 231 leftovers with 226 regressions, or says Claude judged the 1,060-item diagnostic cohort. Root README and STUDY_OVERVIEW label denominators explicitly.

Places a reader could still slip:

| File | Location | Wording | Risk | Severity |
|---|---|---|---|---|
| `claude_residual_panel/README.md` | Scope line | “residual items only (expected n = 231)” without “not 226 regressions” | Folder entry; nearby FINAL title | major (role), see C2 |
| Residual `CROSS_FAMILY_SYNTHESIS.md` | “Reading” | “That mixture is the **cross-family result**.” | True for the 231-item question; same *filename* as the 226-item synthesis | major |
| Root README | Residual row | “42.0% Grok-only (97/231)” | Those 97 are Claude-**decisive**, not still ambiguous | minor |
| Residual CROSS_FAMILY | Result bullets | “Grok-only **ambiguity** (Claude high-consensus decisive): **42.0%**” | Parenthetical saves it; the label fights the parenthesis | minor |
| `SILVER_FINDINGS.md` | Resolver line | “Stage C 231 items” | Resolver queue size, not the residual experiment definition (same 231 leftovers) | cosmetic if read with “resolver” |
| `docs/STUDY_OVERVIEW.md` | ASCII map | “1,061-claim diagnostic cohort (226 / 335 / 250 / 250)” then Claude “226 regressions” | Correct; dashed vs solid is easy to miss in ASCII | minor |
| `analysis_v2/reports/FINDINGS.md` | Unique claims | “226 regress… counts are claims, never model-observations” | Good. 115+151 model-observations ≠ 226 | none |
| `presentation_dossier_comprehensive.md` | Abstract | +9.11 pp overall | Correct pooled rate; not +7.35 / +10.87 | leave (bannered) |

**Intentional different N’s (keep):** 10,000 claims; 40,000 predictions; 1,061 cohort claims; 1,060 judged; 226 unique regressions; 231 Grok Stage C leftovers; 3,390 Claude full judgments; 1,155 Claude residual judgments; 801 Cursor resolver items (308+262+231).

---

## 9. Experiment-role discrepancies

### GLM

Current docs generally get this right: Stage A replication only; partial Stage B provenance; no completed GLM A→B→C.

| File | Issue | Severity |
|---|---|---|
| `silver_adjudication_v1/reports/ADJUDICATION_LOG.md` § “Stage freezes” / deviations | “Stage C structured evidence reconstructed from the official FEVER wiki archive” appears under an early GLM-era log. This is **evidence reconstruction**, not GLM Stage C judging. Easy to misread as a finished GLM Stage C panel. | minor |
| `PUBLICATION_ARTIFACT_AUDIT.md` | Correctly says (at `9a4ee4e`) that `silver_adjudication_v1/README.md` still described a GLM-only study. That README is no longer written that way. The audit sentence is **historically true**, not current. | major as snapshot-as-current (see §6) |
| Cursor README / SILVER_FINDINGS / CROSS_PANEL / docs/LIMITATIONS / silver README | Explicitly exclude incomplete GLM B/C from A→B→C math | none |

No file presents incomplete GLM Stage B/C as scientific evidence.

### Claude residual vs Claude full

| File | Issue | Severity |
|---|---|---|
| Residual README | “Cross-family validation”; start FINAL; no mention of full panel | critical (C2) |
| Residual CROSS_FAMILY filename + last sentence | Same basename as the final synthesis; “the cross-family result” | major |
| Residual METHODS title | “Narrow validation of the frozen Cursor/Grok Stage C residual” | major (word “validation”) / role is otherwise correct (231, Stage C only, resolver not run) |
| FINAL §6 heading | “Claude Stage C residual validation (this study)” | minor given banner |
| Full-panel README / METHODS | Correctly separate “earlier 231-item” from “all 226”; “None of its judgments are spliced into this one.” | none |
| Root README / STUDY_OVERVIEW / silver README | Layers 5 vs 6 distinguished | none |

No file says Claude judged all 1,060 cohort items. No file says the 231 leftovers are 231 regressions.

### “Claude replication” collapse

Current root/silver READMEs do **not** collapse GLM, residual, and full Claude into one “second panel.” The collapse risk is **filename + residual README**, not the new navigation layer.

---

## 10. Scientific-language overclaims

Quote → smallest correction. None of these are in the canonical full synthesis’s lead (that document already denies human GT and FEVER relabel).

| File | Phrase | Why too strong | Smallest correction | Severity |
|---|---|---|---|---|
| Residual README L3 | “Cross-family **validation** of the Cursor/Grok Stage C residual” | Family agreement is robustness/replication, not validation against truth | “Cross-family **robustness test** of …” | major |
| Residual METHODS L5 | “Narrow **validation** of the frozen Cursor/Grok Stage C residual” | Same | “Narrow **robustness test** …” | major |
| Residual CLAUDE_FINDINGS L4 | “cross-family residual **validation**” | Same; next sentence correctly denies human validation | “residual **robustness test**” | minor |
| Full-panel README L16 | “cross-family silver **validation**, not human ground truth” | Immediate negation helps; “validation” still invites “the taxonomy is validated” | “cross-family silver **replication**, not human ground truth” | minor |
| Full-panel METHODS L15 | Same phrase | Same | Same swap | minor |
| `docs/LIMITATIONS.md` L7 | “Agreement across families is cross-family silver **validation**.” | Next sentence denies a new gold standard | “silver **replication** / robustness signal” | minor |
| Shared ADJUDICATION_LOG L177 | “Claude residual **validation** is a second generative family” | Same family-as-truth risk | “Claude residual **panel** is a second generative family” | minor |
| FINAL L64 | “Claude does not re-open them.” | Sounds like a study-level invariance | “This residual design does not re-judge those items; Claude full later did.” (banner already exists; add four words: “in this residual experiment,”) | major |
| Residual CROSS_FAMILY L46–47 | “That mixture is the **cross-family result**.” | Sounds study-final | “That mixture is the **residual-panel** cross-family result.” | major |
| SILVER_FINDINGS L91 | “**Warrant ambiguity** is the largest residual: 38.1%” | Fine if “residual” = leftover after C. Can be heard as “largest mechanism” even though utilization is 50.0%. | Keep numbers; optionally “largest **leftover** bucket (residual ambiguity 38.1%); utilization is larger at 50.0%.” | minor |
| Root README L90 | “Both families independently find all three mechanisms” | Acceptable if “mechanism” = disclosure taxonomy. Slightly strong vs “failure-mode categories.” | Already caveated in the next sentences. Optional: “failure-mode categories.” | cosmetic |
| `docs/LIMITATIONS.md` / full LIMITATIONS / README | Progressive disclosure / no GPT internals | Already correctly **denied**. No overclaim. | Leave | none |
| FINDINGS L131–135 | Decomposition is a “hypothesis generator”; “human review … is required” | Correct for v2. Can be read as “the study never decomposed regressions.” | Add: “Later silver A→B→C panels address this as **automated** adjudication, not human review.” | minor |

**Not flagged as overclaim (already careful):** full CROSS_FAMILY_SYNTHESIS lead; full LIMITATIONS “no window into GPT internals”; Cursor LIMITATIONS “No causal claim about GPT”; root README FEVER/gold/silver caveats; residual LIMITATIONS “No causal claim about GPT.”

**Not found:** wording that judge disagreement *establishes* FEVER annotation error; wording that 50.0/11.9/38.1 is judge-independent; wording that 65.9/5.3/28.8 is the true decomposition. The current synthesis explicitly rejects both point estimates as universal.

---

## 11. Terminology inconsistencies

### Intentional distinctions (preserve)

| Term | Meaning | Keep |
|---|---|---|
| Gold evidence | FEVER-designated evidence | Yes. Current docs do not say judges relabel FEVER. |
| Silver adjudication | Automated model-based labels (Grok / GLM / Claude) | Yes. |
| Residual ambiguity | Taxonomy bucket after Stage C (Grok 86/226; Claude 65/226) | Yes. Code labels `silver_*`. |
| Persistent ambiguity | Residual-panel leftover that stays Ambiguous/Unresolved under Claude (134/231) | Yes. Different experiment. |
| Warrant ambiguity | Prose for leftover insufficiency of evidence for a decisive silver verdict | Overlaps residual ambiguity; used in Grok findings / FINAL |
| Grok-only / Claude-resolved | 97/231 Claude high-consensus decisive | Same quantity; two names |
| Representation-sensitive | Broad bucket: title-sensitive + structure-sensitive | Taxonomy in METHODS |
| `silver_title_context_sensitive` / `silver_structured_evidence_sensitive` | Fine labels rolled into representation-sensitive | Keep in methods/code |
| `silver_clear_evidence_utilization_failure` | Fine label for utilization | Keep in methods/code |

### Confusing aliases (manuscript-facing)

Recommend one public term; do not rename code/taxonomy strings.

| Concept | Names now in current docs | Canonical manuscript term | Notes |
|---|---|---|---|
| Utilization | evidence-utilization failure; utilization failure; clear evidence-utilization failure; model-utilization failure (`analysis_v2/README.md`) | **evidence-utilization failure** | “model-utilization” is the pre-silver v2 name. Keep in v2; don’t use it in silver/manuscript tables. |
| Representation | representation-sensitive; representation-sensitivity; representation-sensitive category; evidence-representation failure (v2 README) | **representation-sensitive** | Fine labels (title / structure) stay in methods. |
| Leftover after C (226) | residual ambiguity; warrant ambiguity; Stage C ambiguity | **residual ambiguity** | “Warrant ambiguity” as informal synonym is OK if first use points at the taxonomy bucket. |
| Leftover after residual Claude (231) | persistent ambiguity; persistent cross-family ambiguity | **persistent ambiguity** | Do not call this residual ambiguity without “of the 231.” |
| 97/231 | Grok-only ambiguity; Grok-only; high-consensus resolution; claude_resolved | **Claude-resolved (Grok-only leftover)** | Drop “Grok-only ambiguity” as the primary name. |
| Cross-family agreement | validation; silver validation; replication; robustness | **replication** (full A→B→C); **robustness test** (residual Stage C); **Stage A replication** (GLM) | Never “validated the taxonomy.” |
| Mechanism | mechanism; failure-mode; taxonomy | **failure-mode category** in caveats; **mechanism** OK in tables if LIMITATIONS are adjacent | Do not imply GPT internals. |

---

## 12. Redundancy / ownership analysis

| Cluster | Files | Classification | Action |
|---|---|---|---|
| Study overview | Root README mermaid + `docs/STUDY_OVERVIEW.md` ASCII | **Useful layered documentation** | Keep both. Overview already defers numbers to README. |
| Final synthesis | Full `CROSS_FAMILY_SYNTHESIS.md` vs residual `CROSS_FAMILY_SYNTHESIS.md` vs FINAL vs PUBLICATION_ARTIFACT_AUDIT §1 | **Confusing duplication** (same filename + “final” title on an intermediate file) | Do not delete residual files. Add filename/role notes. One final synthesis only. |
| Residual results | residual CLAUDE_FINDINGS + residual CROSS_FAMILY + FINAL | **Harmless repetition** of 58.0/42.0 if roles stay labeled; **confusing** while FINAL is the README start-here | Change residual README start-here only |
| Limitations | `docs/LIMITATIONS.md` + four layer LIMITATIONS | **Useful layered documentation** | Keep |
| Reproduction | README Level 1 + REPRODUCING + panel READMEs | **Useful layered** at root/silver; **confusing** in `cursor_panel/README.md` and Claude full README (wrong cwd / judge commands) | Fix those two Reproduce blocks |
| Claude findings filename | two `CLAUDE_FINDINGS.md` | **Useful layered** if paths are fully qualified (root README does this). **Ambiguous** in a bare `CLAUDE_FINDINGS.md` citation | Always cite with directory |
| Prior audit vs this audit | `PUBLICATION_ARTIFACT_AUDIT.md` vs this file | **Useful layered** if the first is dated to `9a4ee4e` | Banner the first; do not merge |
| Experiment architecture diagrams | Root mermaid ×2 + STUDY_OVERVIEW ASCII | **Useful layered** | No contradiction found between mermaid and text at `7129bd5` |
| Result tables | README key-findings vs synthesis table vs CLAUDE_FINDINGS table | **Harmless repetition**; numbers agree | Keep |

Do not delete overlapping reports. Consolidate **pointers**, not science.

---

## 13. Broken or misleading links

**Broken relative links:** none (45/45 exist).

**Misleading / historically wrong target for a “current” citation:**

| From | Link / pointer | Problem | Severity |
|---|---|---|---|
| Residual README | `reports/FINAL_EVIDEX_STRENGTHENING.md` as co-start | Intermediate file; bannered, but advertised as the place to start | critical (C2) |
| Residual FINAL banner | `../../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md` | **Correct** target | none |
| Root README supporting table | FINAL as “Intermediate residual synthesis” | Correct role | none |
| Bare `CROSS_FAMILY_SYNTHESIS.md` or `CLAUDE_FINDINGS.md` in any future citation | Two files each | Filename collision | major (ownership), no current broken link |
| `docs/historical/README.md` | Does not list `PUBLICATION_ARTIFACT_AUDIT.md` or shared `ADJUDICATION_LOG.md` | Reader may treat those as current | minor |
| `PUBLICATION_ARTIFACT_AUDIT.md` | Many links to then-stale README / silver README | Correct for `9a4ee4e`; misleading if taken as `7129bd5` | major |

**Ambiguous duplicate filenames:**

- `CLAUDE_FINDINGS.md` — residual vs full  
- `CROSS_FAMILY_SYNTHESIS.md` — residual vs full  
- `ADJUDICATION_LOG.md` — shared vs residual vs full  
- `LIMITATIONS.md` / `METHODS.md` — many layers (expected)

---

## 14. Reproducibility-instruction discrepancies

**Canonical Level 1 at `7129bd5`** (`scripts/verify_all_headlines.py`):

1. `analysis_v2/src/verify_headlines.py`  
2. `silver_adjudication_v1/src/verify_headlines.py --panel cursor`  
3. `silver_adjudication_v1/src/verify_glm_stage_a.py` (read-only)  
4. `silver_adjudication_v1/claude_residual_panel/src/verify_headlines.py`  
5. `silver_adjudication_v1/claude_full_regression_panel/src/verify_headlines.py`  

Root README, REPRODUCING.md, and `silver_adjudication_v1/README.md` match this. They warn that `--panel cursor` is required and that `verify_glm_stage_a.py` does not write. REPRODUCING comments out `cross_panel_stage_a.py` as optional Level 2 **write**. Good.

| File | Instruction | Problem | Severity |
|---|---|---|---|
| `cursor_panel/README.md` § Reproduce | `python run_all.py --panel cursor` then `python src/verify_headlines.py --panel cursor` | Both scripts live in `silver_adjudication_v1/`, not `cursor_panel/`. From this README’s directory the commands fail. `run_all.py` is an orchestrator, not Level 1. | major |
| `claude_full_regression_panel/README.md` § Reproduce | Leads with `derive_and_blind.py`, `run_judges.py packets`, ingest/freeze, `analyze.py unblind` | Last line says judging is not rerunnable. The block still looks like the normal reproduce path and would **write** if followed. Conflicts with REPRODUCING Level 1/3. | major |
| Residual README | No verifier command at all | Residual METHODS does list `python src/verify_headlines.py` (correct from that folder) | minor |
| `analysis_v2/README.md` § Reproduce | `cd analysis_v2` **after** `pip install` / `spacy download` run from implied parent | Order is slightly awkward; `run_all.py` path is correct once cwd is `analysis_v2`. Points at REPRODUCING for Level 1. | cosmetic |
| `PUBLICATION_ARTIFACT_AUDIT.md` | Level 1 missing Claude full; no `verify_glm_stage_a.py`; no `verify_all_headlines.py` | True at `9a4ee4e`; false as current instructions | major (snapshot) |
| REPRODUCING / README | Tests via `scripts/run_all_tests.py` or four separate suites | Matches the collision note about `src/run_judges.py` | none |

No **current** Level 1 doc tells a reader to run a write-producing GLM script as the normal verification path.

---

## 15. Historical-document status

| File | Could a reader mistake it for current science? | Banner / index enough? | Recommendation |
|---|---|---|---|
| `professor_update.md` | Only if banner skipped (1K, wiki blocker, old repo name) | Yes | Leave untouched |
| `presentation_dossier_comprehensive.md` | Only if banner skipped (10K-only, pooled +9.11) | Yes | Leave untouched |
| `docs/historical/README.md` | No — it is the index | Yes | Optional: list two more files |
| `NEXT_EXPERIMENTS.md` | **Yes** — reads as a live ranked plan | Indexed only | Banner on the file |
| `FINAL_EVIDEX_STRENGTHENING.md` | **Possible** — banner good; H1 “Final”; body “last planned” | Partial | One sentence in “What is finished” |
| `SILVER_FINDINGS.md` historical section | **Possible** if someone only reads the heading | Note under heading | Rename heading |
| Shared `ADJUDICATION_LOG.md` | **Yes** | No | Banner (C1) |
| `PUBLICATION_ARTIFACT_AUDIT.md` | **Yes** for repo-readiness, not for 50.0/65.9 science | Commit in header, present-tense body | Snapshot banner |
| `REASON.md` | No | Path + title | Leave untouched |
| Prompts | No (protocol) | N/A | Leave untouched |
| Layer FINDINGS/METHODS from completed panels | No if read as that panel | N/A | Preserve |

---

## 16. Recommended corrections ranked

### Must fix before repository freeze

1. Banner `silver_adjudication_v1/reports/ADJUDICATION_LOG.md` and point to the Claude full log (C1).  
2. Rewrite the residual panel README start-here and role sentence (C2). Do not rewrite residual scientific numbers.

### Should fix

3. One sentence in FINAL “What is finished” / “Claude does not re-open them” making the residual scope explicit (M1).  
4. Header note on residual `CROSS_FAMILY_SYNTHESIS.md`: not the study-level final synthesis; different file, same name (M2).  
5. Banner `analysis_v2/reports/NEXT_EXPERIMENTS.md` (M3).  
6. Snapshot banner on `PUBLICATION_ARTIFACT_AUDIT.md` (`9a4ee4e`, pre-navigation) (M4).  
7. Fix `cursor_panel/README.md` Reproduce to `silver_adjudication_v1/` paths and lead with the verifier (M5).  
8. Lead Claude full README Reproduce with `verify_headlines.py`; move judge commands under “Do not rerun” (M6).  
9. Residual METHODS: “Narrow validation” → “Narrow robustness test” (M7). Residual README “validation” is covered by C2.  
10. Retitle SILVER_FINDINGS `## One next experiment (not run)` to a historical heading (M8).  
11. Always cite `CLAUDE_FINDINGS.md` / `CROSS_FAMILY_SYNTHESIS.md` with their directory (M9).  
12. Residual folder: treat `CLAUDE_FINDINGS.md` as the current residual report; FINAL is intermediate (M10; README change is C2).

### Optional

13. Claude full README: `κ = 0.54` → `0.537`.  
14. Root README / residual synthesis: “Grok-only” → “Claude-resolved (Grok-only leftover).”  
15. `docs/LIMITATIONS.md` and full METHODS: “silver validation” → “silver replication.”  
16. FINDINGS “human review is required”: add a pointer that later silver panels exist and are not human review.  
17. `analysis_v2/README.md`: mark NEXT_EXPERIMENTS historical.  
18. `docs/historical/README.md`: add PUBLICATION_ARTIFACT_AUDIT and the shared ADJUDICATION_LOG.  
19. SILVER_FINDINGS “largest residual” clarification.  
20. Shared log “Stage C structured evidence” wording so it cannot be read as GLM Stage C judging.

### Leave untouched

- Frozen prompts.  
- `REASON.md` and discarded-cache provenance.  
- Professor / presentation scientific bodies (banners already present).  
- Historical numbers inside FINAL and SILVER_FINDINGS residual proposal (after banners/heading).  
- Analysis v2 FINDINGS/METHODS/LIMITATIONS science.  
- Canonical full CROSS_FAMILY_SYNTHESIS, CLAUDE_FINDINGS, verification.md.  
- Do not relocate or rename files in the freeze if a header note will do. Renames are optional later and will break links.

---

## 17. Exact proposed follow-up edits

Patches only. Do not implement until this audit is reviewed.

### E1 — shared silver log banner — `critical`

**File:** `silver_adjudication_v1/reports/ADJUDICATION_LOG.md`  
**Insert at top:**

> **Historical log through Claude residual Stage C.** This file stops at 2026-08-23 residual Claude. It is not the current study close. The later Claude five-judge A→B→C panel on all 226 regressions is recorded in `../claude_full_regression_panel/reports/ADJUDICATION_LOG.md`. Leave the dated entries below unchanged.

### E2 — residual README — `critical`

**File:** `silver_adjudication_v1/claude_residual_panel/README.md`  
**Replace title sentence** “Cross-family validation of …” **with:** “Supporting Stage C robustness test on the 231 Cursor/Grok leftover Ambiguous/Unresolved items. This is not the main Claude replication (that panel is `../claude_full_regression_panel/`, 226 regressions, 3,390 judgments).”  
**Replace** “Start with `reports/CLAUDE_FINDINGS.md` and `reports/FINAL_EVIDEX_STRENGTHENING.md`.” **with:** “Start with `reports/CLAUDE_FINDINGS.md`. `FINAL_EVIDEX_STRENGTHENING.md` is an intermediate write-up. Study-level final synthesis: `../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md`.”

### E3 — FINAL body scope — `major`

**File:** `FINAL_EVIDEX_STRENGTHENING.md` § “What is finished”  
**Replace** “This was the last planned strengthening experiment. No further model family… is required to complete Evidex strengthening.”  
**with:** “This closed the residual Stage C strengthening question as planned at the time. A later Claude A→B→C panel on all 226 regressions is now the main cross-family replication (see banner).”  
**In** “Claude does not re-open them.” **insert** “in this residual experiment,” after “Claude”.

### E4 — residual synthesis filename note — `major`

**File:** `claude_residual_panel/reports/CROSS_FAMILY_SYNTHESIS.md`  
**Insert after H1:** “This file is the residual-conditioned comparison (n = 231). It is not the study-level final synthesis. That file is `../../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md`.”  
**Replace** “That mixture is the cross-family result.” **with** “That mixture is the residual-panel cross-family result.”

### E5 — NEXT_EXPERIMENTS banner — `major`

**File:** `analysis_v2/reports/NEXT_EXPERIMENTS.md`  
**Insert at top:** “**Historical wishlist.** Written before silver adjudication. Item 1’s representation-disclosure test was later run as automated Grok and Claude A→B→C panels, not as human adjudication. See `docs/historical/README.md`.”

### E6 — publication-audit snapshot banner — `major`

**File:** `PUBLICATION_ARTIFACT_AUDIT.md`  
**Insert after the existing audit-date block:** “**Snapshot.** This audit describes commit `9a4ee4e`. Navigation/reproduction work in later commits (`eca7b38`, `7129bd5`) implemented much of §13. Do not read present-tense ‘not publication-ready’ or ‘README is stale’ as the state of those later trees. Scientific headline numbers in this audit remain valid.”

### E7 — SILVER_FINDINGS heading — `major`

**File:** `cursor_panel/reports/SILVER_FINDINGS.md`  
**Replace** `## One next experiment (not run)`  
**with** `## Historical note: the then-next experiment (later run)`  
Keep the existing blockquote and original paragraph.

### E8 — Cursor README Reproduce — `major`

**File:** `cursor_panel/README.md`  
**Replace the bash block with** (from `silver_adjudication_v1/`):

```bash
python src/verify_headlines.py --panel cursor
# optional Level 2 orchestrator, not Level 1:
# python run_all.py --panel cursor
python -m unittest discover -s tests
```

State cwd: `silver_adjudication_v1/`, not `cursor_panel/`.

### E9 — Claude full README Reproduce — `major`

**File:** `claude_full_regression_panel/README.md`  
**Put first:** `python src/verify_headlines.py` and unittest.  
**Move** `derive_and_blind` / `run_judges` / `unblind` under a heading “Do not rerun judging; frozen files are the record.”

### E10 — residual “validation” — `major`

**Files:** residual README (covered by E2); residual METHODS L5; optionally residual CLAUDE_FINDINGS L4.  
**Replace** “validation” **with** “robustness test” where it names the experiment role.

### E11 — kappa rounding — `minor`

**File:** `claude_full_regression_panel/README.md`  
**Replace** `κ = 0.54` **with** `κ = 0.537`.

### E12 — optional manuscript wording

- Root README residual cell: “42.0% Claude-resolved / Grok-only leftover (97/231).”  
- `docs/LIMITATIONS.md`: “cross-family silver replication.”  
- FINDINGS “What these results do NOT establish”: one sentence pointing at later silver panels without calling them human review.

---

## Discrepancy index (for counts)

**Critical (2)**

| ID | File | One-line issue |
|---|---|---|
| C1 | `silver_adjudication_v1/reports/ADJUDICATION_LOG.md` | Log closes the study; Claude full is missing |
| C2 | `claude_residual_panel/README.md` | Current entry points at the intermediate “final” and calls the residual panel “validation” |

**Major (10)** — same items as §16 “Should fix”

| ID | File | One-line issue |
|---|---|---|
| M1 | `FINAL_EVIDEX_STRENGTHENING.md` | Body still says last experiment / Claude does not re-open |
| M2 | residual `CROSS_FAMILY_SYNTHESIS.md` | Same filename as the final synthesis; “the cross-family result” |
| M3 | `analysis_v2/reports/NEXT_EXPERIMENTS.md` | Live plan; no file-level banner |
| M4 | `PUBLICATION_ARTIFACT_AUDIT.md` | Present-tense unreadiness for commit `9a4ee4e` |
| M5 | `cursor_panel/README.md` | Reproduce commands use the wrong cwd; `run_all` as default |
| M6 | `claude_full_regression_panel/README.md` | Reproduce leads with judge/write commands |
| M7 | residual `METHODS.md` | Role title is “Narrow validation” |
| M8 | `SILVER_FINDINGS.md` | Heading still “One next experiment (not run)” |
| M9 | two `CROSS_FAMILY_SYNTHESIS.md` / two `CLAUDE_FINDINGS.md` | Citation trap if the path is omitted |
| M10 | residual CLAUDE_FINDINGS + CROSS_FAMILY + FINAL | Three residual syntheses; folder README still starts at FINAL |

**Minor (18)**

| ID | File | One-line issue |
|---|---|---|
| m1 | Claude full README | κ 0.54 vs 0.537 |
| m2 | FINDINGS / ANALYSIS_LOG | 88.7 vs 88.69 |
| m3 | Root README / residual synthesis | “Grok-only” / “Grok-only ambiguity” for Claude-decisive 97 |
| m4 | residual CLAUDE_FINDINGS | “residual validation” |
| m5 | full README / METHODS | “silver validation” with immediate negation |
| m6 | `docs/LIMITATIONS.md` | “silver validation” |
| m7 | Shared ADJUDICATION_LOG | “Claude residual validation”; Stage C evidence wording |
| m8 | FINAL H1 / “Final mechanism assessment” | Word “final” after an intermediate banner |
| m9 | analysis_v2 FINDINGS | Human review “required” without a later-silver pointer |
| m10 | SILVER_FINDINGS | “largest residual” can be heard as the largest mechanism |
| m11 | Residual README | No Level 1 verifier line |
| m12 | `docs/historical/README.md` | Index omits the publication audit and the shared log |
| m13 | `analysis_v2/README.md` | Lists NEXT_EXPERIMENTS as a current report |
| m14 | `docs/STUDY_OVERVIEW.md` | ASCII map makes dashed supporting edges easy to miss |
| m15 | FINDINGS vs silver tables | 38.1% and 5.3% digit collisions across different denominators |
| m16 | Shared ADJUDICATION_LOG | Fleiss “0.928 B/C” is consistent with SILVER_FINDINGS, not independently registered |
| m17 | full `HEADLINES.json` | κ 0.537 is synthesis-canonical, not a registry field |
| m18 | `analysis_v2/tables/verification.md` | Duplicate “exact duplicate groups | 126” row |

Must-fix items in §16 are C1–C2. Should-fix items in §16 are M1–M10. Optional items are m1–m18 plus the wording nits in §16 Optional.
