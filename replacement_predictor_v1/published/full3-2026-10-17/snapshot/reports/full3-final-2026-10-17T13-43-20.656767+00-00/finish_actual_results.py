"""Read-only independent summary checks and additive actual-results report."""
import collections
import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPERIMENT = ROOT.parent.parent


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a, b):
    assert math.isclose(a, b, abs_tol=1e-12), (a, b)


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(value)


verification = load(ROOT/'ANALYSIS_VERIFICATION.json')
assert verification['status'] == 'PASS'
analysis = Path(verification['analysis_output'])
for name, digest in verification['output_files'].items():
    assert sha(analysis/name) == digest, name
integrity = load(ROOT/'INTEGRITY.json')
assert integrity['status'] == 'PASS' and not integrity['issues']
assert sha(ROOT/'OUTCOMES.jsonl') == integrity['outcomes_sha256']
summary = load(analysis/'summary.json')
outcomes = [json.loads(line) for line in (ROOT/'OUTCOMES.jsonl').read_text(encoding='utf-8').splitlines()]
inputs = [json.loads(line) for line in (EXPERIMENT/'prepared/inputs.jsonl').read_text(encoding='utf-8').splitlines()]
index = {(o['claim_id'], o['model'], o['condition'], o['repetition']): o for o in outcomes}
assert len(index) == len(outcomes) == 180000
assert len({o['job_id'] for o in outcomes}) == 180000
assert all(o['state'] == 'valid' and o['request_attempts'] == 1 for o in outcomes)
ids = sorted({o['claim_id'] for o in outcomes})
assert len(ids) == 10000
gold = {r['claim_id']: r['gold_label'] for r in inputs}
historical = {r['claim_id'] for r in inputs if r['historical_regression']} & set(ids)
for o in outcomes:
    assert o['correct'] == (o['label'] == gold[o['claim_id']])
models = sorted({o['model'] for o in outcomes})
checks = []
for section, selected_ids, reps in [
    ('first_pass', ids, [1]),
    ('repeat_representative', ids, [1, 2, 3]),
    ('historical_cases_first_pass', sorted(historical), [1]),
]:
    frozen = summary[section]
    assert frozen['claims'] == len(selected_ids)
    for model in models:
        for condition in 'ABC':
            records = [index[cid, model, condition, rep] for cid in selected_ids for rep in reps]
            count = sum(o['correct'] for o in records)
            key = model+'/'+condition+'/accuracy_ITT'
            detail = frozen['details'][key]
            assert (detail['assigned_calls'], detail['valid_calls'], detail['correct']) == (len(records), len(records), count)
            close(detail['accuracy_ITT'], count/len(records))
            close(frozen['estimates'][key]['estimate'], count/len(records))
        for pair in ('AB', 'BC', 'AC'):
            bins = collections.Counter()
            for cid in selected_ids:
                for rep in reps:
                    a = index[cid, model, pair[0], rep]['correct']
                    b = index[cid, model, pair[1], rep]['correct']
                    bins['robust_known' if a and b else 'regressions_known' if a else 'rescues_known' if b else 'resistant_known'] += 1
            n = len(selected_ids)*len(reps)
            detail = frozen['details'][model+'/'+pair]
            assert detail['assigned_pairs'] == detail['valid_pairs'] == n
            assert detail['unclassified_pairs'] == 0
            for key in ('robust_known', 'regressions_known', 'rescues_known', 'resistant_known'):
                assert detail[key] == bins[key]
            for suffix, value in [('known_regression_fraction', bins['regressions_known']/n), ('known_rescue_fraction', bins['rescues_known']/n), ('accuracy_difference_ITT', (bins['rescues_known']-bins['regressions_known'])/n)]:
                close(frozen['estimates'][model+'/'+pair+'/'+suffix]['estimate'], value)
    checks.append(section+': all accuracy/pair numerators, denominators and point estimates agree')

