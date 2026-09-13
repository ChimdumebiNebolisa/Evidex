# Cursor silver-adjudication panel

Complete progressive-disclosure panel using **one locked Cursor model** for
all five judges, all three stages, and the resolver.

- Model: `cursor-grok-4.6-high-fast` (see `config.json`)
- Judges: `cursor_judge_1` … `cursor_judge_5`
- This is one model family. It is **not** independent human validation.
- GLM-5.3 contributes only the separate frozen Stage A replication panel.
  Partial GLM Stage B is provenance only and is excluded from these analyses.
- Findings: `reports/SILVER_FINDINGS.md`, `reports/LIMITATIONS.md`,
  `reports/HEADLINES.json`. Mechanism decision: mixed.

## Layout

- `config.json` — model lock (do not change mid-run)
- `judgments/` — raw Cursor outputs (never write into `../judgments/`)
- `freezes/` — stage and pre-unblinding manifests
- `tables/`, `reports/`, `cache/`

Shared blinded cohort and stage files remain in `../data/`.

## Reproduce

Run these from `silver_adjudication_v1/`, not from `cursor_panel/`.

Level 1 (read-only headline verification):

```bash
python src/verify_headlines.py --panel cursor
python -m unittest discover -s tests
```

`--panel cursor` is required. The default panel name is GLM.

Optional Level 2 orchestrator (not the public verification path):

```bash
python run_all.py --panel cursor
```
