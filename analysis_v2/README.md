# Evidex Analysis v2

Research-grade secondary analysis of the existing Evidex experiment
(40,000 GPT-5.4 / GPT-5.4-mini claim-checking observations over 10,000
balanced FEVER claims). **No paid APIs are used**: the existing predictions are
treated as immutable source data; all new computation is local and free.

## Core question

When a model becomes less accurate, remains wrong, or changes behavior after
receiving designated gold evidence, what explains that outcome? The primary
diagnostic cohort is `claim_only correct -> claim_plus_evidence wrong`
(evidence-induced regression), decomposed against model-utilization failure,
evidence-representation failure, and benchmark ambiguity.

## Layout

- `config.py` – paths, constants, seeds, local model names
- `run_all.py` – reproduces everything from immutable source artifacts
- `src/` – one module per analysis stage (see `reports/METHODS.md`)
- `data/derived/` – paired datasets (Parquet), manual-review cohort
- `data/cache/` – expensive local-model caches (embeddings, NLI, spaCy)
- `tables/` – machine-readable results; `figures/` – publication figures
- `reports/` – FINDINGS, METHODS, LIMITATIONS, NOVELTY_BOUNDARIES,
  NEXT_EXPERIMENTS, ANALYSIS_LOG
- `tests/` – unit tests for critical logic

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
cd analysis_v2
python run_all.py            # full pipeline (stages are cached)
python -m pytest tests/ -q   # or: python -m unittest discover -s tests
```

Optional stages (NLI, clustering) degrade gracefully if their models or
libraries are unavailable; the rest of the pipeline still completes.

## Data protection

Everything under the repository root outside `analysis_v2/` is treated as an
immutable source artifact and is unchanged from `main`. All derived data lives
in `analysis_v2/data/`. During development, CWE-22 output-path guards were
briefly added to three original analysis scripts to appease the environment's
security scanner; they were reverted to pristine upstream form in the cleanup
pass because the analysis does not depend on them.
