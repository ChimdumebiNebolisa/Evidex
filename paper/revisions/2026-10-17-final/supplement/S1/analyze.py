"""Offline analysis from immutable request/response artifacts, independent of runner parsing/DB."""
import argparse
import collections
import csv
import itertools
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent/'.deps'))
import numpy as np
from common import HERE, MODELS, RETURNED_MODELS, digest, load, read_inputs, value_hash, write_new

def observation(run, job):
    """First substantive HTTP 200 is final even when malformed; no valid-label hunting."""
    parent = Path(run)/'attempts'/job['job_id']; attempts = sorted(parent.glob('attempt-*'))
    state = 'missing'; chosen = None; usage_events = []; submitted = 0
    for directory in attempts:
        req = directory/'request.json'
        if not req.exists():
            continue
        submitted += 1
        request_record = load(req)
        if request_record['job']['job_id'] != job['job_id'] or value_hash(request_record['body']) != job['request_sha256']:
            raise ValueError('Request provenance mismatch: ' + job['job_id'])
        if (directory/'transport-error.json').exists():
            state = 'uncertain'; break
        if not (directory/'receipt.json').exists() or not (directory/'response.bin').exists():
            state = 'uncertain'; break
        receipt = load(directory/'receipt.json')
        if digest(directory/'response.bin') != receipt['raw_sha256']:
            raise ValueError('Raw response hash mismatch')
        status = receipt['http_status']
        raw = (directory/'response.bin').read_bytes()
        try:
            obj = json.loads(raw)
        except (ValueError, UnicodeError):
            obj = {}
        if not isinstance(obj, dict):
            obj = {}
        usage_events.append({'http_status':status,'usage':obj.get('usage'),'attempt':directory.name})
        if status != 200:
            state = 'service_failure'
            error = obj.get('error') or {}
            code = (error.get('code') or error.get('type')) if isinstance(error, dict) else None
            if status not in (502, 503, 504) and not (status == 429 and code == 'rate_limit_exceeded'):
                break
            state = 'pending_retry' if submitted < 3 else 'service_failure'
            continue
        state = 'invalid'; chosen = {'returned_model': obj.get('model'), 'usage': obj.get('usage'), 'attempt': directory.name}
        if obj.get('model') not in RETURNED_MODELS[job['model']]:
            state = 'model_mismatch'; break
        choices = obj.get('choices')
        if isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict):
            ch = choices[0]; msg = ch.get('message') or {}
            if isinstance(msg, dict):
                text = msg.get('content')
                if ch.get('finish_reason') == 'stop' and not msg.get('refusal') and isinstance(text, str) and text.strip() in ('Supported', 'Refuted'):
                    state = 'valid'; chosen['label'] = text.strip()
        break
    return {'state': state, 'label': (chosen or {}).get('label'), 'attempt_directories': len(attempts),
            'usage_events':usage_events, **(chosen or {})}

def cluster_intervals(rows, metrics, draws=2000):
    """Joint claim-text cluster bootstrap, label strata standardized equally when both exist.
    metrics is n_claims x n_metrics; repeated calls have already been reduced per claim.
    Same cluster weight is used across labels, conditions, models and metrics.
    """
    if not rows:
        return [None]*metrics.shape[1]
    groups = {key: i for i, key in enumerate(sorted({r['text_cluster'] for r in rows}))}
    n = len(groups); m = metrics.shape[1]
    sums = np.zeros((2, n, m)); counts = np.zeros((2, n, m))
    for r, values in zip(rows, metrics):
        s = 0 if r['gold_label'] == 'Supported' else 1; g = groups[r['text_cluster']]
        ok = np.isfinite(values); sums[s, g, ok] += values[ok]; counts[s, g, ok] += 1
    rng = np.random.default_rng(20261016); output = []
    active = [s for s in range(2) if counts[s].sum()]
    original_counts = counts.sum(axis=1)
    stratum_weights = np.divide(original_counts, original_counts.sum(axis=0),
                                out=np.zeros_like(original_counts), where=original_counts.sum(axis=0)>0)
    for start in range(0, draws, 100):
        w = rng.multinomial(n, np.ones(n)/n, size=min(100, draws-start))
        estimates = []
        for s in active:
            den = w@counts[s]
            value = np.divide(w@sums[s], den, out=np.full_like(den, np.nan), where=den>0)
            estimates.append(np.where(stratum_weights[s]>0, value*stratum_weights[s], 0))
        output.append(sum(estimates))
    result = np.concatenate(output)
    return [np.nanquantile(result[:, i], [.025, .975]).tolist() if np.isfinite(result[:, i]).any() else None for i in range(m)]

