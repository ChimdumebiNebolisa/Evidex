import collections
import concurrent.futures
import contextlib
import copy
import io
import json
import multiprocessing
import tempfile
import time
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import common
import coordination
import launcher
import rate_policy
import runner
import throughput_projection
from test_operations import fixture, response

NEW = common.HERE/'operational-revisions/2026-10-16-rpm600'


def limits(steady=False, verified=True):
    config = common.load(NEW/'limits-600.json')
    p = config['rate_policy']
    p['capacity_evidence'] = {'verified':verified,'source':'SYNTHETIC TEST CAPACITY ONLY','shared_rpm':600,'shared_tpm':600000}
    if steady:
        p['ramp_rpm'] = [600]
    return config


def contend(args):
    path,index,clock,model = args; store = runner.Store(path)
    try:
        c = coordination.Coordinator(store,limits(steady=True),clock=lambda:clock,jitter=lambda:0)
        try:
            delay = c.admission({'job_id':'wave-'+str(index),'model':model},1,100)
            return delay==0
        except coordination.Stopped:
            return False
    finally:
        store.db.close()


class ThroughputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.path = Path(self.temp.name)
        self.rows,self.jobs = fixture(1); self.store = runner.Store(self.path,self.jobs,{'synthetic_only':True})
        self.clock = 1000.; self.config = limits()
        self.c = coordination.Coordinator(self.store,self.config,clock=lambda:self.clock,jitter=lambda:.005)
        self.c.begin_session()

    def tearDown(self):
        self.store.db.close(); self.temp.cleanup()

    def rate(self):
        return rate_policy.current(self.config['rate_policy'],self.c.policy_state(self.clock),self.clock)

    def send(self,status=200,headers=None,raw=None):
        job,n,lock = self.store.claim()
        try:
            self.c.acquire(job,n,200)
            return runner.run_attempt(self.store,self.rows[0],job,n,lambda _: (status,raw or response(job['model']),headers or {},False))
        finally:
            lock.__exit__(None,None,None)

    def test_gradual_ramp_and_positive_jitter(self):
        for step,rpm in enumerate([60,120,240,360,480,600]):
            self.clock = 1000+step*60
            self.assertEqual(self.rate(),rpm)
        self.assertEqual(self.c.admission({'job_id':'a','model':'gpt-5.4'},1,100),0)
        self.assertGreaterEqual(self.store.db.execute("SELECT until_at FROM op_gates WHERE scope='pace:shared'").fetchone()[0]-self.clock,.1049)

    def test_unverified_capacity_cannot_activate_600(self):
        cfg = limits(verified=False)
        c = coordination.Coordinator(self.store,cfg,clock=lambda:self.clock)
        self.clock += 3600
        buckets = c.effective_buckets(self.clock)
        self.assertTrue(all(b['rpm']==60 and b['tpm']==60000 for b in buckets))

    def test_verified_lower_shared_limits_still_bind(self):
        self.config['rate_policy']['capacity_evidence'].update(shared_rpm=400,shared_tpm=100000)
        self.clock += 600
        self.assertEqual(self.rate(),400)
        self.assertEqual(self.c.effective_buckets(self.clock)[0]['tpm'],100000)

    def test_rolling_600_rpm_is_aggregate_and_no_burst(self):
        self.config['rate_policy']['ramp_rpm']=[600]
        times=[]
        for i in range(650):
            job={'job_id':'j'+str(i),'model':common.MODELS[i%2]}
            while True:
                wait=self.c.admission(job,1,100)
                if wait==0:
                    times.append(self.clock); break
                self.clock += wait+.000001
        self.assertTrue(all(b-a>=.1 for a,b in zip(times,times[1:])))
        self.assertTrue(all(times[i]-times[i-600]>=60 for i in range(600,len(times))))
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],650)

    def test_shared_token_window_and_large_request(self):
        self.config['rate_policy']['ramp_rpm']=[600]
        for b in self.config['buckets']:b['tpm']=1000
        self.assertEqual(self.c.admission({'job_id':'a','model':'gpt-5.4'},1,800),0)
        self.clock += 49
        self.assertGreater(self.c.admission({'job_id':'b','model':'gpt-5.4-mini'},1,800),10)
        with self.assertRaises(ValueError):
            self.c.admission({'job_id':'too-large','model':'gpt-5.4-mini'},1,1001)

    def test_throttle_halves_shared_rate_and_obeys_long_reset(self):
        self.clock += 600
        self.assertEqual(self.rate(),600)
        r=self.send(429,{'Retry-After':'17','x-ratelimit-reset-tokens':'1m2s'},common.encoded({'error':{'code':'rate_limit_exceeded'}}))
        self.assertEqual(r['state'],'pending'); self.assertEqual(self.rate(),300)
        self.assertGreater(self.c.admission({'job_id':'other','model':'gpt-5.4-mini'},1,100),62)
        self.clock += 63
        self.send()
        self.assertEqual(self.rate(),360)
        self.assertEqual(len(list(self.path.rglob('request.json'))),2)
        self.assertEqual(len(list(self.path.rglob('response.bin'))),2)

    def test_overload_reduces_rate_without_adding_retries(self):
        self.clock += 600
        r=self.send(503,raw=common.encoded({'error':{'code':'server_is_overloaded'}}))
        self.assertEqual(r['state'],'pending'); self.assertEqual(self.rate(),300)
        job=self.jobs[0]
        r=runner.interpret(job,{'http_status':429,'received_at_utc':'test','raw_sha256':'test'},common.encoded({'error':{'code':'slow_down'}}),1)
        self.assertEqual(r['state'],'service_failure')

    def test_restart_retains_penalty_and_restarts_ramp(self):
        self.clock += 600; self.send(503)
        self.assertEqual(self.rate(),300)
        other=runner.Store(self.path)
        try:
            c=coordination.Coordinator(other,self.config,clock=lambda:self.clock)
            c.begin_session()
            self.assertEqual(c.policy_state(self.clock)['adaptive_rpm'],300)
            self.assertEqual(rate_policy.current(self.config['rate_policy'],c.policy_state(self.clock),self.clock),60)
            self.clock+=600
            self.assertEqual(rate_policy.current(self.config['rate_policy'],c.policy_state(self.clock),self.clock),300)
        finally:other.db.close()

    def test_no_recovery_without_successful_traffic(self):
        state=rate_policy.initial(self.config['rate_policy'],1000)
        rate_policy.throttle(self.config['rate_policy'],state,1600)
        self.assertEqual(rate_policy.current(self.config['rate_policy'],state,10000),300)
        rate_policy.success(self.config['rate_policy'],state,10000)
        self.assertEqual(rate_policy.current(self.config['rate_policy'],state,10000),360)

    def test_auth_quota_and_model_halts_override_ramp(self):
        for status,raw in [(401,common.encoded({'error':{'code':'invalid_api_key'}})),(429,common.encoded({'error':{'code':'insufficient_quota'}})),(200,response(model='unexpected'))]:
            with tempfile.TemporaryDirectory() as d:
                s=runner.Store(d,self.jobs,{'synthetic_only':True}); c=coordination.Coordinator(s,limits(steady=True),jitter=lambda:.001)
                job,n,lock=s.claim()
                try:
                    c.acquire(job,n,100); runner.run_attempt(s,self.rows[0],job,n,lambda _: (status,raw,{},False))
                    with self.assertRaises(coordination.Stopped):c.admission({'job_id':'new','model':'gpt-5.4-mini'},1,100)
                finally:lock.__exit__(None,None,None); s.db.close()

    def test_twenty_processes_enforce_aggregate_600_target(self):
        ctx=multiprocessing.get_context('spawn'); grants=0
        with concurrent.futures.ProcessPoolExecutor(20,mp_context=ctx) as pool:
            for wave in range(30):
                clock=1000+wave*.101
                replies=list(pool.map(contend,[(str(self.path),wave*20+i,clock,common.MODELS[wave%2]) for i in range(20)]))
                self.assertEqual(sum(replies),1); grants+=sum(replies)
            c=coordination.Coordinator(self.store,limits(steady=True),clock=lambda:1003.1)
            state=c.policy_state(1003.1);rate_policy.throttle(c.config['rate_policy'],state,1003.1);c.save_policy(state,'synthetic_throttle')
            first=list(pool.map(contend,[(str(self.path),1000+i,1003.2,'gpt-5.4') for i in range(20)]))
            blocked=list(pool.map(contend,[(str(self.path),2000+i,1003.301,'gpt-5.4-mini') for i in range(20)]))
            self.assertEqual(sum(first),1);self.assertFalse(any(blocked))
        self.assertEqual(grants,30)
        self.assertEqual(len(self.store.db.execute('SELECT DISTINCT model FROM op_attempts').fetchall()),2)

    def test_projection_accounts_for_actual_jitter_and_worker_capacity(self):
        cfg=limits(steady=True);cfg['rate_policy']['jitter_seconds']=[.005,.005]
        jobs=[{'model':common.MODELS[i%2]} for i in range(120)]
        fast=throughput_projection.simulate(jobs,[100]*120,cfg,.15,overhead=.003,startup=2)
        self.assertGreater(fast['seconds'],120*.1)
        self.assertGreaterEqual(fast['mean_admission_interval_seconds'],.108)
        slow=throughput_projection.simulate(jobs,[100]*120,cfg,10,workers=20,overhead=.003,startup=2)
        self.assertGreaterEqual(slow['seconds'],60)
        self.assertGreater(slow['seconds'],fast['seconds'])

    def test_new_revision_chain_preserves_both_previous_seals(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d);old=b/'operational-revisions/2026-10-16-workers20';new=b/'operational-revisions/2026-10-16-rpm600'
            common.write_new(b/'code.py',b'original',binary=True)
            common.write_new(b/'protocol-freeze.json',{'files':{'code.py':common.digest(b/'code.py')}})
            common.write_new(old/'original/code.py',b'original',binary=True)
            (b/'code.py').write_bytes(b'first revision')
            common.write_new(old/'revision.json',{'original_freeze_sha256':common.digest(b/'protocol-freeze.json'),
                'original_files':{'code.py':(old/'original/code.py').relative_to(b).as_posix()},'files':{'code.py':common.digest(b/'code.py')}})
            common.write_new(new/'original/code.py',b'first revision',binary=True)
            (b/'code.py').write_bytes(b'second revision')
            common.write_new(new/'revision.json',{'original_freeze_sha256':common.digest(b/'protocol-freeze.json'),
                'previous_revision_sha256':common.digest(old/'revision.json'),
                'previous_files':{'code.py':(new/'original/code.py').relative_to(b).as_posix()},'files':{'code.py':common.digest(b/'code.py')}})
            result=common.verify_freeze(b);self.assertIn('throughput_revision_sha256',result)
            (new/'original/code.py').write_bytes(b'changed history')
            with self.assertRaises(ValueError):common.verify_freeze(b)

    def test_twenty_worker_mock_late_queue_overhead_and_duplicate_prevention(self):
        rows,jobs=fixture(180000)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); store=runner.Store(p,jobs,{'synthetic_only':True,'purpose':'late-queue performance fixture'})
            store.db.execute("UPDATE jobs SET state='synthetic_prior_terminal' WHERE ordinal<179880")
            common.write_new(p/'mock-inputs.json',rows)
            cfg=limits(steady=True)
            fixture_coord=coordination.Coordinator(store,cfg)
            store.db.execute('BEGIN IMMEDIATE')
            store.db.executemany('INSERT INTO op_attempts(job_id,attempt,model,started,ended,reserved,state) VALUES(?,1,?,0,0,100,?)',
                [(str(i),common.MODELS[i%2],'synthetic_prior_terminal') for i in range(179880)])
            store.db.execute("UPDATE meta SET value='179880' WHERE key='op_admission_count'")
            for model,tpm in [('gpt-5.4',1000000),('gpt-5.4-mini',2000000)]:
                for metric,cap in [('requests',5000),('tokens',tpm)]:
                    store.db.execute('INSERT INTO op_headers VALUES(?,?,?,?,?,?)',('model:'+model,metric,json.dumps([model]),cap,cap,time.time()+60))
            store.db.execute('COMMIT')
            started=time.perf_counter()
            try:
                with contextlib.redirect_stdout(io.StringIO()):report=launcher.launch(store,cfg,540000,interval=5,mock=True)
                elapsed=time.perf_counter()-started
                calls=[dict(r) for r in store.db.execute('SELECT * FROM op_attempts WHERE started>0 ORDER BY started')]
                self.assertEqual(len(calls),120); self.assertEqual(report['states']['valid'],120)
                self.assertEqual(len(list(p.rglob('request.json'))),120)
                self.assertTrue(all(b['started']-a['started']>=.0999 for a,b in zip(calls,calls[1:])))
                self.assertTrue(all(r['state']=='valid' for r in calls))
                window=calls[-1]['started']-calls[0]['started']; gaps=[b['started']-a['started'] for a,b in zip(calls,calls[1:])]
                overhead=max(0,sum(gaps)/len(gaps)-.105)
                launch_record=common.load(next((p/'launches').glob('*/launch.json')))
                launch_start=__import__('datetime').datetime.fromisoformat(launch_record['at_utc']).timestamp()
                record={'at_utc':common.now(),'synthetic_only':True,'generation_calls':0,'workers':20,'queue_rows':180000,
                    'prior_terminal_rows':179880,'mock_calls':120,'completed_valid':120,'mean_admission_interval_seconds':sum(gaps)/len(gaps),
                    'prior_ledger_rows':179880,
                    'provider_header_budgets_seeded':True,
                    'target_interval_plus_mean_jitter_seconds':.105,'observed_extra_interval_seconds':overhead,
                    'startup_to_first_admission_seconds':calls[0]['started']-launch_start,
                    'admission_window_seconds':window,'observed_mock_rpm':119/window*60,'elapsed_seconds':elapsed,
                    'limit':'Mock transport sleeps 0.15 seconds; measures local queue/limiter/worker overhead, not provider sustained throughput'}
                artifact=common.HERE/'test-artifacts'/('rpm600-'+common.now().replace(':','-'))/'benchmark.json'
                common.write_new(artifact,record)
            finally:store.db.close()
