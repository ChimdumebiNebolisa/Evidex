# Study-level limitations

Layer-specific lists remain authoritative. This page only states limits that apply to the manuscript as a whole.

## Silver, not human

Cursor/Grok, GLM, and Claude judgments are model-based. Agreement across families is cross-family silver validation. It is not expert human adjudication and does not create a new gold standard.

## FEVER is not on trial

NLI disagreement and judge–FEVER disagreement mark candidate ambiguity. They do not prove a FEVER label is wrong.

## No window into GPT internals

The 40,000 GPT rows are labels only. Progressive disclosure describes how a *judge panel* changes as evidence representation changes. It does not observe why a GPT model flipped.

## Benchmark scope

Binary Supported/Refuted FEVER, 2017-era Wikipedia claims, designated gold evidence (not a retrieved open-web context). `NOT ENOUGH INFO` is excluded by design.

## Shared GPT family

Both experiment models are GPT-5.4 variants. Transition concordance can reflect family-correlated errors.

## Judge-family-sensitive proportions

The mixed-mechanism *ordering* (utilization largest, representation smallest, residual in between) appears in both complete A→B→C panels. The exact split (Grok 50.0/11.9/38.1 vs Claude 65.9/5.3/28.8) is not judge-independent. Do not quote one panel’s percentages as if they were the unique decomposition.

## Supporting experiments are conditioned

- GLM: Stage A only. Later GLM stages are incomplete and unused in A→B→C math.
- Claude residual: 231 items selected as Grok Stage C leftovers, not a random 226 or a re-run of the 1,060-item panel.

## Layer-specific documents

- [`analysis_v2/reports/LIMITATIONS.md`](../analysis_v2/reports/LIMITATIONS.md)
- [`silver_adjudication_v1/cursor_panel/reports/LIMITATIONS.md`](../silver_adjudication_v1/cursor_panel/reports/LIMITATIONS.md)
- [`silver_adjudication_v1/claude_residual_panel/reports/LIMITATIONS.md`](../silver_adjudication_v1/claude_residual_panel/reports/LIMITATIONS.md)
- [`silver_adjudication_v1/claude_full_regression_panel/reports/LIMITATIONS.md`](../silver_adjudication_v1/claude_full_regression_panel/reports/LIMITATIONS.md)
