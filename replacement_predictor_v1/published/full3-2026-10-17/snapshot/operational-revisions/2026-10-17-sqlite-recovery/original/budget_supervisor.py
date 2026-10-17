"""Operational $35 forecast guard around the unchanged twenty-worker launcher."""
import argparse
import collections
import json
import os
import sys
import threading
import time
import _thread
from pathlib import Path
import common
import coordination
import launcher
import runner

HERE = common.HERE
REVISION = HERE/'operational-revisions/2026-10-16-budget35'
LIMITS = HERE/'operational-revisions/2026-10-16-operator600/limits-operator600.json'
CEILING = 35.0
INTERVAL = 2.0


def verify():
    common.verify_freeze()
    selected = common.load(LIMITS.parent/'revision.json')
    for group in ('files','unchanged_source_hashes','previous_seals'):
        for name,expected in selected[group].items():
            if common.digest(HERE/name) != expected:
                raise ValueError('Operator revision verification failed: '+name)
    record = common.load(REVISION/'revision.json')
    for group in ('files','previous_seals','unchanged_source_hashes'):
        for name,expected in record[group].items():
            if common.digest(HERE/name) != expected:
                raise ValueError('Budget revision verification failed: '+name)


def cost(model, prompt, completion):
    rates = common.RATES[model]
    return (prompt*rates['input']+completion*rates['output'])/1e6


