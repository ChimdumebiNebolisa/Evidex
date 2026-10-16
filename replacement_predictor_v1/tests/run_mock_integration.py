"""Synthetic end-to-end execution and analysis. Never instantiates the API transport."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import HERE, encoded, write_new, digest, now
import prepare, runner, analyze
from test_experiment import claims_fixture, response

base=HERE/'test-artifacts'/now().replace(':','-');claims=claims_fixture();jobs=prepare.make_jobs(claims,'full3')
for r in claims:r['historical_regression']=r['claim_id']=='1'
write_new(base/'prepared/inputs.jsonl',b''.join(encoded(r) for r in claims),binary=True)
write_new(base/'prepared/full3/jobs.jsonl',b''.join(encoded(j) for j in jobs),binary=True)
plan={'design':'full3','purpose':'SYNTHETIC_MOCK_ONLY','jobs':len(jobs),'inputs_sha256':digest(base/'prepared/inputs.jsonl'),'jobs_sha256':digest(base/'prepared/full3/jobs.jsonl')}
write_new(base/'prepared/full3/plan.json',plan)
store=runner.Store(base/'run',jobs,{'plan_sha256':digest(base/'prepared/full3/plan.json'),'test':'synthetic'})
by_id={r['claim_id']:r for r in claims};calls=0;failed_once=False
while True:
    item=store.claim()
    if item is None:break
    job,n,lock=item
    try:
        if job['claim_id']=='2' and job['model']=='gpt-5.4-mini' and job['condition']=='C' and job['repetition']==3:
            # Intentionally interrupted before request creation; leave inflight for analysis coverage.
            continue
        def fake(payload):
            global calls,failed_once
            calls+=1
            if not failed_once:
                failed_once=True;return 503,encoded({'error':{'code':'overloaded'}}),{},False
            label=by_id[job['claim_id']]['gold_label']
            if job['condition']=='B':label='Refuted' if label=='Supported' else 'Supported'
            if job['claim_id']=='1' and job['model']=='gpt-5.4-mini' and job['condition']=='B' and job['repetition']==1:label='Supported, because of evidence'
            return 200,response(label,model=job['model']),{'x-synthetic-test':'true'},False
        runner.run_attempt(store,by_id[job['claim_id']],job,n,fake)
    finally:lock.__exit__(None,None,None)
analyze.HERE=base;analyze.read_inputs=lambda:claims
report=analyze.analyze(base/'prepared/full3',base/'run',base/'analysis')
assert report['status_counts']=={'valid':34,'invalid':1,'missing':1},report['status_counts']
assert report['first_pass']['details']['gpt-5.4/AB']['regressions_known']==2
assert report['first_pass']['details']['gpt-5.4-mini/AB']['unclassified_pairs']==1
assert report['historical_cases_first_pass']['claims']==1
assert (base/'analysis/observations.csv').is_file()
record={'status':'PASS','synthetic_only':True,'generation_calls':0,
          'planned_jobs':len(jobs),'mock_transport_attempts':calls,'states':report['status_counts'],
          'artifacts':str(base),'summary_sha256':digest(base/'analysis/summary.json')}
write_new(base/'integration-check.json',record)
# The first delivery summary is immutable; later local test runs retain separate timestamped summaries.
if not (HERE/'MOCK_INTEGRATION.json').exists():write_new(HERE/'MOCK_INTEGRATION.json',record)
store.db.close();print('PASS: end-to-end mock execution, raw artifacts, failure coverage, independent analysis and CSV output')
