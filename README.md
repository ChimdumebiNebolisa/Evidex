# Evidex

Evidex asks when designated gold evidence helps or harms LLM fact-checking, and what mechanisms explain cases where a model is correct without evidence and wrong after receiving it.

The experiments are finished. This repository is the research record: a 10,000-claim paired GPT study, a secondary analysis of those 40,000 predictions, and blinded silver adjudication under progressive disclosure. All adjudication is automated. It is not human annotation and does not relabel FEVER gold.

The scientific record underlying the manuscript is frozen at tag `evidex-artifact-v1`.

## Manuscript

**Current manuscript draft:**
[`paper/evidex-manuscript-draft.pdf`](paper/evidex-manuscript-draft.pdf)

**LaTeX sources:**
[`paper/`](paper/)

First manuscript draft for internal/coauthor review. Not a submitted version.

## How to read this study

The primary adjudication panel used the locked Grok model executed through Cursor; the README refers to this simply as the Grok panel.

1. **Primary behavioral experiment.** 10,000 balanced FEVER Supported/Refuted claims; GPT-5.4 and GPT-5.4-mini; no-evidence vs gold-evidence; 40,000 predictions.
2. **Primary analysis (`analysis_v2`).** Paired transitions, statistics, features, two local NLI diagnostics, leakage checks, verification.
3. **Primary mechanism study.** Grok five-judge A→B→C progressive-disclosure panel on the diagnostic cohort. This is the initial failure-mode decomposition.
4. **Supporting robustness.** GLM-5.3 Stage A replication. Purpose: test whether the early ambiguity pattern is Grok-family-specific.
5. **Intermediate cross-family robustness.** Claude residual Stage C on 231 Grok leftover items. Purpose: test whether Grok's final residual ambiguity persists under another family.
6. **Main cross-family replication.** Claude five-judge A→B→C on all 226 unique regressions (3,390 judgments). Purpose: test whether the entire failure-mode decomposition generalizes across judge families.
7. **Final synthesis.** Both Grok and Claude independently recover all three broad failure categories in the same rank order, but exact prevalence differs by judge family.

Layers 4 and 5 are supporting robustness checks. They do not receive equal billing with the two complete A→B→C panels.

The map below is the research logic, not a file tree. Dashed edges are supporting checks.

```mermaid
flowchart TD
    A["10,000 FEVER claims<br/>GPT-5.4 + GPT-5.4-mini<br/>No evidence vs gold evidence<br/>40,000 predictions"]

    B["226 unique evidence-induced regressions"]

    C["Grok primary A→B→C panel<br/>Progressive disclosure<br/>sentences → +titles → +structure"]

    D["Initial failure-mode decomposition<br/>50.0% utilization failure<br/>11.9% representation-sensitive<br/>38.1% residual ambiguity"]

    E["GLM-5.3 Stage A replication<br/>Test whether early ambiguity<br/>is specific to the Grok family"]

    F["Claude residual Stage C<br/>231 Grok residual items<br/>Test whether residual ambiguity<br/>persists across judge families"]

    G["Full Claude A→B→C replication<br/>all 226 regressions<br/>3,390 judgments<br/>Test whether the complete<br/>failure-mode picture generalizes"]

    H["Cross-family synthesis<br/>Same qualitative ordering<br/>Different exact prevalence<br/>74.3% agreement · κ = 0.537"]

    A --> B
    B --> C
    C --> D

    C -.-> E
    D -.-> F

    B --> G

    D --> H
    G --> H
```

## Key findings

Denominators are not interchangeable. Claude residual Stage C and Claude full A→B→C answer different questions.

| Finding | Result | Denominator |
|---|---|---|
| GPT-5.4 evidence gain | 88.69% → 96.04% (**+7.35 pp**) | 10,000 claims |
| GPT-5.4-mini evidence gain | 84.67% → 95.54% (**+10.87 pp**) | 10,000 claims |
| Unique regressions | **226** claims (40 both models, 186 exactly one) | claims, not model-observations |
| Grok mechanism split | **50.0%** utilization · **11.9%** representation-sensitive · **38.1%** residual ambiguity | 226 regressions |
| Claude full-panel mechanism split | **65.9%** utilization · **5.3%** representation-sensitive · **28.8%** residual ambiguity | same 226 regressions |
| Cross-family taxonomy agreement | **74.3%** exact and broad (κ = 0.537) | 226 paired assignments |
| GLM Stage A replication | modal verdict agreement **0.862** | 1,060 judged items |
| Claude residual split | **58.0%** persistent (134/231) · **42.0%** Claude-resolved Grok residuals (97/231) | 231 Stage C leftovers; supporting |

```mermaid
flowchart LR
    subgraph Grok["Grok, 226 regressions"]
        g1["utilization 50.0%"]
        g2["representation 11.9%"]
        g3["residual 38.1%"]
    end
    subgraph Claude["Claude A→B→C, 226 regressions"]
        c1["utilization 65.9%"]
        c2["representation 5.3%"]
        c3["residual 28.8%"]
    end
    Grok ---|agreement 74.3%| Claude
```

