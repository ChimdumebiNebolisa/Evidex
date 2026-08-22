# Evidex Silver Adjudication v1

A blinded, GLM-only silver-adjudication layer over the Evidex Analysis v2
findings. Five isolated GLM-5.3 judges adjudicate ~1,100 matched claims
through three progressive-disclosure stages (sentence-only evidence → +page
titles → +structured FEVER evidence), a GLM resolver handles non-consensus
items, and outputs are frozen and hashed before any unblinding join to
Analysis v2 transitions, FEVER labels, and NLI diagnostics.

**What this is:** a GLM-family silver adjudication — a reproducible,
blinded second opinion that helps decompose why designated gold evidence
sometimes fails to produce the expected verdict (model utilization vs
evidence representation vs claim-evidence ambiguity).

**What this is not:** human ground truth, independent model-family
validation, or proof that FEVER labels are wrong. All generative judges are
GLM-5.3 from the same family; within-family agreement may overstate truly
independent agreement. See `reports/LIMITATIONS.md`.

## Layout

- `config.py` / `run_all.py` — configuration and resumable orchestrator
- `prompts/` — judge rubric, resolver rubric, disclosure protocol (versioned)
- `src/` — one module per pipeline stage
- `data/blinded/` — judge-facing stage files (leak-validated)
- `data/derived/` — cohort manifest, ID map, freeze manifest, unblinded joins
- `data/cache/` — wiki archive + extracted pages (gitignored)
- `judgments/` — raw per-judge/stage outputs (append-only after freeze)
- `tables/`, `figures/`, `reports/`, `tests/`

## Reproduce

```bash
python run_all.py                 # validates prerequisites; builds cohort,
                                  # blinded stages; reports judge gaps.
                                  # Judge/resolver subagent execution is driven
                                  # by src/run_judges.py batch files; completed
                                  # judgments are cached and reused.
python -m unittest discover -s tests
python src/verify_headlines.py
```

## Protections

- Analysis v2 artifacts and original experiment outputs are read-only.
- Blinding is machine-validated before judging (prohibited fields absent,
  opaque IDs carry no cohort/label signal).
- An unblinding gate refuses to join outcomes unless the freeze manifest
  exists and every hash matches.
- All new GLM inference is confined to the blinded adjudication and
  disagreement resolution defined in `prompts/`.
