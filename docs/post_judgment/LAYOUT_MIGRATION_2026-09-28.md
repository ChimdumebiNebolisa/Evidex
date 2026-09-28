# Organized layout after the correction study

This is a path migration from commit `33121b773ecbd438fc4c473d5b3cd3a06f8961fd`, not a new scientific analysis. The 121 renamed files retain their content. The full old-to-new map and hashes are in [`ROOT_LAYOUT_MIGRATION_2026-09-28.json`](ROOT_LAYOUT_MIGRATION_2026-09-28.json). The verifier accepts only CRLF-to-LF equivalence for text files; the historical PDF is byte-exact.

The repository root now contains entry documents, license/citation files and dependency information. Full-study inputs, predictions, old scripts, the old manuscript and pilot outputs live under `historical/`; the current manuscript and correction package remain separate.

The 774-entry historical inventory, 37-file correction implementation fingerprint, 103-file prepared-output inventory, 18-file protocol freeze and original artifact tag have not been rewritten. `tools/verify_layout.py` reads the original inventories and checks each old path at its mapped location, including a comparison of moved content to the pre-layout Git commit. It also checks the unchanged protocol freeze, prepared-output inventory and tag.

The original scripts contain literal root paths. They are preserved at the pre-layout commit and are run by `tools/run_frozen.py` from a temporary worktree. Calling those scripts directly from the organized tree is not a supported command. This limitation is explicit; a future native path migration would require a new, versioned implementation and fresh verification. No generated manuscript numbers, judge outputs, or original provenance records are silently rewritten to make old code pass at new paths.

The old layout remains checkable at commit `33121b7`, and the scientific artifact remains checkable at tag `evidex-artifact-v1`. The layout verifier must pass before any original command is run through the adapter. The current draft's LaTeX references to the moved historical bibliography and accuracy table were updated; it compiles from this branch.

## Verification in this environment

- `verify_layout.py`, the pre-layout `verify_outputs.py`, the required-job schema check, amended status, and the corrected draft's static check pass. The PDF builds at 21 pages.
- The legacy headline/test suites have numerical successes but fail their raw freeze checks on this Linux checkout because of historical line-ending differences. The same limitation existed before the layout migration.
- Full byte-for-byte amended-result verification fails here for generated SVGs and provenance-derived files. Running that command directly at unchanged commit `33121b7` produces the same differences. This is an environment-sensitive reproduction limit, not a layout-induced change. Use the original recorded verification environment for the complete historical check; do not regenerate or overwrite committed result artifacts merely to silence this difference.
