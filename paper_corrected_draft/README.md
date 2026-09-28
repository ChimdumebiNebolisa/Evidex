# Corrected submission draft — 2026-09-28 (for coauthor review)

`evidex-corrected-draft.pdf` is the compiled draft. The historical draft in `paper/` is
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
Figures 1–2 are reused unchanged from `../paper/` and `../analysis_v2/figures/`.

```
python corrections_v2/amendment_2026-09-28/amended_analysis.py status   # expect ready_under_amendment_A1
python paper_corrected_draft/make_assets.py
python paper_corrected_draft/check_draft.py
cd paper_corrected_draft && latexmk -pdf main.tex && cp main.pdf evidex-corrected-draft.pdf
```

The PDF was built with TeX Live 2025 (Debian packages) under WSL.

## Decisions for the authors

1. **Main selection.** The draft makes the accepted outputs primary, by amendment, and reports
   first-valid as sensitivity. The alternative is to make first-valid primary, since it is closer
   to the frozen rule. No conclusion changes either way; this choice is about how the paper is
   framed.
2. **The error-ending Grok output** (`p01_C_j5_b09`, attempt 1). It is counted as a valid output
   in the first-valid sensitivity. It changes one non-regression label.
3. **The v2 taxonomy.** Approve its category names and priority order. It was specified post hoc.
4. **Title.** "Diagnosing" was changed to "Characterizing" because the adjudication is descriptive.
5. **Retained Stage A/B judgments.** The draft combines historical A/B judgments with new C
   judgments. This rests on documented, but not independently verified, fresh-context isolation.
6. **Follow-up panels.** The residual Claude panel and the Stage C resolver were not run. Either
   state their absence (current draft) or run them before submission.
7. **Venue, affiliations, and whether to do human review** of the 54–58 Grok–Claude category
   disagreements before submission.
