import concurrent.futures
import hashlib
import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common
import prepare
import runner
import analyze

def claims_fixture():
    return [dict(claim_id=str(i), claim_text='Claim '+str(i), gold_evidence='Evidence '+str(i),
                 gold_label=gold, evidence_set_id='test-'+str(i), text_cluster='cluster-'+str(i),
                 repeat_representative=True, historical_regression=(i==1),
                 historical_labels={m:{'claim_only':'Supported','claim_plus_evidence':'Refuted'} for m in common.MODELS})
            for i,gold in [(1,'Supported'),(2,'Refuted')]]

def response(label='Supported', model='gpt-5.4', finish='stop', refusal=None):
    return common.encoded({'id':'fake-response','model':model,'choices':[{'finish_reason':finish,
                'message':{'role':'assistant','content':label,'refusal':refusal}}],
                'usage':{'prompt_tokens':30,'completion_tokens':2,'total_tokens':32,
                         'completion_tokens_details':{'reasoning_tokens':0}}})

def claim_worker(path):
    store=runner.Store(path); item=store.claim()
    if item is None:return 0
    job,n,lock=item
    try:return 1
    finally:lock.__exit__(None,None,None);store.db.close()

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)
        self.claim=claims_fixture()[0]
        self.job={'job_id':'1_gpt-5.4_A_r01','claim_id':'1','model':'gpt-5.4','condition':'A','repetition':1,
                  'order':0,'request_sha256':common.value_hash(common.request(self.claim,'gpt-5.4','A'))}
        self.store=runner.Store(self.path,[self.job],{'test':True})
    def tearDown(self):
        self.store.db.close();self.temp.cleanup()
    def send(self, transport):
        item=self.store.claim();self.assertIsNotNone(item);job,n,lock=item
        try:return runner.run_attempt(self.store,self.claim,job,n,transport)
        finally:lock.__exit__(None,None,None)
    def test_exact_label_rule_and_no_invalid_retry(self):
        for s in ['supported','"Supported"','Supported.','Supported because yes','not supported. Refuted','']:
            r=runner.interpret(self.job,{'http_status':200,'received_at_utc':'test','raw_sha256':'test'},response(s),1)
            self.assertEqual(r['state'],'invalid',s)
        r=self.send(lambda _: (200,response('Supported because yes'),{},False))
        self.assertEqual(r['state'],'invalid');self.assertIsNone(self.store.claim())
    def test_raw_written_before_parser_and_saved_complete(self):
        original=runner.interpret;raw=response('  Supported\n')
        def inspect(*args,**kwargs):
            p=self.path/'attempts'/self.job['job_id']/'attempt-01'
            self.assertEqual((p/'response.bin').read_bytes(),raw);self.assertTrue((p/'receipt.json').is_file())
            return original(*args,**kwargs)
        with patch.object(runner,'interpret',side_effect=inspect):r=self.send(lambda _: (200,raw,{'x-request-id':'fake'},False))
        self.assertEqual(r['label'],'Supported');self.assertIsNone(self.store.claim())
    def test_truncation_and_refusal_never_accepted(self):
        rec={'http_status':200,'received_at_utc':'t','raw_sha256':'h'}
        self.assertEqual(runner.interpret(self.job,rec,response('Supported',finish='length'),1)['state'],'invalid')
        self.assertEqual(runner.interpret(self.job,rec,response('Supported',refusal='No'),1)['parsed_status'],'refused')
        self.assertEqual(runner.interpret(self.job,rec,b'not json',1)['state'],'model_mismatch')
    def test_transient_retry_and_bound(self):
        for n in [1,2,3]:
            r=self.send(lambda _: (503,common.encoded({'error':{'code':'overloaded'}}),{},False))
            self.assertEqual(r['state'],'pending' if n<3 else 'service_failure')
        self.assertIsNone(self.store.claim());self.assertEqual(len(list((self.path/'attempts'/self.job['job_id']).glob('attempt-*'))),3)
    def test_first_success_after_transient_keeps_failure(self):
        self.send(lambda _: (429,common.encoded({'error':{'code':'rate_limit_exceeded'}}),{},False))
        result=self.send(lambda _: (200,response('Refuted'),{},False))
        self.assertEqual(result['attempt'],2);self.assertEqual(result['label'],'Refuted')
        self.assertTrue((self.path/'attempts'/self.job['job_id']/'attempt-01/response.bin').exists())
    def test_independent_analysis_distinguishes_pending_retry(self):
        self.send(lambda _: (503,common.encoded({'error':{'code':'overloaded'}}),{},False))
        self.assertEqual(analyze.observation(self.path,self.job)['state'],'pending_retry')
    def test_quota_and_model_mismatch_halt(self):
        r=self.send(lambda _: (429,common.encoded({'error':{'code':'insufficient_quota'}}),{},False))
        self.assertEqual(r['state'],'service_failure');self.assertIsNotNone(self.store.db.execute("SELECT value FROM meta WHERE key='halt_reason'").fetchone())
    def test_unexpected_model_halts(self):
        r=self.send(lambda _: (200,response(model='different-model'),{},False))
        self.assertEqual(r['state'],'model_mismatch');self.assertIsNone(self.store.claim())
    def test_network_timeout_uncertain_not_reissued(self):
        def timeout(_):raise TimeoutError('Unknown acceptance')
        self.assertEqual(self.send(timeout)['state'],'uncertain');self.assertIsNone(self.store.claim())
    def test_interrupted_after_receipt_recovery_uses_no_transport(self):
        with patch.object(runner,'finish',side_effect=RuntimeError('simulated crash')):
            with self.assertRaises(RuntimeError):self.send(lambda _: (200,response('Refuted'),{},False))
        actions=runner.recover(self.store);self.assertIn('saved_response_valid',actions[0]['action'])
        self.assertEqual(self.store.counts(),{'valid':1});self.assertIsNone(self.store.claim())
    def test_request_without_receipt_is_uncertain(self):
        job,n,lock=self.store.claim()
        try:common.write_new(self.path/'attempts'/job['job_id']/'attempt-01/request.json',{'body':common.request(self.claim,'gpt-5.4','A')})
        finally:lock.__exit__(None,None,None)
        runner.recover(self.store);self.assertEqual(self.store.counts(),{'uncertain':1})
    def test_pre_request_crash_is_resumable(self):
        _,_,lock=self.store.claim();lock.__exit__(None,None,None)
        runner.recover(self.store);self.assertEqual(self.store.counts(),{'pending':1})
        self.assertEqual(self.send(lambda _: (200,response(),{},False))['attempt'],2)
    def test_prelaunch_recovery_does_not_consume_service_retry_allowance(self):
        _,_,lock=self.store.claim();lock.__exit__(None,None,None);runner.recover(self.store)
        for i in range(1,4):
            r=self.send(lambda _: (503,common.encoded({'error':{'code':'overloaded'}}),{},False))
            self.assertEqual(r['request_attempt_count'],i)
            self.assertEqual(r['state'],'pending' if i<3 else 'service_failure')
        self.assertIsNone(self.store.claim())
    def test_active_worker_is_not_recovered(self):
        _,_,lock=self.store.claim()
        try:self.assertEqual(runner.recover(self.store)[0]['action'],'active_worker_skipped')
        finally:lock.__exit__(None,None,None)
    def test_two_processes_claim_same_job_only_once(self):
        context=multiprocessing.get_context('spawn')
        with concurrent.futures.ProcessPoolExecutor(2,mp_context=context) as pool:
            results=list(pool.map(claim_worker,[str(self.path)]*2))
        self.assertEqual(sum(results),1)
    def test_attempt_file_cannot_be_overwritten(self):
        p=self.path/'test.json';common.write_new(p,{'a':1})
        with self.assertRaises(FileExistsError):common.write_new(p,{'a':2})
        self.assertEqual(common.load(p),{'a':1})
    def test_same_plan_cannot_accidentally_start_second_run(self):
        registry=self.path/'registry';runner.bind_plan_to_run(registry,'hash',self.path/'first')
        runner.bind_plan_to_run(registry,'hash',self.path/'first')
        with self.assertRaises(ValueError):runner.bind_plan_to_run(registry,'hash',self.path/'second')
    def test_partial_response_is_retained_and_never_retried(self):
        import http.client
        def partial(_):raise http.client.IncompleteRead(b'partial body',100)
        self.assertEqual(self.send(partial)['state'],'uncertain')
        p=self.path/'attempts'/self.job['job_id']/'attempt-01/partial-response.bin'
        self.assertEqual(p.read_bytes(),b'partial body');self.assertIsNone(self.store.claim())