def summarize(claims, jobs, observations, group_name, repetitions):
    ids = {r['claim_id'] for r in claims}
    selected = [j for j in jobs if j['claim_id'] in ids and j['repetition'] in repetitions]
    assigned = {(j['claim_id'], j['model'], j['condition'], j['repetition']) for j in selected}
    indexed = {(j['claim_id'], j['model'], j['condition'], j['repetition']): observations[j['job_id']] for j in selected}
    counts = collections.Counter(o['state'] for j in selected for o in [observations[j['job_id']]])
    metrics = []; names = []; details = {}
    for model in MODELS:
        for condition in 'ABC':
            values = []; correct = valid = total = 0
            for r in claims:
                os_ = [indexed[r['claim_id'], model, condition, rep] for rep in repetitions if (r['claim_id'], model, condition, rep) in assigned]
                total += len(os_); good = sum(o['state'] == 'valid' for o in os_); yes = sum(o['label'] == r['gold_label'] for o in os_)
                valid += good; correct += yes; values.append(yes/len(os_) if os_ else np.nan)
            name = model+'/'+condition+'/accuracy_ITT'; names.append(name); metrics.append(values)
            details[name] = {'correct': correct, 'assigned_calls': total, 'valid_calls': valid,
                             'accuracy_ITT': correct/total if total else None,
                             'accuracy_valid_only': correct/valid if valid else None,
                             'accuracy_identification_bounds': [correct/total, (correct+total-valid)/total] if total else None}
        for left, right in [('A', 'B'), ('B', 'C'), ('A', 'C')]:
            reg = []; rescue = []; deltas = []; complete = reg_n = rescue_n = robust_n = resistant_n = unknown = total = 0
            for r in claims:
                rs = []; ss = []; ds = []
                for rep in repetitions:
                    k = r['claim_id'], model, left, rep; q = r['claim_id'], model, right, rep
                    if k not in assigned or q not in assigned:
                        continue
                    a, b = indexed[k], indexed[q]; total += 1
                    ca = a['label'] == r['gold_label']; cb = b['label'] == r['gold_label']
                    ds.append(int(cb)-int(ca))
                    if a['state'] == b['state'] == 'valid':
                        x = ca and not cb; y = not ca and cb
                        reg_n += x; rescue_n += y; complete += 1; rs.append(float(x)); ss.append(float(y))
                        robust_n += ca and cb; resistant_n += not ca and not cb
                    else:
                        unknown += 1
                        # Known-rate denominator is all assigned pairs; unclassified contributes zero, not a guessed label.
                        rs.append(0.); ss.append(0.)
                reg.append(np.mean(rs) if rs else np.nan); rescue.append(np.mean(ss) if ss else np.nan); deltas.append(np.mean(ds) if ds else np.nan)
            name = model+'/'+left+right
            details[name] = {'assigned_pairs': total, 'valid_pairs': complete, 'regressions_known': reg_n,
                             'rescues_known': rescue_n, 'robust_known': robust_n, 'resistant_known': resistant_n, 'unclassified_pairs': unknown,
                             'regression_valid_pair_rate': reg_n/complete if complete else None,
                             'regression_identification_bounds': [reg_n/total, (reg_n+unknown)/total] if total else None,
                             'rescue_identification_bounds': [rescue_n/total, (rescue_n+unknown)/total] if total else None}
            for suffix, values in [('known_regression_fraction', reg), ('known_rescue_fraction', rescue), ('accuracy_difference_ITT', deltas)]:
                names.append(name+'/'+suffix); metrics.append(values)
    matrix = np.array(metrics).T if claims else np.empty((0, len(names)))
    cis = cluster_intervals(claims, matrix)
    estimates = {name: {'estimate': float(np.nanmean(matrix[:, i])) if np.isfinite(matrix[:, i]).any() else None, 'cluster_bootstrap_95': cis[i]} for i, name in enumerate(names)}
    return {'group': group_name, 'claims': len(claims), 'text_clusters': len({r['text_cluster'] for r in claims}),
            'repetitions': repetitions, 'status_counts': dict(counts), 'details': details, 'estimates': estimates,
            'uncertainty': '2000 joint text-cluster bootstrap draws; original observed label-stratum weights (50/50 for full and representative sample); repeats reduced within claim; fixed provider occasion. Identification bounds include all unclassified outputs.'}

