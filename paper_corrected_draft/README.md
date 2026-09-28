# Corrected manuscript draft — 2026-09-28 (for coauthor review)

This is a corrected draft of the Evidex manuscript. It is **not** a submission, and it replaces
nothing: the historical draft in `paper/` is hash-pinned and unchanged.

- Behavioral findings (RQ1/RQ2 and the NLI characterization) are carried over unchanged.
- The historical mechanism splits, the ordering claim and the old taxonomy agreement are withdrawn.
  They appear only in the appendix list of withdrawn results.
- Corrected diagnostics come from the dated post-judgment deviation analysis
  (`docs/post_judgment/POST_JUDGMENT_ANALYSIS_NOTE_2026-09-28.md`), not from the frozen protocol's
  primary analysis, which is incomplete.
- `CLAIM_MAPPING.md` maps each old claim to its corrected status.

## Layout

The draft reuses unchanged pinned files by relative path instead of copying them:
`../paper/tables/tab_accuracy.tex`, `../paper/references.bib`, and two figures in
`../analysis_v2/figures/`. Every other section is new or rewritten here.

## Build

No LaTeX toolchain (`pdflatex`, `latexmk`, `tectonic`, `bibtex`) is installed on the machine that
prepared this draft, so **it has not been compiled**. With a TeX distribution:

```
cd paper_corrected_draft
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

`python paper_corrected_draft/check_draft.py` runs a static check that needs no toolchain:

- brace and environment balance;
- every `\input` and figure target exists;
- every `\ref` has a `\label`;
- every citation key is in the bibliography;
- withdrawn historical figures appear only in the appendix list of withdrawn results.

## Needs coauthor judgment

1. **Main selection.** The draft reports both the accepted outputs and the Claude first-valid
   selection. Choosing one as the main estimate is a post-judgment decision.
2. **The error-ending Grok output** (`p01_C_j5_b09` slot 1). It is excluded from both selections and
   reported as a sensitivity result. Whether an unfinished run counts as a "response" under the
   first-valid rule is a protocol interpretation.
3. **Whether the deviation analysis can carry diagnostic claims at all.** The alternative is to
   report the diagnostics as pending, as proposed in `corrections_v2/MANUSCRIPT_CHANGES.md`.
4. **The v2 descriptive taxonomy.** It was specified post hoc and is marked "requires coauthor
   review" in the frozen protocol. That covers category names, priority order, and treating
   additional-evidence cases separately.
5. **Title and RQ3/RQ4 wording.** "Diagnosing" and "failure modes" may overstate what descriptive
   judge outcomes show.
6. **Hybrid provenance.** Consensus paths use retained historical A/B judgments with new C
   judgments. The retention is justified only by the documented, not independently verified,
   fresh-context isolation.
7. **Figures.** No corrected figure is included. Provisional SVG plots exist under
   `corrections_v2/deviation_review/provisional_results/`. Whether to adopt, redraw or omit them
   needs a decision.
8. **Follow-up panels not run.** These are the new residual Claude panel, the Stage C resolver and
   the optional historical residual panel. Decide whether the paper needs any of them, or states
   their absence as in Limitations.
9. **Disagreement review.** The discussion proposes human review of the 54–58 claim-level
   category disagreements.
10. **Affiliations and venue.** These are still TODO, as in the historical draft.