class DesignTests(unittest.TestCase):
    def test_complete_messages_match_historical_templates(self):
        r=claims_fixture()[0]
        a='Classify the claim as Supported or Refuted.\nOutput only one word: Supported or Refuted.\n\nClaim: Claim 1'
        self.assertEqual(common.messages(r,'A'),[{'role':'user','content':a}])
        self.assertEqual(common.messages(r,'B')[0]['content'],a+'\nEvidence: Evidence 1')
        self.assertEqual(common.messages(r,'C')[0]['content'],a.replace('Refuted.\nOutput','Refuted based only on the evidence provided.\nOutput',1)+'\nEvidence: Evidence 1')
    def test_repetitions_fresh_jobs_and_random_order(self):
        jobs=prepare.make_jobs(claims_fixture(),'full3');self.assertEqual(len(jobs),36)
        self.assertEqual(len({j['job_id'] for j in jobs}),36)
        self.assertEqual(jobs,prepare.make_jobs(claims_fixture(),'full3'))
        self.assertEqual(len({j['request_sha256'] for j in jobs}),12)
        self.assertGreater(len({j['condition'] for j in jobs[:8]}),1)
    def test_frozen_file_mutation_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);common.write_new(p/'test.json',{'a':1});common.write_new(p/'protocol-freeze.json',{'files':{'test.json':common.digest(p/'test.json')}})
            common.verify_freeze(p);(p/'test.json').write_text('changed')
            with self.assertRaises(ValueError):common.verify_freeze(p)

