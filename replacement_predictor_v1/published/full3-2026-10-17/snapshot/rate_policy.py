"""Operational ramp and adaptive ceiling; shared by the limiter and offline projection."""
import math


def validate(policy):
    levels = policy['ramp_rpm']
    assert levels and levels == sorted(set(levels)) and 0 < levels[0] <= levels[-1] <= 600
    assert policy['step_seconds'] >= 1 and policy['recovery_seconds'] >= 1
    assert 0 < policy['minimum_rpm'] <= levels[0]
    assert 0 < policy['throttle_factor'] < 1 and policy['recovery_step_rpm'] > 0
    lo, hi = policy['jitter_seconds']
    assert math.isfinite(lo) and math.isfinite(hi) and 0 < lo <= hi
    evidence = policy['capacity_evidence']
    if evidence['verified']:
        assert evidence['source'] and evidence['shared_rpm'] > 0 and evidence['shared_tpm'] > 0
    assert policy['unverified_shared_rpm'] > 0 and policy['unverified_shared_tpm'] > 0


def supported(policy):
    evidence = policy['capacity_evidence']
    if evidence['verified']:
        return min(policy['ramp_rpm'][-1], evidence['shared_rpm']), evidence['shared_tpm']
    return min(policy['ramp_rpm'][-1], policy['unverified_shared_rpm']), policy['unverified_shared_tpm']


def initial(policy, clock):
    cap, _ = supported(policy)
    return {'epoch':clock, 'adaptive_rpm':cap, 'next_recovery':clock+policy['recovery_seconds']}


def current(policy, state, clock):
    cap, _ = supported(policy)
    phase = min(len(policy['ramp_rpm'])-1, int(max(0,clock-state['epoch'])/policy['step_seconds']))
    return min(cap, policy['ramp_rpm'][phase], state['adaptive_rpm'])


def throttle(policy, state, clock):
    state['adaptive_rpm'] = max(min(policy['minimum_rpm'],supported(policy)[0]), current(policy,state,clock)*policy['throttle_factor'])
    state['next_recovery'] = clock+policy['recovery_seconds']


def success(policy, state, clock):
    if clock >= state['next_recovery'] and state['adaptive_rpm'] < supported(policy)[0]:
        state['adaptive_rpm'] = min(supported(policy)[0], state['adaptive_rpm']+policy['recovery_step_rpm'])
        state['next_recovery'] = clock+policy['recovery_seconds']


def buckets(config, state, clock):
    policy = config['rate_policy']; rpm = current(policy,state,clock)
    ratio = rpm/policy['ramp_rpm'][-1]; _, shared_tpm = supported(policy)
    return [{**b, 'rpm':min(b['rpm'],rpm), 'tpm':min(b['tpm']*ratio,shared_tpm)} for b in config['buckets']]


def pace(bucket, tokens):
    return max(60/bucket['rpm'],60*tokens/bucket['tpm'],
               86400/bucket['rpd'] if bucket.get('rpd') else 0,
               86400*tokens/bucket['tpd'] if bucket.get('tpd') else 0)
