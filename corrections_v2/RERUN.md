# Exact rerun scope and execution instructions

No judge run has been launched. `generated/rerun_manifest.json` is the machine-readable authority: each job has its exact model, item IDs, packet path/hash, output path, count and launch prompt. `generated/impact_items.jsonl` maps every planned judgment to its claim, selected set and source files.

## Required and optional work

| Purpose | Namespace | Required model (exact historical slug) | Items | Judgments | Fresh contexts / calls, no retries |
|---|---|---|---:|---:|---:|
| Correct Grok diagnostic C | p01 | `cursor-grok-4.6-high-fast` | 1,060 | 5,300 | 55 (5 × 11 batches) |
| Correct Claude full C | p02 | `claude-opus-5-thinking-high` | 226 | 1,130 | 15 (5 × 3 batches) |
| Optional fixed historical residual cohort C | p03 | `claude-opus-5-thinking-high` | 231 | 1,155 | 15 (5 × 3 batches) |

Required total: **6,430 judgments, 70 contexts**. Including the optional fixed-cohort sensitivity test: **7,585 judgments, 85 contexts**. “Calls” here means one historical Cursor Task launch per judge/batch, not a claim that the provider bills exactly one API request per Task. Two schema retries per job are the configured maximum; worst-case launches would be 210 required / 255 including optional, not the baseline expectation.

Affected-item lists are exact, not inferred from verdict changes: `evidence_audit.jsonl` identifies 936 chosen-text mismatches (935 judged), 190 in the regression cohort, and alternative-only changes. `rerun_manifest.json` lists every item selected for the conservative full-C rerun. `SA-000352` remains provider-filtered and is not retried. Every v2 C packet changes because annotation-boundary/availability metadata also changes. Batch contexts can couple items, so apparently unaffected items inside an old batch are not treated as independent reusable C judgments.

Retain the original A/B files and their recorded freezes. They are content-identical to the reconstructed A/B inputs and were run in documented fresh stage contexts. No A/B reruns are required for this correction under that protocol. If deliberately changing their visible Unicode encoding or representation in a new experiment, those changed inputs would need new judgments.

## Prepare and inspect locally

Run from the repository root:

```powershell
python corrections_v2/reproduce.py --pages corrections_v2/generated/historical_pages_used.json
python corrections_v2/build_report_data.py
python corrections_v2/verify_outputs.py
python corrections_v2/rerun.py list
python corrections_v2/rerun.py show-job p01_C_j1_b01
python corrections_v2/rerun.py show-job p02_C_j1_b01
```

`show-job` prints the exact dispatch specification, including `launch_prompt`. The optional residual jobs start at `p03_C_j1_b01`. Only judge-facing `corrections_v2/blind_io/pNN/stage_c/` paths appear in those prompts; do not give judges the manifest, this report, source IDs, FEVER/GPT labels or prior judgments.

## Historical execution route

The repository's `run_judges.py` scripts validate and freeze outputs; **they do not invoke a model**. Historical judging used a Cursor Task orchestrator. There is no verified headless judge-launch command in this repository, and the present Codex agent tools do not expose either locked slug. Do not fabricate a shell/API command or route these jobs to a current default model.

Once running in an environment that exposes the locked model, the exact operation for each required job is:

```text
Cursor Task:
  model = job.model
  fresh isolated context = true
  prompt = job.launch_prompt
  inherited conversation/context = none
  Auto/inherit routing = disabled
  browsing/external retrieval = disabled
```

This is an orchestration specification, not an executable CLI command. Read the matching config/model lock first. Use one context per job, never one context to simulate five judges. Keep the frozen A/B hashes linked in the new record. Judges read exactly the packet and write exactly its new output path. No judgment should be copied from a v1 file or between panels. All new contexts must be blind to this audit. Retain provider model/version, request/session ID, actual routing, date, account interruptions, retries and any deviations in a new execution log.

After delivery, the exact local validation command is:

```powershell
python corrections_v2/rerun.py validate
```

Before any inference, this intentionally returns exit code 1 with 85 missing jobs. It neither launches nor retries anything. If only the required panels are executed, p03 remains explicitly missing/optional; do not manufacture records to make the validator pass. `verify_outputs.py` checks preparation and accepts absent judgment files; it cannot certify inference.

On completion, freeze the new packet hashes, actual model/session provenance and raw output hashes in a new versioned freeze; then compute consensus with the same documented five-judge rule. Retain historical A/B consensus with provenance, recompute all C-dependent transitions, apply the reviewed v2 taxonomy, and regenerate affected tables/figures in a v2 namespace. Do not run legacy analysis entry points against these outputs or overwrite v1 freezes. This task prepares packets and validates delivered schemas; it deliberately does not implement a general inference/evaluation harness.

## Work whose count depends on fresh results

* **Grok resolver:** the primary compared taxonomy uses raw consensus. The original full pipeline also ran a same-model resolver on non-high-consensus cases. To reproduce that secondary output/gate, rerun C resolver judgments on the new non-high-consensus set. If its size is K, require K new resolver judgments, conventionally `ceil(K/100)` contexts, exact IDs and count determined after fresh consensus. Old C resolver outputs are not reusable. A/B resolver outputs remain historical and unchanged. Do not silently drop the resolver if claiming to reproduce the entire old pipeline.
* **New residual cohort:** after corrected Grok C is frozen, derive the new residual set of size R. This is not necessarily the historical 231. A new Claude residual analysis requires 5R judgments and `5 * ceil(R/77)` contexts with new opaque IDs, even for overlapping claims, because selection and batch context differ. The p03 jobs answer only a fixed-historical-cohort sensitivity question. Its 58% historical persistence estimate cannot be transported to the new cohort.
* **Information-versus-formatting ablation:** a separately proposed chosen-only structured C arm on all 226 regressions, for both families, requires 2,260 judgments / 30 contexts (15 per family), in addition to the prepared full-C arms. There are 41 regressions with new alternative sentence text. Pre-specify the comparison and keep all 226 in the arm to avoid selecting on new verdicts. No such new arm is included in the prepared or executed counts. This estimates a judge response to disclosure, not the cause of GPT errors.

## Unavailable models and costs

Availability is unverified through the historical execution route; neither lock is callable from this task. If a slug is unavailable, record the block and stop that historical rerun. A replacement model belongs in a separately named `replication_v3_<model>_<date>` study with its own model/version lock, prompt hashes, fresh IDs, complete A/B/C trajectories, freezes and estimand. It cannot supply corrected v2 judgments under the old model's name.

A full two-family replication of the same primary samples, including all A/B/C stages, would require 15,900 Grok-sample judgments plus 3,390 Claude-sample judgments = 19,290 judgments / 210 fresh batch contexts, excluding retries, resolver work and residual analysis. These are workload counts, not a commitment to use replacements. No cost estimate is given without a verified execution route and pricing.
