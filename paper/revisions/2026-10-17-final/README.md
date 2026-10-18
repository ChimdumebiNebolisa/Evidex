# Latest completed Evidex manuscript — October 17, 2026

**Evidence Benefits and Repeated Classification Losses in LLM Fact Verification**

Chimdumebi Mitchell Nebolisa and Jessica Udry

- [Read the manuscript PDF](manuscript.pdf) — the inspected 13-page layout.
- [Download the editable Word version](manuscript.docx).
- [LaTeX source](manuscript.tex), [master template](manuscript.template.tex), and [bibliography](references.bib).
- [Supplements S1–S5 with supporting files](supplement/SUPPLEMENT.md), or [download the supplementary ZIP](supplements-S1-S5.zip).
- [Jessica feedback revision tracker](REVISION_TRACKER.md) and [full 98-entry tracker](REVISION_TRACKER.csv).
- [Document agreement record](DOCUMENT_AGREEMENT.json) and [publication file manifest](PUBLICATION_MANIFEST.json).

This is the latest completed revision, incorporating the remaining September 22 and October 2 feedback. It distinguishes fixed-instruction evidence addition from the subsequent instruction change in the completed 180,000-response experiment. Related Work ends with the study-specific discussion; general methodology precedes experiment settings and results. Repeated-call comparisons and worked regression/rescue examples accompany the exploratory AI taxonomy and its stated limitations.

S1–S5 cover execution/accounting, full statistical records, selected-case coding/review, historical context, and FEVER release correspondence. They include later supporting records that are separate from the [original pinned results bundle](../../../replacement_predictor_v1/published/full3-2026-10-17/README.md). Raw request/response bytes, databases, private backups and temporary QA/build files are excluded. Existing backup-verification records describe local preservation; they are not backup contents.

The PDF, Word, source, examples, bibliography and tracker are copied from the completed local revision. Publication changes only navigation/access wording. No experiment, statistical definition, result or reference label was changed. All PDF pages and bounded Word content renders were inspected in the completed revision. Full native Microsoft Word pagination remains unverified; use the PDF as the layout reference.

## Compile the source

From this directory, run `tectonic -X compile --untrusted manuscript.tex` or `latexmk -pdf manuscript.tex` with the necessary LaTeX packages installed. The source uses references.bib and figures/workflow.pdf. No experiment or inference command is needed.

## Earlier records

- [Earlier manuscript draft](../../evidex-manuscript-draft.pdf) remains preserved.
- [Historical study documents](../../../docs/historical/README.md) and the [previous repository overview](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/README.md) describe earlier work; they are not extra observations from the present experiment.
- FEVER/Wikipedia material retains its original rights; the project code license does not relicense third-party data. See [data provenance](../../../docs/DATA_PROVENANCE.md).
