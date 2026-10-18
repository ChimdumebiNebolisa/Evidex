# Evidex

Evidex studies how supplying designated evidence changes LLM fact-verification classifications, including aggregate accuracy, paired regressions and rescues, and variation across repeated calls.

## Latest completed manuscript

**Evidence Benefits and Repeated Classification Losses in LLM Fact Verification**

Chimdumebi Mitchell Nebolisa and Jessica Udry — completed editorial revision, October 17, 2026.

| Material | Latest version |
|---|---|
| Manuscript | [PDF](paper/revisions/2026-10-17-final/manuscript.pdf) · [Word](paper/revisions/2026-10-17-final/manuscript.docx) |
| Editable source | [LaTeX](paper/revisions/2026-10-17-final/manuscript.tex) · [revision directory](paper/revisions/2026-10-17-final/README.md) |
| Supplements S1–S5 | [Index and supporting files](paper/revisions/2026-10-17-final/supplement/SUPPLEMENT.md) · [ZIP download](paper/revisions/2026-10-17-final/supplements-S1-S5.zip) |
| Jessica feedback tracker | [Final actions](paper/revisions/2026-10-17-final/REVISION_TRACKER.md) · [complete tracker CSV](paper/revisions/2026-10-17-final/REVISION_TRACKER.csv) |

The manuscript reports the completed **180,000-response experiment**: 10,000 balanced binary FEVER records, two models, three input conditions, and three fresh calls per cell. It separates evidence addition under a fixed classification instruction from a subsequent evidence-only instruction change. Paired outcomes, repeated-call comparisons and concrete examples complement accuracy. The selected-case taxonomy is exploratory, uses unblinded AI interpretation, and does not constitute human validation or establish internal mechanisms.

## Frozen results and supporting records

- [Original published results bundle](replacement_predictor_v1/published/full3-2026-10-17/README.md), pinned at [commit 3893a57](https://github.com/ChimdumebiNebolisa/Evidex/tree/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17), preserves protocol/source snapshots, frozen analysis and provenance/accounting records.
- The [new companion supplements](paper/revisions/2026-10-17-final/supplement/SUPPLEMENT.md) assemble S1–S5, including later statistical audit and coding-review records. Those later files are not attributed to the original pinned bundle.
- Individual raw request/response bytes, terminal databases and private backups remain local and are excluded from this publication update.

This update publishes completed documents and supporting material. It changes no frozen experiment output or historical data and runs no new experiments.

## Earlier manuscripts and historical work

The [earlier paper draft](paper/evidex-manuscript-draft.pdf), [earlier corrected draft directory](paper_corrected_draft/README.md), [correction records](corrections_v2/README.md), and [historical documents](docs/historical/README.md) remain preserved. They describe earlier cohorts, analyses and automated judging procedures. Their findings and qualifications are separated from the present experiment in Supplement S4.

The [previous repository overview at 3893a57](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/README.md) is available as historical context. The original `evidex-artifact-v1` tag remains an earlier scientific record; it is not the version identifier for the latest manuscript.

## License and third-party data

Project code is under the [MIT License](LICENSE). That license does not relicense FEVER, Wikipedia text or other third-party material. See [data provenance](docs/DATA_PROVENANCE.md).

For citation information, see [CITATION.cff](CITATION.cff).
