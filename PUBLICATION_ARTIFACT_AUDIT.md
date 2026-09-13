# Evidex publication artifact audit

**Audit date:** 2026-09-13
**Audited commit:** `9a4ee4e` (`research/evidex-claude-full-regression-panel-v1`, after `f4b1454`)
**Scope:** read-only inspection. No frozen judgments, freeze manifests, prompts, taxonomy definitions, or experimental outputs were modified.
**Assumption:** Phase 2 should add a publication-facing navigation layer rather than relocating frozen experiment directories.

---

## 1. Executive assessment of repository readiness

The science is complete and internally consistent. The repository is **not yet publication-ready as a public research artifact**.

What is already strong:

- The primary 10K paired experiment, Analysis v2, Cursor/Grok A→B→C panel, GLM Stage A replication, Claude residual panel, and Claude full-regression A→B→C panel all exist as frozen, hash-checked artifacts.
- Independent headline verifiers exist for Analysis v2, Cursor/Grok, Claude residual, and Claude full-regression.
- Panel-level reports already contain methods, findings, limitations, and (for Claude full) a correct cross-family synthesis.

What blocks a clean public release:

1. The **root README is scientifically stale**. It still describes Claude as a residual-only Stage C test and presents the Cursor/Grok split as if it were the final mechanism assessment.
2. Several **supporting documents still claim to be the final synthesis** (`FINAL_EVIDEX_STRENGTHENING.md`) or still list the Claude residual panel as the one next experiment (`SILVER_FINDINGS.md`).
3. **`silver_adjudication_v1/README.md` still describes the whole silver layer as a GLM-only study.**
4. There is **no single reproduction entry point** that a fresh reader can follow from headline verification through all four judge-family artifacts.
5. The **root is a working laboratory**, not a manuscript map: 1K pilots, 10K pilots, shard leftovers, an old pipeline archive, and two outdated status memos sit beside the canonical 10K files that Analysis v2 actually reads.
6. **Level 1 verification is possible today** if the reader knows which scripts to run. The root README does not tell them to run the Claude full-regression verifier, and one advertised command (`python src/verify_headlines.py --panel cursor`) is easy to mis-run because the default panel is GLM.

Readiness verdict: **scientifically complete, documentation-lagging, structurally noisy**. The smallest safe path to a public artifact is documentation and navigation, not restructuring frozen experiments.

---

## 2. Canonical scientific hierarchy

Keep this order in every public-facing document. Do not give GLM or Claude residual equal billing with the two complete A→B→C panels. Do not rewrite them as failures.

| Rank | Layer | What it is | Canonical location | Status |
|---|---|---|---|---|
| 1 | Primary behavioral experiment | 10,000 balanced FEVER claims; GPT-5.4 and GPT-5.4-mini; no-evidence vs gold-evidence; 40,000 predictions | Root `experiment_*_balanced_10000_v1.*` (not the `*_pilot` files) | Complete |
| 2 | Primary analysis | Paired transitions, statistics, features, two local NLI diagnostics, leakage, verification | `analysis_v2/` | Complete |
| 3 | Primary mechanism study | Cursor/Grok five-judge A→B→C progressive disclosure on the 1,061-claim cohort (judged N = 1,060) | `silver_adjudication_v1/cursor_panel/` | Complete, frozen |
| 4 | Supporting robustness | GLM-5.3 Stage A replication against Cursor Stage A | Shared `silver_adjudication_v1/judgments/stage_a/` plus `cursor_panel/reports/CROSS_PANEL_STAGE_A_REPLICATION.md` | Complete for Stage A; later GLM stages are provenance only |
| 5 | Intermediate cross-family robustness | Claude five-judge Stage C on 231 Grok residual items | `silver_adjudication_v1/claude_residual_panel/` | Complete, frozen; selection-conditioned |
| 6 | Main cross-family replication | Claude five-judge A→B→C on all 226 unique regressions; 3,390 judgments | `silver_adjudication_v1/claude_full_regression_panel/` | Complete, frozen, verified |
| 7 | Final cross-family synthesis | Qualitative mechanism ordering replicates; exact proportions are judge-family-sensitive | `silver_adjudication_v1/claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md` | This is the current final synthesis |

**Current final numbers (do not alter):**

- Grok: 50.0% utilization / 11.9% representation-sensitive / 38.1% residual ambiguity
- Claude: 65.9% / 5.3% / 28.8%
- Taxonomy agreement 74.3%, Cohen's κ 0.537

**Historical, not in the core hierarchy:**

- 1,000-claim balanced run and all `*_pilot` files
- `archive_old_pipeline/`
- Incomplete GLM Stages B/C
- Claude full-regression interruption snapshot (`STOPPING_POINT.json`)
- Quarantined / discarded Claude packets

---

## 3. Stale documentation findings

Do not edit these files in this pass. Each item below is now misleading for a manuscript reader.

### 3.1 Root `README.md` (highest priority)

The file predates the completed Claude full-regression panel.

**Opening framing**

- Lines 5–6: “test only the remaining ambiguous cases with a second model family.” That was true of the residual panel. It is no longer the main Claude experiment.
- The mermaid map (`Validation` subgraph, lines 37–44) shows only “Claude 5-judge Stage C / 231 residual items only,” then feeds `persist` and `grokonly` into `Final synthesis / MIXED MECHANISM`. The completed 226-claim A→B→C replication is absent. The final synthesis node is wired to residual persistence, not to the two-family mechanism table.

**Key Findings table**

- Line 55: “Claude did not re-judge the full silver panel, and Claude does not reopen the Cursor regression taxonomy.” Both clauses are now false as a description of the study. Claude independently re-ran A→B→C on all 226 regressions and independently applied the same taxonomy rules.
- The table reports the Cursor/Grok mechanism split and the Claude residual 58.0/42.0 split, but not the Claude full-regression 65.9/5.3/28.8 split, not 3,390 judgments, and not 74.3% / κ 0.537.
- The “supported mechanism assessment” sentence (line 65) still treats “model-family-specific conservatism in part of the residual” as a co-equal headline with the three-way regression decomposition.

