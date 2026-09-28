# Reproducing the Evidex record in the organized layout

This branch relocates files after the completed study. It does not rewrite the historical protocol or its verifier. The original paths and scripts are available at commit `33121b773ecbd438fc4c473d5b3cd3a06f8961fd`; the initial scientific artifact remains at tag `evidex-artifact-v1`.

From the repository root, first check all moved bytes and the original inventories:

```bash
python tools/verify_layout.py
```

Run original commands in the preserved layout through a temporary Git worktree:

```bash
python tools/run_frozen.py -- python corrections_v2/verify_outputs.py
python tools/run_frozen.py -- python corrections_v2/rerun.py validate --scope required
python tools/run_frozen.py -- python corrections_v2/amendment_2026-09-28/amended_analysis.py verify
python tools/run_frozen.py -- python scripts/verify_all_headlines.py
python tools/run_frozen.py -- python scripts/run_all_tests.py
```

`run_frozen.py` validates the organized files before the checkout. It runs the exact pre-layout code and deletes the temporary checkout on exit. It does not regenerate moved data or run model inference. To reproduce original inference with new outputs, use the archived [historical instructions](docs/historical/REPRODUCING.md) in a separate checkout; those instructions name the old paths and may incur model costs.

Some full-suite hash checks are environment-sensitive: historical raw freezes can fail on Linux line endings, and generated SVG/provenance files may differ across plotting environments. These same failures occur at the unchanged pre-layout commit in this Linux environment. See the [verification note](docs/post_judgment/LAYOUT_MIGRATION_2026-09-28.md); numerical verification and the original source hashes are separate checks.

Check the current manuscript from this branch:

```bash
python paper_corrected_draft/check_draft.py
cd paper_corrected_draft
latexmk -pdf main.tex
```

The committed `evidex-corrected-draft.pdf` is the reviewed document. The historical corrected Stage C outputs and amended analysis are not a preregistered replication of the original experiment. [Current status](docs/CURRENT_STATUS.md) and [the migration note](docs/post_judgment/LAYOUT_MIGRATION_2026-09-28.md) describe their provenance and the limits of the layout adapter.
