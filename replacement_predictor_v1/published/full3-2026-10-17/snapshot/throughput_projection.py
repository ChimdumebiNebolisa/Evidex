"""Offline twenty-worker scheduling projection. Never constructs an API transport."""
import argparse
import collections
import copy
import heapq
import json
import random
from pathlib import Path
from common import HERE, digest, load, now, read_inputs, request, verify_freeze, write_new
from coordination import reservation, validate_limits
import rate_policy
import smoke_projection


def simulate(jobs, charges, config, latency, workers=20, overhead=0, startup=0, seed=20261016):
    """Model the limiter's pacing, rolling budgets, jitter and .5-second wait cap."""
    rng=random.Random(seed); p=config['rate_policy']; state=rate_policy.initial(p,0)
    low,high=p['jitter_seconds']; gates={}; windows={}; used={}
    heap=[(0,i,None) for i in range(min(workers,len(jobs)))]; heapq.heapify(heap)
    assigned=0; starts=[]; completions=[]
    while heap:
        clock,worker,index=heapq.heappop(heap)
        if index is None:
            if assigned>=len(jobs):continue
            index=assigned;assigned+=1
        job=jobs[index]; model=job['model']; tokens=charges[index]
        buckets=[b for b in rate_policy.buckets(config,state,clock) if model in b['models']]
        wait=max([0,*[gates.get(b['id'],0)-clock for b in buckets]])
        gate_wait=wait
        if wait<=0:
            for b in buckets:
                for label,window,rpm,tpm in [('minute',60,b['rpm'],b['tpm']),('day',86400,b.get('rpd'),b.get('tpd'))]:
                    if rpm is None and tpm is None:continue
                    key=b['id'],label; history=windows.setdefault(key,collections.deque()); total=used.get(key,0)
                    while history and history[0][0]<=clock-window:
                        total-=history.popleft()[1]
                    used[key]=total; count=len(history)
                    if (rpm is not None and count+1>rpm) or (tpm is not None and total+tokens>tpm):
                        for timestamp,charge in history:
                            total-=charge;count-=1
                            wait=max(wait,timestamp+window-clock+.001)
                            if (rpm is None or count+1<=rpm) and (tpm is None or total+tokens<=tpm):break
        if wait>0:
            # Whole .5-second sleeps under an unchanged pacing gate have no state effect.
            # Collapse them offline; retain the actual final jittered wakeup.
            if gate_wait>=.5:
                whole=int(gate_wait/.5);clock+=whole*.5;wait=gate_wait-whole*.5
                wake=clock if wait<1e-10 else clock+min(wait+rng.uniform(low,high),.5)
            else:
                wake=clock+min(wait+rng.uniform(low,high),.5)
            heapq.heappush(heap,(wake,worker,index)); continue
        starts.append(clock)
        for b in buckets:
            gates[b['id']]=clock+rate_policy.pace(b,tokens)+rng.uniform(low,high)+(overhead if b['id']=='shared' else 0)
            for label,window,rpm,tpm in [('minute',60,b['rpm'],b['tpm']),('day',86400,b.get('rpd'),b.get('tpd'))]:
                if rpm is None and tpm is None:continue
                key=b['id'],label;windows.setdefault(key,collections.deque()).append((clock,tokens));used[key]=used.get(key,0)+tokens
        duration=latency[model] if isinstance(latency,dict) else latency
        done=clock+duration;completions.append(done)
        heapq.heappush(heap,(done,worker,None))
    elapsed=max(completions,default=0)+startup
    return {'seconds':elapsed,'hours':elapsed/3600,'admission_window_seconds':starts[-1]-starts[0] if len(starts)>1 else 0,
            'mean_admission_interval_seconds':(starts[-1]-starts[0])/(len(starts)-1) if len(starts)>1 else 0,
            'calls':len(starts)}


