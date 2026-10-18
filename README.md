# Evidex

Evidex examines how adding designated evidence changes LLM fact-verification classifications. The study measures overall accuracy, which correct decisions become incorrect, which incorrect decisions are rescued, and how outcomes vary across fresh calls with the same prompt.

## Read the paper

**Evidence Benefits and Repeated Classification Losses in LLM Fact Verification**

Chimdumebi Mitchell Nebolisa and Jessica Udry. Latest completed manuscript revision: **October 17, 2026**.

| Material | Links |
|---|---|
| Manuscript | [PDF](paper/revisions/2026-10-17-final/manuscript.pdf) · [Word](paper/revisions/2026-10-17-final/manuscript.docx) |
| Editable source | [LaTeX](paper/revisions/2026-10-17-final/manuscript.tex) · [bibliography](paper/revisions/2026-10-17-final/references.bib) |
| Supplements S1–S5 | [Index and supporting files](paper/revisions/2026-10-17-final/supplement/SUPPLEMENT.md) · [ZIP download](paper/revisions/2026-10-17-final/supplements-S1-S5.zip) |
| Jessica feedback tracker | [Final revision actions](paper/revisions/2026-10-17-final/REVISION_TRACKER.md) · [complete tracker CSV](paper/revisions/2026-10-17-final/REVISION_TRACKER.csv) |
| Reproducibility | [Instructions, scripts and tests](paper/revisions/2026-10-17-final/reproducibility/README.md) · [final provenance records](paper/revisions/2026-10-17-final/reproducibility/provenance/) |

The [manuscript directory](paper/revisions/2026-10-17-final/README.md) contains the complete current package. Supplements cover execution and accounting (S1), statistical records (S2), exploratory coding and review history (S3), historical findings (S4), and FEVER release correspondence (S5).

## Experiment

The completed experiment contains **180,000 valid responses**: 10,000 balanced binary FEVER records × two models × three conditions × three fresh calls. The models are GPT-5.4 and GPT-5.4-mini; the reference labels are Supported and Refuted. Selected benchmark evidence is supplied directly, with no retrieval.

| Condition | Input | Comparison |
|---|---|---|
| A | Claim only | Claim-only baseline |
| B | Claim and selected evidence; the same classification instruction as A | A→B isolates evidence addition under a fixed instruction |
| C | Same claim and evidence as B; adds “based only on the evidence provided” | B→C tests the additional instruction restriction |

Each repetition is a fresh stateless call. A **regression** is a correct classification becoming incorrect against the unchanged reference label; a **rescue** is the reverse. The repeated-call analysis separately measures correct-to-incorrect outcomes under an identical prompt and disagreement between returned labels.

## Key findings

The following are **primary first-pass results**: repetition index 1, with 10,000 assigned claims per model and condition. Gains are percentage points.

| Model | A accuracy | B accuracy | C accuracy | A→B gain |
|---|---:|---:|---:|---:|
| GPT-5.4 | 88.58% | 96.17% | 96.22% | +7.59 |
| GPT-5.4-mini | 84.90% | 95.45% | 95.70% | +10.55 |

- Evidence addition produced **857 rescues and 98 regressions** for GPT-5.4, and **1,200 rescues and 145 regressions** for GPT-5.4-mini. Aggregate gains therefore coexist with losses on individual claims.
- The subsequent instruction restriction produced smaller first-pass accuracy changes: **+0.05** and **+0.25** percentage points, respectively.
- Across all three matched repetitions, **186 model–claim cases across 160 distinct claims** regressed every time under evidence addition. This describes recurrence in the recorded calls, not permanent failure.

The manuscript and [full results report](replacement_predictor_v1/published/full3-2026-10-17/ACTUAL_RESULTS.md) provide confidence intervals, complete paired outcomes, repeated summaries and denominators. Repeated summaries include repetition 1; they are not an independent replication of the first pass.

These findings concern a fixed balanced binary FEVER slice, supplied evidence, two related models and the recorded collection period. The selected-case taxonomy uses unblinded AI interpretation with incomplete second review and no human validation. Its categories describe visible comparison demands; they do not establish internal mechanisms or population error prevalence. A benchmark regression does not by itself establish factual deterioration.

## Verify the publication

From the repository root, use Python 3.10 or later:

```sh
cd paper/revisions/2026-10-17-final
python reproducibility/verify_publication.py
python -m unittest discover -s reproducibility/tests -p "test_*.py"
```

These standard-library checks verify publication file hashes, agreement with the completed source/PDF/Word records, and supplementary ZIP contents. They make no model calls and do not rerun the scientific analysis. See the [reproducibility guide](paper/revisions/2026-10-17-final/reproducibility/README.md) for source snapshots, Word-export dependencies and their limitations. Historical analysis scripts retain their original directory assumptions and are separate from these portable checks.

## Research record and access

| Record | What it contains |
|---|---|
| [Current manuscript and companion supplements](paper/revisions/2026-10-17-final/README.md) | Latest paper, S1–S5, later statistical audit and taxonomy-review records, feedback tracker and reproducibility material |
| [Frozen published results bundle](replacement_predictor_v1/published/full3-2026-10-17/README.md) | Protocol/source snapshots, frozen analysis, prepared inputs, observations and provenance/accounting records |
| Locally preserved artifacts | Individual raw request/response bytes, terminal databases and private backups; excluded from the public package |

The original results bundle is pinned at [commit 3893a57](https://github.com/ChimdumebiNebolisa/Evidex/tree/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/replacement_predictor_v1/published/full3-2026-10-17). Later audit and taxonomy-review files are provided in the companion supplements, rather than attributed to that original bundle. See the [supplement access notes](paper/revisions/2026-10-17-final/supplement/SUPPLEMENT.md#access-and-version-boundaries) for the precise boundaries.

## Earlier work

The [earlier manuscript draft](paper/evidex-manuscript-draft.pdf), [earlier corrected draft](paper_corrected_draft/README.md), [correction records](corrections_v2/README.md), and [historical documents](docs/historical/README.md) remain preserved. Earlier prediction cohorts, NLI diagnostics and automated judging procedures are distinguished from the present experiment in Supplement S4.

The [previous repository overview](https://github.com/ChimdumebiNebolisa/Evidex/blob/3893a57e6f9addadf2b2fcd2d5a4e7251abcb677/README.md) and the original `evidex-artifact-v1` tag document earlier stages of the project; neither identifies the latest manuscript version.

## License and citation

Project code is under the [MIT License](LICENSE). That license does not relicense FEVER, Wikipedia text or other third-party material. See [data provenance](docs/DATA_PROVENANCE.md) and [CITATION.cff](CITATION.cff).