class Projection:
    def __init__(self, features, priors):
        # Local prompt estimates use the already-frozen o200k_base + seven framing tokens.
        self.features = features; self.priors = priors
        self.totals = {m:{'calls':0,'prompt':0} for m in common.MODELS}
        for model,estimate in features.values():
            self.totals[model]['calls'] += 1; self.totals[model]['prompt'] += estimate

    @classmethod
    def prepared(cls):
        sys.path.insert(0,str(HERE/'.deps'))
        os.environ.setdefault('TIKTOKEN_CACHE_DIR',str(HERE/'.deps/token-cache'))
        import tiktoken
        enc = tiktoken.get_encoding('o200k_base')
        claims = {r['claim_id']:r for r in common.read_inputs()}; cache = {}; features = {}
        jobs = [json.loads(line) for line in (HERE/'prepared/full3/jobs.jsonl').read_text(encoding='utf-8').splitlines()]
        for job in jobs:
            key = job['claim_id'],job['condition']
            if key not in cache:
                payload = common.request(claims[key[0]],job['model'],key[1])
                cache[key] = sum(len(enc.encode(m['content'],disallowed_special=())) for m in payload['messages'])+7
            features[job['job_id']] = job['model'],cache[key]
        priors = {m:{'calls':0,'prompt':0,'completion':0,'estimate':0} for m in common.MODELS}
        for path in sorted((HERE/'runs/smoke/attempts').glob('*/attempt-*/result.json')):
            saved = common.load(path.parent/'request.json'); result = common.load(path)
            model = saved['body']['model']; usage = result['usage']; prior = priors[model]
            if not coordination.complete_usage(usage):
                raise ValueError('Preserved smoke usage missing')
            prior['calls'] += 1; prior['prompt'] += usage['prompt_tokens']; prior['completion'] += usage['completion_tokens']
            prior['estimate'] += sum(len(enc.encode(m['content'],disallowed_special=())) for m in saved['body']['messages'])+7
        if any(p['calls']!=6 for p in priors.values()):
            raise ValueError('Expected preserved twelve-call smoke')
        return cls(features,priors)

    def snapshot(self, db, clock=None):
        clock = time.time() if clock is None else clock
        # A consistent WAL read; never hold a writer lock while computing forecasts.
        db.execute('BEGIN')
        try:
            rows = [dict(r) for r in db.execute('SELECT * FROM op_attempts')]
            states = dict(db.execute('SELECT state,count(*) FROM jobs GROUP BY state'))
            terminal = {r[0] for r in db.execute("SELECT id FROM jobs WHERE state NOT IN ('pending','inflight')")}
            stops = list(db.execute("SELECT value FROM meta WHERE key IN ('halt_reason','stop_requested')"))
            db.execute('COMMIT')
        except BaseException:
            db.execute('ROLLBACK'); raise
        samples = {m:dict(p) for m,p in self.priors.items()}
        usages = {m:{'prompt_tokens':0,'completion_tokens':0} for m in common.MODELS}
        ended = collections.Counter(); touched = collections.defaultdict(set)
        known = 0.; reserved = 0.; unknown = 0; active = set(); recent = 0
        for row in rows:
            model = row['model']; key = row['job_id']; expected_model,estimate = self.features[key]
            if model != expected_model:raise ValueError('Ledger model mismatch')
            usage = json.loads(row['usage'] or 'null')
            if row['ended'] is not None:
                ended[model] += 1; touched[model].add(key)
            else:
                active.add(key)
            if row['state'] not in (None,'pending'):
                terminal.add(key)
            if coordination.complete_usage(usage):
                known += cost(model,usage['prompt_tokens'],usage['completion_tokens'])
                for metric in ('prompt_tokens','completion_tokens'):usages[model][metric] += usage[metric]
                if row['http_status']==200:
                    sample = samples[model]; sample['calls'] += 1; sample['estimate'] += estimate
                    sample['prompt'] += usage['prompt_tokens']; sample['completion'] += usage['completion_tokens']
            else:
                # Missing usage and in-flight/uncertain transmissions are never zero cost.
                reserved += cost(model,row['reserved'],common.SETTINGS['max_completion_tokens'])
                unknown += 1
            if row['ended'] and row['ended']>clock-60 and row['http_status']==200:recent += 1
        remaining = {m:dict(t) for m,t in self.totals.items()}
        for key in terminal|active:
            model,estimate = self.features[key]
            remaining[model]['calls'] -= 1; remaining[model]['prompt'] -= estimate
        future = 0.; details = {}
        for model,sample in samples.items():
            multiplier = (self.priors[model]['calls']+ended[model])/(self.priors[model]['calls']+len(touched[model]))
            input_ratio = sample['prompt']/sample['estimate']; mean_output = sample['completion']/sample['calls']
            prediction = cost(model,remaining[model]['prompt']*input_ratio,remaining[model]['calls']*mean_output)*multiplier
            future += prediction
            details[model] = {'usage':usages[model],'forecast_samples_including_smoke':sample['calls'],
                'actual_to_local_prompt_ratio':input_ratio,'mean_completion_tokens':mean_output,
                'attempt_multiplier':multiplier,'remaining_projected_usd':prediction}
        complete = sum(n for s,n in states.items() if s not in ('pending','inflight'))
        return {'at_utc':common.now(),'completed_jobs':complete,'states':states,
            'failures':sum(n for s,n in states.items() if s not in ('pending','inflight','valid')),
            'admissions':len(rows),'successful_http_calls_last_60_seconds':recent,
            'known_usage_cost_usd':known,'unreported_and_inflight_reservation_usd':reserved,
            'attempts_without_reported_usage':unknown,'remaining_forecast_usd':future,
            'projected_total_cost_usd':known+reserved+future,'pause_above_usd':CEILING,
            'per_model':details,'stop_reason':stops[0][0] if stops else None,
            'forecast_basis':'Known usage plus reserved unknown/inflight cost plus remaining prepared input scaled by smoke+live usage and observed completion means/retry multiplier; no cache discount; not an invoice'}


def enforce(db, snapshot, ceiling=CEILING):
    if snapshot['projected_total_cost_usd'] > ceiling:
        reason = 'Budget forecast exceeds $'+str(ceiling)+'; admissions paused; drain recording; review before resume'
        # Preserve the first existing operational stop and every sticky halt.
        db.execute("INSERT OR IGNORE INTO meta VALUES('stop_requested',?)",(reason,))
        return reason
    return snapshot.get('stop_reason')