repeat_aggregates = {}
for section, selected_ids in [('repeat_variation', ids), ('historical_cases_repeated', sorted(historical))]:
    frozen = summary[section]
    assert frozen['claims_assigned_repeats'] == len(selected_ids)
    seen = set()
    values = collections.defaultdict(list)
    aggregate = collections.defaultdict(collections.Counter)
    for row in frozen['per_claim_outcomes']:
        cid, model = row['claim_id'], row['model']
        assert cid in selected_ids
        kind = row.get('condition', row.get('comparison'))
        assert (cid, model, kind) not in seen
        seen.add((cid, model, kind))
        a = [index[cid, model, kind[0], rep] for rep in (1, 2, 3)]
        assert row['assigned_repetitions'] == 3
        if 'condition' in row:
            changes = sum(x['label'] != y['label'] for x, y in itertools.combinations(a, 2))
            expected = changes/3
            assert row['complete'] and row['valid_repetitions'] == 3
            assert row['distinct_labels'] == len({x['label'] for x in a})
            assert row['all_repeats_same'] == (changes == 0)
            close(row['disagreement_fraction'], expected)
            values[model+'/'+kind+'/identical_prompt_disagreement'].append(expected)
            aggregate[model+'/'+kind]['claims_with_any_disagreement'] += changes > 0
            aggregate[model+'/'+kind]['disagreeing_repeat_pairs'] += changes
            aggregate[model+'/'+kind]['total_repeat_pairs'] += 3
        else:
            b = [index[cid, model, kind[1], rep] for rep in (1, 2, 3)]
            regression = sum(x['correct'] and not y['correct'] for x, y in zip(a, b))
            rescue = sum(not x['correct'] and y['correct'] for x, y in zip(a, b))
            different = sum(x['label'] != y['label'] for x, y in zip(a, b))
            baseline = sum(x['correct'] and not y['correct'] for i, x in enumerate(a) for j, y in enumerate(a) if i != j)/6
            assert row['regressions'] == regression and row['rescues'] == rescue
            assert row['regression_every_repetition'] == (regression == 3)
            assert row['changed_every_repetition'] == (different == 3)
            for key, number in [('rescue_fraction', rescue/3), ('label_change_fraction', different/3), ('persistence_fraction', regression/3), ('same_left_prompt_directional_loss', baseline)]:
                close(row[key], number)
            values[model+'/'+kind+'/excess_loss_over_identical_left_prompt'].append(regression/3-baseline)
            aggregate[model+'/'+kind]['regression_on_'+str(regression)+'_of_3'] += 1
            aggregate[model+'/'+kind]['rescue_on_'+str(rescue)+'_of_3'] += 1
    assert len(seen) == len(selected_ids)*len(models)*5
    for key, numbers in values.items():
        assert frozen['estimates'][key]['complete_claims'] == len(selected_ids)
        close(frozen['estimates'][key]['estimate_complete_claims'], sum(numbers)/len(numbers))
    repeat_aggregates[section] = {k: dict(v) for k, v in aggregate.items()}
    checks.append(section+': every per-claim repeat record and aggregate point estimate agrees')

for model in models:
    a, b = summary['usage_accounting'][model], integrity['usage'][model]
    assert a['receipts'] == a['receipts_with_usage'] == b['requests'] == b['receipts_with_usage'] == 90000
    assert a['receipts_without_usage'] == 0
    for reported, direct in [('reported_prompt_tokens', 'prompt_tokens'), ('reported_completion_tokens', 'completion_tokens'), ('reported_reasoning_tokens', 'reasoning_tokens'), ('reported_cached_prompt_tokens', 'cached_prompt_tokens')]:
        assert a[reported] == b[direct]
checks.append('Frozen usage accounting agrees with independent complete-attempt accounting')

def pct(x):
    return f'{100*x:.2f}'


def interval(est):
    return ' to '.join(pct(x) for x in est['cluster_bootstrap_95'])


lines = [
    '# Evidex full3 actual results', '',
    'Analysis and integrity verification: **PASS**. Frozen analysis exited 0 at 2026-10-17 23:35:33 UTC (6:35 pm Central); output verification passed at 23:35:42 UTC. Collection completed at 13:42:03 UTC. No paid calls were made during offline finalization.', '',
    'Across three repetitions, adding the supplied gold evidence (A to B) increased accuracy by 7.55 percentage points for gpt-5.4 and 10.79 points for gpt-5.4-mini. Adding the evidence-only instruction (B to C) changed accuracy by +0.02 and +0.17 points, respectively; both repeated-summary 95% intervals include zero. Evidence rescued more errors than it introduced, but introduced some regressions. These comparisons apply to the frozen claim set, prompts and provider occasion.', '',
    '## Design and denominators', '',
    '10,000 claims; 9,855 claim-text clusters; two models; three conditions; three repetitions: 180,000 planned and valid calls. First-pass cells contain 10,000 calls; repeated cells contain 30,000 calls, reduced within claim for uncertainty. The repeated summary includes repetition 1 and is not an independent replication. Label strata have the original 50/50 weights. All confidence intervals below are the unchanged frozen 2,000-draw joint claim-text-cluster bootstrap intervals; no bootstrap was rerun.', '',
    '- A: claim only, generic classification instruction.',
    '- B: claim plus gold evidence, same generic classification instruction.',
    '- C: claim plus gold evidence, with “based only on the evidence provided” added.', '',
    'Returned snapshots: gpt-5.4-2026-03-05 and gpt-5.4-mini-2026-03-17 (90,000 calls each).', '',
    '## Accuracy', '',
    '| Summary | Model | Condition | Correct / assigned (all valid) | Accuracy % | 95% interval % |',
    '|---|---|---|---:|---:|---|',
]
for section, label in [('first_pass', 'First pass'), ('repeat_representative', 'Three repetitions')]:
    part = summary[section]
    for model in models:
        for c in 'ABC':
            k = model+'/'+c+'/accuracy_ITT'; d = part['details'][k]; e = part['estimates'][k]
            lines.append(f'| {label} | {model} | {c} | {d["correct"]:,} / {d["assigned_calls"]:,} | {pct(e["estimate"])} | {interval(e)} |')
