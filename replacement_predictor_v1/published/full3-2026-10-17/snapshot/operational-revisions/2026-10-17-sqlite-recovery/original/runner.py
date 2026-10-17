"""Durable, bounded, synchronous OpenAI runner. CLI never infers without --live."""
import argparse
import contextlib
import http.client
import json
import os
import re
import sqlite3
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from common import (HERE, ENDPOINT, MODELS, RETURNED_MODELS, encoded, digest, load,
                    now, read_inputs, request, value_hash, verify_freeze, write_new)

MAX_ATTEMPTS = 3
TRANSIENT_HTTP = {502, 503, 504}
WORKER_ID = uuid.uuid4().hex

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Transport:
    def __init__(self):
        self.key = os.environ.get('OPENAI_API_KEY', '').strip()
        if not self.key:
            raise ValueError('OPENAI_API_KEY is unavailable; set it locally, never in this repository or chat')
        self.opener = urllib.request.build_opener(NoRedirect())

    def send(self, url, payload=None):
        body = encoded(payload) if payload is not None else None
        req = urllib.request.Request(url, data=body, headers={'Authorization': 'Bearer ' + self.key,
                    'Content-Type': 'application/json'}, method='POST' if body is not None else 'GET')
        try:
            response = self.opener.open(req, timeout=120)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            # Error responses can echo a supplied key. Redaction is explicit in metadata.
            safe = raw.replace(self.key.encode(), b'[REDACTED_CREDENTIAL]')
            safe = re.sub(rb'sk-[A-Za-z0-9_*.-]{8,}', b'[REDACTED_CREDENTIAL]', safe)
            headers = {k: v for k, v in response.headers.items()
                       if k.lower() not in ('set-cookie', 'authorization', 'proxy-authorization')}
            return response.status, safe, headers, safe != raw

    def __call__(self, payload):
        return self.send(ENDPOINT, payload)

def preflight(output=HERE/'availability'):
    result = {'checked_at_utc': now(), 'route': 'https://api.openai.com/v1',
              'generation_calls': 0, 'models': {}, 'status': 'unverified'}
    try:
        transport = Transport()
        for model in MODELS:
            status, raw, headers, redacted = transport.send('https://api.openai.com/v1/models/' + model)
            try:
                obj = json.loads(raw)
            except ValueError:
                obj = {'unparseable_response': True}
            result['models'][model] = {'http_status': status, 'response': obj,
                                      'request_id': headers.get('x-request-id'), 'credential_redacted': redacted}
        result['status'] = 'model_metadata_access_verified' if all(v['http_status'] == 200 and v['response'].get('id') == m for m, v in result['models'].items()) else 'access_check_failed'
    except (ValueError, OSError) as exc:
        result['status'] = 'credential_unavailable' if not os.environ.get('OPENAI_API_KEY') else 'transport_failed'
        result['error_type'] = type(exc).__name__
    path = Path(output)/(result['checked_at_utc'].replace(':', '-') + '.json')
    write_new(path, result)
    return result, path

