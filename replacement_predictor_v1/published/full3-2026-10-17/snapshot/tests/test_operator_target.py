"""Mock-only checks for the operator-selected, unverified-capacity configuration."""
import concurrent.futures
import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import common
import coordination
import rate_policy
import runner
from test_operations import fixture, response

REVISION = common.HERE/'operational-revisions/2026-10-16-operator600'


def config():
    return common.load(REVISION/'limits-operator600.json')


def contend(args):
    path,index,clock,model = args
    store = runner.Store(path)
    try:
        c = coordination.Coordinator(store,config(),clock=lambda:clock,jitter=lambda:.001)
        try:
            return c.admission({'job_id':'actor-'+str(index),'model':model},1,100)==0
        except coordination.Stopped:
            return False
    finally:
        store.db.close()


class OperatorTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.path = Path(self.temp.name)
        self.rows,self.jobs = fixture(1); self.store = runner.Store(self.path,self.jobs,{'synthetic_only':True})
        self.clock = 1000.; self.config = config()
        self.c = coordination.Coordinator(self.store,self.config,clock=lambda:self.clock,jitter=lambda:.001)
        self.c.begin_session()

    def tearDown(self):
        self.store.db.close(); self.temp.cleanup()

    def send(self,status=200,headers=None,raw=None):
        job,n,lock = self.store.claim()
        try:
            self.c.acquire(job,n,200)
            return runner.run_attempt(self.store,self.rows[0],job,n,
                lambda _: (status,raw or response(job['model']),headers or {},False))
        finally:
            lock.__exit__(None,None,None)

    def test_operator_target_ramps_to_600_without_false_capacity_claim(self):
        p = self.config['rate_policy']
        self.assertFalse(p['capacity_evidence']['verified'])
        self.assertIsNone(p['capacity_evidence']['shared_rpm'])
        self.assertIsNone(p['capacity_evidence']['shared_tpm'])
        for step,rpm in enumerate([60,120,240,360,480,600]):
            self.clock = 1000+60*step
            self.assertEqual(self.c.effective_buckets(self.clock)[0]['rpm'],rpm)
        self.assertEqual(rate_policy.supported(p),(600,600000))
        self.assertEqual(self.config['buckets'][1]['rpm'],5000)
        self.assertEqual(self.config['buckets'][1]['tpm'],1000000)
        self.assertEqual(self.config['buckets'][2]['rpm'],5000)
        self.assertEqual(self.config['buckets'][2]['tpm'],2000000)
        for name in ('shared_family','project_organization_aggregate','daily_requests','daily_tokens'):
            self.assertIsNone(self.config['provider_limits'][name])

    def test_prior_configuration_and_seals_remain_valid(self):
        common.verify_freeze()
        baseline = common.load(REVISION/'BASELINE.json')
        for group in ('unchanged_source_hashes','previous_seals','prior_limits'):
            for name,expected in baseline[group].items():
                self.assertEqual(common.digest(common.HERE/name),expected)
        prior = common.load(common.HERE/'operational-revisions/2026-10-16-rpm600/limits-600.json')
        self.assertEqual(rate_policy.supported(prior['rate_policy']),(60,60000))

    def test_lower_observed_project_and_model_limits_still_bind(self):
        self.clock += 360
        self.send(headers={'x-ratelimit-limit-project-requests':'2',
            'x-ratelimit-remaining-project-requests':'0','x-ratelimit-reset-project-requests':'12s',
            'x-ratelimit-limit-tokens':'1000','x-ratelimit-remaining-tokens':'1000',
            'x-ratelimit-reset-tokens':'10s'})
        other = {'job_id':'other','model':'gpt-5.4-mini'}
        self.assertGreater(self.c.admission(other,1,100),12)
        self.clock += 31
        self.assertEqual(self.c.admission(other,1,100),0)
        self.clock += 31
        with self.assertRaises(ValueError):
            self.c.admission({'job_id':'oversize','model':'gpt-5.4'},1,1001)

    def test_retry_after_cooldown_and_adaptive_reduction_remain_shared(self):
        self.clock += 360
        result = self.send(429,{'Retry-After':'17','x-ratelimit-reset-tokens':'1m2s'},
            common.encoded({'error':{'code':'rate_limit_exceeded'}}))
        self.assertEqual(result['state'],'pending')
        self.assertEqual(self.c.effective_buckets(self.clock)[0]['rpm'],300)
        self.assertGreater(self.c.admission({'job_id':'other','model':'gpt-5.4-mini'},1,100),62)
        self.assertEqual(len(list(self.path.rglob('request.json'))),1)
        self.assertEqual(len(list(self.path.rglob('response.bin'))),1)
        self.assertFalse(self.config['rate_policy']['capacity_evidence']['verified'])

    def test_operator_token_budget_remains_aggregate(self):
        self.clock += 360
        self.assertEqual(self.c.admission({'job_id':'a','model':'gpt-5.4'},1,400000),0)
        self.clock += 41
        self.assertGreater(self.c.admission({'job_id':'b','model':'gpt-5.4-mini'},1,400000),18)
        with self.assertRaises(ValueError):
            self.c.admission({'job_id':'oversize','model':'gpt-5.4-mini'},1,600001)

    def test_twenty_processes_share_target_lower_headers_halts_and_no_duplicates(self):
        ctx = multiprocessing.get_context('spawn')
        with concurrent.futures.ProcessPoolExecutor(20,mp_context=ctx) as pool:
            for wave in range(20):
                clock = 1360+wave*.11
                results = list(pool.map(contend,[(str(self.path),wave*20+i,clock,common.MODELS[wave%2]) for i in range(20)]))
                self.assertEqual(sum(results),1)
            self.clock = 1363
            first = self.store.db.execute('SELECT job_id,model FROM op_attempts LIMIT 1').fetchone()
            with self.assertRaises(ValueError):
                self.c.admission(dict(first),1,100)
            self.store.db.execute('INSERT INTO op_headers VALUES(?,?,?,?,?,?)',
                ('project','requests',json.dumps(list(common.MODELS)),60,60,1423))
            one = list(pool.map(contend,[(str(self.path),1000+i,1363,common.MODELS[i%2]) for i in range(20)]))
            blocked = list(pool.map(contend,[(str(self.path),2000+i,1363.2,common.MODELS[i%2]) for i in range(20)]))
            self.assertEqual(sum(one),1); self.assertFalse(any(blocked))
            self.store.halt('Synthetic global halt')
            halted = list(pool.map(contend,[(str(self.path),3000+i,1365,common.MODELS[i%2]) for i in range(20)]))
            self.assertFalse(any(halted))
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM op_attempts').fetchone()[0],21)
