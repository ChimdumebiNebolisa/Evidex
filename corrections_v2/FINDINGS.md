# Findings: historical verification and proposed correction

The two reported defects reproduce. The original behavioral results remain supported; the claimed cross-family ordering of diagnostic failure modes does not survive even the proposed rule-only reanalysis as stated. Results for corrected evidence are **pending**, not estimated from old judgments.

## Independent checks

The starting checkout was clean at `776d09b`; there were no subsequent fixes. All work is on `codex/methodology-correction-v2`. The frozen artifact tag and all historical data/manuscript files are preserved. The legacy Level 1 verifiers all pass: Analysis v2 69/69, Grok 33/33, GLM Stage A, Claude residual 38/38, Claude full 21/21. These establish reproduction of the historical record, not methodological validity.

From the 40,000 original prediction labels, independently comparing each output with FEVER (and checking stored correctness and evidence metadata):

| Model | Correct claim only → evidence | Persistent success | Improvements | Persistent failure | Regressions |
|---|---|---:|---:|---:|---:|
| GPT-5.4 | 8,869 → 9,604 (+7.35 pp) | 8,754 | 850 | 281 | 115 |
| GPT-5.4-mini | 8,467 → 9,554 (+10.87 pp) | 8,316 | 1,238 | 295 | 151 |

The union is 226 claims: 40 shared, 75 GPT-5.4-only, 111 mini-only. No GPT rerun is required to retain those observed outcomes. They remain outcomes of the original prompts, not evidence of repeat-run stability.

## Evidence reconstruction

The original resolver used tab field 1; Stage C used the last field, often a hyperlink target. Exact selected sets were recovered by recomputing the original SHA-1-based set ID from the annotation index and ordered NFC-normalized pointers, then checking ordered page titles and sentence-array length. All 1,061 chosen sets have matching ordered pointers; there is no observed pointer-level wrong-set selection in this cohort. Old packets omitted annotation indices, so identity among duplicate annotations cannot be established from the old packet alone. The old count/page-set heuristic was nevertheless unsafe and has been removed.

* 936/1,061 chosen-set text mismatches; 190/226 among regressions.
* 927 claims contain verified last-field extraction errors.
* 10 claims had unavailable structured selected text because decomposed Unicode titles were absent from the historical cache; local shard lookup with normalized keys recovered them. One also has an extraction error, hence 927 + 10 − 1 = 936.
* Alternative text changes on 140 claims: extraction errors on 139, previously unavailable text on 2, with overlap. Alternatives are checked against annotation pointer sequences separately from the selected set.
* All 1,149 chosen sentence occurrences and 816 alternative occurrences in v2 are available from local archival data. Alternative occurrences include separately preserved duplicate annotations. Selected text matches the canonical original arrays exactly. No unexplained text conflicts occurred.
* The full original concatenated gold evidence remains in the old packets. Consequently, corruption is demonstrated, but its effect on a judge's verdict cannot be deduced without rerunning.

Examples: `SA-000001` / claim 42669 stores “Neil Gaiman” instead of the full Emperor Norton sentence; `SA-000002` / 104811 stores “Singapore Airlines.” `SA-000329` / 10689 has unavailable Cléopâtre/Opéra de Monte-Carlo structured text. `SA-001042` / 192203 exhibits both causes. Full texts and exact pointers are in `generated/representative_cases.json`.

The fix shares one parser with the original resolver; preserves sentence text, ordered pointers, selected identity and all annotation boundaries; makes missing chosen and alternative text separately explicit; and rejects canonical-text conflicts. The v2 packet also preserves duplicate annotation boundaries and adds availability metadata. These are disclosed representation changes beyond replacing the faulty field. Every C packet therefore has a new identity and requires fresh judgments in the v2 design.

Stage C adds sentence text beyond the original selected sentences for 149 cohort claims, including 41 regressions. C is not a pure formatting manipulation. A new chosen-only structured arm would be needed to separate the contribution of alternative text from structure (see RERUN).

## Taxonomy

Raw active judge records were independently aggregated with the documented five-judge consensus rules, then checked against every frozen A/B/C consensus and legacy label in the Grok and full Claude panels. Quarantined outputs were excluded. The original rules now live explicitly in `taxonomy_legacy_v1.py`; existing historical analysis entry points still use those unchanged rules.

Among legacy utilization cases, 36/113 Grok and 46/149 Claude C verdicts disagree with FEVER. They cannot be taken as evidence that GPT failed to use evidence supporting the FEVER answer. Across all regressions, C-decisive FEVER disagreements number 47 and 51. Examples in the generated case file include Grok `SA-000025` / claim 134927, whose FEVER label is Supported while A/B/C consensus is Refuted. Judge rationales are observations, not proof that FEVER is wrong.

