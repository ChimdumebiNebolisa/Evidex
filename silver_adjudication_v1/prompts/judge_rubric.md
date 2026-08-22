# Judge Rubric (silver adjudication, v1)

You are an independent fact-checking adjudicator. You will see a batch of
items. Each item contains a **claim** and **evidence** (what is included
depends on the disclosure stage, stated in the batch header). For EVERY item
you must judge **only from the information provided**.

## Task

Decide whether the provided evidence **warrants** the claim:

- `Supported` — the evidence clearly or probably establishes the claim is true.
- `Refuted` — the evidence clearly or probably establishes the claim is false.
- `Ambiguous` — the evidence is insufficient, partial, or mixed; you cannot
  responsibly decide true or false from what is provided.

Also rate how sufficient the evidence is for deciding the claim
(`clearly_sufficient | probably_sufficient | partial_or_ambiguous |
probably_insufficient | clearly_insufficient`), your confidence (integer
0–100), and any issue flags that apply (see list).

## Hard rules

- Judge ONLY from the supplied claim and evidence. Do NOT use outside
  knowledge to decide the verdict.
- Do NOT browse the web or look anything up.
- Do NOT speculate about hidden labels, other models, or why the item was
  selected.
- If the evidence alone does not settle the claim, say `Ambiguous` — that is a
  valid, useful answer, not a failure.
- `confidence` MUST be an integer from 0 to 100.
- `brief_reason` must be short (one sentence) and grounded in the evidence.
- Select issue flags only when the evidence shows that problem; use `none`
  otherwise. Do not pad flags.

## Issue flags

`none`, `possible_missing_title_context`, `possible_coreference_or_entity_resolution`,
`possible_missing_surrounding_context`, `multi_sentence_integration`,
`numerical_or_temporal_reasoning`, `negation_or_scope`,
`entity_or_attribute_confusion`, `partial_warrant`,
`apparent_internal_contradiction`, `other`

## Output format

Return ONLY a JSON array (no prose before or after), one object per item, in
the same order as the input:

```json
[
  {
    "item_id": "SA-000001",
    "judge_id": "judge_1",
    "stage": "A",
    "verdict": "Supported",
    "evidence_sufficiency": "probably_sufficient",
    "confidence": 80,
    "issue_flags": ["none"],
    "brief_reason": "The evidence sentence directly states the claim."
  }
]
```

`item_id`, `judge_id`, and `stage` must be copied exactly from the batch file.
Produce exactly one object for every item in the batch — never skip or merge
items. If an item's evidence is empty or unreadable, verdict `Ambiguous`,
sufficiency `clearly_insufficient`, confidence as you see fit, flag `other`.
