# Evidex full3 — completed results for analysis

**Completed and verified on 2026-10-17. No additional paid inference or rerun is needed.**

Start with [actual results](ACTUAL_RESULTS.md), then [compact machine-readable summary](SUMMARY_COMPACT.json). The compact file retains all aggregate accuracy, paired regression/rescue, repeat variability, historical-case, confidence-interval and usage results from the unchanged frozen analysis. Large per-claim arrays remain in the complete compressed frozen summary.

## Results at a glance

10,000 claims × 2 models × 3 conditions × 3 repetitions = **180,000 valid calls**. Zero terminal failed, invalid, uncertain or missing outcomes; no duplicate admissions/response IDs/raw hashes. All usage was recorded. Frozen-rate cost: **$29.78757825**, not a reconciled provider invoice.

| Model | A: claim only | B: claim + gold evidence | C: B + evidence-only instruction |
|---|---:|---:|---:|
| gpt-5.4 | 88.61% | 96.16% | 96.18% |
| gpt-5.4-mini | 84.73% | 95.52% | 95.69% |

These are averages over three repetitions (30,000 calls per cell). The report also contains first-pass results (10,000 per cell). Repetition 1 is included in the repeated summary. Evidence improved accuracy while introducing some regressions. The repeated B→C accuracy intervals include zero for both models. The frozen 2,000-draw bootstrap jointly resamples 9,855 claim-text clusters; conclusions are bounded to the fixed prompts, claim set and provider occasion.

## Read these first

- [Full results report, all comparisons and denominators](ACTUAL_RESULTS.md)
- [Compact summary with all aggregate estimates and confidence intervals](SUMMARY_COMPACT.json)
- [Protocol](snapshot/PROTOCOL.md)
- [Prepared input verification](snapshot/prepared/input-verification.json)
- [Frozen analysis source](snapshot/analyze.py)
- [Current settings and exact message construction](snapshot/common.py)
- [Integrity/accounting PASS](snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/INTEGRITY.json)
- [Analysis-output verification PASS](snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/ANALYSIS_VERIFICATION.json)
- [Independent pair/repeat checks and numeric supplement](snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/RESULTS_VERIFICATION.json)
- [Manifest of every source/published hash and compressed file](MANIFEST.json)

## Complete data and frozen outputs

| File | Contents |
|---|---|
| [Frozen summary.json.gz](snapshot/runs/full3/analysis-2026-10-17T18-43-50.666851+00-00/summary.json.gz) | Complete unchanged summary including per-claim repeat arrays |
| [observations.csv.gz](snapshot/runs/full3/analysis-2026-10-17T18-43-50.666851+00-00/observations.csv.gz) | All 180,000 frozen observation rows |
| [provenance.json.gz](snapshot/runs/full3/analysis-2026-10-17T18-43-50.666851+00-00/provenance.json.gz) | All 180,000 raw-response provenance hashes |
| [OUTCOMES.jsonl.gz](snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/OUTCOMES.jsonl.gz) | Independently reconciled outcomes, correctness, request counts and models |
| [Prepared inputs.jsonl](snapshot/prepared/inputs.jsonl) | Claims, gold labels/evidence, clusters and historical flags |
| [Prepared full3 jobs.jsonl.gz](snapshot/prepared/full3/jobs.jsonl.gz) | All randomized planned jobs and prepared request hashes |
| [Final artifact inventory.jsonl.gz](snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/ARTIFACT_INVENTORY.jsonl.gz) | All 720,008 preserved artifact paths, sizes and hashes |
| [Response hashes.json.gz](snapshot/reports/full3-final-2026-10-17T13-43-20.656767+00-00/RESPONSE_HASHES.json.gz) | Independent raw-response hash map |

Files ending in `.gz` are losslessly compressed. In Python use `gzip.open(path, 'rt', encoding='utf-8')` to read them; source and published SHA256 values are in the manifest. GitHub may not preview large or compressed files; download the raw file or use the compact summary for browser-based review.

## Operational history and interpretation

The snapshot includes every experiment report and operational revision document, saved tests, incident/recovery evidence, process/exit records, seal records and current implementation/tests. The collection finished normally; a later Windows update interrupted only the first offline analysis. The preserved recovery used unchanged frozen scientific source and settings and passed final output verification. Earlier launch/readme documents describe historical authorization and commands; they are **not instructions to start another run**.

Database backups and individual raw inference artifacts remain preserved locally. The manifest inventories the excluded database copies; their hashes and integrity records are published. The full raw-artifact inventory is included, but this documentation package alone cannot rerun byte-level checks against unpublished raw response bytes. No credentials or environment files are included. This publication adds no new inference and changes no original experiment artifacts.

## Suggested request for ChatGPT

> Analyze this completed Evidex full3 experiment. Start with ACTUAL_RESULTS.md, SUMMARY_COMPACT.json and PROTOCOL.md. Check the assigned denominators and paired comparisons; distinguish first-pass results from summaries including all three repetitions. Assess evidence benefits, regressions, rescues, identical-prompt variability, and the small B-to-C differences using the frozen confidence intervals. Explain the fixed-provider-occasion and historical-snapshot limits. Do not invent missing results or treat this recorded usage cost as a reconciled invoice. Use the complete compressed outputs and independent outcomes if you need per-claim analysis.