Inspection shows substantive conflicts: for `SA-000025`, the judge distinguishes a Paris premiere from a global premiere; for `SA-000137`, the claim says May 27 but supplied text says March 27; for Claude `CF-000010`, the supplied text says a season premiered January 2, 2017 while the claim denies a January 2017 start. These examples explain why a decisive opposite-label verdict cannot support the original utilization interpretation. They do not authorize changing FEVER labels.

The broad A-nondecisive/C-decisive branch absorbs 15 Grok and 5 Claude title-resolution cases into structure sensitivity. This precedence was explicitly documented in the old Claude methods; the defect is a mismatch between the taxonomy's meaning and its rule, not an undocumented implementation difference between panels. (Grok has 16 A→B resolutions total; one is nondecisive again at C and falls into the first legacy branch.)

The proposed v2 taxonomy separates each stage's decisiveness and FEVER agreement, first decisive/gold-agreeing stage, title/C resolution, reversals and losses of decisiveness. Final nondecisiveness and decisive disagreement take priority. Gold-agreeing paths then distinguish nonmonotonic paths, sentence-only agreement, title-associated agreement, and C-associated agreement with/without added text. Only A gold agreement in a regression/resistant case is marked `sentence_only_utilization_compatible`; that remains a compatibility statement, not a causal explanation of GPT.

### Legacy versus proposed rules, using the SAME OLD judgments

| Classification | Grok /226 | Claude /226 |
|---|---:|---:|
| Legacy utilization | 113 | 149 |
| Of those, C disagrees with FEVER | 36 | 46 |
| v2 sentence-only gold-agreeing, stable path | 77 | 103 |
| v2 final nondecisive | 86 | 65 |
| v2 decisive judge–FEVER disagreement | 47 | 51 |
| v2 title-disclosure gold-agreeing | 9 | 3 |
| v2 structured-disclosure gold-agreeing, no new text | 3 | 2 |
| v2 additional-evidence gold-agreeing | 2 | 0 |
| v2 nonmonotonic judge path, final gold agreement | 2 | 2 |
| Corrected-packet v2 results | **PENDING** | **PENDING** |

The seven v2 categories sum to 226 per panel. Historical C fields can contain fragments; the old-input added-text flag describes what those packets presented and does not certify valid alternative evidence. None of these C-dependent rows can be presented as results for repaired packets.

A separate A-only field identifies 86 Grok and 110 Claude regressions with sentence-only gold-agreeing consensus, irrespective of their later path. This field can be retained/recomputed from A alone. It must not be confused with the stable-path 77/103 categories or reported as a proven rate of GPT utilization failure.

Under these proposed descriptive rules, final nondecisiveness (86) exceeds stable sentence-only gold agreement (77) for Grok. Thus “utilization is largest in both families” and “the ordering replicates” must be withdrawn pending revised definitions and fresh C judgments. The former 50–66% range is not a defensible uncertainty interval for utilization failure.

## Stage dependence, preservation, and limits

Every A item equals the original GPT claim/evidence. Every B item now equals the historical B record exactly, including Unicode spelling of displayed titles; normalization is confined to lookup keys. Claude A/B reuse was checked through the CF→SA map, and both Claude C panels' old inputs equal the shared old C records through their ID maps.

The protocol and Claude methods specify fresh context per `(judge, batch, stage)`. Packet builders supply only current-stage evidence, not earlier answers. A/B freezes precede C; C does not feed back into A/B computations. On that documented protocol, retain A/B raw judgments and A/B-only results. Pair them with new C only after a new C freeze, explicitly describing the hybrid provenance. A→C/B→C transitions and all C-dependent claims must be recomputed. Raw model-session transcripts are not available to independently prove the historical runtime isolation. If later evidence contradicts the documented isolation, retain A/B as historical observations only and rerun complete trajectories in a new version.

All 14 residual-panel freeze entries match this Windows checkout. Simulated LF-only bytes fail 13 text hashes, while CRLF bytes match their recorded hashes; the parquet remains an exact-byte match. `freeze_eol_audit.json` records expected/raw/LF/CRLF digests. This reproduces the previously reported Linux explanation without rewriting manifests or accepting arbitrary content drift. Existing residual verifiers are still raw-byte strict on other platforms; use the supplementary audit to distinguish EOL drift from real changes.

No paid inference, new judge run, push, merge or publication occurred. Model availability through the historical Cursor Task execution route is not established by these local checks. The current tool surface does not expose the locked judge models. Cost is not estimated. Source text has local archive hashes and exact selected-text agreement, but no newly obtained independent publisher checksum. All required local source text was found; no missing-data blocker remains for reconstruction. Fresh C judgments and coauthor review remain necessary for corrected scientific conclusions.
