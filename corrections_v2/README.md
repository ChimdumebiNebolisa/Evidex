# Evidex methodological correction v2

Status: local corrections and deterministic reanalysis complete; **corrected-packet judgments pending**. Proposed taxonomy requires coauthor review. Nothing here relabels FEVER or changes the original correct-to-wrong regression definition. No inference is launched by these scripts.

Start with [FINDINGS.md](FINDINGS.md), [RERUN.md](RERUN.md), and [MANUSCRIPT_CHANGES.md](MANUSCRIPT_CHANGES.md). The original manuscript and all historical predictions, packets, judgments, tables, figures, and freeze manifests remain unchanged.

The offline fresh-judgment pipeline is implemented in `analysis_pipeline.py`,
`analysis_io.py`, and `analysis_core.py`. Start execution handoff with
[CURSOR_HANDOFF.md](CURSOR_HANDOFF.md) and the dated
[post hoc correction protocol](protocol/analysis_spec_2026-09-27.md).
The exact 775-to-774 reconciliation is in
[INVENTORY_RECONCILIATION.md](INVENTORY_RECONCILIATION.md): the page snapshot moved
to `inputs/` and remains separately integrity-checked.

From the repository root:

```powershell
python corrections_v2/reproduce.py
python corrections_v2/verify_outputs.py
python corrections_v2/reproduce.py
python corrections_v2/verify_outputs.py
python -m unittest discover -s corrections_v2/tests -v
```

Each command above exits 0 on success. Reproduction now includes the downstream report build and freeze/EOL audit, and seals all generated hashes after their final writes. Verification is read-only. Two runs work even after the correction package is tracked/committed. The equivalent explicit snapshot command is `python corrections_v2/reproduce.py --pages corrections_v2/inputs/historical_pages.json`.

The pinned historical page snapshot is included in `inputs/`; no gitignored cache, archive scan, download, or model call is needed. Its identity is in `baseline/page_snapshot.json`; original acquisition hashes are preserved in `inputs/archive_provenance.json`. The 774 historical source identities are fixed in `baseline/historical_inputs.json`, anchored to source commit `776d09b`, with raw hashes retained from reviewed correction commit `0cc36f0`. Historical and snapshot checks run BEFORE any output write. Substantive drift exits nonzero; it is never accepted by recording a new hash.

Provenance is separated: immutable baseline inventories in `baseline/`; actual correction code/configuration identity in `generated/code_hashes.json` (LF-equivalent text SHA-256); generated exact bytes in `generated/output_hashes.json`. No inventory hashes itself. `source_revision.json` distinguishes scientific artifact commit, source baseline commit and implementation Git revision. Actual code fingerprints include uncommitted corrections, so HEAD alone is not asserted to contain all executed changes.

New artifacts use deterministic UTF-8/LF serialization, and scoped `.gitattributes` enforces LF checkout only within `corrections_v2/`. Packet hashes are exact actual-byte hashes; EOL folding is NOT accepted for new packets. Historical text permits only CRLF→LF equivalence: no whitespace stripping, value changes, record removal/reordering, BOM changes, or missing final newline. Binary files require exact bytes. `historical_integrity.json` distinguishes `exact_recorded_bytes` from `eol_only_equivalent`; neither the historical freeze manifests nor the artifact tag is rewritten. Audit reports of raw bytes can legitimately differ across checkouts even though packet bytes reproduce identically.

Handoff ZIP files are binary (`*.zip -text`), not subject to text EOL conversion.

`reproduce.py` writes only `generated/` and `blind_io/`; it refuses to run once delivered `*.output.json` files exist. Do not run historical unblind/figure-generation commands to create v2 outputs: their paths and rules belong to v1. Standalone report builders are maintenance helpers: if you run one, run the full reproduction command afterward to finalize inventories before verification.

Prepared inputs and judgment completeness are separate checks:

```powershell
python corrections_v2/verify_outputs.py
python corrections_v2/rerun.py validate --scope required
python corrections_v2/rerun.py validate --scope optional
python corrections_v2/rerun.py validate --scope all
```

Preparation exits 0 when inputs and generated artifacts verify, even with no judgments. With current pending judgments, each completion command exits 1. Required scope is the default: it exits 0 once the 70 required jobs / 6,430 judgments are schema-valid, regardless of absent/invalid optional outputs. Explicit `all` also requires 15 optional jobs / 1,155 judgments. Missing or malformed selected outputs exit 1. The JSON report separately identifies preparation, schema validity, required/optional completeness, unassessed execution provenance and uncomputed/unvalidated consensus. A schema-complete result does not prove inference, routing, provenance or scientific validity.

For isolated committed-checkout regression tests (temporary local Git objects/clones, no branch update or push):

```powershell
python corrections_v2/tests/check_clean_checkout.py --autocrlf true
python corrections_v2/tests/check_clean_checkout.py --autocrlf false
```

Both exit 0 when the integration checks pass. The script prints its OS and retained log directory, runs reproduction twice, verifies identical output hashes, and proves historical drift fails before writes. `false` on Windows tests LF checkout behavior, not native Linux; native Linux requires executing the command under Linux. See [VERIFICATION.md](VERIFICATION.md) for environments actually exercised and historical raw-freeze limitations.

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
| `historical_integrity.json`, `snapshot_integrity.json`, `freeze_eol_audit.json` | Exact versus EOL-only historical verification observations |
| `code_hashes.json`, `source_revision.json`, `output_hashes.json` | Separate implementation identity and finalized generated-byte inventory |

Historical reference: base commit `776d09b40e9161800bf87238eb2cac4fe102df8e`; annotated tag `evidex-artifact-v1` resolves to commit `29102c39427fac01ff46c77c28365feb91f6397b` (the tag object's hash is different). No tag was moved.

## Offline corrected-analysis lifecycle

Finalize preparation before dispatch, then freeze the dated protocol and export
the operator bundle (all commands offline, expected exit 0):

```powershell
python corrections_v2/reproduce.py
python corrections_v2/verify_outputs.py
python corrections_v2/analysis_pipeline.py freeze-spec
python corrections_v2/analysis_pipeline.py export-handoff
```

While fresh judgments are absent, these commands exit 1 with explicit pending
status and do not create scientific tables, plots or estimates:

```powershell
python corrections_v2/analysis_pipeline.py status --panel primary
python corrections_v2/analysis_pipeline.py freeze --panel primary
python corrections_v2/analysis_pipeline.py analyze --panel primary --version run001
```

After actual execution and reviewed provenance, `freeze` and `analyze` exit 0;
`python corrections_v2/analysis_pipeline.py verify-result --version run001`
verifies linked exact-byte freezes and generated artifacts. Integrity/spec drift
exits 2. Completed result versions cannot be overwritten. No inference is ever
invoked. `rerun.py validate` remains schema-only; analysis additionally requires
complete execution records/evidence and a judgment freeze.

The analysis reproduces the historical consensus rule in fixed judge-slot order,
reports order-sensitive modal ties, joins retained A/B with provenance, applies
the unchanged proposed v2 taxonomy, computes transitions/agreement and documented
post hoc statistics, and writes versioned CSV/JSON/SVG artifacts and deterministic
representative cases. Grok-complete runs prepare a newly selected Claude residual
cohort and separate resolver jobs. See the handoff for conditional-panel commands,
safe resume/retry procedures and model-routing/isolation gates. Exact historical
model availability remains unverified.