**How the Investigation Works**

- Step 4 (lines 72–73) is titled “Claude cross-family residual test” and stops there. There is no step 5 for the 226-claim A→B→C panel and no step 6 for the current synthesis.

**Research Artifacts table**

- Lists residual `CLAUDE_FINDINGS.md`, residual `CROSS_FAMILY_SYNTHESIS.md`, and `FINAL_EVIDEX_STRENGTHENING.md` as if they were the latest Claude and synthesis artifacts.
- Does not list `silver_adjudication_v1/claude_full_regression_panel/reports/CLAUDE_FINDINGS.md` or `.../CROSS_FAMILY_SYNTHESIS.md`.
- Does not list Claude full figures or `HEADLINES.json`.

**Reproduction commands**

- Analysis v2 block is usable.
- Silver block (lines 100–106) verifies Cursor and Claude residual only. It never runs `claude_full_regression_panel/src/verify_headlines.py` or that panel’s tests.
- `python src/verify_headlines.py --panel cursor` is correct only if `config.py` is imported with `--panel cursor`. The default panel is GLM. A reader who omits the flag will verify the incomplete GLM namespace, not Cursor.

**Limitations**

- Line 134: “Claude sample is residual-conditioned. The 231 items are Grok Stage C leftovers, not a re-run of the 1,060-item panel.” Still true of the residual panel; false as the study-level Claude limitation. The main Claude sample is now 226 regressions across three stages.
- Line 136 links only analysis, Cursor, and residual limitations. Omits `claude_full_regression_panel/reports/LIMITATIONS.md`.

**Diagrams**

- The single mermaid figure is now the most visible stale object in the repository.

### 3.2 Other stale or role-confused documents

| Path | Problem |
|---|---|
| `silver_adjudication_v1/README.md` | Entire file describes a GLM-only A→B→C study with a GLM resolver. Cursor/Grok is the completed primary panel; GLM Stage B/C never finished; Claude panels are unmentioned. |
| `silver_adjudication_v1/README.md` line 18 | Points to `reports/LIMITATIONS.md`, which does not exist at that path. Limitations live under each panel. |
| `silver_adjudication_v1/cursor_panel/reports/SILVER_FINDINGS.md` § “One next experiment (not run)” | The 231-item residual panel **was run**. The section is now historical. |
| `silver_adjudication_v1/claude_residual_panel/reports/FINAL_EVIDEX_STRENGTHENING.md` | Title and “Final mechanism assessment” still present residual 58.0/42.0 as the last layer. Legitimate as an intermediate synthesis; misleading as “final.” |
| `analysis_v2/README.md` | Accurate for v2, but “everything outside analysis_v2 is an immutable source artifact and is unchanged from `main`” is a development note, not a publication claim. |
| `analysis_v2/reports/NEXT_EXPERIMENTS.md` | Written before silver adjudication. Item 1 is essentially what the Grok and Claude A→B→C panels later did. Keep as historical planning; do not present as current roadmap. |
| `professor_update.md` | Dated 2026-04-05. Describes a 1K migration, missing wiki shards, and a repo name (`research-symposium-etamu-2026`) that is not this repository. Actively misleading if left at root. |
| `presentation_dossier_comprehensive.md` | Accurate for the 10K behavioral layer only. Stops before Analysis v2 and all adjudication. Fine as a historical talk dossier; not a study overview. |
| `silver_adjudication_v1/claude_full_regression_panel/freezes/STOPPING_POINT.json` | Frozen interruption snapshot. Numerically stale (`B` incomplete, 1,731/3,390). **Do not edit.** Document it as a historical capacity-stop record superseded by `freeze_stage_B.json` / `freeze_stage_C.json`. |
| `silver_adjudication_v1/claude_full_regression_panel/freezes/missing_work_manifest.json` | Regenerated after completion (`complete: true`). Fine as a completeness snapshot; the filename still sounds like leftover work. |

Panel-internal findings reports for Cursor, Claude residual, and Claude full are **not stale as science**. They become stale only when the root or a “final” document cites the wrong one as the last word.

---

## 4. Artifact classification table

Legend for the last four columns: **Ref** = referenced by current analysis/verification code; **Move** / **Archive** / **Delete** = safe *in principle* for a later packaging pass. “No” means do not do it for the public release. Recommendations are conservative.

### 4.1 Root files and directories