lines += ['', '## Paired regressions and rescues', '',
    'Regression means correct in the left condition and wrong in the right; rescue means wrong to correct. Rates use all assigned pairs, not only initially correct or incorrect cases. All pairs are valid and classified. Accuracy change equals (rescues minus regressions) / assigned pairs. The supplement retains both-correct and both-wrong counts.', '',
    '| Summary | Model | Pair | Assigned pairs | Regressions (%, 95% interval) | Rescues (%, 95% interval) | Accuracy change pp (95% interval) |',
    '|---|---|---|---:|---|---|---|']
for section, label in [('first_pass', 'First pass'), ('repeat_representative', 'Three repetitions')]:
    part = summary[section]
    for model in models:
        for pair in ('AB', 'BC', 'AC'):
            k = model+'/'+pair; d = part['details'][k]
            es = [part['estimates'][k+'/'+s] for s in ('known_regression_fraction', 'known_rescue_fraction', 'accuracy_difference_ITT')]
            reg, rescue, delta = es
            lines.append(f'| {label} | {model} | {pair} | {d["assigned_pairs"]:,} | {d["regressions_known"]:,} ({pct(reg["estimate"])}; {interval(reg)}) | {d["rescues_known"]:,} ({pct(rescue["estimate"])}; {interval(rescue)}) | {pct(delta["estimate"])} ({interval(delta)}) |')
lines += ['', '## Repeat variability', '',
    'Identical-prompt disagreement averages the three unordered repeat-pair label disagreements within each claim. Its denominator is 10,000 complete claims per cell (30,000 repeat pairs); it is not the proportion of claims with any disagreement. Both are shown.', '',
    '| Model | Condition | Claims with any disagreement / 10,000 | Disagreeing repeat pairs / 30,000 | Mean disagreement % (95% interval) |',
    '|---|---|---:|---:|---|']
for model in models:
    for c in 'ABC':
        a = repeat_aggregates['repeat_variation'][model+'/'+c]
        e = summary['repeat_variation']['estimates'][model+'/'+c+'/identical_prompt_disagreement']
        lines.append(f'| {model} | {c} | {a["claims_with_any_disagreement"]:,} | {a["disagreeing_repeat_pairs"]:,} | {pct(e["estimate_complete_claims"])} ({interval(e)}) |')
lines += ['', 'The frozen excess-loss comparison subtracts the mean directional correct-to-wrong loss across the six ordered repeats of the left prompt from the paired-condition regression rate. All 10,000 claims are complete.', '',
    '| Model | Pair | Excess loss pp (95% interval) | Claims regressing in all 3 repetitions / 10,000 |',
    '|---|---|---|---:|']
for model in models:
    for pair in ('AB', 'BC'):
        e = summary['repeat_variation']['estimates'][model+'/'+pair+'/excess_loss_over_identical_left_prompt']
        n = repeat_aggregates['repeat_variation'][model+'/'+pair].get('regression_on_3_of_3', 0)
        lines.append(f'| {model} | {pair} | {pct(e["estimate_complete_claims"])} ({interval(e)}) | {n:,} |')
lines += ['', 'Persistence over three calls does not establish a stable individual causal effect. Full per-claim repeat outcomes and the independently checked 0/1/2/3 regression and rescue histograms are retained in the supplement.', '',
    '## Coverage and integrity', '',
    '180,000 unique planned jobs, admissions, substantive responses and valid final outcomes. Zero terminal failed, invalid, uncertain, missing or pending jobs; zero duplicate admissions, response IDs or raw-response hashes; no unclassified analysis pairs. All 180,000 jobs used exactly one actual request. Eight earlier recovery-only attempt directories contain no API request; ordinal 2 is the first actual call for those jobs. These are not API retries.', '',
    '720,008 attempt artifacts were inventoried and hashed; all 165,792 sealed baseline artifacts were preserved. Every saved request/settings hash, raw receipt hash, frozen interpretation, plan/run identity and old/new operational seal passed the completed integrity check. Final database backup, failed/partial/recovery records and the original Windows-interrupted analysis records remain preserved. The offline recovery changed no scientific source or settings.', '',
    '## Recorded usage and cost', '',
    '| Model | Calls with usage | Prompt tokens | Completion tokens | Reported cached / reasoning tokens | Frozen-rate cost USD |',
    '|---|---:|---:|---:|---:|---:|']
