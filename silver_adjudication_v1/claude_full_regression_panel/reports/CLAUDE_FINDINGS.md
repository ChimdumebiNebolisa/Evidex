# Claude full-regression panel — findings

Independent Claude A→B→C adjudication of all **226 unique** GPT regression
claims. Every judgment was produced under blinding and frozen before any join
to regression, GPT, FEVER or Grok metadata.

These are model-based silver judgments. They are not human validation and do
not establish ground truth.

## Panel

- Cohort: 226 regressions (claim correct without evidence, incorrect with the
  designated FEVER evidence), union across both GPT models.
- Judges: **five isolated judges**, fresh subagent per `(judge, batch, stage)`.
- Model: `claude-opus-5-thinking-high` for all judgments, no substitution.
- Judgments: **1,130** per stage, **3,390** total, 0 missing, 0 malformed.
- All three stage freezes plus the pre-unblinding manifest verified unchanged.

## Stage results (Claude consensus)

| Stage | Supported | Refuted | Ambiguous | Unresolved |
|---|---|---|---|---|
| A (sentence-level) | 60 | 100 | 66 | 0 |
| B (adds titles) | 60 | 102 | 63 | 1 |
| C (structured evidence) | 62 | 99 | 62 | 3 |

Counting Ambiguous and Unresolved together as non-decisive:

- Stage A non-decisive: **29.2%**
- Stage B non-decisive: **28.3%**
- Stage C non-decisive: **28.8%**
- Stage C high-consensus rate: **71.2%**

The panel is internally consistent. Pairwise agreement is 93.4% / 93.8% / 92.6%
across stages A/B/C, Fleiss' kappa 0.897 / 0.904 / 0.884, mean confidence
72.4 / 72.5 / 71.8. No judge is an outlier: per-judge Ambiguous rates span
22.1–30.1% at Stage A and 23.0–27.4% at Stage C.

## Stage transitions

Progressive disclosure moves relatively few cases:

- resolved by titles (A ambiguous → B decisive): 3.98%
- resolved only by structured evidence: 3.10%
- still non-decisive after Stage C: 28.76%
- decisive verdict reversals after titles: 0.00%
- decisive verdict reversals after structured evidence: 0.00%
- consensus label changes A→B: 7.08%; B→C: 7.08%

Adding titles and structure therefore resolves some ambiguity but never flips a
Claude consensus from Supported to Refuted or vice versa.

## Claude mechanism decomposition

Applied by the shared Evidex taxonomy rules, unchanged, after unblinding:

| Mechanism | Fine category | n | % | 95% CI |
|---|---|---|---|---|
| Evidence-utilization failure | `silver_clear_evidence_utilization_failure` | 149 | 65.9% | 59.5–71.8 |
| Representation-sensitive | `silver_structured_evidence_sensitive` | 12 | 5.3% | 3.1–9.1 |
| Representation-sensitive | `silver_title_context_sensitive` | 0 | 0.0% | 0.0–1.7 |
| Residual ambiguity | `silver_partial_or_ambiguous_warrant` | 65 | 28.8% | 23.3–35.0 |
| Other | `silver_unresolved` | 0 | 0.0% | 0.0–1.7 |

Claude's decomposition is mixed: a clear majority of regressions look like
evidence-utilization failures, a substantial minority are residual ambiguity,
and representation-sensitivity is a small but non-zero category.

## By regression type

| Subgroup | n | utilization failure | representation-sensitive | residual ambiguity |
|---|---|---|---|---|
| Shared by both GPT models | 40 | 47.5% | 5.0% | 47.5% |
| One GPT model only | 186 | 69.9% | 5.4% | 24.7% |
| `gpt-5.4` only | 75 | 65.3% | 6.7% | 28.0% |
| `gpt-5.4-mini` only | 111 | 73.0% | 4.5% | 22.5% |

Regressions shared by both GPT models are markedly more likely to remain
non-decisive for Claude after Stage C than model-specific ones (47.5% vs 24.7%;
OR 2.75, 95% CI 1.36–5.57, p = 0.0065). This is consistent with shared
regressions being disproportionately genuinely hard or under-warranted items
rather than model-specific failures, but it is an exploratory association on
226 items and is not corrected for multiple comparisons.

## Artifacts

Per-stage consensus and agreement tables, the taxonomy assignment per item, the
confusion matrices and the statistical tests are under `tables/`. Frozen
judgments are under `judgments/`, freeze manifests under `freezes/`.
