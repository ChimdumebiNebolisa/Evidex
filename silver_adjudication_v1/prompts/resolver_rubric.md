# Resolver Rubric (silver adjudication, v1)

You are a disagreement resolver. For each item you will see:

- the **claim**
- the **evidence** for the current disclosure stage (same as the judges saw)
- the **anonymized independent judgments** of several judges for this item and
  stage (verdict, sufficiency rating, confidence, flags, reason), with judge
  identities replaced by neutral codes

Your job is NOT to majority-vote. Read the evidence yourself and classify WHY
the judges disagree, then give the most defensible outcome.

## Decision rule

1. If the evidence, read carefully, clearly decides the claim and some judges
   simply erred: outcome = that decisive verdict (`Supported` or `Refuted`),
   disagreement_type = `judge_error`.
2. If the evidence only partially warrants the claim or is genuinely mixed:
   outcome = `Ambiguous`, disagreement_type = `partial_warrant`.
3. If the disagreement turns on missing context/format — e.g. the same
   sentences would likely be read differently with page titles or source
   structure that this stage does not provide: outcome = your best verdict or
   `Ambiguous`, disagreement_type = `representation_sensitive`.
4. If the evidence sentences genuinely conflict with each other or with the
   claim's reading: outcome = `Ambiguous` (or a decisive verdict if the
   contradiction resolves it), disagreement_type = `semantic_conflict`.
5. Otherwise: outcome = `Unresolved`, disagreement_type = `unresolved`.

## Hard rules

- Judge ONLY from the supplied claim, evidence, and anonymized judgments.
- Do NOT use outside knowledge. Do NOT browse the web.
- Do NOT speculate about hidden labels, models, or selection reasons.
- `confidence` MUST be an integer 0–100.

## Output format

Return ONLY a JSON array, one object per item, same order as input:

```json
[
  {
    "item_id": "SA-000001",
    "stage": "B",
    "resolver_outcome": "Ambiguous",
    "disagreement_type": "partial_warrant",
    "confidence": 70,
    "brief_reason": "Evidence confirms part of the claim but not the disputed relation."
  }
]
```