| Path | Classification | Scientific role | Ref | Move | Archive | Delete | Recommendation |
|---|---|---|---|---|---|---|---|
| `README.md` | documentation | Study entry point; currently stale | yes (human) | no | no | no | Rewrite in Phase 2 |
| `LICENSE` | documentation | MIT for project code | no | no | no | no | Keep; add third-party notices |
| `requirements-openai.txt` | reproducibility dependency | Level 3 GPT inference only | yes | no | no | no | Keep; document as optional |
| `experiment_config.py` | canonical manuscript-supporting | 10K experiment constants | yes | no | no | no | Keep at root; code uses it |
| `extract_fever_balanced_sample.py` | canonical manuscript-supporting | Sampling | yes | no | no | no | Keep |
| `prepare_fever_wiki_pages.py` | canonical manuscript-supporting | Wiki prep (Level 3) | yes | no | no | no | Keep |
| `resolve_gold_evidence.py` | canonical manuscript-supporting | Evidence resolution (Level 3) | yes | no | no | no | Keep |
| `expand_experiment_runs.py` | canonical manuscript-supporting | 40K expansion (Level 3) | yes | no | no | no | Keep |
| `run_fact_check_experiment.py` | canonical manuscript-supporting | GPT inference (Level 3) | yes | no | no | no | Keep |
| `analyze_experiment_results.py` | canonical manuscript-supporting | 10K summaries | yes | no | no | no | Keep |
| `merge_parallel_results.py` | supporting robustness / historical | Shard merge | yes | no | later | no | Keep; label as execution helper |
| `parallelize_remaining_runs.py` | historical / execution helper | Shard split | yes | no | later | no | Keep |
| `create_pilot_runs_subset.py` | historical pilot | 1K/pilot subsetting | yes | no | later | no | Keep; do not feature |
| `aggregate_manual_annotations.py` | supporting / unclear | Manual annotation helper | unclear | no | later | no | Needs manual review before any move |
| `shared_task_dev.jsonl` | reproducibility dependency | FEVER dev source (~4.2 MB) | yes | no | no | no | Keep; add FEVER license notice |
| `fever_balanced_10000_v1_source.csv` | canonical | Canonical 10K sample | yes (`analysis_v2`, silver) | **no** | no | no | Do not move; hardcoded |
| `sample_provenance_balanced_10000_v1.csv` | canonical | Sampling provenance | yes | **no** | no | no | Do not move |
| `resolve_summary_balanced_10000_v1.json` | canonical | Evidence-resolve summary | yes | **no** | no | no | Do not move |
| `experiment_results_balanced_10000_v1.csv` | canonical | 40K predictions (~26.2 MB) | yes | **no** | no | no | Do not move; Analysis v2 source |
| `experiment_runs_balanced_10000_v1.csv` | canonical | 40K run table (~25.7 MB) | yes | **no** | no | no | Do not move |
| `experiment_summary_balanced_10000_v1.csv` | canonical | Accuracy table | README | no | no | no | Keep at root or link from README |
| `experiment_metrics_balanced_10000_v1.csv` | generated output | Metrics | dossier | no | no | no | Keep |
| `experiment_tracker_balanced_10000_v1.csv` | generated output | Tracker (~2.2 MB) | sampling scripts | no | no | no | Keep |
| `experiment_tracker_with_evidence_balanced_10000_v1.csv` | generated output | Tracker + evidence (~6.2 MB) | scripts | no | no | no | Keep |
| `sample_validation_balanced_10000_v1.json` | canonical | Sample validation | docs | no | no | no | Keep |
| `dataset_validation_balanced_10000_v1.json` | canonical | Pre-expansion validation | scripts | no | no | no | Keep |
| `error_taxonomy_counts_balanced_10000_v1.csv` | generated output | Error themes | dossier | no | no | no | Keep; secondary |
| `evidence_condition_errors_balanced_10000_v1.csv` | generated output | Evidence-condition errors | unclear | no | later | no | Keep unless unused after review |
| `example_failure_cases_balanced_10000_v1.csv` | generated output | Example failures | dossier | no | later | no | Keep |
| `manual_annotations_evidence_failures_balanced_10000_v1.csv` | supporting / unclear | Manual labels | `aggregate_manual_annotations.py` | no | no | no | Manual review; do not delete |
| `*_balanced_10000_v1_pilot.*` | historical pilot | 50-claim / 200-row 10K-pipeline pilot | scripts | no | later | no | Leave in place; hide from README |
| `fever_balanced_1000_v1_source.csv` and all `*_balanced_1000_v1*` | historical pilot | Earlier 1K balanced run | scripts | no | later | no | Leave in place; hide from README |
| `parallel_shards_balanced_10000_v1/` | generated / historical | ~43 MB shard copies of already-merged 10K files | merge script | no | later | **no** | Do not delete; optional later archive *after* confirming merge provenance |
| `archive_old_pipeline/` | archived legacy | Pre-balanced experiment CSVs | no current analysis | no | already archived | **no** | Leave; do not feature |
| `wiki-pages/` | reproducibility dependency | FEVER wiki shards (~7.3 GB, gitignored) | Level 3 scripts | n/a | n/a | no | Document how to obtain; do not commit |
| `analysis_v2/` | canonical | Primary analysis | yes | no | no | no | Keep |
| `silver_adjudication_v1/` | canonical + supporting | All judge panels | yes | no | no | no | Keep in place |
| `presentation_dossier_comprehensive.md` | historical documentation | 10K talk dossier | no | later | later | no | Relabel or move to `docs/historical/` in Phase 2 |
| `professor_update.md` | historical / obsolete | April 2026 1K status | no | later | later | no | Relabel or move to `docs/historical/` |
| `.gitignore` | reproducibility dependency | Ignores wiki, caches, `.env` | n/a | no | no | no | Extend for Claude-full cache (see §11) |
| `.mimosa/`, `.zcode/`, `.pytest_cache/`, `__pycache__/` | temporary/debug/cache | Local tool caches | no | n/a | n/a | yes (untracked) | Already gitignored or should stay ignored |

### 4.2 Analysis v2

| Path | Classification | Role | Ref | Move | Archive | Delete | Recommendation |
|---|---|---|---|---|---|---|---|
| `analysis_v2/reports/FINDINGS.md` | canonical | Primary analysis narrative | verifier | no | no | no | Keep |
| `analysis_v2/reports/METHODS.md` | canonical | Analysis methods | human | no | no | no | Keep |
| `analysis_v2/reports/LIMITATIONS.md` | canonical | Analysis limits | README | no | no | no | Keep |
| `analysis_v2/reports/NOVELTY_BOUNDARIES.md` | supporting documentation | Claim boundaries | human | no | no | no | Keep |
| `analysis_v2/reports/NEXT_EXPERIMENTS.md` | historical planning | Pre-adjudication roadmap | no | no | no | no | Keep; mark historical |
| `analysis_v2/reports/ANALYSIS_LOG.md` | documentation | Execution log | no | no | no | no | Keep |
| `analysis_v2/tables/*` | generated / canonical | Derived tables + `verification.md` | yes | no | no | no | Keep |
| `analysis_v2/figures/*.png` | generated / canonical | Six analysis figures | `generate_figures.py` | no | no | no | Keep; see §10 |
| `analysis_v2/data/derived/*.parquet` | generated output | Paired datasets (committed) | yes | no | no | no | Keep; Level 1/2 depend on them |
| `analysis_v2/src/verify_headlines.py` | canonical | Level 1 verifier | README | no | no | no | Keep |
| `analysis_v2/run_all.py` | canonical | Level 2 orchestrator | README | no | no | no | Keep; document optional NLI stages |
| `analysis_v2/tests/` | reproducibility | Unit tests | yes | no | no | no | Keep |
| `analysis_v2/requirements.txt` | reproducibility dependency | Analysis stack | yes | no | no | no | Keep |