def repeated_summary(claims, jobs, observations):
    index = {(j['claim_id'], j['model'], j['condition'], j['repetition']): observations[j['job_id']] for j in jobs}
    assigned = collections.defaultdict(list)
    for j in jobs:
        assigned[j['claim_id'], j['model'], j['condition']].append(j['repetition'])
    outcomes = []; metric_names = []; columns = []
    for model in MODELS:
        for condition in 'ABC':
            per_claim = []; complete_claims = incomplete = 0
            for r in claims:
                reps = sorted(assigned[r['claim_id'], model, condition]); os_ = [index[r['claim_id'], model, condition, rep] for rep in reps]
                good = len(reps) >= 2 and all(o['state'] == 'valid' for o in os_)
                if not good:
                    per_claim.append(np.nan); incomplete += 1
                    outcomes.append({'claim_id':r['claim_id'],'model':model,'condition':condition,
                                     'assigned_repetitions':len(reps),'valid_repetitions':sum(o['state']=='valid' for o in os_),
                                     'complete':False,'status_counts':dict(collections.Counter(o['state'] for o in os_))})
                    continue
                pairs = list(itertools.combinations(os_, 2)); disagree = sum(a['label'] != b['label'] for a, b in pairs)/len(pairs)
                per_claim.append(disagree); complete_claims += 1
                outcomes.append({'claim_id': r['claim_id'], 'model': model, 'condition': condition,
                     'assigned_repetitions': len(reps), 'valid_repetitions': len(os_), 'disagreement_fraction': disagree,
                     'distinct_labels': len({o['label'] for o in os_}), 'all_repeats_same': disagree == 0, 'complete':True})
            metric_names.append(model+'/'+condition+'/identical_prompt_disagreement'); columns.append(per_claim)
        for left, right in [('A', 'B'), ('B', 'C')]:
            excess = []
            for r in claims:
                reps = sorted(set(assigned[r['claim_id'], model, left]) & set(assigned[r['claim_id'], model, right]))
                a = [index[r['claim_id'], model, left, rep] for rep in reps]; b = [index[r['claim_id'], model, right, rep] for rep in reps]
                if len(reps) < 2 or not all(o['state'] == 'valid' for o in a+b):
                    excess.append(np.nan); continue
                changed = [x['label'] == r['gold_label'] and y['label'] != r['gold_label'] for x, y in zip(a, b)]
                rescued = [x['label'] != r['gold_label'] and y['label'] == r['gold_label'] for x, y in zip(a,b)]
                different = [x['label'] != y['label'] for x,y in zip(a,b)]
                baseline = [x['label'] == r['gold_label'] and y['label'] != r['gold_label'] for i, x in enumerate(a) for k, y in enumerate(a) if i != k]
                excess.append(float(np.mean(changed)-np.mean(baseline)))
                outcomes.append({'claim_id': r['claim_id'], 'model': model, 'comparison': left+right,
                   'assigned_repetitions': len(reps), 'regressions': sum(changed),
                   'rescues':sum(rescued),'rescue_fraction':float(np.mean(rescued)),
                   'label_change_fraction':float(np.mean(different)), 'changed_every_repetition':all(different),
                   'persistence_fraction': float(np.mean(changed)), 'regression_every_repetition': all(changed),
                   'same_left_prompt_directional_loss': float(np.mean(baseline))})
            metric_names.append(model+'/'+left+right+'/excess_loss_over_identical_left_prompt'); columns.append(excess)
    mat = np.array(columns).T if claims else np.empty((0, len(metric_names)))
    cis = cluster_intervals(claims, mat)
    return {'claims_assigned_repeats': len(claims), 'per_claim_outcomes': outcomes,
            'estimates': {name: {'complete_claims': int(np.isfinite(mat[:, i]).sum()),
                    'estimate_complete_claims': float(np.nanmean(mat[:, i])) if np.isfinite(mat[:, i]).any() else None,
                    'cluster_bootstrap_95': cis[i]} for i, name in enumerate(metric_names)},
            'limit': 'Complete-repeat summaries have selected denominators; incomplete claims are reported rather than imputed. Persistence across these repetitions is not an individual stable causal effect.'}