class AnalysisTests(unittest.TestCase):
    def test_hand_calculated_transitions_repeats_and_missing_outputs(self):
        claims=claims_fixture();jobs=prepare.make_jobs(claims,'full3');obs={}
        for j in jobs:
            if j['claim_id']=='1':label='Refuted' if j['condition']!='A' or j['repetition']==3 else 'Supported'
            else:label='Supported' if j['condition']=='A' else 'Refuted'
            obs[j['job_id']]={'state':'valid','label':label}
        summary=analyze.summarize(claims,jobs,obs,'test',[1])
        paired=summary['details']['gpt-5.4/AB'];self.assertEqual(paired['regressions_known'],1);self.assertEqual(paired['rescues_known'],1)
        repeated=analyze.repeated_summary(claims,jobs,obs)
        row=next(x for x in repeated['per_claim_outcomes'] if x.get('claim_id')=='1' and x.get('model')=='gpt-5.4' and x.get('condition')=='A')
        self.assertAlmostEqual(row['disagreement_fraction'],2/3)
        row=next(x for x in repeated['per_claim_outcomes'] if x.get('claim_id')=='1' and x.get('model')=='gpt-5.4' and x.get('comparison')=='AB')
        self.assertAlmostEqual(row['persistence_fraction'],2/3);self.assertAlmostEqual(row['same_left_prompt_directional_loss'],1/3)
        jid=next(j['job_id'] for j in jobs if j['claim_id']=='1' and j['model']=='gpt-5.4' and j['condition']=='B' and j['repetition']==1)
        obs[jid]={'state':'invalid','label':None};bad=analyze.summarize(claims,jobs,obs,'test',[1])
        self.assertEqual(bad['details']['gpt-5.4/AB']['unclassified_pairs'],1)
        self.assertEqual(bad['details']['gpt-5.4/AB']['regression_identification_bounds'],[0.,.5])
    def test_independent_parser_ignores_result_json_and_uses_raw(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d);r=claims_fixture()[0];j=prepare.make_jobs([r],'full1')[0];attempt=path/'attempts'/j['job_id']/'attempt-01'
            raw=response('Refuted',model=j['model']);common.write_new(attempt/'request.json',{'job':j,'body':common.request(r,j['model'],j['condition'])})
            common.write_new(attempt/'response.bin',raw,binary=True);common.write_new(attempt/'receipt.json',{'http_status':200,'raw_sha256':common.digest(attempt/'response.bin')})
            common.write_new(attempt/'result.json',{'label':'Supported','state':'valid'})
            self.assertEqual(analyze.observation(path,j)['label'],'Refuted')
    def test_bootstrap_clusters_repetitions_not_independent_rows(self):
        rows=claims_fixture();rows[1]['text_cluster']=rows[0]['text_cluster']
        ci=analyze.cluster_intervals(rows,analyze.np.array([[1.],[0.]]),draws=100)
        self.assertEqual(ci,[[.5,.5]])

if __name__=='__main__':unittest.main()