### 4.3 Silver adjudication

| Path | Classification | Role | Ref | Move | Archive | Delete | Recommendation |
|---|---|---|---|---|---|---|---|
| `silver_adjudication_v1/cursor_panel/` | canonical | Primary A→B→C mechanism study | yes | **no** | no | no | Do not move |
| `silver_adjudication_v1/claude_full_regression_panel/` | canonical | Main cross-family replication | yes | **no** | no | no | Do not move |
| `silver_adjudication_v1/claude_residual_panel/` | supporting robustness | Intermediate residual test | yes | **no** | no | no | Do not move; do not demote scientifically |
| `silver_adjudication_v1/judgments/stage_a/` | supporting robustness | Frozen GLM Stage A | yes | **no** | no | no | Do not move |
| `silver_adjudication_v1/judgments/stage_b/` | historical / provenance | Incomplete GLM Stage B | freeze/logs | **no** | no | no | Keep as provenance |
| `silver_adjudication_v1/judgments/stage_c/` | historical | GLM Stage C missing stubs only | tests | **no** | no | no | Keep |
| `silver_adjudication_v1/data/blinded/` | canonical | Shared blinded A/B/C packets | yes | **no** | no | no | Do not move |
| `silver_adjudication_v1/data/derived/` | canonical | Cohort, id map, GLM freeze | yes | **no** | no | no | Do not move |
| `silver_adjudication_v1/prompts/` | canonical | Shared rubric and disclosure protocol | yes | **no** | no | no | Do not alter |
| `silver_adjudication_v1/src/` | canonical | Cursor/GLM pipeline + Cursor verifier | yes | no | no | no | Keep |
| `silver_adjudication_v1/tests/` | reproducibility | GLM + Cursor tests | yes | no | no | no | Isolate in pytest (see §7) |
| `silver_adjudication_v1/blind_io/` | canonical provenance | Claude-full judge I/O (neutral paths) | panel code | **no** | no | no | Do not move; contains local usernames (see §11) |
| `silver_adjudication_v1/claude_full_regression_panel/cache/discarded/` | temporary/debug kept as audit | Quarantined blinding-fix and duplicate packets | log | no | no | **no** | Keep; they document protocol deviations |
| `silver_adjudication_v1/claude_full_regression_panel/freezes/STOPPING_POINT.json` | historical freeze sidecar | Capacity-stop record | log | no | no | **no** | Do not edit |
| `silver_adjudication_v1/README.md` | documentation | Stale GLM-centric intro | human | no | no | no | Rewrite in Phase 2 |
| `silver_adjudication_v1/reports/ADJUDICATION_LOG.md` | documentation | GLM/shared execution log | human | no | no | no | Keep |
| `silver_adjudication_v1/figures/` | empty generated slot | Unused | no | no | no | no | Ignore |
| `silver_adjudication_v1/requirements.txt` | reproducibility dependency | Stats/plotting | yes | no | no | no | Keep |

---

## 5. Dependency and path risks

Frozen experimental directories should stay where they are. Movement risk is high.

### Hardcoded root paths (do not move these files)

`analysis_v2/config.py` reads, by filename:

- `experiment_results_balanced_10000_v1.csv`
- `experiment_runs_balanced_10000_v1.csv`
- `fever_balanced_10000_v1_source.csv`
- `sample_provenance_balanced_10000_v1.csv`
- `resolve_summary_balanced_10000_v1.json`

`silver_adjudication_v1/config.py` reads:

- `analysis_v2/data/derived/paired_enriched.parquet`
- `fever_balanced_10000_v1_source.csv`

Root sampling scripts default to `shared_task_dev.jsonl`. Shard scripts default to `parallel_shards_balanced_10000_v1/`.

**Recommendation:** if a later cleanup wants a `data/primary_10k/` directory, that is a dedicated path-update project with tests, not a Phase 2 docs task.

### Frozen directories (do not move)

| Directory | Why movement is unsafe |
|---|---|
| `cursor_panel/` | Freeze manifests hash local files; tests assert `JUDGMENTS_DIR`; verifier walks `judgments/stage_*` |
| `claude_residual_panel/` | Own freeze manifest, id map, blinded file, verifier |
| `claude_full_regression_panel/` | Own freeze manifests, `blind_io` relative packets, verifier, tests |
| `silver_adjudication_v1/data/blinded/` | Shared packets; freeze hashes |
| `silver_adjudication_v1/judgments/` | GLM freeze `data/derived/freeze_stage_A.json` |
| `silver_adjudication_v1/prompts/` | Versioned rubric used by all panels |
| `silver_adjudication_v1/blind_io/` | Judge-facing packets and launch prompts; moving reintroduces the path-leak problem that forced the first Stage A quarantine |

### Relative-path and import risks

- Three different `src/run_judges.py` modules (`silver_adjudication_v1/src`, `claude_residual_panel/src`, `claude_full_regression_panel/src`) with incompatible signatures. Importing more than one in a single pytest process collides (see §7).
- `config.py` `apply_panel()` mutates globals. Cursor tests already `tearDown` back to GLM. A process-wide `SILVER_PANEL` env var would leak across tests.
- Claude full launch prompts embed **absolute Windows paths** (`C:\Users\Chimdumebi\evidex\...`). Those files are historical judge inputs. Do not rewrite them; rewriting would change committed experimental provenance. Document that they are machine-local snapshots.

### Freeze-manifest risk