for model in models:
    u = integrity['usage'][model]
    lines.append(f'| {model} | {u["receipts_with_usage"]:,} | {u["prompt_tokens"]:,} | {u["completion_tokens"]:,} | {u["cached_prompt_tokens"]:,} / {u["reasoning_tokens"]:,} | {integrity["recorded_cost_by_model_usd"][model]:.8f} |')
lines += ['',
    'Total: **12,888,042 prompt tokens; 962,517 completion tokens; $29.78757825** using the frozen undiscounted input/output rates (per million: gpt-5.4 $2.50/$15.00; mini $0.75/$4.50). Cache and reasoning fields were present and zero on all 180,000 receipts. Completion usage already includes any reasoning tokens; none were added twice. No saved attempt is missing usage, and no uncertain transmission remains in this ledger. No cache discount was applied. This is independently reconciled recorded usage and frozen-rate arithmetic, **not an independently reconciled provider invoice**. The cumulative $35 guard was preserved.', '',
    '## Limits and unresolved issues', '',
    'No unresolved integrity or accounting mismatch was found. Provider invoice reconciliation remains outside these recorded artifacts. Intervals describe claim-text-cluster sampling uncertainty on this frozen set and provider occasion; they do not measure changes across provider snapshots or dates. The selected historical-case summaries and recorded historical-label comparisons remain in the frozen summary; they cannot recreate or identify undocumented historical model changes and are not the primary full-set comparison. No claim that C reliably improves on B is supported by the repeated accuracy intervals, which include zero. No new inference, invalid-response replacement, redesign or scientific reanalysis was performed.', '',
    '## Evidence and checks', '',
    f'- [Frozen summary]({(analysis/"summary.json").as_posix()})',
    f'- [Frozen observations]({(analysis/"observations.csv").as_posix()})',
    f'- [Frozen provenance]({(analysis/"provenance.json").as_posix()})',
    '- [Analysis verification](ANALYSIS_VERIFICATION.json)',
    '- [Completed integrity/accounting](INTEGRITY.json)',
    '- [Independent outcomes](OUTCOMES.jsonl)',
    '- [Independent comparison verification and numeric supplement](RESULTS_VERIFICATION.json)',
    '- [Report-generation/check source](finish_actual_results.py)', '',
    'Output hashes were rechecked against ANALYSIS_VERIFICATION.json. Independently checked first-pass, repeated and selected historical accuracy/pair numerators and denominators against OUTCOMES.jsonl, plus every full-set and historical per-claim repeat record and aggregate point estimate. Frozen confidence intervals were transcribed without recomputation.', '',
    'What changed: added this report and independent comparison verification. Files changed: ACTUAL_RESULTS.md, RESULTS_VERIFICATION.json and finish_actual_results.py; original artifacts and frozen analysis outputs were preserved. Verification run: read-only outcome/summary comparisons and recorded output/outcome hash checks. Result: PASS. Remaining uncertainty: provider invoice reconciliation and the stated scope of statistical inference.', '',
]
result = {'status': 'PASS', 'at_utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': sha(Path(__file__)), 'analysis_output': str(analysis), 'output_hashes': verification['output_files'], 'outcomes_sha256': sha(ROOT/'OUTCOMES.jsonl'), 'checks': checks, 'confidence_intervals': 'Copied from unchanged frozen 2000-draw analysis; not recomputed', 'repeat_aggregates': repeat_aggregates, 'accuracy_and_pairs': {k: summary[k] for k in ('first_pass', 'repeat_representative', 'historical_cases_first_pass')}, 'usage': integrity['usage'], 'cost_usd': integrity['recorded_cost_by_model_usd'], 'invoice_reconciled': False}
write_new(ROOT/'RESULTS_VERIFICATION.json', json.dumps(result, indent=2)+'\n')
write_new(ROOT/'ACTUAL_RESULTS.md', '\n'.join(lines))
print(json.dumps({'status': 'PASS', 'checks': checks, 'report': str(ROOT/'ACTUAL_RESULTS.md'), 'report_sha256': sha(ROOT/'ACTUAL_RESULTS.md'), 'repeat_aggregates': repeat_aggregates['repeat_variation']}))
