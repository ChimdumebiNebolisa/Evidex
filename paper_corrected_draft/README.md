# Corrected submission draft — 2026-09-28 (for coauthor review)

`evidex-corrected-draft.pdf` is the compiled draft. The historical draft in `historical/paper/` is
hash-pinned and unchanged.

- Behavioral findings (RQ1/RQ2 and the NLI characterization) are carried over unchanged.
- Adjudication results (RQ3/RQ4) come from the 70 accepted Stage C outputs, analysed under the
  dated post-judgment amendment A1 (`corrections_v2/amendment_2026-09-28/AMENDMENT_A1.md`), with
  the first-valid outputs as sensitivity.
- The historical mechanism splits, the ordering claim and the old taxonomy agreement are withdrawn.
  They appear only in the appendix list of withdrawn results.
- `CLAIM_MAPPING.md` maps each old claim to its corrected status.

## Sources and build

Tables 2–4 and Figures 3–4 are generated from
`corrections_v2/amendment_2026-09-28/results/` by `make_assets.py`. Table 1, the bibliography and
Figures 1–2 are reused unchanged from `../historical/paper/` and `../analysis_v2/figures/`.

```
python tools/run_frozen.py -- python corrections_v2/amendment_2026-09-28/amended_analysis.py status   # expect ready_under_amendment_A1
python paper_corrected_draft/make_assets.py
python paper_corrected_draft/check_draft.py
cd paper_corrected_draft && latexmk -pdf main.tex && cp main.pdf evidex-corrected-draft.pdf
```

The PDF was built with TeX Live 2025 (Debian packages) under WSL.

## Provisional editorial choices (change freely)

- Title: "Characterizing" replaces the historical "Diagnosing", because the adjudication is
  descriptive.
- The error-ending Grok output (`p01_C_j5_b09`, attempt 1) counts as valid in the first-valid
  sensitivity; it changes one non-regression label from Ambiguous to Unresolved.
- Figures and tables are top-of-page floats; Tables 1–4 are placed just before the Results
  section, Figures 1–4 within it.

## Decisions for the authors

1. **Amendment A1 and the main selection.** Endorse the post-judgment amendment and the
   accepted outputs as primary, or make first-valid primary (closer to the frozen rule). No
   conclusion changes either way.
2. **The v2 taxonomy.** Approve its category names and priority order. It was specified post hoc.
3. **Retained Stage A/B judgments.** Accept combining historical A/B with new C judgments, which
   rests on documented but not independently verified fresh-context isolation.
4. **Before submission:** whether to run the residual Claude panel, the Stage C resolver or a
   human review of the 54–58 Grok–Claude category disagreements (the draft states that none was
   run); the venue; affiliations.