Do not regenerate or pretty-print freeze JSON/parquet. Headline verifiers recompute hashes from disk bytes. Even harmless whitespace changes fail verification.

---

## 6. Reproducibility assessment

### Level 1 — headline verification (public artifact must support this)

Recompute manuscript numbers from committed/frozen results. No API keys. No wiki shards.

| Layer | Command (from the relevant directory) | Works today? | Gap |
|---|---|---|---|
| Analysis v2 | `python src/verify_headlines.py` | Yes, if pandas/scipy/statsmodels/pyarrow are installed and `experiment_results_balanced_10000_v1.csv` plus the two paired parquets remain at their current paths | Root README does not say this is the primary public check |
| Cursor/Grok | `python src/verify_headlines.py --panel cursor` from `silver_adjudication_v1/` | Yes, if `--panel cursor` is passed | Default without the flag is GLM; GLM Stage B/C are incomplete |
| Claude residual | `python claude_residual_panel/src/verify_headlines.py` | Yes | Advertised; still supporting, not final |
| Claude full | `python claude_full_regression_panel/src/verify_headlines.py` | Yes (21/21 at audit time) | **Missing from root README** |

**Level 1 gaps to close in documentation only:**

- One copy-pasteable verification block covering all four verifiers.
- Explicit note that Level 1 does not require OpenAI, Claude, Grok, GLM, spaCy, or transformers.
- Explicit note that `STOPPING_POINT.json` is not a completeness oracle; use `missing_work_manifest.json` (`complete: true`) and the three stage freezes.

### Level 2 — analysis reproduction

Regenerate derived tables, figures, consensus, taxonomy, and comparisons from committed experimental outputs.

| Layer | What a fresh user can do | Gap |
|---|---|---|
| Analysis v2 | `python run_all.py` rebuilds paired data, stats, features, figures, leakage, then verifies | Optional stages (NLI, embeddings, clustering) need Hugging Face / spaCy models. README already says they degrade; `REQUIRED` in `run_all.py` still includes `linguistic_features` (spaCy). A machine without spaCy may fail a “required” stage |
| Cursor/Grok | Consensus and taxonomy already frozen; `run_all.py --panel cursor` is an orchestrator, not something a public user should rerun for new judgments | Need a documented “recompute tables from frozen judgments only” path vs “do not launch judges” |
| Claude residual | `src/analyze.py` / `verify_headlines.py` from frozen judgments | Same |
| Claude full | `src/consensus_agreement.py all` and `src/analyze.py` can recompute consensus/taxonomy **after** freeze verification | Public docs should say: recompute is allowed; unblinding already happened; do not relaunch judges |

Level 2 should be documented as: *regenerate derived artifacts from frozen inputs; never overwrite freeze manifests or raw judgment jsonl.*

### Level 3 — model inference recreation (optional, non-deterministic)

| Inference | Requirements | Public stance |
|---|---|---|
| GPT 10K | `OPENAI_API_KEY`, `wiki-pages/` shards (~7.3 GB, not in git), FEVER source | Optional. Will not reproduce byte-identical 40K predictions |
| Cursor/Grok judges | Cursor `cursor-grok-4.6-high-fast` | Do not require. Frozen judgments are the record |
| GLM judges | Environment-specific GLM-5.3 subagents | Do not require |
| Claude judges | `claude-opus-5-thinking-high` | Do not require. Protocol forbids substitution |

The public artifact must not require Level 3 to verify the paper.

### Missing packaging pieces

- No `CITATION.cff`
- No `pyproject.toml` / `environment.yml`
- No root `REPRODUCING.md`
- No `docs/` directory
- Three separate `requirements.txt` files, no unified “verify-only” extra (pandas/scipy/pyarrow would suffice for Level 1)

---

## 7. Test-suite assessment

| Suite | How to run | Result when run alone (prior session / design) |
|---|---|---|
| `analysis_v2/tests` | `python -m pytest tests` or unittest | Isolated; OK |
| `silver_adjudication_v1/tests` | `python -m unittest discover -s tests` | Cursor + shared silver; OK alone |
| `claude_residual_panel/tests` | from that directory | OK alone |
| `claude_full_regression_panel/tests` | from that directory | 27 passed at completion |

**Known collision (pre-existing, confirmed earlier in this research branch):**

Running `silver_adjudication_v1/tests` and `silver_adjudication_v1/claude_residual_panel/tests` in **one pytest process** fails because both directories contain `src/run_judges.py`. Python binds the first import to the name `run_judges`. Residual `valid_record()` then has the wrong signature (`TypeError: valid_record() missing 1 required positional argument: 'judge'`). Claude full has a third `run_judges.py`.

This is not a scientific defect. It is a packaging defect.

**Smallest safe fix (Phase 2, do not change experiment logic):**

1. Do not rename or merge the three `run_judges.py` files.
2. Add a thin root or `silver_adjudication_v1` test runner that executes each suite in a **subprocess** with `cwd` set to that suite’s directory (or with an isolated `sys.path`).
3. Optionally add `conftest.py` files that refuse to collect foreign `src/` directories.
4. Document four separate commands in `REPRODUCING.md`.
5. Do not advertise `pytest silver_adjudication_v1 tests claude_residual_panel/tests` as a single command until isolation exists.

Preferred shape:

```text
python -m pytest analysis_v2/tests
python -m unittest discover -s silver_adjudication_v1/tests
python -m unittest discover -s silver_adjudication_v1/claude_residual_panel/tests
python -m unittest discover -s silver_adjudication_v1/claude_full_regression_panel/tests
```

or one wrapper script that calls those four as subprocesses and ORs the exit codes.

---

## 8. Proposed documentation architecture

There is currently no `docs/` directory. Add a thin layer. Do **not** duplicate panel findings.