def analyze(plan_dir, run_dir, output):
    plan_dir = Path(plan_dir); run_dir = Path(run_dir); output = Path(output)
    if output.exists():
        raise ValueError('Choose a new analysis output directory; never overwrite reports')
    plan = load(plan_dir/'plan.json')
    if digest(plan_dir/'jobs.jsonl') != plan['jobs_sha256'] or digest(HERE/'prepared/inputs.jsonl') != plan['inputs_sha256']:
        raise ValueError('Plan digest mismatch')
    if load(run_dir/'run.json')['plan_sha256'] != digest(plan_dir/'plan.json'):
        raise ValueError('Run and plan identities differ')
    claims = read_inputs(); jobs = [json.loads(x) for x in (plan_dir/'jobs.jsonl').read_text(encoding='utf-8').splitlines()]
    observed = {j['job_id']: observation(run_dir, j) for j in jobs}
    assigned_ids = {j['claim_id'] for j in jobs}; claims = [r for r in claims if r['claim_id'] in assigned_ids]
    all_reps = sorted({j['repetition'] for j in jobs}); repeated_ids = {j['claim_id'] for j in jobs if j['repetition'] > 1}
    representative = [r for r in claims if r['claim_id'] in repeated_ids and (plan['design'].startswith('full') or r['repeat_representative'])]
    historical_repeat = [r for r in claims if r['claim_id'] in repeated_ids and r['historical_regression']]
    report = {'design': plan['design'], 'purpose': plan['purpose'], 'planned_jobs': len(jobs),
              'status_counts': dict(collections.Counter(o['state'] for o in observed.values())),
              'first_pass': summarize(claims, jobs, observed, 'all_assigned_claims_repetition_1', [1]),
              'repeat_representative': summarize(representative, jobs, observed, 'prospectively_random_repeat_records', all_reps),
              'repeat_variation': repeated_summary(representative, jobs, observed),
              'historical_cases_first_pass': summarize([r for r in claims if r['historical_regression']], jobs, observed, 'selected_historical_regression_cases', [1]),
              'historical_cases_repeated': repeated_summary(historical_repeat, jobs, observed),
              'historical_comparison_limit': 'New calls cannot recreate or identify changes in undocumented historical model snapshots; historical normalized labels are a separate recorded baseline.'}
    unfinished = sum(o['state'] in ('missing','pending_retry') for o in observed.values())
    report['completion_status'] = 'incomplete_planned_work' if unfinished else 'all_jobs_terminal_with_nonresponses' if any(o['state']!='valid' for o in observed.values()) else 'all_jobs_valid'
    report['interpretation_gate'] = 'Unfinished run: estimates are provisional and missing cells remain in identification bounds' if unfinished else 'Terminal outcomes include all invalids/nonresponses; report their denominators'
    comparisons = []
    first = {(j['claim_id'],j['model'],j['condition']):observed[j['job_id']] for j in jobs if j['repetition']==1}
    for m in MODELS:
        for new, old in [('A', 'claim_only'), ('C', 'claim_plus_evidence')]:
            pairs = [(r, first[r['claim_id'],m,new]) for r in claims if (r['claim_id'],m,new) in first]
            comparisons.append({'model': m, 'new_condition': new, 'historical_condition': old, 'assigned': len(pairs),
                     'valid_new': sum(o['state'] == 'valid' for r, o in pairs),
                     'same_label': sum(o['label'] == r['historical_labels'][m][old] for r, o in pairs)})
    report['historical_label_comparisons'] = comparisons
    accounting = {}
    for model in MODELS:
        events = [event for j in jobs if j['model']==model for event in observed[j['job_id']]['usage_events']]
        known = [event['usage'] for event in events if isinstance(event.get('usage'),dict)]
        accounting[model]={'receipts':len(events),'receipts_with_usage':len(known),
             'receipts_without_usage':len(events)-len(known),
             'reported_prompt_tokens':sum(u.get('prompt_tokens',0) for u in known),
             'reported_completion_tokens':sum(u.get('completion_tokens',0) for u in known),
             'reported_reasoning_tokens':sum((u.get('completion_tokens_details') or {}).get('reasoning_tokens',0) for u in known),
             'reported_cached_prompt_tokens':sum((u.get('prompt_tokens_details') or {}).get('cached_tokens',0) for u in known),
             'limit':'Only available reported usage; absent usage and uncertain transmissions do not imply zero billed usage.'}
    report['usage_accounting']=accounting
    write_new(output/'summary.json', report)
    with (output/'observations.csv').open('x', encoding='utf-8', newline='') as f:
        fields = ['job_id', 'claim_id', 'model', 'condition', 'repetition', 'state', 'label', 'attempt_directories', 'returned_model']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); writer.writeheader()
        for j in jobs:
            writer.writerow({**j, **observed[j['job_id']]})
    write_new(output/'provenance.json', {'analysis_source_sha256': digest(Path(__file__)),
            'plan_sha256': digest(plan_dir/'plan.json'), 'inputs_sha256': plan['inputs_sha256'],
            'raw_response_files': {str(p.relative_to(run_dir)): digest(p) for p in (run_dir/'attempts').rglob('response.bin')}})
    print(json.dumps({'output': str(output), 'purpose': plan['purpose'], 'status_counts': report['status_counts']}))
    return report

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--plan', type=Path, required=True); p.add_argument('--run-dir', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); analyze(args.plan, args.run_dir, args.output)
