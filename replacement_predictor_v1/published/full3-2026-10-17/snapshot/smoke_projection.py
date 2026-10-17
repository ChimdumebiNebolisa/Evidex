"""Operational projection from recorded smoke latency/usage/limits; no inference or analysis changes."""
import argparse
import collections
import json
from pathlib import Path
from common import HERE, MODELS, RATES, digest, load, now, read_inputs, request, verify_freeze, write_new
from coordination import complete_usage, reservation, validate_limits
from launcher import DEFAULT_LIMITS, WORKERS


def project(smoke_dir, limits):
    verify_freeze(); validate_limits(limits)
    smoke_dir = Path(smoke_dir)
    smoke_plan = HERE/'prepared/smoke'
    if load(smoke_dir/'run.json')['plan_sha256'] != digest(smoke_plan/'plan.json'):
        raise ValueError('Use the registered twelve-call smoke run')
    expected = {j['job_id']:j for j in [json.loads(x) for x in (smoke_plan/'jobs.jsonl').read_text(encoding='utf-8').splitlines()]}
    rows = {r['claim_id']:r for r in read_inputs()}; observations = collections.defaultdict(list)
    unresolved = []; headers_seen = []; usage_missing = 0
    for jid, job in expected.items():
        directories = sorted((smoke_dir/'attempts'/jid).glob('attempt-*'))
        valid = False
        for directory in directories:
            if not (directory/'request.json').exists():
                continue
            if not (directory/'receipt.json').exists() or not (directory/'response.bin').exists():
                unresolved.append(jid); continue
            saved = load(directory/'request.json'); receipt = load(directory/'receipt.json')
            if digest(directory/'response.bin') != receipt['raw_sha256']:
                raise ValueError('Smoke response digest mismatch')
            if saved['body'] != request(rows[job['claim_id']],job['model'],job['condition']):
                raise ValueError('Smoke request differs from prepared messages/settings')
            import runner
            from datetime import datetime
            result = runner.interpret(job,receipt,(directory/'response.bin').read_bytes(),saved['attempt'])
            valid = valid or result['state']=='valid'
            u = result.get('usage')
            if not complete_usage(u):
                usage_missing += 1
            elapsed = (datetime.fromisoformat(receipt['received_at_utc'])-datetime.fromisoformat(saved['started_at_utc'])).total_seconds()
            observations[job['model']].append({'latency':elapsed,'usage':u,'status':receipt['http_status']})
            headers_seen.append({'model':job['model'],'headers':{k.lower():v for k,v in receipt['headers'].items() if k.lower().startswith('x-ratelimit-') or k.lower()=='retry-after'}})
        if not valid:
            unresolved.append(jid)
    if unresolved or usage_missing:
        return {'at_utc':now(),'status':'INCOMPLETE_OR_MISSING_USAGE','unresolved_jobs':sorted(set(unresolved)),
                'receipts_without_usage':usage_missing,'projection':None,
                'reason':'Do not rerun terminal invalid/uncertain jobs; review retained records. Missing usage is not zero cost.'}
    local = load(HERE/'COST_ESTIMATE.json')
    baseline = {d['design']:d for d in local['designs']}
    per_model = {}; work_seconds = 0; reserve_sums = collections.Counter(); pacing = collections.Counter()
    jobs = [json.loads(x) for x in (HERE/'prepared/full3/jobs.jsonl').read_text(encoding='utf-8').splitlines()]
    token_cache = {}
    for job in jobs:
        key = job['claim_id'],job['condition']
        if key not in token_cache:
            token_cache[key] = reservation(request(rows[key[0]],job['model'],key[1]))
        factor = len(observations[job['model']])/6
        tokens = token_cache[key]; reserve_sums[job['model']] += tokens*factor
        for b in limits['buckets']:
            if job['model'] in b['models']:
                pacing[b['id']] += (max(60/b['rpm'],60*tokens/b['tpm'],86400/b['rpd'] if b.get('rpd') else 0,86400*tokens/b['tpd'] if b.get('tpd') else 0)+.105)*factor
    observed_cost = 0; full_cost = 0
    for model in MODELS:
        events = observations[model]; n = len(events); success = [e for e in events if e['status']==200]
        mean = sum(e['latency'] for e in events)/n
        prompt = sum(e['usage'].get('prompt_tokens',0) for e in events)
        output = sum(e['usage'].get('completion_tokens',0) for e in events)
        # Scale inputs by the full/smoke prepared prompt-token ratio, output by observed per-job rate.
        projected_prompt = prompt*baseline['full3']['models'][model]['input_tokens_estimate']/baseline['smoke']['models'][model]['input_tokens_estimate']
        projected_output = output/6*90000
        cost = (projected_prompt*RATES[model]['input']+projected_output*RATES[model]['output'])/1e6
        observed_cost += (prompt*RATES[model]['input']+output*RATES[model]['output'])/1e6; full_cost += cost
        work_seconds += mean*(n/6)*90000
        per_model[model] = {'smoke_attempts':n,'successful_http_calls':len(success),'mean_latency_seconds':mean,
             'maximum_latency_seconds':max(e['latency'] for e in events),'reported_prompt_tokens':prompt,
             'reported_completion_tokens':output,'projected_full3_usd_at_frozen_standard_rates':cost,
             'reserved_tokens_full3':reserve_sums[model]}
    # Exposed provider budgets can lower runtime throughput beneath configured ceilings.
    header_bounds = []
    for event in headers_seen:
        h = event['headers']
        for prefix in ('project-', 'organization-'):
            for metric, demand in [('requests',sum(90000*len(observations[m])/6 for m in MODELS)),('tokens',sum(reserve_sums.values()))]:
                try:
                    cap = float(h['x-ratelimit-limit-'+prefix+metric])
                    if cap > 0:
                        header_bounds.append(60*demand/cap)
                except (KeyError, ValueError):
                    pass
    # Per-model headers are also enforced by the launcher; include the tightest observed limits.
    for model in MODELS:
        for event in [e for e in headers_seen if e['model']==model]:
            h = event['headers']
            for metric,demand in [('requests',90000),('tokens',reserve_sums[model])]:
                try:
                    cap = float(h['x-ratelimit-limit-'+metric])
                    if cap > 0:
                        group = limits['header_groups'][model]
                        members = [m for m,g in limits['header_groups'].items() if g==group]
                        demand = sum(90000*len(observations[m])/6 for m in members) if metric=='requests' else sum(reserve_sums[m] for m in members)
                        header_bounds.append(60*demand/cap)
                except (KeyError,ValueError):
                    pass
    runtime = max([work_seconds/WORKERS,*pacing.values(),*header_bounds])
    return {'at_utc':now(),'status':'PROVISIONAL_TWELVE_CALL_PROJECTION','workers':WORKERS,
            'per_model':per_model,'observed_smoke_usd_at_frozen_standard_rates':observed_cost,
            'projected_full3_usd_at_frozen_standard_rates':full_cost,'projected_runtime_hours':runtime/3600,
            'configured_bucket_pacing_hours':{k:v/3600 for k,v in pacing.items()},
            'measured_latency_work_hours_at_20_workers':work_seconds/WORKERS/3600,
            'provider_header_minimum_hours':max(header_bounds,default=0)/3600,
            'limits_used':limits,'observed_rate_limit_headers':headers_seen,
            'limits':'Small smoke is not a steady-state benchmark. Input scaling assumes local token estimates transfer; retry rate, changing limits, shared traffic, cooldowns and long tails can increase runtime/cost. No cache discount; frozen standard rates, recheck current prices before launch.'}


if __name__=='__main__':
    p = argparse.ArgumentParser(); p.add_argument('--smoke-run',type=Path,default=HERE/'runs/smoke')
    p.add_argument('--limits',type=Path,default=DEFAULT_LIMITS); p.add_argument('--output',type=Path,required=True)
    args = p.parse_args(); report = project(args.smoke_run,load(args.limits)); write_new(args.output,report)
    print(json.dumps(report,indent=2))
