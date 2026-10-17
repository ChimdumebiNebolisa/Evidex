"""Pre-inference release checks: frozen identities, prepared jobs, tests and preservation."""
import ast
import collections
import json
import re
from pathlib import Path
import common
from common import HERE, ROOT, digest, load, read_inputs, value_hash, verify_freeze

def main():
    checks={};errors=[]
    seal=verify_freeze();checks['frozen_files_match']=True
    rows=read_inputs();by_id={r['claim_id']:r for r in rows}
    checks['10000_unique_records']=len(rows)==len(by_id)==10000
    checks['balanced_reference_labels']=collections.Counter(r['gold_label'] for r in rows)=={'Supported':5000,'Refuted':5000}
    checks['selected_pointer_count']=sum(len(r['selected_pointers']) for r in rows)==11137
    syntax=ast.parse((ROOT/'run_fact_check_experiment.py').read_text(encoding='utf-8'))
    prompts={n.targets[0].id:ast.literal_eval(n.value) for n in syntax.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('PROMPT_CLAIM_ONLY','PROMPT_CLAIM_PLUS')}
    checks['A_and_C_exact_historical_messages']=all(common.messages(r,'A')[0]['content']==prompts['PROMPT_CLAIM_ONLY'].format(claim=r['claim_text']) and common.messages(r,'C')[0]['content']==prompts['PROMPT_CLAIM_PLUS'].format(claim=r['claim_text'],gold_evidence=r['gold_evidence']) for r in rows)
    checks['B_only_adds_evidence_to_A']=all(common.messages(r,'B')[0]['content']==common.messages(r,'A')[0]['content']+'\nEvidence: '+r['gold_evidence'] for r in rows)
    request_hashes={}
    for design,n in [('full3',180000),('hybrid3',84000),('smoke',12)]:
        p=HERE/'prepared'/design;plan=load(p/'plan.json');jobs=[json.loads(l) for l in (p/'jobs.jsonl').read_text(encoding='utf-8').splitlines()]
        checks[design+'_job_count_and_unique_ids']=len(jobs)==len({j['job_id'] for j in jobs})==n==plan['jobs']
        checks[design+'_artifact_hashes']=digest(p/'jobs.jsonl')==plan['jobs_sha256'] and digest(HERE/'prepared/inputs.jsonl')==plan['inputs_sha256']
        valid=True
        for j in jobs:
            key=j['claim_id'],j['model'],j['condition']
            if key not in request_hashes:request_hashes[key]=value_hash(common.request(by_id[key[0]],key[1],key[2]))
            if j['request_sha256']!=request_hashes[key]:valid=False;break
        checks[design+'_all_exact_request_hashes']=valid
        if design=='full3':checks['full3_balanced_cells']=set(collections.Counter((j['model'],j['condition'],j['repetition']) for j in jobs).values())=={10000}
    text=(HERE/'TEST_RESULTS.txt').read_text(encoding='utf-8')
    matches=re.findall(r'Ran (\d+) tests?',text)
    checks['unit_tests_pass']=bool(matches) and int(matches[-1])>=24 and text.strip().endswith('OK') and 'FAILED' not in text
    checks['unit_test_count']=int(matches[-1]) if matches else 0
    integrations=sorted((HERE/'test-artifacts').glob('*/integration-check.json'))
    latest=load(integrations[-1]);summary=Path(latest['artifacts'])/'analysis/summary.json'
    provenance=load(summary.parent/'provenance.json')
    checks['latest_mock_integration_pass']=latest['status']=='PASS' and latest['generation_calls']==0 and digest(summary)==latest['summary_sha256']
    checks['integration_used_current_analysis']=provenance['analysis_source_sha256']==digest(HERE/'analyze.py')
    (HERE/'LATEST_MOCK_INTEGRATION.json').write_text(json.dumps(latest,indent=2),encoding='utf-8')
    preservation=load(HERE/'PRESERVATION.json')
    checks['historical_preservation']=not preservation['historical_files_changed'] and not preservation['unexpected_new_files'] and preservation['tracked_diff_unchanged'] and preservation['staged_diff_unchanged']
    checks['no_generation_request_artifacts']=not any((HERE/'runs').rglob('request.json'))
    checks['no_credentials_in_new_tracked_candidates']=True
    for p in HERE.rglob('*'):
        if not p.is_file() or any(x in p.parts for x in ('.deps','runs','test-artifacts','__pycache__')):continue
        if p.suffix not in ('.py','.md','.json','.txt','.csv'):continue
        if re.search(rb'sk-(?:proj-)?[A-Za-z0-9_-]{24,}',p.read_bytes()):errors.append('Possible credential in '+str(p))
    checks['no_credentials_in_new_tracked_candidates']=not errors
    for name in ['README.md','PROTOCOL.md','COST_ESTIMATE.md']:
        for url in re.findall(r'\]\(([^)]+)\)',(HERE/name).read_text(encoding='utf-8')):
            if url.startswith(('http://','https://')):continue
            if url=='RELEASE_CHECK.json':continue # This report is written at the end of this invocation.
            if not (HERE/url).is_file():errors.append('Missing document link: '+url)
    checks['document_links_exist']=not any(x.startswith('Missing document') for x in errors)
    checks['account_access_verified']=False
    # Account availability is an explicit launch limitation, not a mocked success.
    required=[v for k,v in checks.items() if isinstance(v,bool) and k!='account_access_verified']
    checks['local_build_checks_pass']=all(required) and not errors
    checks['live_readiness']='BLOCKED_PENDING_CREDENTIAL_MODEL_ACCESS_AND_APPROVED_PAID_SMOKE'
    checks['protocol_freeze_sha256']=digest(HERE/'protocol-freeze.json');checks['errors']=errors
    (HERE/'RELEASE_CHECK.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2))
    if not checks['local_build_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
