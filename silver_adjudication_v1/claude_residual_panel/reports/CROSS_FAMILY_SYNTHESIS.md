# Cross-family residual synthesis

> This is the residual-conditioned cross-family comparison (n = 231). It is
> **not** the study-level final synthesis. That file is
> [`../../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md`](../../claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md).

Question: among the 231 Cursor/Grok Stage C residual Ambiguous/Unresolved
items, how often does an independent Claude Opus panel also find Stage C
evidence insufficient for a decisive Supported/Refuted verdict?

## What was compared

- Frozen Cursor/Grok Stage C consensus (`cursor-grok-4.6-high-fast`).
- Frozen Claude raw five-judge consensus (`claude-opus-5-thinking-high`).
- Comparison only after both judgment freezes and the Claude
  pre-unblinding manifest.

Claude judges did not see Grok verdicts, GLM outputs, or that the items
were selected as residuals.

## Result

- Persistent cross-family ambiguity: **58.0%** (134/231; CI 51.5–64.1).
- Claude-resolved Grok residuals (high-consensus decisive): **42.0%** (97/231).
- Claude-internal disagreement at the consensus-taxonomy level: **0**.
- Exact consensus-label agreement: **56.3%**. Cursor labels on this set
  are only Ambiguous/Unresolved, so agreement is mostly shared Ambiguous
  labels, not shared decisive warrants.

## FEVER after unblinding

Of the 97 Claude-decisive items, **62/97** (63.9%) match FEVER gold and
**35/97** do not. Claude Supported tracks FEVER Supported more closely
(33 agree / 5 Claude-Refuted) than Claude Supported vs FEVER Refuted
(30 Claude-Supported / 29 Claude-Refuted). FEVER disagreement is not a
license to relabel the benchmark.

## Subgroup pattern

Shared GPT regressions in the residual set remain the most persistent
(75.0% of 24). Residual regressions as a whole persist more often than
residual resistant items (68.6% vs 53.6%; OR 1.89). Control residuals
are few (24 rescue, 9 robust) and too small for a strong claim.

## Reading

The Grok residual is **not** purely family-specific conservatism, and it
is **not** purely intrinsic warrant ambiguity. It is a mixture: most of
the residual still looks underdetermined to a second generative family,
while a large high-consensus slice does not. That mixture is the
residual-panel cross-family result.
