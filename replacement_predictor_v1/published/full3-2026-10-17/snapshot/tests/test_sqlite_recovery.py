"""Offline reproductions and concurrency checks for SQLite operational recovery."""
import json
import sqlite3
import tempfile
import threading
import time
import unittest
import multiprocessing
import collections
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import common
import coordination
import runner
import sqlite_runtime
import sqlite_coordination
from unittest.mock import patch
from test_operations import fixture,config,response


def stress_actor(path, counter, sent):
    import sqlite_supervisor  # Same bindings/import path used by spawned live workers.
    store=runner.Store(path)
    cfg=common.load(common.HERE/'operational-revisions/2026-10-16-operator600/limits-operator600.json')
    c=coordination.Coordinator(store,cfg)
    inputs={r['claim_id']:r for r in common.read_inputs()}
    try:
        while not c.stop_reason():
            item=store.claim()
            if item is None:break
            job,n,lock=item
            try:
                c.acquire(job,n,coordination.reservation(common.request(inputs[job['claim_id']],job['model'],job['condition'])))
                def transport(payload):
                    with counter.get_lock():counter.value+=1
                    sent.set();time.sleep(.03)
                    return 200,response(job['model']),{'x-ratelimit-limit-requests':'5000',
                        'x-ratelimit-remaining-requests':'4990','x-ratelimit-reset-requests':'12ms',
                        'x-ratelimit-limit-tokens':str(1000000 if job['model']=='gpt-5.4' else 2000000),
                        'x-ratelimit-remaining-tokens':'900000','x-ratelimit-reset-tokens':'1s'},False
                runner.run_attempt(store,inputs[job['claim_id']],job,n,transport)
            except coordination.Stopped:break
            finally:lock.__exit__(None,None,None)
    finally:store.db.close()


def stress_blocker(path,sent):
    if not sent.wait(20):raise RuntimeError('No mock response to contend with')
    ready=threading.Event();hold_writer(path,ready,1)


def hold_writer(path, ready, seconds):
    db=sqlite3.connect(Path(path)/'jobs.sqlite',isolation_level=None)
    try:
        db.execute('BEGIN IMMEDIATE');ready.set();time.sleep(seconds);db.execute('COMMIT')
    finally:db.close()


class SQLiteRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)
        self.rows,self.jobs=fixture(2)
        self.connection_patch=patch.object(runner,'sqlite3',sqlite_runtime);self.connection_patch.start()
        self.store=runner.Store(self.path,self.jobs,{'synthetic_only':True})
        self.c=sqlite_coordination.Coordinator(self.store,config(),clock=lambda:1000,jitter=lambda:.001)
        self.store.db.execute('PRAGMA busy_timeout=20')

    def tearDown(self):
        self.store.db.close();self.connection_patch.stop();self.temp.cleanup()

    def test_blocked_poll_reads_budget_without_competing_for_writer(self):
        self.c.gate('pace:shared',1001)
        ready=threading.Event();thread=threading.Thread(target=hold_writer,args=(self.path,ready,.25))
        thread.start();self.assertTrue(ready.wait(2))
        try:
            start=time.monotonic()
            wait=self.c.admission({'job_id':'poll','model':'gpt-5.4'},1,100)
            self.assertGreater(wait,0)
            self.assertLess(time.monotonic()-start,.15)
        finally:thread.join()

    def test_response_database_retry_never_repeats_transport(self):
        job,n,lock=self.store.claim();calls=[]
        try:
            self.c.acquire(job,n,200)
            ready=threading.Event();thread=threading.Thread(target=hold_writer,args=(self.path,ready,.25))
            thread.start();self.assertTrue(ready.wait(2))
            try:
                def transport(payload):
                    calls.append(payload)
                    return 200,response(job['model']),{},False
                result=runner.run_attempt(self.store,self.rows[0],job,n,transport)
            finally:thread.join()
            self.assertEqual(result['state'],'valid');self.assertEqual(len(calls),1)
            self.assertEqual(len(list(self.path.rglob('request.json'))),1)
            self.assertEqual(len(list(self.path.rglob('response.bin'))),1)
            self.assertEqual(self.store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],1)
        finally:lock.__exit__(None,None,None)

    def test_database_retry_is_bounded_and_recovery_does_not_resend(self):
        self.store.db.retry_seconds=.06;self.store.db.retry_attempts=2
        job,n,lock=self.store.claim();calls=[]
        try:
            self.c.acquire(job,n,200)
            ready=threading.Event();thread=threading.Thread(target=hold_writer,args=(self.path,ready,.3))
            thread.start();self.assertTrue(ready.wait(2))
            try:
                def transport(payload):
                    calls.append(payload);return 200,response(job['model']),{},False
                with self.assertRaises(sqlite3.OperationalError):
                    runner.run_attempt(self.store,self.rows[0],job,n,transport)
            finally:thread.join()
        finally:lock.__exit__(None,None,None)
        before={str(p):common.digest(p) for p in self.path.rglob('*') if p.name in ('request.json','response.bin','receipt.json','result.json')}
        actions=runner.recover(self.store)
        self.assertEqual(actions[0]['action'],'reconstructed_from_saved_response_valid')
        self.assertEqual(len(calls),1)
        self.assertEqual(before,{str(Path(p)):common.digest(p) for p in before})
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],1)

    def test_unrelated_sql_error_is_not_retried(self):
        before=self.store.db.stats['busy_retries']
        with self.assertRaises(sqlite3.OperationalError):self.store.db.execute('SELECT no_such_column FROM jobs')
        self.assertEqual(self.store.db.stats['busy_retries'],before)

    def test_read_only_polls_still_obey_longer_header_reset_and_duplicate_checks(self):
        self.c.gate('pace:shared',1001)
        self.store.db.execute('INSERT INTO op_headers VALUES(?,?,?,?,?,?)',
            ('project','tokens',json.dumps(list(common.MODELS)),1000,0,1012))
        self.assertGreaterEqual(self.c.admission({'job_id':'poll','model':'gpt-5.4-mini'},1,100),12)
        self.store.db.execute('INSERT INTO op_attempts(job_id,attempt,model,started,reserved) VALUES(?,?,?,?,?)',('duplicate',1,'gpt-5.4',1000,100))
        with self.assertRaises(ValueError):self.c.admission({'job_id':'duplicate','model':'gpt-5.4'},1,100)

    def test_outstanding_union_matches_original_query(self):
        rows=[('a',1,'gpt-5.4',900,None,100),('b',1,'gpt-5.4',1001,1002,200),
              ('c',1,'gpt-5.4-mini',1002,None,300),('d',1,'gpt-5.4',None,None,400)]
        self.store.db.executemany('INSERT INTO op_attempts(job_id,attempt,model,started,ended,reserved) VALUES(?,?,?,?,?,?)',rows)
        old='SELECT reserved FROM op_attempts WHERE model IN (?,?) AND (ended IS NULL OR started>=?) AND NOT (job_id=? AND attempt=?)'
        new='SELECT reserved FROM op_attempts WHERE model IN (?,?) AND ended IS NULL AND (started<? OR started IS NULL) AND NOT (job_id=? AND attempt=?) UNION ALL SELECT reserved FROM op_attempts WHERE model IN (?,?) AND started>=? AND NOT (job_id=? AND attempt=?)'
        args=(*common.MODELS,1000,'a',1)
        self.assertEqual(collections.Counter(r[0] for r in self.store.db.execute(old,args)),
                         collections.Counter(r[0] for r in self.store.db.execute(new,args+args)))

    def test_twenty_process_populated_queue_with_monitor_contention_interrupt_and_resume(self):
        import budget_supervisor as guard
        import sqlite_supervisor
        backup=common.HERE/'operational-revisions/2026-10-17-sqlite-recovery/backup/jobs.sqlite'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d);source=sqlite3.connect(backup.as_uri()+'?mode=ro',uri=True);target=sqlite3.connect(path/'jobs.sqlite')
            source.backup(target);source.close();target.close()
            store=runner.Store(path);cfg=common.load(sqlite_supervisor.budget_supervisor.LIMITS)
            c=coordination.Coordinator(store,cfg)
            selected=[r[0] for r in store.db.execute("SELECT id FROM jobs WHERE state='pending' ORDER BY ordinal LIMIT 120")]
            store.db.execute("UPDATE jobs SET state='synthetic_not_selected' WHERE state='pending'")
            store.db.executemany("UPDATE jobs SET state='pending' WHERE id=?",[(x,) for x in selected])
            store.db.execute("DELETE FROM meta WHERE key IN ('stop_requested','op_owner')")
            prior=store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0];self.assertEqual(prior,41446)
            projection=guard.Projection.prepared();ctx=multiprocessing.get_context('spawn');counter=ctx.Value('i',0);sent=ctx.Event()
            def phase(label,interrupt):
                store.db.execute("INSERT OR REPLACE INTO meta VALUES('op_owner',?)",(label,))
                c.begin_session();state=c.policy_state(time.time());state['epoch']=time.time()-360;c.save_policy(state)
                done=threading.Event();monitor=threading.Thread(target=guard.watch,args=(path,projection,path/label,done))
                monitor.start();processes=[ctx.Process(target=stress_actor,args=(str(path),counter,sent)) for _ in range(20)]
                blocker=ctx.Process(target=stress_blocker,args=(str(path),sent)) if interrupt else None
                if blocker:blocker.start()
                try:
                    for process in processes:process.start()
                    deadline=time.monotonic()+90
                    while any(p.is_alive() for p in processes) and time.monotonic()<deadline:
                        if interrupt and store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0]>=prior+20:
                            c.stop('Synthetic interruption; preserve admitted responses')
                        time.sleep(.05)
                    self.assertFalse(any(p.is_alive() for p in processes))
                    for process in processes:process.join();self.assertEqual(process.exitcode,0)
                    if blocker:blocker.join(timeout=5);self.assertEqual(blocker.exitcode,0)
                finally:
                    done.set();monitor.join(timeout=15)
                    for process in processes+([blocker] if blocker else []):
                        if process.is_alive():process.terminate();process.join()
                runner.recover(store)
                self.assertFalse((path/label/'monitor-error.json').exists())
            try:
                phase('synthetic-phase1',True)
                saved={str(p):common.digest(p) for p in path.rglob('response.bin')};self.assertTrue(saved)
                self.assertLess(counter.value,120)
                store.db.execute("DELETE FROM meta WHERE key='stop_requested'")
                phase('synthetic-phase2',False)
                self.assertEqual(counter.value,120)
                self.assertEqual(store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],prior+120)
                self.assertEqual(len(list(path.rglob('request.json'))),120)
                self.assertEqual(len(list(path.rglob('response.bin'))),120)
                self.assertTrue(all(common.digest(p)==h for p,h in saved.items()))
                self.assertTrue(all(store.db.execute('SELECT state FROM jobs WHERE id=?',(j,)).fetchone()[0]=='valid' for j in selected))
                self.assertEqual(store.db.execute('SELECT max(n) FROM (SELECT count(*) n FROM op_attempts GROUP BY job_id)').fetchone()[0],1)
                known=projection.snapshot(store.db)['known_usage_cost_usd'];self.assertGreater(known,6.86945225)
                events=[json.loads(line) for p in (path/'sqlite-runtime').glob('*.jsonl') for line in p.read_text().splitlines()]
                self.assertTrue(any(r['event']=='database_busy' for r in events))
                common.write_new(common.HERE/'test-artifacts'/('sqlite-recovery-'+common.now().replace(':','-'))/'stress.json',
                    {'synthetic_only':True,'generation_calls':0,'workers':20,'queue_rows':180000,'prior_ledger_rows':prior,
                     'mock_calls':counter.value,'responses':120,'duplicate_admissions':0,'saved_responses_survived':True,
                     'monitoring_and_writer_contention_exercised':True,'new_database_retry_events':sum(r['event']=='database_busy' for r in events),
                     'max_recorded_transaction_seconds':max((r.get('max_transaction_seconds',0) for r in events),default=0),
                     'prior_cumulative_spending_preserved':True})
            finally:store.db.close()