@contextlib.contextmanager
def job_lock(path):
    """OS releases lock on process exit; never expires an active worker's lease."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open('a+b')
    if path.stat().st_size == 0:
        stream.write(b'0'); stream.flush()
    stream.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        stream.close()
        yield False
        return
    try:
        yield True
    finally:
        stream.seek(0)
        if os.name == 'nt':
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(stream, fcntl.LOCK_UN)
        stream.close()

class Store:
    def __init__(self, path, jobs=None, identity=None):
        self.path = Path(path); self.path.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path/'jobs.sqlite', timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE, payload TEXT NOT NULL,
          state TEXT NOT NULL DEFAULT 'pending', attempt INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);''')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if 'ready_at' not in {r[1] for r in self.db.execute('PRAGMA table_info(jobs)')}:
                self.db.execute('ALTER TABLE jobs ADD COLUMN ready_at REAL NOT NULL DEFAULT 0')
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise
        if identity is not None:
            if (self.path/'run.json').exists():
                if load(self.path/'run.json') != identity:
                    raise ValueError('Run identity differs; choose a new run directory')
            else:
                write_new(self.path/'run.json', identity)
        if jobs is not None:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                count = self.db.execute('SELECT count(*) FROM jobs').fetchone()[0]
                if not count:
                    self.db.executemany('INSERT INTO jobs(id,ordinal,payload) VALUES(?,?,?)',
                                        [(j['job_id'], j['order'], json.dumps(j)) for j in jobs])
                elif count != len(jobs):
                    raise ValueError('Job count differs from plan')
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK'); raise

    def halt(self, reason):
        self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)', ('halt_reason', reason))

    def claim(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if self.db.execute("SELECT value FROM meta WHERE key IN ('halt_reason','stop_requested')").fetchone():
                self.db.execute('COMMIT'); return None
            for row in self.db.execute("SELECT * FROM jobs WHERE state='pending' AND ready_at<=? ORDER BY ordinal LIMIT 64", (time.time(),)).fetchall():
                lock = job_lock(self.path/'locks'/(row['id']+'.lock'))
                if not lock.__enter__():
                    lock.__exit__(None, None, None); continue
                n = row['attempt'] + 1
                submitted = len(list((self.path/'attempts'/row['id']).glob('attempt-*/request.json')))
                if submitted >= MAX_ATTEMPTS:
                    self.db.execute("UPDATE jobs SET state='service_failure' WHERE id=?", (row['id'],))
                    lock.__exit__(None, None, None); continue
                self.db.execute("UPDATE jobs SET state='inflight',attempt=? WHERE id=?", (n, row['id']))
                self.db.execute('COMMIT')
                return json.loads(row['payload']), n, lock
            self.db.execute('COMMIT'); return None
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def state(self, jid, state):
        self.db.execute('UPDATE jobs SET state=? WHERE id=?', (state, jid))

    def counts(self):
        return {r[0]: r[1] for r in self.db.execute('SELECT state,count(*) FROM jobs GROUP BY state')}

def interpret(job, receipt, raw, attempt, request_count=None):
    """Raw files already exist before this function is called. No guessed labels."""
    status = receipt['http_status']; request_count = attempt if request_count is None else request_count
    try:
        obj = json.loads(raw)
    except (ValueError, UnicodeError):
        obj = {}
    if not isinstance(obj, dict):
        obj = {}
    result = {'job_id': job['job_id'], 'attempt': attempt, 'label': None,
              'request_attempt_count':request_count,
              'parsed_status': None, 'accepted': False, 'returned_model': obj.get('model'),
              'response_id': obj.get('id'), 'usage': obj.get('usage'),
              'system_fingerprint': obj.get('system_fingerprint'), 'service_tier': obj.get('service_tier'),
              'completed_at_utc': receipt['received_at_utc'], 'raw_sha256': receipt['raw_sha256']}
    error = obj.get('error') if isinstance(obj.get('error'), dict) else {}
    error_code = error.get('code') or error.get('type')
    if status != 200:
        transient = status in TRANSIENT_HTTP or (status == 429 and error_code == 'rate_limit_exceeded')
        result.update(parsed_status='service_error', error_code=error_code,
                      reason='transient_service_error' if transient else 'nonretryable_service_error',
                      state='pending' if transient and request_count < MAX_ATTEMPTS else 'service_failure')
        result['retry_after_seconds'] = 2**request_count if result['state'] == 'pending' else None
        return result
    if obj.get('model') not in RETURNED_MODELS[job['model']]:
        result.update(parsed_status='model_mismatch', state='model_mismatch', reason='unexpected_or_missing_returned_model')
        return result
    choices = obj.get('choices')
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        result.update(parsed_status='invalid_schema', state='invalid', reason='expected_exactly_one_choice')
        return result
    choice = choices[0]; msg = choice.get('message') or {}; msg = msg if isinstance(msg, dict) else {}
    content = msg.get('content'); finish = choice.get('finish_reason')
    result['finish_reason'] = finish
    if msg.get('refusal') or finish == 'content_filter':
        result.update(parsed_status='refused', state='invalid', reason='provider_refusal_or_filter')
    elif finish != 'stop':
        result.update(parsed_status='incomplete', state='invalid', reason='finish_reason_not_stop')
    elif isinstance(content, str) and content.strip() in ('Supported', 'Refuted'):
        result.update(label=content.strip(), parsed_status='exact_label', state='valid', accepted=True, reason='first_successful_http_response_exact_label')
    else:
        result.update(parsed_status='non_exact_label', state='invalid', reason='not_a_standalone_case_sensitive_label')
    return result

def finish(store, job, attempt, directory):
    saved_request = load(directory/'request.json')
    if saved_request['job']['job_id'] != job['job_id'] or value_hash(saved_request['body']) != job['request_sha256']:
        raise ValueError('Attempt request does not match its prepared job')
    receipt = load(directory/'receipt.json'); raw = (directory/'response.bin').read_bytes()
    if digest(directory/'response.bin') != receipt['raw_sha256']:
        raise ValueError('Response digest mismatch')
    submitted = len(list(directory.parent.glob('attempt-*/request.json')))
    result = interpret(job, receipt, raw, attempt, request_count=submitted)
    if (directory/'result.json').exists():
        if load(directory/'result.json') != result:
            raise ValueError('Existing interpretation differs')
    else:
        write_new(directory/'result.json', result)
    coordinator = getattr(store, 'coordinator', None)
    if coordinator:
        coordinator.record(job, attempt, receipt, result, saved_request)
    store.state(job['job_id'], result['state'])
    if result['state'] == 'model_mismatch':
        store.halt('Unexpected returned model; protocol revision required, no substitution')
    if receipt['http_status'] in (400, 401, 403, 404) or result.get('error_code') in ('insufficient_quota', 'billing_hard_limit_reached'):
        store.halt('Nonretryable request/access/quota failure; inspect retained error')
    return result

def run_attempt(store, claim, job, attempt, transport):
    directory = store.path/'attempts'/job['job_id']/f'attempt-{attempt:02d}'
    payload = request(claim, job['model'], job['condition'])
    if value_hash(payload) != job['request_sha256']:
        raise ValueError('Request differs from prepared job')
    write_new(directory/'request.json', {'job': job, 'attempt': attempt, 'body': payload,
                                        'started_at_utc': now(), 'endpoint': ENDPOINT,
                                        'worker_id': WORKER_ID, 'process_id': os.getpid()})
    try:
        status, raw, headers, redacted = transport(payload)
    except (OSError, TimeoutError, http.client.IncompleteRead) as exc:
        partial = getattr(exc, 'partial', b'')
        if partial:
            key = getattr(transport, 'key', '')
            if key:
                partial = partial.replace(key.encode(), b'[REDACTED_CREDENTIAL]')
            partial = re.sub(rb'sk-[A-Za-z0-9_*.-]{8,}', b'[REDACTED_CREDENTIAL]', partial)
            write_new(directory/'partial-response.bin', partial, binary=True)
        write_new(directory/'transport-error.json', {'error_type': type(exc).__name__, 'at_utc': now(),
                  'reason': 'May have reached provider; never automatically reissue an uncertain request'})
        store.state(job['job_id'], 'uncertain')
        if getattr(store, 'coordinator', None):
            store.coordinator.uncertain(job, attempt)
        return {'state': 'uncertain'}
    write_new(directory/'response.bin', raw, binary=True)
    write_new(directory/'receipt.json', {'http_status': status, 'headers': headers,
              'received_at_utc': now(), 'raw_sha256': digest(directory/'response.bin'),
              'credential_redacted': redacted})
    return finish(store, job, attempt, directory)

def recover(store):
    results = []
    for row in store.db.execute("SELECT * FROM jobs WHERE state='inflight'").fetchall():
        with job_lock(store.path/'locks'/(row['id']+'.lock')) as acquired:
            if not acquired:
                results.append({'job_id': row['id'], 'action': 'active_worker_skipped'}); continue
            job = json.loads(row['payload']); directory = store.path/'attempts'/row['id']/f"attempt-{row['attempt']:02d}"
            try:
                if (directory/'receipt.json').exists() and (directory/'response.bin').exists():
                    result = finish(store, job, row['attempt'], directory)
                    action = 'reconstructed_from_saved_response_' + result['state']
                elif not (directory/'request.json').exists():
                    store.state(row['id'], 'pending'); action = 'no_request_created_safe_to_schedule'
                    write_new(directory/'recovery.json', {'at_utc': now(), 'reason': action})
                else:
                    store.state(row['id'], 'uncertain'); action = 'request_exists_no_complete_receipt_do_not_reissue'
                    write_new(directory/'recovery.json', {'at_utc': now(), 'reason': action})
            except (OSError, ValueError):
                store.state(row['id'], 'uncertain'); action = 'damaged_artifact_retained_do_not_reissue'
            results.append({'job_id': row['id'], 'action': action})
    return results

def open_plan(plan_path, run_path):
    seal = verify_freeze(); plan_path = Path(plan_path).resolve(); run_path = Path(run_path).resolve()
    if not plan_path.is_relative_to(HERE/'prepared') or not run_path.is_relative_to(HERE/'runs'):
        raise ValueError('Plans must be under prepared/ and runs under replacement_predictor_v1/runs/')
    plan = load(plan_path/'plan.json')
    if digest(plan_path/'jobs.jsonl') != plan['jobs_sha256'] or digest(HERE/'prepared/inputs.jsonl') != plan['inputs_sha256']:
        raise ValueError('Plan/input hashes differ')
    if str((plan_path/'plan.json').relative_to(HERE)).replace('\\', '/') not in seal['files']:
        raise ValueError('Plan was not frozen')
    jobs = [json.loads(x) for x in (plan_path/'jobs.jsonl').read_text(encoding='utf-8').splitlines()]
    if len(jobs) != plan['jobs']:
        raise ValueError('Truncated job plan')
    bind_plan_to_run(HERE/'runs/registrations', digest(plan_path/'plan.json'), run_path)
    store = Store(run_path, jobs, {'plan_sha256': digest(plan_path/'plan.json'),
                        'protocol_freeze_sha256': digest(HERE/'protocol-freeze.json'), 'design': plan['design'],
                        'purpose': plan['purpose']})
    return store, {r['claim_id']: r for r in read_inputs()}

def bind_plan_to_run(registrations, plan_hash, run_path):
    """Prevent accidental duplicate executions of one plan in another directory."""
    path = Path(registrations)/(plan_hash+'.json')
    value = {'plan_sha256': plan_hash, 'run_directory': str(Path(run_path).resolve())}
    if not path.exists():
        try:
            write_new(path, value)
        except FileExistsError:
            pass
    if load(path) != value:
        raise ValueError('This plan is bound to another run directory; resume that directory')

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['preflight', 'run', 'recover', 'status'])
    parser.add_argument('--plan', type=Path, default=HERE/'prepared/full3')
    parser.add_argument('--run-dir', type=Path, default=HERE/'runs/full3')
    parser.add_argument('--live', action='store_true'); parser.add_argument('--max-attempts', type=int)
    args = parser.parse_args()
    if args.command in ('run','recover'):
        parser.error('Use launcher.py for coordinated execution/recovery; no inference was made')
    if args.command == 'preflight':
        result, path = preflight(); print(json.dumps({'status': result['status'], 'record': str(path), 'generation_calls': 0}))
        raise SystemExit(0 if result['status'] == 'model_metadata_access_verified' else 2)
    store, _ = open_plan(args.plan, args.run_dir)
    try:
        print(json.dumps(store.counts(), indent=2))
    finally:
        store.db.close()

if __name__ == '__main__':
    main()