| File | What belongs there | What must not be duplicated |
|---|---|---|
| `README.md` | One-screen study claim, hierarchy, key numbers, pointers, Level 1 verify commands, license/citation | Full methods, full tables, residual-only synthesis presented as final |
| `REPRODUCING.md` | Level 1 / 2 / 3 exactly; dependency sets; “do not rerun judges”; freeze-integrity commands; test commands | Scientific interpretation |
| `CITATION.cff` | Citation metadata for the repository | Narrative |
| `docs/STUDY_OVERVIEW.md` | Longer architecture walk-through; mermaid diagrams; which report is canonical at each layer | Copy-paste of FINDINGS.md |
| `docs/DATA_PROVENANCE.md` | FEVER → 10K sample → gold evidence → 40K predictions → paired parquet → silver cohort → opaque IDs; what is committed vs gitignored | Judge-level results |
| `docs/ADJUDICATION_PROTOCOL.md` | Pointers to the existing rubric and disclosure protocol; isolation rules; freeze-before-unblinding; model locks | A rewritten rubric (the rubric stays in `silver_adjudication_v1/prompts/`) |
| `docs/LIMITATIONS.md` | Study-level limits only; then links to the four existing LIMITATIONS files | A second scientific limitations essay |
| `docs/historical/` (optional) | `professor_update.md`, presentation dossier, or copies/links | Anything a reader might mistake for current results |

**Avoid duplication rule:** each headline number should have one *canonical report* and one *verifier*. The root README quotes the number and links to the report. `HEADLINES.json` remains the machine registry.

---

## 9. Proposed README outline

Do not write the README in this pass. This is the Phase 2 outline.

1. **Title and one-paragraph question**
   When designated gold evidence helps or harms LLM fact-checking, and what mechanisms explain correct-to-wrong regressions.
2. **Status line**
   Experiments finished. Automated silver adjudication, not human validation. FEVER gold is not relabeled.
3. **Canonical hierarchy** (numbered 1–7, matching §2)
   Short clause each. Mark 4 and 5 as supporting / intermediate.
4. **Diagram 1 — full study architecture** (see below)
5. **Key findings table** with denominators
   - GPT-5.4 / mini evidence gains (10,000 claims)
   - 226 unique regressions
   - Grok mechanism split (226 regressions)
   - Claude mechanism split (226 regressions)
   - 74.3% agreement, κ 0.537
   - One row, clearly secondary: Claude residual 58.0% persistent / 42.0% Grok-only on 231 leftovers
6. **Diagram 2 — concise cross-family result** (see below)
7. **How to read the repo**
   Table of canonical reports only (v2 FINDINGS, Cursor SILVER_FINDINGS, Claude-full CLAUDE_FINDINGS + CROSS_FAMILY_SYNTHESIS). Supporting reports in a second, visually quieter table.
8. **Reproduce (Level 1 first)**
   Four verifier commands. Link to `REPRODUCING.md` for Level 2/3.
9. **Limitations (five bullets, study-level)**
   Silver not human; FEVER not overturned; no GPT-internal causal claim; binary 2017 FEVER; judge-family-sensitive proportions.
10. **Citation, license, third-party data**
11. **What this repository is not**
    Not a demo app. Not unfinished work. Historical pilots live at root but are not the study.

### Diagram 1 — full study architecture (specify, do not draw yet)

Left-to-right or top-to-bottom:

- FEVER 10K balanced → paired GPT 40K → four transitions
- Analysis v2 → 1,061-claim cohort (226 / 335 / 250 / 250)
- **Primary path (solid):** cohort → Cursor/Grok A→B→C → Grok taxonomy
- **Supporting (dashed):** GLM Stage A replication
- **Intermediate (dashed):** 231 Grok Stage C leftovers → Claude residual Stage C
- **Primary replication (solid):** 226 regressions → Claude A→B→C → Claude taxonomy
- **Final node:** cross-family synthesis (ordering shared; proportions family-sensitive)

Do not wire the residual 58/42 split into the final node as if it were the mechanism decomposition.

### Diagram 2 — concise final cross-family result (specify, do not draw yet)

A two-column comparison, not a flowchart:

| | Utilization | Representation | Residual |
|---|---|---|---|
| Grok | 50.0% | 11.9% | 38.1% |
| Claude | 65.9% | 5.3% | 28.8% |

Caption: same rank order; non-overlapping utilization CIs; agreement 74.3%, κ = 0.537. Silver judgments, not human ground truth.

Optional tiny third row or footnote: residual panel asked a different question (persistence of Stage C leftovers) and is not this table.

---

## 10. Proposed figure strategy

Existing committed figures (19 PNGs). Classification is by scientific role, not visual redesign. Do not regenerate in Phase 2 unless a caption is factually wrong.

### Analysis v2 (`analysis_v2/figures/`)

| File | Recommendation |
|---|---|
| `fig1_transition_matrices.png` | Manuscript + README |
| `fig2_transitions_by_label.png` | Manuscript or appendix |
| `fig3_cross_model_matrix.png` | Manuscript |
| `fig4_similarity_by_transition.png` | Appendix / supplement |
| `fig5_evidence_set_size.png` | Appendix |
| `fig6_nli_disagreement.png` | Manuscript (NLI diagnostic is a v2 headline) |

### Cursor/Grok (`cursor_panel/figures/`)

| File | Recommendation |
|---|---|
| `fig7_taxonomy_distribution.png` | Manuscript + README (Grok mechanism split) |
| `fig3_resolution_flow.png` | Manuscript (progressive disclosure) |
| `fig1_agreement_by_stage.png` | Appendix (panel reliability) |
| `fig2_ambiguity_by_cohort.png` | Manuscript or appendix |
| `fig4_sensitivity_by_cohort.png` | Appendix |
| `fig5_verdict_change_rates.png` | Appendix |
| `fig6_glm_vs_nli_disagreement.png` | Supplement (robustness / GLM), not a main-text peer of fig7 |

### Claude residual (`claude_residual_panel/figures/`)