def project(limits_path, benchmark_path, output):
    verify_freeze(); config=load(limits_path);validate_limits(config); benchmark=load(benchmark_path)
    assert benchmark['synthetic_only'] and benchmark['generation_calls']==0
    # Reuse the existing frozen cost/usage calculation; replace only its old timing approximation.
    old=smoke_projection.project(HERE/'runs/smoke',config)
    if old['status']!='PROVISIONAL_TWELVE_CALL_PROJECTION':raise ValueError('A complete preserved smoke is required')
    rows={r['claim_id']:r for r in read_inputs()}
    jobs=[json.loads(x) for x in (HERE/'prepared/full3/jobs.jsonl').read_text(encoding='utf-8').splitlines()]
    cache={};charges=[]
    for job in jobs:
        key=job['claim_id'],job['condition']
        if key not in cache:cache[key]=reservation(request(rows[key[0]],job['model'],key[1]))
        charges.append(cache[key])
    # Calibrate incremental local overhead against a matched virtual benchmark rather than
    # adding its measured jitter/wakeup overhead twice.
    conditional=copy.deepcopy(config)
    conditional['rate_policy']['capacity_evidence']={'verified':True,'source':'CONDITIONAL PROJECTION ASSUMPTION ONLY',
        'shared_rpm':600,'shared_tpm':600000}
    steady=copy.deepcopy(conditional);steady['rate_policy']['ramp_rpm']=[600]
    fixture_jobs=[{'model':('gpt-5.4','gpt-5.4-mini')[i%2]} for i in range(120)]
    virtual=simulate(fixture_jobs,[200]*120,steady,.15)
    extra=max(0,benchmark['mean_admission_interval_seconds']-virtual['mean_admission_interval_seconds'])
    latency={m:v['mean_latency_seconds'] for m,v in old['per_model'].items()}
    startup=benchmark['startup_to_first_admission_seconds']
    target=simulate(jobs,charges,conditional,latency,overhead=extra,startup=startup)
    slower=simulate(jobs,charges,conditional,{m:v*2 for m,v in latency.items()},overhead=extra,startup=startup)
    active=target if config['rate_policy']['capacity_evidence']['verified'] else simulate(jobs,charges,config,latency,overhead=extra,startup=startup)
    total=sum(charges);rolling=sum(charges[:600]);maximum=rolling
    for i in range(600,len(charges)):
        rolling+=charges[i]-charges[i-600];maximum=max(maximum,rolling)
    report={'at_utc':now(),'generation_calls':0,'workers':20,'full3_jobs':len(jobs),
        'config_sha256':digest(limits_path),'benchmark_sha256':digest(benchmark_path),
        'capacity_verified':config['rate_policy']['capacity_evidence']['verified'],
        'effective_supported_rpm':rate_policy.supported(config['rate_policy'])[0],
        'active_configuration_projection':active,'conditional_600_rpm_projection':target,
        'conditional_600_rpm_with_double_smoke_mean_latency':slower,
        'conditional_600_rpm_plus_10_percent_attempt_time_hours':target['hours']*1.1,
        'full3_cost_usd':old['projected_full3_usd_at_frozen_standard_rates'],
        'full3_cost_usd_with_10_percent_more_attempts':old['projected_full3_usd_at_frozen_standard_rates']*1.1,
        'known_smoke_cost_usd':old['observed_smoke_usd_at_frozen_standard_rates'],
        'smoke_mean_latency_seconds':latency,'jitter_seconds':config['rate_policy']['jitter_seconds'],
        'mock_benchmark':benchmark,'matched_virtual_benchmark':virtual,'calibrated_extra_interval_seconds':extra,
        'token_reservations':{'total':total,'mean':total/len(charges),'max_per_call':max(charges),'max_600_consecutive_planned_calls':maximum},
        'assumptions':['600-RPM scenario requires verified shared/project capacity of at least 600 RPM and 600,000 TPM; it is not a finding about account entitlement',
            'No new throttles, external account traffic, missing responses or interrupts; stable advertised model limits',
            'Local queue/worker overhead calibrated from 120 mocked calls on 20 processes with 180,000-row queue and ledger',
            'Measured smoke means cover two claims; long-tail/provider latency, concurrent-account traffic and retries can lengthen execution',
            'Simulation reuses the live rate-policy and pace functions and .5-second polling/jitter rules; it is not a paid throughput benchmark',
            'No additional funds or inference authorization assumed; $5 is insufficient for the roughly $30 full3 projection']}
    write_new(output,report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limits',type=Path,required=True);p.add_argument('--benchmark',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=project(a.limits,a.benchmark,a.output)
    print(json.dumps({k:v for k,v in r.items() if k not in ('mock_benchmark','assumptions')},indent=2))
