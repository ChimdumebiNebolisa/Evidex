# Exploratory claim/evidence codebook, version 1

Developed after observing the completed experiment. Basis: the 30-case pilot in PILOT_NOTES.md/PILOT_SAMPLE.csv. Definitions were fixed before reading/coding the remaining 386 selected claims. This is an exploratory case study codebook, not a preregistered causal model or a validated instrument. AI-assisted single-analyst coding is unblinded to model, contrast, reference and predictions. No human validation, independent coding or agreement statistic is claimed.

## Units and overlap

The reusable feature unit is a **claim and its complete supplied evidence**, keyed by claim ID. Read all supplied text, not just a matching phrase. Each of the 465 selected model–claim–contrast cases inherits that claim's feature codes, then receives a case-specific prediction/outcome interpretation. One claim can occur across models, contrasts and selection routes; preserve those flags without pretending the observations are independent claims.

Use multiple labels when different visible features apply. Codes describe what the task contains, regardless of whether a model succeeded. Do not assign a code merely because an error occurred. Do not code boilerplate dates, names, brackets or pronouns unless they matter to the claim/evidence relation. A fallback DIRECT cannot accompany another substantive feature code. UNCLEAR is for an unresolved feature account; it is not a missing annotation. Overlapping label percentages need not sum to 100%.

## Feature axis

| Code | Definition and inclusion | Exclusions/boundary | Pilot example | Establishes / does not establish |
|---|---|---|---|---|
| NEG | Explicit denial, absence, negative prefix or restriction whose polarity matters: not, never, no, uninvolved; fiction/non-fiction when it flips the category. | An antonym that changes the event role without explicit denial can be REL instead. Do not infer hidden negation processing. | 129011: “uninvolved” versus an explicit album–artist relation; 75904: “does not” versus >80%. | Visible polarity contrast; no evidence of a negation-processing mechanism. |
| SCOPE | Quantifier, exclusivity, scalar degree or universality changes the proposition: only, all, almost, barely, definitive/superlative wording. | A simple exact count/date belongs to NUM. Qualifiers that do not affect the comparison are not sufficient. | 88865 “barely”; 52907 “almost annual”; 57522 “only.” | A scope/degree distinction exists; it may also appear in successes and need not cause errors. |
| REL | Relation, semantic role, direction, agent/patient, authorship, participation, kinship or temporal ordering is the discriminating feature. | A different filler in the same unchanged role is ENT; numbers are NUM. Can overlap when both role and filler matter. | 165882 written/portrayed; 193883 renamed/birth name; 56381 uncle/parent. | What relation must be compared; not proof of role-binding failure inside a model. |
| ENT | Same attribute/role with a different person, country, place, work or other categorical filler, including nationality or attribution. | Do not tag every named entity. Type/granularity equivalence without a changed referent is LEX. | 86175 Russian/American; 57522 Ron Howard/Olivier Megaton; 154761 Isabella/Columbus. | Observable entity/attribute mismatch or match; not memory retrieval evidence. |
| NUM | Truth depends on an exact count, rank, date, duration, ordinal, temporal comparison, percentage or calendar calculation. | A background year unrelated to the claim is excluded. A first-on-label claim may also be GAP if the supplied chronology does not settle it. | 218245 13th/16th; 4100 1930s/1960s; 85350 weekday/date. | A precision/comparison demand; not automatic evidence of numerical reasoning failure. |
| LEX | Plausible paraphrase, type hierarchy, genre distinction, semantic granularity or ambiguous ordinary meaning affects entailment. | Do not tag a straightforward repeated word or every ordinary fact. ENT/REL should identify concrete substitutions rather than broad semantic wording. | 152008 myths/legends; 164996 marine mammals/mammals; 29256 serial/anthology series. | A semantic reading/generalization is needed; it can explain neither direction nor mechanism by itself. |
| CTX | Missing/implicit antecedent, generic-title sense, decontextualized sentence, cross-sentence entity linkage or multiple possible referents requires contextual binding. | A proper name alone is insufficient. Do not use unseen Wikipedia context as if it was in the executed prompt. | 89458 evidence “It”; 86175 album–artist–nationality bridge; 94603 “she.” | Context must be supplied or resolved; not proof the provided evidence is unusable. |
| GAP | The supplied evidence does not directly settle a material clause, event, exclusivity or attribute; interpretation needs a bridge, external fact, stronger entailment rule or omitted contextual fact. | Not a statement that the full FEVER evidence archive is wrong. Do not confuse absence of support with contradiction; codes never change scores. | 152752 first album on label; 88941 definitive status; 174893 demolition absent from location evidence. | Selected evidence is insufficient/indirect for the relevant proposition; not proof the reference or prediction is false. |
| TXT | Awkward, malformed, fragmented or extraction-marked wording creates a material ambiguity beyond the substantive proposition. | Do not code ordinary punctuation, every -LRB- token, or benign article omissions. | 88865 “from 972 and 992”; 172753 “made for film” when its meaning is unresolved. | Observable wording limitation; not a model-specific cause. |
| DIRECT | Straightforward local factual match or mismatch with no other distinctive feature under this codebook. Fallback only. | Never use to assert indisputable correctness or to conceal uncertainty. If another feature applies, omit DIRECT. | 179302: United States explicitly included among countries regulating franchising. | A useful ordinary comparison case; not a mechanistic explanation. |
| UNCLEAR | After full reading, no defensible feature account can be assigned or competing readings prevent confident coding. Record the competing readings. | Not a synonym for a wrong prediction, an unreviewed record or missing evidence. Can accompany a tentative substantive code if uncertainty is explained. | 150693 person/goddess readings may warrant LEX plus uncertainty; residual cases can use UNCLEAR alone. | Limits of this coding; no inferred model process. |