| File | Recommendation |
|---|---|
| `fig1_claude_consensus.png` | Supplement (supporting experiment) |
| `fig2_cross_family_taxonomy.png` | Supplement; do not use as the main cross-family figure |
| `fig3_persistent_by_cohort.png` | Supplement |

### Claude full (`claude_full_regression_panel/figures/`)

| File | Recommendation |
|---|---|
| `fig1_mechanism_by_family.png` | Manuscript + README (this is the current cross-family figure) |
| `fig2_stage_ambiguity.png` | Manuscript (stage-level family gap) |
| `fig3_mechanism_confusion.png` | Manuscript or appendix (claim-level disagreement) |

Redundant if both residual fig2 and full fig1 are shown as “the” cross-family result. Full fig1 wins.

Obsolete: none of the PNGs are scientifically obsolete. Several **captions and README placements** would be obsolete if they implied residual-only Claude validation.

---

## 11. Public-release hygiene findings

Nothing was deleted. Findings only.

### Secrets

- No committed `.env` and no API key files found.
- `run_fact_check_experiment.py` reads `OPENAI_API_KEY` from the environment or a local `.env` (gitignored). Good.
- Do a final `gitleaks` / `git log -S sk-` sweep before making the repo public; this audit used workspace search only.

### Account-specific / absolute paths

- `silver_adjudication_v1/blind_io/launch_prompts/**/*.txt` and `index.json` contain `C:\Users\Chimdumebi\evidex\...`.
- These are committed historical judge-launch artifacts. **Do not rewrite** (provenance).
- Public implication: the author’s Windows username is in the git history. Acceptable for a named research repo; mention in `DATA_PROVENANCE.md`. Do not “clean” by force-pushing.

### Caches and temporary files

- `.gitignore` already drops `wiki-pages/`, `.env`, `*.gguf`, `silver_adjudication_v1/data/cache/`, `cursor_panel/cache/`, `claude_residual_panel/cache/`.
- **Gap:** `claude_full_regression_panel/cache/` is **not** gitignored. Queue JSON and discarded packets are tracked. The discarded packets should stay (protocol audit). Future cache noise should be ignored without deleting committed discarded files — use a narrow ignore such as `cache/queue_*.json` if desired, not `cache/`.

### Large tracked artifacts

Approximate tracked files >1 MB: 10K results/runs (~52 MB), tracker+evidence (~6 MB), four shard pairs (~43 MB), `shared_task_dev.jsonl` (~4.2 MB), 1K results/runs (~3 MB), analysis parquets (~3 MB). No Git LFS.

`parallel_shards_balanced_10000_v1/` duplicates data already in the merged 10K CSVs. **Do not delete** until merge provenance is written down. Optional later archive.

`wiki-pages/` (~7.3 GB) is local and gitignored. Good. `__MACOSX` junk under wiki-pages should stay untracked.

### Licensing / redistribution

- Project `LICENSE` is MIT (code).
- `shared_task_dev.jsonl` is FEVER shared-task data. FEVER and Wikipedia text are **not** MIT-relicensed by this file.
- Gold-evidence strings in the 10K CSVs are reconstructed Wikipedia sentences.
- Public release needs a `NOTICE` or `docs/DATA_PROVENANCE.md` section: FEVER citation, Wikipedia license, “we redistribute a derived research sample.”
- Hugging Face model names in `analysis_v2/config.py` are used locally at Level 2; they are not vendored.

### Duplicate generated files

- Blind inbox JSONL vs ingested `judgments/` copies for Claude full: intentional (`ingest` copies). Keep both.
- `tables/claude_full_unblinded.csv` and `freezes/claude_full_unblinded.parquet`: derived pair. Keep.
- 10K `*_pilot` vs full files: easy to confuse; hide pilots in the README.

### Model-provider metadata

- Judge ids (`cursor_judge_*`, `claude_full_judge_*`) and model lock strings are scientific metadata. Keep.
- Launch-prompt absolute paths are the only personal-filesystem leak identified.

---

## 12. Recommended cleanup actions (ranked)

### Must do before manuscript / public release

1. Rewrite root `README.md` so Claude full A→B→C and the 65.9/5.3/28.8 vs 50.0/11.9/38.1 comparison are the cross-family headline, and residual/GLM are supporting.
2. Replace the stale mermaid architecture diagram; add the concise two-family result diagram.
3. Add `REPRODUCING.md` with Level 1 (all four verifiers), Level 2, and optional Level 3.
4. Add a one-line status banner to `FINAL_EVIDEX_STRENGTHENING.md` and to the Cursor “One next experiment (not run)” section stating they are intermediate/historical. **Do not rewrite their scientific numbers.**
5. Rewrite `silver_adjudication_v1/README.md` so it describes four artifacts (Cursor primary, GLM Stage A supporting, Claude residual supporting, Claude full primary replication).
6. Move or clearly label `professor_update.md` so a public visitor cannot take it as current status.
7. Add `CITATION.cff` and a FEVER/Wikipedia data-notice paragraph.
8. Document that `STOPPING_POINT.json` is an interruption snapshot, not the final completeness record.

### Should do

1. Create `docs/STUDY_OVERVIEW.md`, `docs/DATA_PROVENANCE.md`, `docs/ADJUDICATION_PROTOCOL.md`, `docs/LIMITATIONS.md` as pointers, not new science.
2. Add a subprocess test runner so a single “run all tests” command does not hit the `run_judges` import collision.
3. Add a `verify-only` dependency set (pandas, numpy, scipy, statsmodels, pyarrow) distinct from optional NLI/spaCy.
4. Clarify in `analysis_v2/run_all.py` docs which stages are truly required without spaCy/transformers.
5. Relocate `presentation_dossier_comprehensive.md` to `docs/historical/` **or** add a header that it covers the 10K layer only.
6. Ignore future Claude-full queue cache without deleting committed discarded packets.
7. Choose manuscript figures per §10; do not regenerate unless captions are wrong.

### Optional

