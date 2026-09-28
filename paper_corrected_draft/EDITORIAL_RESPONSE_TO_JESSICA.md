# Editorial response to Jessica Udry's comments

Source: `MitchManuscript_Mu_Re_09.21.2026 (1).docx`, containing 26 comments and 143 tracked insertions and deletions.
That document annotates an older draft.
Its edits were applied to the current corrected draft (`paper_corrected_draft/`) only where the passage still exists.
Withdrawn findings were not restored.
Factual answers are the authors' answers (2026-09-28), not new analysis.
No numbers, tables, figures, taxonomy, output selection or research artifacts were changed.

Status key:
- **Addressed**: the passage still exists in the current draft and was revised.
- **Withdrawn**: the old passage belongs to results withdrawn in the correction; it survives only in Appendix C, where it is labelled withdrawn.

## Comments

| ID | Comment (abridged) | Old anchor | Change made | Where in current draft | Status |
|---|---|---|---|---|---|
| 16 | Explain what FEVER is and why you chose it | "FEVER dataset" (Intro) | Defined FEVER as a Wikipedia claim-verification dataset with Supported, Refuted and Not Enough Info labels and annotated evidence. Gave the reason for choosing it: a balanced 10,000-claim development sample with designated evidence allows a paired with/without comparison that keeps retrieval out. Stated the restriction to two labels and that the sample does not represent all of FEVER. | Intro, second paragraph; Related Work 2.1 | Addressed |
| 42 | Clarify "evidence representation … changes the warrant" | Old three diagnostic situations, item 2 | Replaced with the author answer: a correct-to-wrong change is an observed regression, not its cause. The three possible sources are stated plainly. The claim of a representation effect is not retained (Discussion 5.4 says no pure representation effect is measured). | Intro, fourth paragraph; Discussion 5.4 | Addressed (old representation claim withdrawn) |
| 56 | Explain "progressive-disclosure silver adjudication" | Intro | Defined "silver" as automated model judgments, not expert human ground truth. Defined progressive disclosure: Stage A sentence text (as GPT saw it), Stage B adds titles, Stage C adds structured evidence with available alternatives. Stated why the stages answer the question. | Intro, fourth paragraph; Methods 3.7 | Addressed |
| 60 | What are the "diagnostic decompositions" and "measurement uncertainty"? | Intro | Old phrase removed. Stated that the two judge families can assign the same claim to different categories. This is presented as dependence on the measurement instrument, not as a statistical interval for true prevalence. | Intro, "two findings" paragraph; Discussion 5.5 | Addressed |
| 64 | What is "the first shared task"? | Related Work | Identified as the 2018 FEVER shared task (retrieve Wikipedia evidence and classify claims; best FEVER score 64.21%). | Related Work 2.1 | Addressed |
| 67 | Is "extended the content of" accurate? | Related Work (later datasets) | Each dataset description was rewritten and checked against its source abstract (see citation table). | Related Work 2.1 | Addressed |
| 69 | Logical flow of the claim-only-artifact sentence | Related Work (Schuster 2019) | Moved into its own paragraph with an explicit link: claim-only cues mean accuracy with evidence does not show what the evidence contributed, which motivates comparing claims with and without evidence. | Related Work 2.1, second paragraph | Addressed |
| 70 | Move current-study material to the end of the section | "Our experiment holds retrieval fixed…" | All description of the current study moved to a new final subsection. | Related Work 2.5 | Addressed |
| 71 | Clarify the logic linking to the current study | Same passage | Added the gap bridge from the author answer: aggregate gains and prior evidence-use work do not show how often correct-to-wrong changes occur under paired gold evidence, or whether an automated characterization is stable across judge families. | Related Work 2.5 | Addressed |
| 81 | How does designating evidence as gold solve the problem? | LLM-with-evidence paragraph | Rewrote per the author answer. Gold evidence is annotated FEVER evidence placed directly in the input. It removes retrieval failure as an explanation within this paired experiment only. It does not guarantee attention, sufficiency for every reader, or a known internal cause. | Related Work 2.2 (end) and 2.5; Methods 3.3 | Addressed |
| 87 | Is "relevant information … where and how it is written" accurate? | Liu et al. 2024 | "how it is written" is not supported by the source. Narrowed to position of relevant information in long inputs. | Related Work 2.2 | Addressed |
| 90 | Is "regressions demonstrate the failure is not due to retrieval" accurate? | Related Work | Not accurate as stated. Replaced with the within-experiment wording from the author answer (see 81). | Related Work 2.5 | Addressed |
| 104 | The evidence-sufficiency paragraph is unclear | Related Work | Rewrote per the author answer. Evidence appearing in a prompt differs from a judge finding it sufficient. A nondecisive verdict is a judge outcome, not proof of insufficiency. | Related Work 2.3 | Addressed |
| 119 | "What does it mean then?" (disagreement with FEVER) | Related Work | A decisive verdict opposite to FEVER is disagreement with the benchmark label, not proof of a dataset error. Stated in both places. | Related Work 2.3; Discussion 5.2 | Addressed |
| 123 | Explain exactly what "judges" are | Related Work | Defined an LLM judge. Stated that each panel is five isolated runs per stage of a locked model (Grok or Claude) applying the same rubric to the same 226 regressions, and that Grok also judges the larger diagnostic cohort. Stated that these are model-based judges, not independent human experts. | Related Work 2.4 and 2.5; Methods 3.6 and 3.7 | Addressed |
| 124 | "We treat judge-family disagreement as a result" is vague | Related Work | Replaced: agreement supports a description both panels produce; disagreement indicates sensitivity to the judge family. | Related Work 2.5; Discussion 5.5 | Addressed |
| 133 | Does "Neither panel is human ground truth" strengthen the claims? | Related Work (Jessica deleted it) | Sentence removed. Its content is kept as a definition ("model-based judges, not independent human experts") and in Limitations. Any wording implying the two panels bound a true prevalence was removed. | Related Work 2.5; Limitations | Addressed |
| 138 | Give context before the research questions | Methods (research questions) | Added a paragraph describing the two-part structure (behavioral measurement, then judge-panel description) before the research-question list. The introduction now links the contributions to the research questions in one connected sentence. | Methods 3.1; Intro (Contributions) | Addressed |
| 140 | List-like "robust across both panels" passage | Old results (utilization failure largest; category ordering replicates) | Old claims not retained. The current counterpart ("What depends on the judge family") was rewritten as connected prose with no withdrawn claims. | Results 4.7; withdrawn claims listed only in Appendix C | Withdrawn (old content); current counterpart addressed |
| 151 | Missing verb / unclear ("wrong unit for reliability engineering") | Discussion 5.1 | Rewritten: "Aggregate accuracy is nevertheless the wrong unit for evaluating reliability, because it nets these movements against each other." | Discussion 5.1 | Addressed |
| 153 | Confusing "1.15–1.51% is small … and large if …" | Discussion 5.1 | Replaced with concrete counts: 115/10,000 (1.15%) and 151/10,000 (1.51%) correct-to-wrong changes, and 226 distinct claims. Aggregate accuracy improves, yet condition-level accuracy conceals these reversals. | Discussion 5.1; Intro, third paragraph | Addressed |
| 163 | Is "accuracy labels" correct? | Discussion 5.2 (Jessica's insertion) | Replaced with "predicted labels, not rationales or confidence scores that would show why GPT changed its answer." Also applied in Methods 3.3 and Limitations. | Discussion 5.2; Methods 3.3; Limitations | Addressed |
| 169 | "What does this mean?" (utilization-failure interval, 50–66%) | Old Discussion | Legacy taxonomy result, withdrawn. It appears only in Appendix C, labelled withdrawn. The current Discussion reports the sentence-only shares (34.1% and 46.9%) as compatible with, but not establishing, a GPT utilization failure. | Discussion 5.2 and 5.5; Appendix C | Withdrawn |
| 170 | "cite" (50.0/11.9/38.1 passage) | Old Discussion | Passage withdrawn. No citation added, because the passage no longer exists in the current text. | Appendix C only | Withdrawn |
| 171 | Explain why the finding matters | Same passage | Passage withdrawn. The current significance statement concerns judge-family dependence as a property of the measurement. | Discussion 5.5 | Withdrawn |
| 173 | Limitations read like a bulleted list | Limitations | Rewrote as five explanatory paragraphs: automated judges (what they cannot show, within-panel agreement, uneven coverage); FEVER scope (binary sample, designated evidence, one model family); mechanism; post hoc correction and the combination of retained A/B with new C judgments; the amendment. All disclosures kept; no operational log detail. | Limitations | Addressed |

## Tracked insertions and deletions

These were applied where the passage survives, including:
- "recipe" → "method";
- the regression wording "classified correctly without evidence … incorrectly after";
- "Evidence helps … but it also";
- "Simply counting …" (now "Counting regressions cannot distinguish these situations");
- "The study yields two findings";
- removal of "restated in Section 3.1";
- "makes" in the present tense;
- "relevant information";
- "This study seeks to answer four questions";
- "The takeaway from these findings is not that gold evidence fails. It succeeds on average …";
- "This is consistent with prior work showing …";
- "This finding is expected …";
- removal of "not a defect to be explained away";
- "otherwise regressions remain invisible";
- "but still induces" (Conclusion).

These edits were not adopted verbatim because they are inaccurate for the current methods:

| Jessica's wording | Problem | Wording used instead |
|---|---|---|
| "regressions are not consistent across the two GPT models" | 40 of the 226 claims regress for both models, so the regressions are partly shared | "only 40 of the 226 claims regress for both models" |
| "silver instruments applied to the same blinded packets as those we presented to GPT-5.4 and GPT-5.4-mini" | Only the Stage A input equals the GPT evidence prompt; Stages B and C add context | Stage A is described as "exactly as GPT received them" |
| "Agreement between the judge and evaluator models" | The agreement is between the two judge families | "Where the two panels agree" |
| "If designated evidence still produces regressions, this demonstrates … not due to failed retrieval" | Overstated | Within-experiment wording from author answer 4 |
| "stored accuracy labels only" | GPT runs stored predicted labels | "predicted labels" |
| Edits inside withdrawn passages (legacy residual-ambiguity category, "second most frequent category", three-way shares) | The passages are withdrawn | Not carried into the current text |
| "claim-evidence" with a hyphen | Typography only | LaTeX en dash (`--`) kept, by convention |

## Citation-to-claim verification

Each claim was checked against the source's published abstract on ACL Anthology, NeurIPS or PMLR.

| Citation | Claim in current draft | Result |
|---|---|---|
| Thorne et al. 2018a (FEVER) | 185,445 Wikipedia-derived claims; Supported/Refuted/NotEnoughInfo; evidence recorded for the first two classes | Verified |
| Thorne et al. 2018b (shared task) | First FEVER shared task; retrieve Wikipedia evidence and classify claims; best FEVER score 64.21% | Verified |
| Guo et al. 2022 (survey) | Claim detection, evidence retrieval, and claim verification (verdict prediction and, where applicable, justification production) | Resolved: opening sentence revised by the authors to match the survey's framework (2026-09-28) |
| Wadden et al. 2020 (SciFact) | Expert-written scientific claims; abstracts that support or refute | Verified |
| Schuster et al. 2021 (VitaminC) | Contrastive pairs from Wikipedia revisions; nearly identical evidence supports or does not | Verified |
| Jiang et al. 2020 (HoVer) | Evidence from up to four Wikipedia articles | Verified |
| Aly et al. 2021 (FEVEROUS) | Evidence as sentences and/or table cells | Verified |
| Schuster et al. 2019 | Claim-only classifiers competitive on FEVER via claim cues | Verified |
| Longpre et al. 2021 | Question answering; reliance on memorized knowledge when the passage contradicts it | Verified (now scoped to question answering) |
| Liu et al. 2024 | Use of relevant information depends on its position in long contexts | Verified after narrowing ("how it is written" removed) |
| Shi et al. 2023 | Irrelevant context distracts reasoning | Verified |
| Wan et al. 2024 | Relevance weighed heavily; stylistic features humans value largely ignored | Verified (made precise) |
| Mamta & Cocarascu 2025 | LLM fact verification on FEVER brittle under small perturbations | Verified |
| Atanasova et al. 2022 | Models often fail to recognize insufficiency after evidence omission | Verified |
| Glockner et al. 2024 (AmbiFC) | Conflicting but valid interpretations; argue against single labels | Verified |
| Zheng et al. 2023 | Position, verbosity, self-enhancement biases | Verified ("self-preference" renamed to match) |
| Liu et al. 2023 (G-Eval) | Potential bias of LLM evaluators toward LLM-generated text | Verified |
| Chen et al. 2024 | Misinformation-oversight, gender, authority and beauty biases in human and LLM judges | Verified after correction (it was previously cited for position/verbosity, which it does not study) |
| Shi et al. 2025 | Position bias varies across judges and tasks | Verified |
| Huang et al. 2025 | Fine-tuned judges are not a general substitute for GPT-4 | Verified after narrowing (previously "not interchangeable substitutes for one another") |

No citation was added.
Comment 170's "cite" refers to a withdrawn passage.

## Author queries

- **AQ1 (resolved 2026-09-28):** The Guo et al. 2022 decomposition was checked against the survey's framework. The opening sentence of Related Work 2.1 now reads: "Automated fact-checking is commonly organized into claim detection, evidence retrieval, and claim verification; the last stage includes verdict prediction and, where applicable, justification production." The following sentence now names evidence retrieval and verdict prediction explicitly as the stages FEVER measures, since FEVER does not cover justification production.

No author queries remain open.