## Evidence/reference alignment axis (separate from model predictions)

Assign exactly one assessment. This is an apparent relation on the supplied text, not human adjudication of the underlying world.

| Assessment | Inclusion | Boundary and example |
|---|---|---|
| supports_gold | The ordinary relevant reading of the supplied text supports the frozen Supported label or explicitly contradicts the claim for a Refuted label. | 218245: evidence's 16th rank contradicts claim's 13th. Do not call a missing fact an explicit contradiction. |
| conflicts_gold | An explicit discriminating fact or transparent deterministic calculation supports the opposite benchmark decision. Record the fact/calculation. | 4100: claim 1930s, evidence 1960s, frozen Supported; 154761: Isabella versus Columbus, frozen Supported. 85350: datetime.date(1964,8,14).strftime('%A') is Friday, not Monday. These remain apparent reference tensions requiring human source review, not silently corrected gold. |
| insufficient | A material element needed to justify the benchmark decision is absent and no decisive explicit contradiction is supplied. | 174893: location is given; demolition is not. This does not prove the benchmark label wrong. |
| ambiguous | Competing reasonable semantic or contextual readings yield different support judgments; identify the ambiguity. | 88865 “barely”; 29256 serial/anthology; 172753 “made for film” versus adapted. Do not select the reading that best matches a model's output. |

## Case-specific interpretation axis

Always retain frozen benchmark outcomes. For each case, show all three A/B/C predictions and every matched outcome. If reference alignment is supports_gold, disagreement with the reference is an **apparent prediction error supported by supplied-text review**. If conflicts_gold, call it a **benchmark-defined error with apparent reference tension**. If insufficient or ambiguous, call it **benchmark-defined error with unresolved evidence/interpretation**. A rescue is a benchmark rescue even if text review raises the same reference concern. This axis is generated from the explicit alignment judgment and predictions, not an unseen rationale.

## Uncertainty and review status

Record feature/assessment justification with a specific claim/evidence distinction; quote only short relevant phrases while retaining complete text in the case file. Use high/moderate/low confidence in the annotation, not confidence in the model's latent mechanism. All records remain `AI-coded_unblinded; human_review_not_performed`. Flag conflicts, insufficiency, ambiguity and low confidence for human review. “No human review” is a disclosure, not an agreement statistic.

## Application and frozen definitions

1. Freeze this file's SHA256 in CODEBOOK_FREEZE.json.
2. Re-read and recode the 30 pilot claims under these final definitions; retain PILOT_NOTES.md as the earlier provisional record.
3. Apply unchanged definitions to all remaining selected claims. Use UNCLEAR rather than inventing a post hoc category. Any later proposed code must be listed as future work, not silently added.
4. Reuse the same claim-level codes across models/contrasts, retain case-level outcome distinctions, and compare selected regression groups with the sampled rescue/stayed-wrong/stayed-correct groups.
5. Report denominators for selected cases and distinct claims. Do not present selected category proportions as full-dataset prevalence, causal attribution, generalization to deployed retrieval, or permanent individual failure.
