# Poster presentation info

## Evidex at the April 15, 2026 Annual Research Symposium

This folder documents the research available around the time of Chimdumebi Mitchell Nebolisa's poster presentation at the East Texas A&M University Annual Research Symposium. It separates that stage of Evidex from the later regression-mechanism analyses and manuscript.

**Presentation title:** *When Fact-Checking LLMs Get It Wrong Even With Gold Evidence*  
**Authors:** Chimdumebi Mitchell Nebolisa and Jessica Udry  
**Presenter:** Chimdumebi Mitchell Nebolisa  
**Presentation date:** April 15, 2026  
**Presentation ID:** 046

The event metadata above comes from the author's presentation/CV record. The scientific snapshot below is grounded in the repository's April 10 commit, not reconstructed from today's results.

> **Historical reconstruction, not the final poster file.** This folder was assembled after the presentation from commit [`414806d6b26ea59dcdd2ac663c4a8c35e8e6c916`](https://github.com/ChimdumebiNebolisa/Evidex/tree/414806d6b26ea59dcdd2ac663c4a8c35e8e6c916), dated April 10, 2026. It establishes what the repository documented before the presentation. It does not establish that every sentence or table appeared on the displayed poster. The original exported poster has not been included here.

## What the research covered at that point

The presentation-era question was whether supplying designated gold evidence improves LLM fact-checking compared with showing a claim alone, and what errors remain even when evidence is supplied.

The documented workflow was:

1. Sample 10,000 FEVER development claims: 5,000 `SUPPORTS` and 5,000 `REFUTES`, with sampling seed 42. `NOT ENOUGH INFO` was excluded.
2. Resolve FEVER evidence pointers into readable text from local Wikipedia shards.
3. Evaluate the same claims using `gpt-5.4` and `gpt-5.4-mini`, each under `claim_only` and `claim_plus_evidence` conditions.
4. Score 40,000 model-condition decisions against the FEVER labels and examine remaining errors.

The historical dossier also documents a 50-claim, 200-decision pilot before the full run. That pilot is distinct from the full 10,000-claim experiment.

Source: the unedited [April presentation dossier](presentation_dossier_comprehensive.md).

## Results already documented before the presentation

| Model | Claim-only accuracy | Gold-evidence accuracy | Gain, percentage points | Incorrect evidence-condition decisions |
| --- | ---: | ---: | ---: | ---: |
| GPT-5.4 | 88.69% | 96.04% | +7.35 | 396 / 10,000 |
| GPT-5.4-mini | 84.67% | 95.54% | +10.87 | 446 / 10,000 |
| Combined across models | 86.68% | 95.79% | +9.11 | 842 / 20,000 |

The historical record contains 36,494 correct decisions out of 40,000 overall (91.23%). These are **model-condition decisions**, not 40,000 distinct claims.

The main result at this stage was that gold evidence improved average accuracy substantially, but did not eliminate errors. The presentation dossier additionally described number/date, negation, and comparative-wording themes among incorrect decisions, and counted supported-to-refuted versus refuted-to-supported errors.

These original error-theme observations are preserved in the dossier as historical analysis. They are not the later progressive-disclosure mechanism taxonomy.

Sources: [summary counts](experiment_summary_balanced_10000_v1.csv), [model metrics](experiment_metrics_balanced_10000_v1.csv), and [error-direction counts](error_taxonomy_counts_balanced_10000_v1.csv). These files are unchanged copies from the April 10 snapshot.

## What must not be backdated to the poster

The [current project overview](../README.md) includes subsequent work that should be described separately:

- Analysis v2, including the identified cohort of 226 unique evidence-induced correct-to-wrong regressions and its additional paired statistics and diagnostics.
- Grok, GLM, and Claude automated adjudication and robustness studies, including the full 3,390-judgment Claude replication.
- Cross-family mechanism agreement and synthesis, and the manuscript in preparation.

The earlier prediction files later supported these analyses, but the presence of underlying data before the poster does not establish that a later analysis or finding had already been completed or presented then.

In particular, **842 incorrect evidence-condition decisions is not the same measure as 226 unique evidence-induced regressions**. The former counts incorrect decisions with evidence; the latter identifies claims that changed from correct without evidence to incorrect with it. Do not substitute one number for the other.

The subsequent coherence/non-independent-evidence follow-up is also outside this historical snapshot. It is a later research direction, not a result of the April poster.

## How to describe the chronology

**Poster-stage work:**

> Presented a FEVER-based study of 10,000 balanced claims and 40,000 model-condition decisions, comparing claim-only and gold-evidence fact verification and analyzing errors that remained despite evidence.

**Subsequent development:**

> Subsequently extended the project with paired regression analysis and automated cross-family adjudication; manuscript in preparation.

Use the first description for the April presentation and both, clearly separated, for the overall Evidex research record. Neither description asserts that later findings were presented in April.

## Files and provenance

- [Presentation dossier](presentation_dossier_comprehensive.md): original pre-presentation narrative, preserved without rewriting.
- [Experiment summary](experiment_summary_balanced_10000_v1.csv): original group-level counts.
- [Experiment metrics](experiment_metrics_balanced_10000_v1.csv): original model-level gains and evidence-error rates.
- [Error-direction counts](error_taxonomy_counts_balanced_10000_v1.csv): original direction-of-error summary.
- [Source and preservation notes](PROVENANCE.md): immutable source links, blob hashes, and the limits of this reconstruction.

For the present-day study, use the [main README](../README.md) and [manuscript](../paper/). Keep this folder historical rather than updating its scientific results as the project grows.