def watch(run_dir, projection, directory, done, prior_owner=None):
    store = None
    try:
        store = runner.Store(run_dir); milestone = False; last_log = 0
        # Wait until the existing launcher has cleared an explicit resume stop and
        # taken ownership; never mistake the previous stop for this session's halt.
        while not done.is_set():
            owner = store.db.execute("SELECT value FROM meta WHERE key='op_owner'").fetchone()
            if owner and owner[0]!=prior_owner:break
            done.wait(.05)
        while not done.is_set():
            snapshot = projection.snapshot(store.db)
            reason = enforce(store.db,snapshot)
            if reason:snapshot['stop_reason'] = reason
            crossed = snapshot['completed_jobs']>=1000 and not milestone
            if crossed:
                common.write_new(directory/'first-1000-completed.json',snapshot); milestone = True
            if crossed or reason or time.monotonic()-last_log>=10:
                common.write_new(directory/('snapshot-'+str(time.time_ns())+'.json'),snapshot)
                last_log = time.monotonic()
            if reason:break
            done.wait(INTERVAL)
    except BaseException as exc:
        try:
            if store:
                store.db.execute("INSERT OR IGNORE INTO meta VALUES('stop_requested',?)",('Cost monitor failed; admissions paused; inspect supervisor artifacts',))
            common.write_new(directory/'monitor-error.json',{'at_utc':common.now(),'error_type':type(exc).__name__})
        finally:
            _thread.interrupt_main()  # Existing launcher SIGINT handler drains workers, including if SQLite failed.
    finally:
        if store:store.db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true'); parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    if not args.live:parser.error('--live is required; no model requests made')
    verify(); config = common.load(LIMITS); coordination.validate_limits(config)
    projection = Projection.prepared()
    store,_ = runner.open_plan(HERE/'prepared/full3',HERE/'runs/full3')
    try:
        with runner.job_lock(store.path/'supervisor.lock') as owned:
            if not owned:raise ValueError('A cost supervisor already owns full3')
            launcher.bind_revision(store); coordination.Coordinator(store,config)
            before = projection.snapshot(store.db)
            if before['projected_total_cost_usd']>CEILING:
                enforce(store.db,before); raise ValueError('Initial budget forecast exceeds $35; no inference')
            if store.db.execute("SELECT 1 FROM meta WHERE key='halt_reason'").fetchone():
                raise ValueError('Sticky defined halt remains; inspect before resuming')
            if before['stop_reason'] and not args.resume:raise ValueError('Prior stop requires inspection and --resume')
            access,path = runner.preflight()
            if access['status']!='model_metadata_access_verified':
                raise ValueError('Account metadata access unavailable; no inference; see '+str(path))
            directory = store.path/'supervision'/common.now().replace(':','-')
            common.write_new(directory/'start.json',{'at_utc':common.now(),'budget_ceiling_usd':CEILING,
                'monitor_interval_seconds':INTERVAL,'workers':20,'limits_sha256':common.digest(LIMITS),
                'supervisor_revision_sha256':common.digest(REVISION/'revision.json'),
                'operator_revision_sha256':common.digest(LIMITS.parent/'revision.json'),
                'user_authorized_full3':True,'user_reports_additional_funding':True,'initial_forecast':before})
            done = threading.Event()
            owner = store.db.execute("SELECT value FROM meta WHERE key='op_owner'").fetchone()
            monitor = threading.Thread(target=watch,args=(store.path,projection,directory,done,owner[0] if owner else None),daemon=True)
            monitor.start()
            try:
                launcher.launch(store,config,540000,resume=args.resume)
            finally:
                done.set(); monitor.join(timeout=30)
                final = projection.snapshot(store.db); enforce(store.db,final)
                if final['completed_jobs']>=1000 and not (directory/'first-1000-completed.json').exists():
                    common.write_new(directory/'first-1000-completed.json',final)
                common.write_new(directory/'finished.json',final)
                print(json.dumps(final),flush=True)
    finally:
        store.db.close()


if __name__=='__main__':
    main()
