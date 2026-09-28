# Evidex â€” current status (2026-09-28)

Start here. The root `README.md`, `REPRODUCING.md` and the documents under `corrections_v2/` are
hash-pinned. They describe the repository before the corrected Stage C judgments were run, and they
cannot be edited without breaking their verifiers. `docs/post_judgment/SUPERSEDED_DOCUMENTS_2026-09-28.md`
says what is out of date in each one.

## Where things stand

| Item | Status |
|---|---|
| Behavioral study: 10,000 FEVER claims, 40,000 GPT predictions, +7.35 / +10.87 pp, 226 unique regressions | Unchanged. Frozen at tag `evidex-artifact-v1` (`29102c3`) |
| Historical diagnostic adjudication (v1) | Defective Stage C evidence text and taxonomy. Its mechanism splits are withdrawn as estimates. Files preserved unchanged |
| Correction protocol v2 (post hoc, frozen 2026-09-27) | Unchanged. Not a preregistration |
| Required corrected Stage C judgments | **Present.** 70/70 jobs, 6,430/6,430 schema-valid judgments (55 Grok jobs, 15 Claude jobs) |
| Optional fixed historical residual panel | **Not run.** 15 jobs / 1,155 judgments |
| Frozen-protocol primary analysis | **Incomplete.** Execution provenance fails the frozen validator: six jobs over the three-attempt cap, and 13 `unknown`-session collision records. No judgment freeze, no `corrections_v2/results/` |
| Protocol follow-ups (new residual Claude panel, Stage C resolver) | Not generated or run, because they depend on the primary freeze |
| Post-judgment deviation analysis | **Exists.** Separately labeled and dated. It applies the frozen analysis code to the accepted outputs and to a first-valid selection, both chosen after the outputs were inspected. See the note below |
| Amendment A1 (post-judgment, 2026-09-28) | **Adopted by the authors.** Allows up to 9 attempts and checks session uniqueness on the agent of each launched slot (101 slots, 101 distinct agents, all read from WSL event logs). The 13 `unknown`-session records are pre-launch exits of duplicate runners, not model attempts; each slot's real attempt is identified from its event log and the runner log (`session_evidence.json`). Explicitly selects the accepted outputs. Status `ready_under_amendment_A1`. Results in `corrections_v2/amendment_2026-09-28/results/` are identical in every estimate to the provisional analysis. Not preregistered |
| Corrected manuscript | `paper_corrected_draft/evidex-corrected-draft.pdf` (compiled, 21 pages, revised for Jessica Udry's editorial comments; see `paper_corrected_draft/EDITORIAL_RESPONSE_TO_JESSICA.md`), for coauthor review. Its decisions list is in `paper_corrected_draft/README.md` |

## Read next

0. `corrections_v2/amendment_2026-09-28/AMENDMENT_A1.md`: the rule change the corrected paper uses.
1. `docs/post_judgment/POST_JUDGMENT_ANALYSIS_NOTE_2026-09-28.md`: the corrected results and what
   they can support.
2. `corrections_v2/deviation_review/DEVIATION_ASSESSMENT_2026-09-28.md` and
   `corrections_v2/deviation_review/attempt_table.md`: the execution deviations and their evidence.
3. `docs/post_judgment/TECHNICAL_SUPPLEMENT_2026-09-28.md`: recovered files, input checks, the 12
   combinations, and reproduction.
4. `paper_corrected_draft/README.md` and `paper_corrected_draft/CLAIM_MAPPING.md`: the corrected
   draft and the oldâ†’new claim map.
5. `docs/post_judgment/IMMUTABILITY_MAP_2026-09-28.md`: what must never change.
6. `docs/post_judgment/REPOSITORY_MAP_2026-09-28.md`: where everything lives.

## Commands

| Command | Expected |
|---|---|
| `python corrections_v2/verify_outputs.py` | exit 0: historical, implementation and inventory hashes verify. Its closing phrase "corrected judgments pending" is fixed text in fingerprinted code and is out of date |
| `python corrections_v2/rerun.py validate --scope required` | exit 0: required judgments complete (70 jobs, 6,430 schema-valid). This command checks schema completeness only and reports execution provenance as not assessed. The optional 15 jobs are listed as missing |
| `python corrections_v2/analysis_pipeline.py status --panel primary` | exit 1, status `incomplete`: retry limit exceeded for six jobs, plus `reused_session` |
| `python corrections_v2/deviation_review/provisional_analysis.py verify` | exit 0: committed provisional results reproduce from tracked inputs |
| `python corrections_v2/amendment_2026-09-28/amended_analysis.py status` | exit 0, `ready_under_amendment_A1` |
| `python corrections_v2/amendment_2026-09-28/amended_analysis.py verify` | exit 0: committed A1 results reproduce from tracked inputs |
| `python -m unittest discover -s corrections_v2/amendment_2026-09-28/tests` | exit 0 |
| `python paper_corrected_draft/make_assets.py` | regenerates the draft's Tables 2â€“4 and Figures 3â€“4 from the A1 results |
| `python -m unittest discover -s corrections_v2/deviation_review/tests` | exit 0 |
| `python paper_corrected_draft/check_draft.py` | exit 0: static consistency of the draft |
| `python scripts/run_all_tests.py`, `python scripts/verify_all_headlines.py` | historical test and headline runners. They need the historical Python dependencies |

No command in this repository launches model inference.