1. After writing merge provenance, consider git-archiving `parallel_shards_balanced_10000_v1/` in a later dedicated PR.
2. `pyproject.toml` extras for `verify`, `analysis`, `inference`.
3. Git LFS for the two ~26 MB CSVs (only if clone size becomes a problem; not required for correctness).
4. A single `scripts/verify_all_headlines.py` that subprocess-calls the four verifiers.
5. Manual review of `aggregate_manual_annotations.py` and `manual_annotations_*.csv` for whether they belong in the paper.

### Do not touch

- Any file under `judgments/`
- Any `freeze_*.json`, freeze parquet, or `freeze_manifest.json`
- `STOPPING_POINT.json` bytes
- `prompts/judge_rubric.md`, resolver rubric, disclosure protocol
- Taxonomy rule functions
- Blinded jsonl, id maps, discarded Claude packets
- Analysis v2 paired parquets (unless a later Level 2 regeneration is an explicit, tested project)
- Root 10K result/run/source/provenance filenames or locations
- Historical pilots and `archive_old_pipeline/` (do not delete)
- Scientific numbers in findings reports

---

## 13. Exact proposed Phase 2 changes

Phase 2 is documentation and navigation only. No experiment reruns. No freeze edits. No directory moves of frozen panels.

### Files to create

- `REPRODUCING.md`
- `CITATION.cff`
- `docs/STUDY_OVERVIEW.md`
- `docs/DATA_PROVENANCE.md`
- `docs/ADJUDICATION_PROTOCOL.md`
- `docs/LIMITATIONS.md`
- `docs/historical/README.md` (index of superseded memos)
- Optional: `scripts/verify_all_headlines.py` and `scripts/run_all_tests.py` (subprocess wrappers only)

### Files to edit (text only)

- `README.md` — full rewrite to the outline in §9
- `silver_adjudication_v1/README.md` — hierarchy-aware intro; fix broken LIMITATIONS link
- `analysis_v2/README.md` — drop or qualify the “unchanged from main” sentence; point to study-level README
- `silver_adjudication_v1/cursor_panel/reports/SILVER_FINDINGS.md` — add a short historical note above “One next experiment (not run)”
- `silver_adjudication_v1/claude_residual_panel/reports/FINAL_EVIDEX_STRENGTHENING.md` — add a banner: intermediate synthesis; canonical final synthesis is the Claude full `CROSS_FAMILY_SYNTHESIS.md`
- `professor_update.md` and `presentation_dossier_comprehensive.md` — either move to `docs/historical/` **or** add obsolescence headers. Prefer headers if any inbound link exists; this audit found no code imports.
- `.gitignore` — only if adding a **narrow** Claude-full queue ignore that cannot match `cache/discarded/`

### Files not to edit in Phase 2

Everything in “Do not touch” above, plus all `HEADLINES.json` files (unless a README rewrite forces a display-string check — then update display strings only after the new README exists, as a follow-on verify pass).

### Phase 2 verification (no new science)

After the README rewrite:

1. Run all four `verify_headlines.py` scripts.
2. Run the four test suites **separately** (or via the new wrapper).
3. Confirm no freeze hash changed (`git diff --stat` should show docs only).
4. Confirm the new README quotes only numbers that already appear in a `HEADLINES.json` or in `analysis_v2/tables/verification.md`.

### Out of scope for Phase 2

- Relocating `experiment_results_balanced_10000_v1.csv`
- Deleting shards, pilots, or `archive_old_pipeline/`
- Regenerating figures
- Rewriting taxonomy or prompts
- Human adjudication
- Force-pushing to strip usernames from `blind_io` history

---

## Manuscript alignment (repository → paper)

| Likely manuscript section | Canonical artifacts |
|---|---|
| Dataset / Experimental Setup | `fever_balanced_10000_v1_source.csv`, `sample_provenance_balanced_10000_v1.csv`, `shared_task_dev.jsonl`, `experiment_config.py`, `analysis_v2/reports/METHODS.md`, `docs/DATA_PROVENANCE.md` (to be written) |
| Primary Results | `experiment_summary_balanced_10000_v1.csv`, `analysis_v2/reports/FINDINGS.md`, `analysis_v2/figures/fig1_*.png`, `fig3_*.png` |
| Regression Analysis | `analysis_v2/tables/unique_claim_counts.csv`, `transition_summary.csv`, `statistical_tests.csv`, `fig6_nli_disagreement.png` |
| Progressive Disclosure | `cursor_panel/reports/SILVER_FINDINGS.md`, `prompts/progressive_disclosure_protocol.md`, `fig3_resolution_flow.png`, `fig7_taxonomy_distribution.png` |
| Cross-Family Replication | `claude_full_regression_panel/reports/CLAUDE_FINDINGS.md`, `CROSS_FAMILY_SYNTHESIS.md`, `fig1_mechanism_by_family.png`, `fig2_stage_ambiguity.png`, `fig3_mechanism_confusion.png` |
| Robustness Analyses | `CROSS_PANEL_STAGE_A_REPLICATION.md`, GLM Stage A judgments, `claude_residual_panel/reports/CLAUDE_FINDINGS.md` |
| Limitations | Four existing `LIMITATIONS.md` files + new study-level `docs/LIMITATIONS.md` |
| Reproducibility | Four `verify_headlines.py` scripts, freeze manifests, `REPRODUCING.md` (to be written) |

---

## Audit method and limits

Inspected: root listing, README and satellite docs, `analysis_v2` and silver layouts, freeze/report/figure/verifier paths, `.gitignore`, `LICENSE`, requirements files, hardcoded path constants, grep for residual-only Claude claims, grep for API keys and absolute user paths, `git ls-files` for large blobs, and the known pytest import collision.

Did not: rerun models, recompute freezes, visually redesign figures, perform a git-history secret scan, or download FEVER’s upstream license text.

**Fact:** the experiments are finished and frozen.
**Interpretation:** the remaining work is packaging and truthful navigation, not more science.