Both families independently find all three mechanisms, in the same rank order. Claude assigns more cases to evidence-utilization failure. That is a judge-family difference, not a confirmation that either split is human ground truth. Automated cross-family agreement does not establish human ground truth. Disagreement with FEVER does not establish FEVER annotation error.

Canonical write-up: [`CROSS_FAMILY_SYNTHESIS.md`](silver_adjudication_v1/claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md). Principal figure: [`fig1_mechanism_by_family.png`](silver_adjudication_v1/claude_full_regression_panel/figures/fig1_mechanism_by_family.png).

## Canonical reports

| Layer | Report |
|---|---|
| Analysis v2 | [`FINDINGS.md`](analysis_v2/reports/FINDINGS.md) · [`METHODS.md`](analysis_v2/reports/METHODS.md) |
| Grok A→B→C | [`SILVER_FINDINGS.md`](silver_adjudication_v1/cursor_panel/reports/SILVER_FINDINGS.md) |
| Claude full A→B→C | [`CLAUDE_FINDINGS.md`](silver_adjudication_v1/claude_full_regression_panel/reports/CLAUDE_FINDINGS.md) |
| Final synthesis | [`CROSS_FAMILY_SYNTHESIS.md`](silver_adjudication_v1/claude_full_regression_panel/reports/CROSS_FAMILY_SYNTHESIS.md) |

Supporting reports (do not treat as the final mechanism paper):

| Layer | Report |
|---|---|
| GLM Stage A | [`CROSS_PANEL_STAGE_A_REPLICATION.md`](silver_adjudication_v1/cursor_panel/reports/CROSS_PANEL_STAGE_A_REPLICATION.md) |
| Claude residual Stage C | [`CLAUDE_FINDINGS.md`](silver_adjudication_v1/claude_residual_panel/reports/CLAUDE_FINDINGS.md) |
| Intermediate residual synthesis | [`FINAL_EVIDEX_STRENGTHENING.md`](silver_adjudication_v1/claude_residual_panel/reports/FINAL_EVIDEX_STRENGTHENING.md) |

Study-level docs: [`REPRODUCING.md`](REPRODUCING.md) · [`docs/STUDY_OVERVIEW.md`](docs/STUDY_OVERVIEW.md) · [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md) · [`docs/ADJUDICATION_PROTOCOL.md`](docs/ADJUDICATION_PROTOCOL.md) · [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

An earlier 1,000-claim run and the `*_pilot` files at the repository root are historical. They are not the manuscript experiment.

## Reproduce headline numbers

Committed summaries, tables, freezes, and reports are enough to verify the paper. No model API is required.

```powershell
python -m pip install pandas numpy scipy statsmodels pyarrow
python analysis_v2/src/verify_headlines.py
python silver_adjudication_v1/src/verify_headlines.py --panel cursor
python silver_adjudication_v1/src/verify_glm_stage_a.py
python silver_adjudication_v1/claude_residual_panel/src/verify_headlines.py
python silver_adjudication_v1/claude_full_regression_panel/src/verify_headlines.py
```

The Grok-panel verifier command **requires** `--panel cursor`. That flag names the frozen `cursor_panel` namespace, not the judge family. Without it the shared verifier defaults to the incomplete GLM namespace.

`verify_glm_stage_a.py` recomputes the GLM–Grok Stage A comparison from frozen judgments (1,060 items; modal agreement 0.862; consensus agreement 0.831) and does not write files.

Or: `python scripts/verify_all_headlines.py` — reads the research record and exits pass/fail. It does not mutate anything.

Level 2 analysis reproduction and optional Level 3 model inference are in [`REPRODUCING.md`](REPRODUCING.md). Re-running GPT or judges is not required and will not reproduce the frozen record bit-for-bit.

## Limitations

- **Automated judges, not humans.** Grok, GLM, and Claude panels are model-based silver labels. Cross-family replication reduces the risk that findings reflect one judge family. It is not a substitute for expert human adjudication.
- **FEVER remains the gold standard.** NLI disagreement and model-judge disagreement flag candidate ambiguity. They do not establish that a FEVER label is incorrect.
- **No causal claim about GPT internals.** Progressive disclosure locates where a judge panel's warrant changes. Original GPT runs recorded labels only.
- **Binary, 2017-era FEVER.** The design excludes NOT ENOUGH INFO and is Wikipedia-based and entity-centric.
- **Proportions are judge-family-sensitive.** The mixed-mechanism *picture* is robust; the 50.0% vs 65.9% utilization split is not a single universal constant.

Fuller lists: [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## License and third-party data

Project **code** is under the MIT License ([`LICENSE`](LICENSE)). That license does **not** relicense FEVER, Wikipedia text, or other third-party material committed as data. See [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md) before redistributing data files.

## Citation

See [`CITATION.cff`](CITATION.cff).
