"""SQLite recovery revision of shared admission control; scientific rules unchanged."""
import contextlib
import email.utils
import json
import math
import random
import re
import time
from datetime import datetime
from common import MODELS, RATES, SETTINGS, now
import rate_policy
from coordination import Stopped


def seconds(value, clock):
    """Retry-After seconds/date and API duration strings, including compound durations."""
    if value is None:
        return None
    value = str(value).strip()
    try:
        result = float(value)
    except ValueError:
        pieces = re.findall(r'(\d+(?:\.\d+)?)(ms|s|m|h|d)', value)
        if pieces and ''.join(n+u for n, u in pieces) == value:
            result = sum(float(n)*{'ms': .001, 's': 1, 'm': 60, 'h': 3600, 'd': 86400}[u] for n, u in pieces)
        else:
            try:
                result = email.utils.parsedate_to_datetime(value).timestamp()-clock
            except (TypeError, ValueError, OverflowError):
                return None
    return max(0, result) if math.isfinite(result) else None


def reservation(payload):
    # UTF-8 bytes conservatively exceed the tokenizer estimate; retain output cap + framing.
    # Provider character-based admission estimates may differ; headers remain authoritative.
    return sum(len(m['content'].encode('utf-8')) for m in payload['messages']) + SETTINGS['max_completion_tokens'] + 32


def complete_usage(usage):
    return isinstance(usage,dict) and all(isinstance(usage.get(k),(int,float)) and math.isfinite(usage[k]) and usage[k]>=0 for k in ('prompt_tokens','completion_tokens'))


def validate_limits(config):
    assert set(config['header_groups']) == set(MODELS), 'Both model header groups are required'
    assert config['buckets'], 'At least one shared bucket is required'
    ids = set()
    for b in config['buckets']:
        assert b['id'] not in ids and b['models'] and set(b['models']) <= set(MODELS)
        ids.add(b['id'])
        assert b.get('rpm') and b.get('tpm'), 'Every bucket needs positive RPM and TPM'
        for key in ('rpm', 'tpm', 'rpd', 'tpd'):
            if b.get(key) is not None:
                assert isinstance(b[key], (int, float)) and math.isfinite(b[key]) and b[key] > 0
    assert any(set(b['models']) == set(MODELS) for b in config['buckets']), 'Shared ceiling required'
    for model in MODELS:
        assert any(b['models'] == [model] for b in config['buckets']), 'Model-specific ceiling required'
    if config.get('rate_policy'):
        rate_policy.validate(config['rate_policy'])


