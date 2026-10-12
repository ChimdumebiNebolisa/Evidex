# Current manuscript — October 11, 2026

**Evidence-Conditioned Classification and Judge Family Sensitivity in LLM Fact Verification**

- [PDF](evidex-corrected-draft.pdf)
- [Editable Word](evidex-corrected-draft.docx)
- [LaTeX master](main.tex), with [bibliography](references.bib)

These formats contain the final reviewed manuscript, including the expanded RQ2, exploratory NLI integration, Figure 1 caption and parallel-method clarification, and removal of the specified defensive sentence. Word was exported from the same LaTeX text, citations, tables and figures. Pagination may differ across formats. This is a neutral coauthor review draft; venue compliance has not been assessed.

## Build and check

```bash
python paper_corrected_draft/check_draft.py
cd paper_corrected_draft
latexmk -pdf main.tex
```

Alternatively, use Tectonic with `tectonic -X compile --untrusted main.tex`. The master includes its methodology and appendices directly, uses the local bibliography, the five `figures/fig1`–`fig5` files, and `tables/sensitivity.tex` and `tables/family_tests.tex`. The published PDF is the reviewed export, rather than an automatically regenerated unreviewed version.

The earlier `sections/`, `appendix.tex`, legacy figure/table files, `make_assets.py` and `CLAIM_MAPPING.md` are retained for traceability; they are not inputs to the current master. Do not use the legacy asset generator to rebuild this version. Earlier current-paper versions also remain in Git history. The hash-pinned manuscript in `../historical/paper/` is unchanged.

## Scientific provenance

The original paired predictions and existing NLI analyses are unchanged. The adjudication reports accepted outputs under the post-execution September 28 amendment A1 as the main analysis, with first-valid outputs as sensitivity. The original September 27 frozen-protocol primary analysis remains incomplete. Judge verdicts remain unvalidated silver judgments; the proposed taxonomy requires coauthor review. Correction records, historical judgments and withdrawn estimates retain their documented status. This replacement makes no new experimental or protocol change.
