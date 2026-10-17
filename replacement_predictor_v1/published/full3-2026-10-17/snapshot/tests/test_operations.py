import concurrent.futures
import contextlib
import io
import json
import multiprocessing
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import common
import coordination
import launcher
import runner
import smoke_projection


def config(rpm=1000000,tpm=100000000):
    return {'header_groups':{m:m for m in common.MODELS},'buckets':[
        {'id':'shared','models':list(common.MODELS),'rpm':rpm,'tpm':tpm},
        *[{'id':m,'models':[m],'rpm':rpm,'tpm':tpm} for m in common.MODELS]]}


def fixture(n=1):
    rows = [{'claim_id':'1','claim_text':'Test claim','gold_evidence':'Test evidence','gold_label':'Supported'}]
    jobs = [{'job_id':str(i),'claim_id':'1','model':common.MODELS[i%2],'condition':('A','B','C')[i%3],
             'repetition':i//6+1,'order':i,
             'request_sha256':common.value_hash(common.request(rows[0],common.MODELS[i%2],('A','B','C')[i%3]))} for i in range(n)]
    return rows,jobs


def response(model='gpt-5.4',label='Supported'):
    return common.encoded({'id':'fake','model':model,'choices':[{'finish_reason':'stop','message':{'content':label}}],
                           'usage':{'prompt_tokens':30,'completion_tokens':2}})


def contend(args):
    path,index = args; store = runner.Store(path)
    try:
        c = coordination.Coordinator(store,config(rpm=60),clock=lambda:1000,jitter=lambda:.01)
        try:
            return c.admission({'job_id':'contend-'+str(index),'model':'gpt-5.4'},1,100)==0
        except coordination.Stopped:
            return False
    finally:
        store.db.close()


class OperationalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.path = Path(self.temp.name)
        self.rows,self.jobs = fixture(1); self.store = runner.Store(self.path,self.jobs,{'test':True})
        self.time = 1000.
        self.c = coordination.Coordinator(self.store,config(),clock=lambda:self.time,jitter=lambda:.025)

    def tearDown(self):
        self.store.db.close(); self.temp.cleanup()

    def admit(self, jid,model='gpt-5.4',tokens=100):
        return self.c.admission({'job_id':jid,'model':model},1,tokens)

    def send(self,status=200,raw=None,headers=None):
        job,attempt,lock = self.store.claim()
        try:
            self.c.acquire(job,attempt,coordination.reservation(common.request(self.rows[0],job['model'],job['condition'])))
            return runner.run_attempt(self.store,self.rows[0],job,attempt,lambda _: (status,raw or response(job['model']),headers or {},False))
        finally:
            lock.__exit__(None,None,None)

    def test_shared_rpm_and_independent_model_limits(self):
        self.c.config = config(rpm=2)
        self.assertEqual(self.admit('a'),0)
        self.assertGreater(self.admit('b','gpt-5.4-mini'),29)
        self.time += 30.1; self.assertEqual(self.admit('b','gpt-5.4-mini'),0)
        self.time += 29.95; self.assertGreater(self.admit('c'),0)
        self.time += .1; self.assertEqual(self.admit('c'),0)

    def test_tokens_are_shared_and_never_refunded(self):
        self.c.config = config(tpm=1000)
        self.assertEqual(self.admit('a',tokens=400),0)
        self.time += 24.1; self.assertEqual(self.admit('b','gpt-5.4-mini',400),0)
        self.time += 24.1; self.assertGreater(self.admit('c',tokens=400),11)
        self.assertEqual(self.store.db.execute('SELECT sum(reserved) FROM op_attempts').fetchone()[0],800)

    def test_daily_limits_persist_across_connections(self):
        self.c.config['buckets'][0]['rpd'] = 1
        self.assertEqual(self.admit('a'),0); self.time += 61
        other = runner.Store(self.path)
        try:
            c = coordination.Coordinator(other,self.c.config,clock=lambda:self.time,jitter=lambda:.025)
            self.assertGreater(c.admission({'job_id':'b','model':'gpt-5.4-mini'},1,100),86000)
        finally:
            other.db.close()

    def test_model_only_bucket_does_not_block_other_model(self):
        self.c.config['buckets'][1]['rpm']=1
        self.assertEqual(self.admit('a'),0); self.time += 1
        self.assertGreater(self.admit('b'),58)
        self.assertEqual(self.admit('c','gpt-5.4-mini'),0)

    def test_cooldown_is_shared_and_retry_ready_before_requeue(self):
        result = self.send(429,common.encoded({'error':{'code':'rate_limit_exceeded'}}),
                           {'Retry-After':'17','X-RateLimit-Reset-Tokens':'1m2s'})
        self.assertEqual(result['state'],'pending')
        self.assertGreater(self.admit('other','gpt-5.4-mini'),62)
        self.assertGreater(self.store.db.execute('SELECT ready_at FROM jobs').fetchone()[0],1002)

    def test_retry_after_date_and_duration_parsing(self):
        self.assertEqual(coordination.seconds('1h2m3.5s',0),3723.5)
        self.assertEqual(coordination.seconds('250ms',0),.25)
        self.assertEqual(coordination.seconds('Thu, 01 Jan 1970 00:00:20 GMT',10),10)
        self.assertIsNone(coordination.seconds('invalid',0))
        self.assertIsNone(coordination.seconds('nan',0))

    def test_project_tokens_apply_to_both_models_and_reset(self):
        self.send(headers={'x-ratelimit-limit-project-tokens':'1000',
                          'x-ratelimit-remaining-project-tokens':'0','x-ratelimit-reset-project-tokens':'10s'})
        self.assertGreater(self.admit('other','gpt-5.4-mini'),10)
        self.time += 61; self.assertEqual(self.admit('other','gpt-5.4-mini'),0)

    def test_model_group_headers_share_request_budget(self):
        self.c.config['header_groups'] = {m:'family' for m in common.MODELS}
        self.send(headers={'x-ratelimit-limit-requests':'100','x-ratelimit-remaining-requests':'0','x-ratelimit-reset-requests':'5s'})
        self.assertGreater(self.admit('other','gpt-5.4-mini'),5)

    def test_exposed_lower_rpm_still_limits_after_short_reset(self):
        self.send(headers={'x-ratelimit-limit-requests':'1','x-ratelimit-remaining-requests':'1','x-ratelimit-reset-requests':'1s'})
        self.time += 2
        self.assertGreater(self.admit('another'),57)

    def test_out_of_order_feedback_cannot_restore_budget(self):
        self.admit('one'); self.time += 1; self.admit('two'); self.time += 1
        receipt = {'http_status':200,'headers':{'x-ratelimit-limit-requests':'10','x-ratelimit-remaining-requests':'1','x-ratelimit-reset-requests':'10s'}}
        result = {'state':'valid','usage':{}}
        self.c.record({'job_id':'two','model':'gpt-5.4'},1,receipt,result,{})
        self.c.record({'job_id':'one','model':'gpt-5.4'},1,{**receipt,'headers':{**receipt['headers'],'x-ratelimit-remaining-requests':'9'}},result,{})
        self.assertLessEqual(self.store.db.execute("SELECT remaining FROM op_headers WHERE metric='requests'").fetchone()[0],0)

    def test_auth_quota_parameter_model_halts_stop_claimed_workers(self):
        for status,raw in [(401,common.encoded({'error':{'code':'invalid_api_key'}})),
                           (429,common.encoded({'error':{'code':'insufficient_quota'}})),
                           (400,common.encoded({'error':{'code':'invalid_parameter'}})),
                           (422,common.encoded({'error':{'code':'invalid_parameter'}})),
                           (200,response(model='wrong'))]:
            with self.subTest(status=status):
                # Use isolated queues so sticky halts cannot be cleared during the test.
                with tempfile.TemporaryDirectory() as d:
                    s = runner.Store(d,self.jobs,{'test':True}); c = coordination.Coordinator(s,config(),jitter=lambda:.01)
                    job,n,lock = s.claim()
                    try:
                        c.acquire(job,n,200); runner.run_attempt(s,self.rows[0],job,n,lambda _: (status,raw,{},False))
                        with self.assertRaises(coordination.Stopped):
                            c.admission({'job_id':'another','model':'gpt-5.4-mini'},1,100)
                        self.assertIsNone(s.claim())
                    finally:
                        lock.__exit__(None,None,None); s.db.close()

    def test_recovery_from_saved_receipt_is_idempotent(self):
        with patch.object(runner,'finish',side_effect=RuntimeError('crash before feedback')):
            with self.assertRaises(RuntimeError):
                self.send(503,common.encoded({'error':{'code':'overloaded'}}),{'Retry-After':'99'})
        runner.recover(self.store)
        gate = self.store.db.execute("SELECT until_at FROM op_gates WHERE scope='cooldown:shared'").fetchone()[0]
        self.assertGreater(gate,self.time+99)
        self.assertEqual(runner.recover(self.store),[])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],1)
        self.assertEqual(self.store.counts(),{'pending':1})

    def test_uncertain_not_reissued_or_refunded(self):
        job,n,lock = self.store.claim()
        try:
            self.c.acquire(job,n,200)
            def timeout(_):
                raise TimeoutError()
            r = runner.run_attempt(self.store,self.rows[0],job,n,timeout)
            self.assertEqual(r['state'],'uncertain'); self.assertIsNone(self.store.claim())
            self.assertEqual(self.store.db.execute('SELECT reserved FROM op_attempts').fetchone()[0],200)
        finally:
            lock.__exit__(None,None,None)

    def test_invalid_response_is_terminal_and_progress_keeps_denominator(self):
        self.send(raw=response(label='Supported.'))
        self.assertIsNone(self.store.claim()); report = self.c.progress()
        self.assertEqual(report['completed_jobs'],1); self.assertEqual(report['failures'],1)
        self.assertEqual(report['available_usage']['gpt-5.4']['completion_tokens'],2)

    def test_cancelled_admission_never_creates_request(self):
        self.c.cancelled = lambda:True
        with self.assertRaises(coordination.Stopped):
            self.admit('a')
        self.assertFalse(any(self.path.rglob('request.json')))

    def test_attempt_cap_and_duplicate_reservation(self):
        self.c.max_attempts = 1; self.assertEqual(self.admit('a'),0)
        with self.assertRaises(ValueError):
            self.admit('a')
        self.assertIsNone(self.admit('b')); self.assertTrue(self.c.stop_reason())

    def test_twenty_processes_share_one_atomic_limiter(self):
        ctx = multiprocessing.get_context('spawn')
        with concurrent.futures.ProcessPoolExecutor(20,mp_context=ctx) as pool:
            results = list(pool.map(contend,[(str(self.path),i) for i in range(20)]))
        self.assertEqual(sum(results),1)

    def test_twenty_processes_observe_shared_cooldown_and_halt(self):
        self.c.gate('cooldown:shared',2000)
        ctx = multiprocessing.get_context('spawn')
        with concurrent.futures.ProcessPoolExecutor(20,mp_context=ctx) as pool:
            self.assertFalse(any(pool.map(contend,[(str(self.path),i) for i in range(20)])))
            self.store.halt('Mock authentication failure')
            self.assertFalse(any(pool.map(contend,[(str(self.path),i+20) for i in range(20)])))
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],0)

    def test_twenty_worker_launcher_mock_run_no_duplicates_and_resume(self):
        rows,jobs = fixture(36)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); store = runner.Store(p,jobs,{'test':True})
            common.write_new(p/'mock-inputs.json',rows)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    report = launcher.launch(store,config(),108,interval=.5,mock=True)
                self.assertEqual(report['states'],{'valid':36})
                artifacts = list(p.rglob('response.bin')); hashes = {str(f):common.digest(f) for f in artifacts}
                self.assertEqual(len(artifacts),36)
                self.assertEqual(store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],36)
                spans = [(r['started'],r['ended']) for r in store.db.execute('SELECT started,ended FROM op_attempts ORDER BY started')]
                self.assertTrue(any(a[1]>b[0] for a,b in zip(spans,spans[1:])), 'Mock requests should overlap')
                finished = common.load(next((p/'launches').glob('*/finished.json')))
                self.assertEqual(finished['worker_exit_codes'],[0]*20)
                coordinator = coordination.Coordinator(store,config())
                coordinator.stop('Mock interruption after completed calls')
                with self.assertRaises(ValueError):
                    launcher.launch(store,config(),108,mock=True)
                with contextlib.redirect_stdout(io.StringIO()):
                    launcher.launch(store,config(),108,resume=True,interval=.5,mock=True)
                self.assertEqual(hashes,{str(f):common.digest(f) for f in p.rglob('response.bin')})
                self.assertEqual(store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],36)
            finally:
                store.db.close()

    def test_sticky_halt_cannot_be_cleared_by_resume(self):
        self.store.halt('Mock quota failure')
        with self.assertRaises(ValueError):
            launcher.launch(self.store,config(),3,resume=True,mock=True)
        self.assertIsNotNone(self.store.db.execute("SELECT value FROM meta WHERE key='halt_reason'").fetchone())

    def test_interrupt_inflight_then_resume_retains_each_response_once(self):
        rows,jobs = fixture(36)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); store = runner.Store(p,jobs,{'test':True})
            common.write_new(p/'mock-inputs.json',rows); stopped = threading.Event()
            def interrupt_after_response():
                s = runner.Store(p); c = coordination.Coordinator(s,config())
                try:
                    deadline = time.monotonic()+45
                    while time.monotonic()<deadline:
                        if s.db.execute('SELECT count(*) FROM op_attempts WHERE ended IS NOT NULL').fetchone()[0]:
                            c.stop('Mock interruption while other jobs remain'); stopped.set(); return
                        time.sleep(.01)
                finally:
                    s.db.close()
            monitor = threading.Thread(target=interrupt_after_response); monitor.start()
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    first = launcher.launch(store,config(),108,interval=.5,mock=True)
                monitor.join(); self.assertTrue(stopped.is_set())
                self.assertGreater(first['states'].get('pending',0),0)
                saved = {str(f):common.digest(f) for f in p.rglob('response.bin')}
                self.assertTrue(saved)
                with contextlib.redirect_stdout(io.StringIO()):
                    final = launcher.launch(store,config(),108,resume=True,interval=.5,mock=True)
                self.assertEqual(final['states'],{'valid':36})
                self.assertEqual(len(list(p.rglob('request.json'))),36)
                self.assertEqual(len(list(p.rglob('response.bin'))),36)
                for name,expected in saved.items():
                    self.assertEqual(common.digest(name),expected)
            finally:
                monitor.join(); store.db.close()

    def smoke_fixture(self,missing=False):
        jobs = [json.loads(x) for x in (common.HERE/'prepared/smoke/jobs.jsonl').read_text(encoding='utf-8').splitlines()]
        rows = {r['claim_id']:r for r in common.read_inputs()}
        path = self.path/'smoke'; common.write_new(path/'run.json',{'plan_sha256':common.digest(common.HERE/'prepared/smoke/plan.json')})
        for i,j in enumerate(jobs):
            if missing and not i:
                continue
            d = path/'attempts'/j['job_id']/'attempt-01'
            raw = response(j['model'])
            common.write_new(d/'request.json',{'job':j,'attempt':1,'body':common.request(rows[j['claim_id']],j['model'],j['condition']),
                                             'started_at_utc':'2026-10-16T00:00:00+00:00'})
            common.write_new(d/'response.bin',raw,binary=True)
            common.write_new(d/'receipt.json',{'http_status':200,'received_at_utc':'2026-10-16T00:00:02+00:00',
                'raw_sha256':common.digest(d/'response.bin'),
                'headers':{'x-ratelimit-limit-project-requests':'10','x-ratelimit-limit-requests':'5'}})
        return path

    def test_smoke_projection_uses_measured_latency_usage_and_limits(self):
        path = self.smoke_fixture()
        with patch.object(smoke_projection,'verify_freeze'):
            report = smoke_projection.project(path,common.load(launcher.DEFAULT_LIMITS))
        self.assertEqual(report['status'],'PROVISIONAL_TWELVE_CALL_PROJECTION')
        self.assertEqual(report['per_model']['gpt-5.4']['mean_latency_seconds'],2)
        self.assertAlmostEqual(report['projected_runtime_hours'],300)
        # 77 long claim/condition payloads add 111.816 s over the RPM+jitter floor across full3.
        self.assertAlmostEqual(report['configured_bucket_pacing_hours']['shared'],55.28106,places=5)
        expected = sum((180*6534021/482*common.RATES[m]['input']+180000*common.RATES[m]['output'])/1e6 for m in common.MODELS)
        self.assertAlmostEqual(report['projected_full3_usd_at_frozen_standard_rates'],expected)

    def test_smoke_projection_reports_incomplete_without_imputing_usage(self):
        path = self.smoke_fixture(missing=True)
        with patch.object(smoke_projection,'verify_freeze'):
            report = smoke_projection.project(path,config())
        self.assertIsNone(report['projection']); self.assertEqual(len(report['unresolved_jobs']),1)

    def test_revision_verifies_original_and_operational_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); op = base/'operational-revisions/2026-10-16-workers20'
            common.write_new(base/'original.py',b'old',binary=True)
            common.write_new(base/'protocol-freeze.json',{'files':{'original.py':common.digest(base/'original.py')}})
            common.write_new(op/'original/original.py',b'old',binary=True)
            (base/'original.py').write_bytes(b'new')
            common.write_new(op/'revision.json',{'original_freeze_sha256':common.digest(base/'protocol-freeze.json'),
                'original_files':{'original.py':'operational-revisions/2026-10-16-workers20/original/original.py'},
                'files':{'original.py':common.digest(base/'original.py')}})
            common.verify_freeze(base)
            (base/'original.py').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                common.verify_freeze(base)


if __name__=='__main__':
    unittest.main()