class Coordinator:
    def __init__(self, store, config, max_attempts=540000, clock=time.time, jitter=None, cancelled=None):
        validate_limits(config)
        self.store = store; self.db = store.db; self.config = config; self.max_attempts = max_attempts
        bounds = config.get('rate_policy',{}).get('jitter_seconds',[.01,.20])
        self.clock = clock; self.jitter = jitter or (lambda: random.uniform(*bounds))
        self.cancelled = cancelled or (lambda: False)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS op_attempts (
            job_id TEXT, attempt INTEGER, model TEXT, started REAL, ended REAL,
            reserved INTEGER, http_status INTEGER, state TEXT, usage TEXT,
            PRIMARY KEY(job_id,attempt));
          CREATE INDEX IF NOT EXISTS op_attempt_time ON op_attempts(started,model);
          CREATE INDEX IF NOT EXISTS op_open_attempts ON op_attempts(model,started) WHERE ended IS NULL;
          CREATE INDEX IF NOT EXISTS op_pending_order ON jobs(state,ordinal);
          CREATE TABLE IF NOT EXISTS op_gates (scope TEXT PRIMARY KEY, until_at REAL);
          CREATE TABLE IF NOT EXISTS op_headers (
            scope TEXT, metric TEXT, models TEXT, cap REAL, remaining REAL, reset_at REAL,
            PRIMARY KEY(scope,metric));
          CREATE TABLE IF NOT EXISTS op_rate_events (at REAL, event TEXT, state TEXT);
        ''')
        self.db.execute("INSERT OR IGNORE INTO meta SELECT 'op_admission_count',CAST(count(*) AS TEXT) FROM op_attempts")
        store.coordinator = self

    def policy_state(self, clock):
        row = self.db.execute("SELECT value FROM meta WHERE key='rate_policy_state'").fetchone()
        return json.loads(row[0]) if row else rate_policy.initial(self.config['rate_policy'],clock)

    def save_policy(self, state, event=None):
        state['effective_rpm'] = rate_policy.current(self.config['rate_policy'],state,self.clock())
        value = json.dumps(state,sort_keys=True)
        self.db.execute("INSERT OR REPLACE INTO meta VALUES('rate_policy_state',?)", (value,))
        if event:
            self.db.execute('INSERT INTO op_rate_events VALUES(?,?,?)',(self.clock(),event,value))

    def begin_session(self):
        if not self.config.get('rate_policy'):
            return
        with self.transaction():
            clock = self.clock(); state = self.policy_state(clock)
            state.update(epoch=clock, adaptive_rpm=min(state['adaptive_rpm'],rate_policy.supported(self.config['rate_policy'])[0]),
                         next_recovery=clock+self.config['rate_policy']['recovery_seconds'])
            self.save_policy(state,'session_start_ramp_reset_penalty_preserved')

    def effective_buckets(self, clock):
        if not self.config.get('rate_policy'):
            return self.config['buckets']
        state = self.policy_state(clock)
        rpm = rate_policy.current(self.config['rate_policy'],state,clock)
        if state.get('effective_rpm') != rpm:
            state['effective_rpm'] = rpm; self.save_policy(state,'effective_rate_changed')
        return rate_policy.buckets(self.config,state,clock)

    @contextlib.contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def stop_reason(self):
        row = self.db.execute("SELECT value FROM meta WHERE key IN ('halt_reason','stop_requested') ORDER BY key LIMIT 1").fetchone()
        return row[0] if row else None

    def stop(self, reason):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES('stop_requested',?)", (reason,))

    def gate(self, scope, until):
        self.db.execute('INSERT INTO op_gates VALUES(?,?) ON CONFLICT(scope) DO UPDATE SET until_at=max(until_at,excluded.until_at)', (scope, until))

    def known_wait(self, model, tokens, clock):
        wait = 0
        scopes = ['cooldown:shared', 'cooldown:'+model]
        buckets = [b for b in self.config['buckets'] if model in b['models']]
        scopes += ['pace:'+b['id'] for b in buckets]
        for scope in scopes:
            row = self.db.execute('SELECT until_at FROM op_gates WHERE scope=?', (scope,)).fetchone()
            if row:
                wait = max(wait, row[0]-clock)
        headers = self.db.execute('SELECT * FROM op_headers').fetchall()
        for h in headers:
            if model not in json.loads(h['models']):continue
            charge = 1 if h['metric']=='requests' else tokens
            if charge>h['cap']:
                raise ValueError('Request exceeds provider-exposed '+h['scope']+' '+h['metric']+' limit')
            pace_gate=self.db.execute('SELECT until_at FROM op_gates WHERE scope=?',('headerpace:'+h['scope']+':'+h['metric'],)).fetchone()
            if pace_gate:wait=max(wait,pace_gate[0]-clock)
            if charge>h['remaining'] and h['reset_at']>clock:
                wait=max(wait,h['reset_at']-clock+.001)
        return wait, headers

    def admission(self, job, attempt, tokens):
        """Atomically reserve shared/model budgets; return delay, or zero on admission."""
        model = job['model']
        # Blocked polls only read. All actual admissions still repeat every check
        # atomically under BEGIN IMMEDIATE; a stale read can only defer a poll.
        if (not self.cancelled() and not self.stop_reason()
                and not self.db.execute('SELECT 1 FROM op_attempts WHERE job_id=? AND attempt=?',(job['job_id'],attempt)).fetchone()
                and int(self.db.execute("SELECT value FROM meta WHERE key='op_admission_count'").fetchone()[0]) < self.max_attempts):
            wait, _ = self.known_wait(model,tokens,self.clock())
            if wait > 0:
                return wait
        with self.transaction():
            clock = self.clock()
            if self.cancelled():
                raise Stopped('Launcher interrupted, replaced or no longer alive')
            if self.stop_reason():
                raise Stopped(self.stop_reason())
            if self.db.execute('SELECT 1 FROM op_attempts WHERE job_id=? AND attempt=?', (job['job_id'], attempt)).fetchone():
                raise ValueError('Attempt already admitted; recovery must decide its disposition')
            if int(self.db.execute("SELECT value FROM meta WHERE key='op_admission_count'").fetchone()[0]) >= self.max_attempts:
                self.stop('Explicit cumulative operational attempt cap reached')
                return None
            wait, headers = self.known_wait(model,tokens,clock)
            # Most waiting workers can return without scanning the rolling attempt windows.
            if wait > 0:
                return wait
            buckets = [b for b in self.effective_buckets(clock) if model in b['models']]
            for b in buckets:
                marks = ','.join('?' for _ in b['models'])
                for key, window, charge in [('rpm', 60, 1), ('tpm', 60, tokens), ('rpd', 86400, 1), ('tpd', 86400, tokens)]:
                    cap = b.get(key)
                    if cap is None:
                        continue
                    if charge > cap:
                        raise ValueError('One request exceeds operational '+b['id']+' '+key+' ceiling')
                    rows = self.db.execute('SELECT started,reserved FROM op_attempts WHERE started>? AND model IN ('+marks+') ORDER BY started', (clock-window, *b['models'])).fetchall()
                    used = sum(1 if key.startswith('rp') else r['reserved'] for r in rows)
                    for r in rows:
                        if used+charge <= cap:
                            break
                        wait = max(wait, r['started']+window-clock+.001)
                        used -= 1 if key.startswith('rp') else r['reserved']
            for h in headers:
                if model not in json.loads(h['models']):
                    continue
                charge = 1 if h['metric'] == 'requests' else tokens
                if charge > h['cap']:
                    raise ValueError('Request exceeds provider-exposed '+h['scope']+' '+h['metric']+' limit')
                pace = self.db.execute('SELECT until_at FROM op_gates WHERE scope=?', ('headerpace:'+h['scope']+':'+h['metric'],)).fetchone()
                if pace:
                    wait = max(wait,pace[0]-clock)
                members = json.loads(h['models']); marks = ','.join('?' for _ in members)
                recent = self.db.execute('SELECT started,reserved FROM op_attempts WHERE started>? AND model IN ('+marks+') ORDER BY started', (clock-60,*members)).fetchall()
                used = sum(1 if h['metric']=='requests' else r['reserved'] for r in recent)
                for r in recent:
                    if used+charge <= h['cap']:
                        break
                    wait = max(wait,r['started']+60-clock+.001)
                    used -= 1 if h['metric']=='requests' else r['reserved']
                if h['reset_at'] <= clock:
                    self.db.execute('UPDATE op_headers SET remaining=cap,reset_at=? WHERE scope=? AND metric=?', (clock+60, h['scope'], h['metric']))
                    remaining = h['cap']
                else:
                    remaining = h['remaining']
                if charge > remaining:
                    wait = max(wait, h['reset_at']-clock+.001)
            if wait > 0:
                return wait
            self.db.execute('INSERT INTO op_attempts(job_id,attempt,model,started,reserved) VALUES(?,?,?,?,?)', (job['job_id'], attempt, model, clock, tokens))
            self.db.execute("UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='op_admission_count'")
            for b in buckets:
                pace = rate_policy.pace(b,tokens)
                self.gate('pace:'+b['id'], clock+pace+self.jitter())
            for h in headers:
                if model in json.loads(h['models']):
                    charge = 1 if h['metric']=='requests' else tokens
                    self.db.execute('UPDATE op_headers SET remaining=remaining-? WHERE scope=? AND metric=?', (charge, h['scope'], h['metric']))
                    self.gate('headerpace:'+h['scope']+':'+h['metric'],clock+60*charge/h['cap']+self.jitter())
            return 0

    def acquire(self, job, attempt, tokens):
        while True:
            wait = self.admission(job, attempt, tokens)
            if wait is None:
                raise Stopped(self.stop_reason())
            if not wait:
                return
            time.sleep(min(wait+self.jitter(), .5))

    def record(self, job, attempt, receipt, result, saved_request):
        """Idempotent feedback before a retry becomes visible to any worker."""
        model = job['model']; headers = {k.lower():v for k,v in receipt['headers'].items()}
        with self.transaction():
            clock = self.clock()
            row = self.db.execute('SELECT * FROM op_attempts WHERE job_id=? AND attempt=?', (job['job_id'], attempt)).fetchone()
            if not row:
                # A pre-revision response recovered offline still supplies cooldown/halt metadata.
                started = datetime.fromisoformat(saved_request['started_at_utc']).timestamp()
                self.db.execute('INSERT INTO op_attempts(job_id,attempt,model,started,reserved) VALUES(?,?,?,?,?)', (job['job_id'], attempt, model, started, reservation(saved_request['body'])))
                self.db.execute("UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='op_admission_count'")
                row = self.db.execute('SELECT * FROM op_attempts WHERE job_id=? AND attempt=?', (job['job_id'], attempt)).fetchone()
            if row['ended'] is not None:
                return
            self.db.execute('UPDATE op_attempts SET ended=?,http_status=?,state=?,usage=? WHERE job_id=? AND attempt=?', (clock, receipt['http_status'], result['state'], json.dumps(result.get('usage')), job['job_id'], attempt))
            if self.config.get('rate_policy'):
                state = self.policy_state(clock)
                if (receipt['http_status']==429 and result.get('error_code')=='rate_limit_exceeded') or receipt['http_status']==503:
                    rate_policy.throttle(self.config['rate_policy'],state,clock)
                    self.save_policy(state,'throttle_shared_rate_reduced')
                elif receipt['http_status']==200:
                    before = dict(state); rate_policy.success(self.config['rate_policy'],state,clock)
                    if state != before:
                        self.save_policy(state,'successful_traffic_gradual_recovery')
            if result['state']=='model_mismatch' or receipt['http_status'] in (400,401,403,404,422) or (receipt['http_status']==429 and result.get('reason')=='nonretryable_service_error') or result.get('error_code') in ('insufficient_quota','billing_hard_limit_reached'):
                self.store.halt('Request/access/quota/model failure; inspect retained error; no automatic reset')
            group = self.config['header_groups'][model]
            groups = [('model:'+group, [m for m,g in self.config['header_groups'].items() if g==group], '')]
            groups += [(scope, list(MODELS), scope+'-') for scope in ('project','organization')]
            reset_delays = []
            for scope, models, prefix in groups:
                for metric in ('requests','tokens'):
                    suffix = prefix+metric
                    reset = seconds(headers.get('x-ratelimit-reset-'+suffix), clock)
                    if reset is not None:
                        reset_delays.append(reset)
                    try:
                        cap = float(headers['x-ratelimit-limit-'+suffix])
                        remain = float(headers['x-ratelimit-remaining-'+suffix])
                    except (KeyError, ValueError, TypeError):
                        continue
                    if not math.isfinite(cap) or not math.isfinite(remain) or cap <= 0 or remain < 0:
                        continue
                    # Stale/out-of-order replies may lower a budget, never restore it prematurely.
                    marks = ','.join('?' for _ in models)
                    outstanding = self.db.execute(
                        'SELECT reserved FROM op_attempts WHERE model IN ('+marks+') AND ended IS NULL AND (started<? OR started IS NULL) AND NOT (job_id=? AND attempt=?) '
                        'UNION ALL SELECT reserved FROM op_attempts WHERE model IN ('+marks+') AND started>=? AND NOT (job_id=? AND attempt=?)',
                        (*models,row['started'],job['job_id'],attempt,*models,row['started'],job['job_id'],attempt)).fetchall()
                    remain = max(0, remain-sum(1 if metric=='requests' else r['reserved'] for r in outstanding))
                    deadline = clock+(reset if reset is not None else 60)+.05
                    old = self.db.execute('SELECT * FROM op_headers WHERE scope=? AND metric=?', (scope,metric)).fetchone()
                    if old and old['reset_at'] > clock:
                        remain = min(remain, old['remaining']); deadline = max(deadline,old['reset_at']); cap = min(cap,old['cap'])
                    self.db.execute('INSERT OR REPLACE INTO op_headers VALUES(?,?,?,?,?,?)', (scope,metric,json.dumps(models),cap,min(cap,remain),deadline))
                    charge = 1 if metric=='requests' else row['reserved']
                    self.gate('headerpace:'+scope+':'+metric,row['started']+60*charge/cap+self.jitter())
            delay = seconds(headers.get('retry-after'), clock)
            if receipt['http_status'] in (429,502,503,504) or delay is not None:
                delay = max([delay or 0, result.get('retry_after_seconds') or 0, *reset_delays])
                self.gate('cooldown:shared', clock+delay+self.jitter())
            if result['state']=='pending':
                ready = clock+(result.get('retry_after_seconds') or 0)+self.jitter()
                self.db.execute('UPDATE jobs SET ready_at=max(ready_at,?) WHERE id=?', (ready,job['job_id']))

    def uncertain(self, job, attempt):
        self.db.execute("UPDATE op_attempts SET ended=?,state='uncertain' WHERE job_id=? AND attempt=? AND ended IS NULL", (self.clock(),job['job_id'],attempt))

    def progress(self):
        clock = self.clock(); counts = self.store.counts(); total = sum(counts.values())
        completed = sum(n for state,n in counts.items() if state not in ('pending','inflight'))
        successes = self.db.execute('SELECT count(*) FROM op_attempts WHERE http_status=200 AND ended>?', (clock-60,)).fetchone()[0]
        terminal = self.db.execute("SELECT count(*) FROM op_attempts WHERE ended>? AND state NOT IN ('pending')", (clock-60,)).fetchone()[0]
        first = self.db.execute('SELECT min(started) FROM op_attempts').fetchone()[0]
        window = min(60,max(1,clock-first)) if first else 60
        rate = successes*60/window; terminal_rate = terminal/window
        usage = {}; missing = 0; known_cost = 0
        for row in self.db.execute('SELECT model,usage FROM op_attempts WHERE ended IS NOT NULL'):
            u = json.loads(row['usage'] or 'null')
            if not complete_usage(u):
                missing += 1; continue
            m = usage.setdefault(row['model'], {'prompt_tokens':0,'completion_tokens':0,'receipts_with_usage':0})
            m['receipts_with_usage'] += 1
            for k in ('prompt_tokens','completion_tokens'):
                m[k] += u.get(k,0)
            known_cost += (u.get('prompt_tokens',0)*RATES[row['model']]['input']+u.get('completion_tokens',0)*RATES[row['model']]['output'])/1e6
        halted = self.stop_reason()
        policy = self.config.get('rate_policy')
        throughput = {'target_rpm':policy['ramp_rpm'][-1], 'effective_rpm':rate_policy.current(policy,self.policy_state(clock),clock),
                      'capacity_verified':policy['capacity_evidence']['verified']} if policy else None
        return {'at_utc':now(),'planned_jobs':total,'completed_jobs':completed,'failures':sum(n for s,n in counts.items() if s not in ('pending','inflight','valid')),
                'throughput_policy':throughput,
                'states':counts,'successful_http_calls_per_minute':rate,'rate_window_seconds':window,
                'available_usage':usage,'finished_attempts_without_usage':missing,
                'known_usage_cost_usd_at_frozen_standard_rates':known_cost,
                'eta_seconds':(total-completed)/terminal_rate if terminal_rate and not halted else None,
                'eta_basis':'Recent terminal-job rate; includes failures, provisional; null when stopped/no completions',
                'stop_reason':halted,'provider_budgets':[dict(r) for r in self.db.execute('SELECT * FROM op_headers')]}
