# Claude full-regression A→B→C panel

Cross-family replication of the complete Evidex progressive-disclosure
adjudication on **all 226 unique GPT regressions**, using a different judge
family from the Cursor/Grok panel that produced the original mechanism
decomposition.

- Model lock: `claude-opus-5-thinking-high` for all five judges, all stages
- Cohort: 226 unique regressions (`correct_to_wrong`, union of `gpt-5.4` and
  `gpt-5.4-mini`), independently recounted from `analysis_v2`
- Stages: A (sentences) → B (+page titles) → C (+reconstructed structured
  FEVER evidence), each frozen before the next is built
- Expected totals: 226 items × 5 judges × 3 stages = **3,390 judgments**
- Rubric, verdict vocabulary, consensus rules, and taxonomy rules are the
  existing Evidex ones, reused unchanged
- This is **cross-family silver validation, not human ground truth**

The earlier 231-item Claude residual panel is a separate, frozen experiment.
None of its judgments are spliced into this one.

## Result

Complete: 3,390/3,390 judgments, all three stages frozen and verified before
unblinding. Applying the unchanged Evidex taxonomy to Claude's own consensus:

| Mechanism | Grok | Claude |
|---|---|---|
| evidence-utilization failure | 113 (50.0%) | 149 (65.9%) |
| representation-sensitive | 27 (11.9%) | 12 (5.3%) |
| residual ambiguity | 86 (38.1%) | 65 (28.8%) |

The mixed-mechanism picture replicates qualitatively — all three mechanisms are
present in both families, in the same rank order — but the proportions shift by
up to 16 pp, and the two families disagree on the mechanism for about one
regression in four (74.3% agreement, κ = 0.54). Read the specific percentages as
judge-family-dependent.

- `reports/CLAUDE_FINDINGS.md` — Claude's own A/B/C results and decomposition
- `reports/CROSS_FAMILY_SYNTHESIS.md` — Grok-vs-Claude comparison and the
  conclusions sorted by how well they survive the family swap
- `reports/ADJUDICATION_LOG.md` — execution record and protocol deviations
- `reports/LIMITATIONS.md`, `reports/METHODS.md`, `figures/`

## Layout

- `config.json` — model lock (do not change mid-run)
- `src/` — cohort derivation/blinding, judge orchestration, consensus,
  taxonomy + Grok comparison, headline verification
- `data/` — blinded stage files and the private `CF-* → SA-* → claim_id` map
- `judgments/stage_{a,b,c}/` — ingested raw judge outputs (append-only)
- `freezes/` — per-stage freezes, consensus, pre-unblinding manifest
- `tables/`, `reports/`, `cache/`, `tests/`

Judge-facing packets, launch prompts, and the raw output inbox live in
`../blind_io/`, which is deliberately named so that no path a judge sees can
reveal how the cohort was selected.

## Reproduce

```bash
cd silver_adjudication_v1/claude_full_regression_panel
python src/derive_and_blind.py all          # 226-item cohort + blinded stages
python src/run_judges.py packets A          # then run one subagent per packet
python src/launch_prompts.py A              # exact wrapper prompt per packet
python src/run_judges.py ingest A
python src/run_judges.py freeze A           # repeat for B, then C
python src/consensus_agreement.py all
python src/analyze.py freeze
python src/analyze.py unblind
python src/analyze.py compare
python src/analyze.py stats
python src/verify_headlines.py
python -m unittest discover -s tests
```

Judging is not rerunnable: frozen judgment files are the record.
