# Reproducing Evidex

The public artifact is designed so a reader can **verify the paper without rerunning proprietary models**.

Do not overwrite freeze manifests, raw judgment files, blinded packets, prompts, or taxonomy definitions.

## Dependency sets

**Level 1 (headline verification)** — enough to check manuscript numbers:

```text
pandas numpy scipy statsmodels pyarrow
```

**Level 2 (analysis reproduction)** — Analysis v2 plus silver table recomputation:

```text
analysis_v2/requirements.txt
silver_adjudication_v1/requirements.txt
```

Optional Analysis v2 stages need spaCy (`en_core_web_sm`), sentence-transformers, and/or transformers. See `analysis_v2/run_all.py`: `nli_analysis`, `semantic_features`, and `clustering_analysis` are optional; `linguistic_features` is currently listed as required and needs spaCy.

**Level 3 (inference recreation)** — not required to verify the paper:

```text
requirements-openai.txt    # GPT 10K only
OPENAI_API_KEY
local FEVER wiki shards under wiki-pages/   # gitignored, ~7 GB
```

Judge inference used Cursor/Grok, GLM-5.3, and `claude-opus-5-thinking-high`. Those runs are finished. Do not substitute models.

## Level 1 — headline verification

From the repository root, with the Level 1 packages installed:

```powershell
python analysis_v2/src/verify_headlines.py
python silver_adjudication_v1/src/verify_headlines.py --panel cursor
python silver_adjudication_v1/src/cross_panel_stage_a.py
python silver_adjudication_v1/claude_residual_panel/src/verify_headlines.py
python silver_adjudication_v1/claude_full_regression_panel/src/verify_headlines.py
```

Or:

```powershell
python scripts/verify_all_headlines.py
```

| Check | What it recomputes | Expected |
|---|---|---|
| Analysis v2 | Accuracies, transitions, unique-regression counts from committed CSVs/parquets | 69/69 in `analysis_v2/tables/verification.md` |
| Cursor/Grok | Consensus, taxonomy, freeze hashes from frozen judgments | `ALL HEADLINES VERIFIED`; includes Grok 50.0% / 11.9% / 38.1% and GLM modal **0.862** |
| GLM Stage A | Frozen GLM Stage A vs frozen Cursor Stage A | 1,060 items; modal **0.862**; consensus **0.831**; GLM ambiguity **0.223**; report `CROSS_PANEL_STAGE_A_REPLICATION.md` |
| Claude residual | 231-item Stage C panel | persistent **58.0%** (134/231) |
| Claude full | 226-regression A→B→C + Grok comparison | 3,390 judgments; Claude 65.9% / 5.3% / 28.8%; agreement **74.3%** |

`verify_headlines.py` **defaults to the GLM panel namespace**. Always pass `--panel cursor` for the completed Grok study.

`cross_panel_stage_a.py` reads only frozen Stage A judgments. Partial GLM Stage B is excluded by construction. The script **rewrites** three supporting files with the same numbers:

- `silver_adjudication_v1/cursor_panel/tables/cross_panel_stage_a_replication.csv`
- `silver_adjudication_v1/cursor_panel/tables/cross_panel_stage_a_consensus_crosstab.csv`
- `silver_adjudication_v1/cursor_panel/reports/CROSS_PANEL_STAGE_A_REPLICATION.md`

That rewrite is recomputation, not new adjudication. Discard incidental diffs; do not treat them as a reason to edit freeze manifests.

`STOPPING_POINT.json` in the Claude full panel is a historical capacity-stop snapshot. Completeness is `freezes/missing_work_manifest.json` (`complete: true`) plus `freeze_stage_{A,B,C}.json`.

## Level 2 — analysis reproduction

Regenerate *derived* tables and figures from committed experimental outputs. Never launch judges.

```powershell
cd analysis_v2
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
python run_all.py
python -m pytest tests -q
```

```powershell
cd silver_adjudication_v1
python -m pip install -r requirements.txt
python src/verify_headlines.py --panel cursor
python src/cross_panel_stage_a.py
```

Claude panels (recompute consensus/taxonomy only after freeze verification; do not unblind as if it were a first look):

```powershell
cd silver_adjudication_v1/claude_residual_panel
python src/verify_headlines.py

cd ../claude_full_regression_panel
python src/verify_headlines.py
```

## Level 3 — optional inference recreation

Non-deterministic. Proprietary models will not reproduce the frozen 40,000 GPT predictions or the silver judgments.

### GPT 10K (already executed)

Requires `OPENAI_API_KEY` and local FEVER wiki shards (`wiki-pages/wiki-pages/wiki-*.jsonl`).

```powershell
python -m pip install -r requirements-openai.txt
python prepare_fever_wiki_pages.py
python extract_fever_balanced_sample.py
python resolve_gold_evidence.py
python expand_experiment_runs.py
python run_fact_check_experiment.py
python analyze_experiment_results.py
```

This rebuilds a completed run. It is not unfinished work.

### Judges

Do not rerun. Frozen files under each panel's `judgments/` are the record. Model locks:

- Cursor/Grok: `cursor-grok-4.6-high-fast`
- GLM: GLM-5.3 (Stage A only is in the supporting comparison)
- Claude: `claude-opus-5-thinking-high`

If a locked model is unavailable, stop. Do not substitute.

## Tests

Run suites **separately**. Several experiment directories contain a `src/run_judges.py`; collecting them in one pytest process collides.

```powershell
python scripts/run_all_tests.py
```

or:

```powershell
python -m pytest analysis_v2/tests -q
python -m unittest discover -s silver_adjudication_v1/tests
python -m unittest discover -s silver_adjudication_v1/claude_residual_panel/tests
python -m unittest discover -s silver_adjudication_v1/claude_full_regression_panel/tests
```
