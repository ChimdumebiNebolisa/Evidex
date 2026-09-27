# Evidex methodological correction v2

Status: local corrections and deterministic reanalysis complete; **corrected-packet judgments pending**. Proposed taxonomy requires coauthor review. Nothing here relabels FEVER or changes the original correct-to-wrong regression definition. No inference is launched by these scripts.

Start with [FINDINGS.md](FINDINGS.md), [RERUN.md](RERUN.md), and [MANUSCRIPT_CHANGES.md](MANUSCRIPT_CHANGES.md). The original manuscript and all historical predictions, packets, judgments, tables, figures, and freeze manifests remain unchanged.

From the repository root:

```powershell
python corrections_v2/reproduce.py --pages corrections_v2/generated/historical_pages_used.json
python corrections_v2/audit_freezes.py
python corrections_v2/build_report_data.py
python -m unittest discover -s corrections_v2/tests -v
python corrections_v2/verify_outputs.py
```

The exported historical page snapshot is included so reproduction does not require a multi-gigabyte archive scan. Its SHA-256 and the original local cache/shard hashes are in `generated/archive_provenance.json`. To audit acquisition independently, `python corrections_v2/reproduce.py` uses the existing local Stage C cache and the documented `wiki-pages/wiki-pages/` shards. It does not download anything. Missing text is explicit; canonical selected-text conflicts fail closed.

`reproduce.py` writes only `generated/` and `blind_io/`; it refuses to run once delivered `*.output.json` files exist. Do not run historical unblind/figure-generation commands to create v2 outputs: their paths and rules belong to v1.

Key artifacts:

| File in `generated/` | Purpose |
|---|---|
| `behavioral_counts.json` | Independent recount from 40,000 predictions |
| `evidence_audit.jsonl` | Exact chosen set IDs, ordered pointers, per-claim mismatch causes |
| `sentence_validation.jsonl` | Chosen/alternative annotation index, pointer, text, availability |
| `stage_b_corrected.jsonl`, `stage_c_corrected.jsonl` | B equal to history; C reconstructed separately |
| `taxonomy_rule_only.csv` | Explicit v1-input reanalysis, not corrected-packet results |
| `representative_cases.json` | Real defective evidence and judge/FEVER disagreement examples |
| `rerun_manifest.json` | Locked models, exact IDs, calls, packet hashes, dispatch prompts |
| `impact_manifest.json`, `impact_items.jsonl` | Source-to-claim dependency map, including every planned item/judge |
| `input_hashes.json`, `archive_provenance.json`, `freeze_eol_audit.json` | Reproducibility and preservation evidence |

Historical reference: base commit `776d09b40e9161800bf87238eb2cac4fe102df8e`; annotated tag `evidex-artifact-v1` resolves to commit `29102c39427fac01ff46c77c28365feb91f6397b` (the tag object's hash is different). No tag was moved.
