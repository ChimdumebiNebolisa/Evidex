# Data provenance and third-party material

## Project license vs data license

The MIT License in [`LICENSE`](../LICENSE) covers **Evidex project code** (scripts, analysis modules, documentation we wrote, configuration).

It does **not** relicense third-party datasets or Wikipedia text. Redistributing files under `*.jsonl` / experiment CSVs / resolved evidence fields is subject to those upstream terms, not to a blanket MIT grant.

If you fork or release this repository, keep this distinction visible. Do not imply that every committed file is MIT-licensed content you created.

## FEVER

Evidex samples claims from the FEVER shared-task development set.

- **Dataset:** Fact Extraction and VERification (FEVER)
- **Paper:** James Thorne, Andreas Vlachos, Christos Christodoulopoulos, and Arpit Mittal. 2018. *FEVER: a Large-scale Dataset for Fact Extraction and VERification.* In *Proceedings of NAACL-HLT*.
- **Project:** https://fever.ai
- **Committed extract:** [`shared_task_dev.jsonl`](../shared_task_dev.jsonl) at the repository root (FEVER development split, used as the sampling frame)
- **Our derived sample:** [`fever_balanced_10000_v1_source.csv`](../fever_balanced_10000_v1_source.csv) — 10,000 claims, 5,000 Supported and 5,000 Refuted, seed 42, `NOT ENOUGH INFO` excluded
- **Sampling record:** [`sample_provenance_balanced_10000_v1.csv`](../sample_provenance_balanced_10000_v1.csv), [`sample_validation_balanced_10000_v1.json`](../sample_validation_balanced_10000_v1.json)

Cite FEVER when you use these files. Follow the FEVER project’s stated terms for the shared-task data. This document does not restate those terms as legal advice.

## Wikipedia-derived evidence

FEVER evidence pointers were resolved against the official FEVER Wikipedia dump (local shards under `wiki-pages/`, **not committed**; ~7 GB; listed in `.gitignore`).

Committed files that contain reconstructed Wikipedia sentence text include, among others:

- `experiment_results_balanced_10000_v1.csv`
- `experiment_runs_balanced_10000_v1.csv`
- `experiment_tracker_with_evidence_balanced_10000_v1.csv`
- `resolve_summary_balanced_10000_v1.json`
- blinded silver packets and frozen judgments that quote supplied evidence sentences

Wikipedia article text is typically offered under Creative Commons Attribution-ShareAlike. Attribution and share-alike obligations, if you redistribute those strings, are **not** replaced by this repository’s MIT license.

The wiki dump itself is an input you must obtain; Evidex does not publish the shards.

## What this repository commits (derived research sample)

| Artifact | Role |
|---|---|
| `shared_task_dev.jsonl` | Upstream FEVER dev split |
| `fever_balanced_10000_v1_source.csv` | Canonical 10K sample |
| `experiment_*_balanced_10000_v1.csv` | GPT runs, results, summaries (not `*_pilot`) |
| `analysis_v2/data/derived/*.parquet` | Paired analysis tables |
| `silver_adjudication_v1/data/` | Blinded cohort, id maps |
| Panel `judgments/` and `freezes/` | Frozen silver outputs |

Historical 1K and pilot files at the root are earlier derived samples of the same kind, not the manuscript experiment.

## What this repository does not commit

- `wiki-pages/` FEVER Wikipedia shards
- API keys (`.env` is gitignored)
- Large local model weights (`*.gguf`, `*.safetensors`)

## Model outputs

GPT predictions and silver-judge verdicts are research outputs of this project. They are not FEVER gold labels and are not human annotations.

## Absolute paths in historical judge prompts

`silver_adjudication_v1/blind_io/launch_prompts/` records the launch text used for Claude full-panel packets, including machine-local Windows paths. Those files are provenance. Do not rewrite them.

## Citation

Use [`CITATION.cff`](../CITATION.cff) for this repository, and cite Thorne et al. (2018) for FEVER.
