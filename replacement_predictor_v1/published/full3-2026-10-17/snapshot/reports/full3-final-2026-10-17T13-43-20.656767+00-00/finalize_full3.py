"""Read-only final reconciliation, followed only on PASS by the frozen analysis."""
import collections
import concurrent.futures
import csv
import datetime
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import common
import coordination
import runner
import sqlite_supervisor

ROOT=common.HERE
REPORT=Path(__file__).resolve().parent
RUN=ROOT/'runs/full3'
PLAN=ROOT/'prepared/full3'
ANALYSIS=RUN/('analysis-'+REPORT.name.removeprefix('full3-final-'))
ANALYSIS_HASH='50878788121b1ac56ae5a65c475049d3360f6781e510fa120b0cff5e87e6919b'
ALLOWED={'request.json','receipt.json','response.bin','result.json','recovery.json','transport-error.json','partial-response.bin'}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def inspect(job,queue,ledger,prior,gold):
    jid=job['job_id'];parent=RUN/'attempts'/jid
    info={'job_id':jid,'files':[],'requests':[],'issues':[],'recoveries':0}
    try:
        dirs=sorted(parent.iterdir(),key=lambda p:int(p.name.removeprefix('attempt-')))
        request_count=0;previous=None;last_started=None
        if not dirs:raise ValueError('Missing attempt directory')
        for d in dirs:
            if not d.is_dir() or not re.fullmatch(r'attempt-\d+',d.name):raise ValueError('Unexpected attempt path')
            ordinal=int(d.name.removeprefix('attempt-'));data={}
            for f in d.iterdir():
                if not f.is_file():raise ValueError('Unexpected nested artifact directory')
                raw=f.read_bytes();relative=f.relative_to(RUN).as_posix();digest=sha(raw)
                info['files'].append({'path':relative,'sha256':digest,'bytes':len(raw),'prior_match':relative in prior})
                if relative in prior and prior[relative]!=digest:raise ValueError('Previously inventoried artifact changed')
                if f.name not in ALLOWED:raise ValueError('Unrecognized attempt artifact')
                data[f.name]=raw
            if 'request.json' not in data:
                if set(data)!={'recovery.json'} or json.loads(data['recovery.json'])['reason']!='no_request_created_safe_to_schedule':
                    raise ValueError('Request-free attempt not justified by original recovery')
                if (jid,ordinal) in ledger:raise ValueError('Admission without a request')
                info['recoveries']+=1;continue
            if previous is not None and previous['state']!='pending':raise ValueError('Submission after terminal outcome')
            request_count+=1
            if request_count>runner.MAX_ATTEMPTS:raise ValueError('API attempt bound exceeded')
            req=json.loads(data['request.json']);body=req['body'];key=jid,ordinal
            if req['job']!=job or req['attempt']!=ordinal or common.value_hash(body)!=job['request_sha256']:
                raise ValueError('Saved request/plan provenance mismatch')
            if req['endpoint']!=common.ENDPOINT or body['model']!=job['model'] or any(body.get(k)!=v for k,v in common.SETTINGS.items()):
                raise ValueError('Frozen request settings changed')
            row=ledger.get(key)
            if not row or row['model']!=job['model'] or row['reserved']!=coordination.reservation(body):
                raise ValueError('Admission missing or reservation/model mismatch')
            if row['ended'] is None:raise ValueError('Unfinished admission after drain')
            if last_started is not None and row['started']<last_started:raise ValueError('Retry order reversed')
            last_started=row['started']
            if not {'receipt.json','response.bin'}<=set(data):
                justified='transport-error.json' in data or ('recovery.json' in data and json.loads(data['recovery.json'])['reason']=='request_exists_no_complete_receipt_do_not_reissue')
                if not justified or queue['state']!='uncertain':raise ValueError('Incomplete response without preserved uncertainty')
                previous={'state':'uncertain','label':None};info['requests'].append({'attempt':ordinal,'state':'uncertain','usage':None,'response_id':None});continue
            receipt=json.loads(data['receipt.json']);raw=data['response.bin']
            if sha(raw)!=receipt['raw_sha256']:raise ValueError('Receipt/raw digest mismatch')
            result=json.loads(data['result.json'])
            replay=runner.interpret(job,receipt,raw,ordinal,request_count=request_count)
            if result!=replay:raise ValueError('Saved interpretation differs from frozen parser')
            if row['state']!=result['state'] or row['http_status']!=receipt['http_status'] or json.loads(row['usage'] or 'null')!=result.get('usage'):
                raise ValueError('Ledger/result/usage mismatch')
            info['requests'].append({'attempt':ordinal,'state':result['state'],'usage':result.get('usage'),
                'response_id':result.get('response_id'),'returned_model':result.get('returned_model'),
                'raw_sha256':receipt['raw_sha256'],'http_status':receipt['http_status']})
            previous=result
        if previous is None or previous['state']!=queue['state']:raise ValueError('Queue/final saved outcome mismatch')
        if queue['attempt']!=max(int(d.name.removeprefix('attempt-')) for d in dirs):raise ValueError('Queue attempt ordinal mismatch')
        info['outcome']={**job,'state':previous['state'],'label':previous.get('label'),'correct':previous.get('label')==gold,
            'attempt_directories':len(dirs),'request_attempts':request_count,'returned_model':previous.get('returned_model')}
    except Exception as exc:
        info['issues'].append({'job_id':jid,'type':type(exc).__name__,'reason':str(exc)})
    return info


def main():
    with runner.job_lock(RUN/'finalization.lock') as owned:
        if not owned:raise ValueError('Another finalizer owns full3')
        sqlite_supervisor.verify()
        if common.digest(ROOT/'analyze.py')!=ANALYSIS_HASH:raise ValueError('Frozen analysis source changed')
        if list(RUN.glob('analysis-*')):raise ValueError('Existing analysis output requires inspection; no duplicate analysis launched')
        supervision=max((RUN/'supervision').iterdir(),key=lambda p:p.stat().st_mtime)
        launch=max((RUN/'launches').iterdir(),key=lambda p:p.stat().st_mtime)
        final_budget=common.load(supervision/'finished.json');finished=common.load(launch/'finished.json')
        if any(finished['worker_exit_codes']) or final_budget['stop_reason']:raise ValueError('Collection did not finish normally')
        for name in ['supervisor.lock','launcher.lock']:
            with runner.job_lock(RUN/name) as free:
                if not free:raise ValueError('Collection ownership remains active')
        plan=common.load(PLAN/'plan.json');identity=common.load(RUN/'run.json')
        if common.digest(PLAN/'jobs.jsonl')!=plan['jobs_sha256'] or common.digest(ROOT/'prepared/inputs.jsonl')!=plan['inputs_sha256']:
            raise ValueError('Prepared jobs or inputs changed')
        if identity['plan_sha256']!=common.digest(PLAN/'plan.json') or identity['design']!='full3':raise ValueError('Run/plan identity mismatch')
        registration=common.load(ROOT/'runs/registrations'/(identity['plan_sha256']+'.json'))
        if registration['run_directory']!=str(RUN.resolve()):raise ValueError('Plan registration changed')
        jobs=[json.loads(x) for x in (PLAN/'jobs.jsonl').read_text().splitlines()]
        by_id={j['job_id']:j for j in jobs};claims={r['claim_id']:r for r in common.read_inputs()}
        if len(jobs)!=180000 or len(by_id)!=180000 or len(claims)!=10000:raise ValueError('Frozen sample size/uniqueness mismatch')
        expected=collections.Counter({(m,c,r):10000 for m in common.MODELS for c in 'ABC' for r in [1,2,3]})
        if collections.Counter((j['model'],j['condition'],j['repetition']) for j in jobs)!=expected:raise ValueError('Model/condition/repetition coverage mismatch')
        db=sqlite3.connect((RUN/'jobs.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        try:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failed')
            rows=[dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY ordinal')]
            states=dict(db.execute('SELECT state,count(*) FROM jobs GROUP BY state'))
            if states.get('pending',0) or states.get('inflight',0):raise ValueError('Nonterminal queue; no final verification/analysis')
            if list(db.execute("SELECT * FROM meta WHERE key IN ('stop_requested','halt_reason')")):raise ValueError('Unresolved stop/halt')
            if len(rows)!=len(jobs) or any(r['id']!=j['job_id'] or r['ordinal']!=j['order'] or json.loads(r['payload'])!=j for r,j in zip(rows,jobs)):
                raise ValueError('Queue coverage/payload/randomized order mismatch')
            queue={r['id']:r for r in rows};ledger={(r['job_id'],r['attempt']):dict(r) for r in db.execute('SELECT * FROM op_attempts')}
            if any(r['ended'] is None for r in ledger.values()):raise ValueError('Response recording not drained')
            target=sqlite3.connect(REPORT/'final-jobs.sqlite');db.backup(target);target.close()
        finally:db.close()
        prior={}
        baseline=common.load(sqlite_supervisor.REVISION/'RECONCILIATION.json')
        prior_path=sqlite_supervisor.REVISION/'ARTIFACT_INVENTORY.jsonl'
        if common.digest(prior_path)!=baseline['inventory_sha256']:raise ValueError('Baseline inventory changed')
        for line in prior_path.read_text().splitlines():
            x=json.loads(line);prior[x['path']]=x['sha256']
        physical={p.name for p in (RUN/'attempts').iterdir()}
        if physical!=set(by_id):raise ValueError('Missing jobs or orphan attempt directories')
        issues=[];observed={};responses={};ids=collections.Counter();raws=collections.Counter();models=collections.Counter()
        seen_admissions=set();preserved=0;files=0;recoveries=0;unknown=0
        usage={m:collections.Counter() for m in common.MODELS}
        with (REPORT/'ARTIFACT_INVENTORY.jsonl').open('x',encoding='utf-8') as inv,(REPORT/'OUTCOMES.jsonl').open('x',encoding='utf-8') as out:
            with concurrent.futures.ThreadPoolExecutor(12) as pool:
                def task(j):return inspect(j,queue[j['job_id']],ledger,prior,claims[j['claim_id']]['gold_label'])
                for i,info in enumerate(pool.map(task,jobs),1):
                    issues.extend(info['issues']);recoveries+=info['recoveries']
                    for f in info['files']:
                        inv.write(json.dumps(f,separators=(',',':'))+'\n');files+=1;preserved+=f['prior_match']
                    for e in info['requests']:
                        seen_admissions.add((info['job_id'],e['attempt']))
                        if e.get('response_id'):ids[e['response_id']]+=1
                        if e.get('raw_sha256'):
                            raws[e['raw_sha256']]+=1
                            responses['attempts/'+info['job_id']+'/attempt-'+str(e['attempt']).zfill(2)+'/response.bin']=e['raw_sha256']
                        if e.get('returned_model'):models[e['returned_model']]+=1
                        u=e['usage'];s=usage[by_id[info['job_id']]['model']]
                        s['requests']+=1
                        if not coordination.complete_usage(u):unknown+=1;s['attempts_without_complete_usage']+=1;continue
                        s['receipts_with_usage']+=1
                        for k in ['prompt_tokens','completion_tokens']:s[k]+=u[k]
                        for key,detail,nested in [('cached_prompt_tokens','prompt_tokens_details','cached_tokens'),('reasoning_tokens','completion_tokens_details','reasoning_tokens')]:
                            if isinstance(u.get(detail),dict) and nested in u[detail]:s[key]+=u[detail][nested];s[key+'_reported_receipts']+=1
                            else:s[key+'_unreported_receipts']+=1
                    if 'outcome' in info:
                        o=info['outcome'];observed[o['job_id']]=o;out.write(json.dumps(o,separators=(',',':'))+'\n')
                    if i%10000==0:print(json.dumps({'phase':'artifact_verification','jobs':i,'issues':len(issues),'at_utc':common.now()}),flush=True)
            for f in [inv,out]:f.flush();os.fsync(f.fileno())
        if seen_admissions!=set(ledger):issues.append({'reason':'Admission/request coverage differs'})
        if preserved!=len(prior):issues.append({'reason':'Baseline artifact coverage differs'})
        if set(observed)!=set(by_id) or collections.Counter(o['state'] for o in observed.values())!=states:issues.append({'reason':'Outcome/queue coverage differs'})
        duplicates=sum(n-1 for n in ids.values() if n>1)
        if duplicates:issues.append({'reason':'Duplicate provider response IDs','count':duplicates})
        costs={m:float((Decimal(str(u['prompt_tokens']))*Decimal(str(common.RATES[m]['input']))+Decimal(str(u['completion_tokens']))*Decimal(str(common.RATES[m]['output'])))/Decimal(1000000)) for m,u in usage.items()}
        known=sum(costs.values())
        if abs(known-final_budget['known_usage_cost_usd'])>1e-8:issues.append({'reason':'Guard/independent recorded cost mismatch'})
        integrity={'at_utc':common.now(),'status':'FAIL' if issues else 'PASS','issues':issues,'states':states,'planned_unique_jobs':len(jobs),
            'queue_integrity':'ok','old_and_new_seals':'PASS','prior_artifacts_preserved':preserved,'artifact_files_hashed':files,'recovery_only_attempts':recoveries,
            'admissions':len(ledger),'jobs_with_multiple_admissions':sum(n>1 for n in collections.Counter(k[0] for k in ledger).values()),
            'duplicate_response_ids':duplicates,'duplicate_raw_hashes':sum(n-1 for n in raws.values() if n>1),'responses':len(responses),
            'usage':usage,'returned_models':models,'recorded_cost_by_model_usd':costs,'known_usage_cost_usd':known,'attempts_without_complete_usage':unknown,
            'unreported_or_uncertain_cost':'Unknown, not zero' if unknown else 'No missing usage in saved attempt ledger',
            'frozen_rates_per_million':common.RATES,'invoice_reconciled':False,'final_budget':final_budget,
            'final_database_backup_sha256':common.digest(REPORT/'final-jobs.sqlite'),
            'inventory_sha256':common.digest(REPORT/'ARTIFACT_INVENTORY.jsonl'),'outcomes_sha256':common.digest(REPORT/'OUTCOMES.jsonl'),
            'verification_source_sha256':common.digest(Path(__file__))}
        common.write_new(REPORT/'INTEGRITY.json',integrity);common.write_new(REPORT/'RESPONSE_HASHES.json',responses)
        if issues:raise ValueError('Integrity issues block frozen analysis; originals preserved')
        sqlite_supervisor.verify()
        if common.digest(ROOT/'analyze.py')!=ANALYSIS_HASH:raise ValueError('Analysis source changed before launch')
        command=[sys.executable,'-B',str(ROOT/'analyze.py'),'--plan',str(PLAN),'--run-dir',str(RUN),'--output',str(ANALYSIS)]
        env=os.environ.copy();env.pop('OPENAI_API_KEY',None)
        with (REPORT/'analysis.stdout.txt').open('x',encoding='utf-8') as stdout,(REPORT/'analysis.stderr.txt').open('x',encoding='utf-8') as stderr:
            child=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            common.write_new(REPORT/'ANALYSIS_PROCESS.json',{'at_utc':common.now(),'pid':child.pid,'parent_pid':os.getpid(),'command':command,'analysis_source_sha256':ANALYSIS_HASH,'output':str(ANALYSIS),'bootstrap_draws':2000})
            print(json.dumps({'phase':'frozen_analysis_started','pid':child.pid,'output':str(ANALYSIS),'at_utc':common.now()}),flush=True)
            code=child.wait()
        common.write_new(REPORT/'ANALYSIS_EXIT.json',{'at_utc':common.now(),'exit_code':code})
        if code:raise ValueError('Frozen analysis failed; output and diagnostics preserved')
        summary=common.load(ANALYSIS/'summary.json');provenance=common.load(ANALYSIS/'provenance.json')
        if provenance['analysis_source_sha256']!=ANALYSIS_HASH or provenance['plan_sha256']!=common.digest(PLAN/'plan.json') or provenance['inputs_sha256']!=plan['inputs_sha256']:
            raise ValueError('Analysis provenance identity mismatch')
        if {k.replace('\\','/'):v for k,v in provenance['raw_response_files'].items()}!=responses:raise ValueError('Analysis raw-response provenance coverage mismatch')
        if summary['planned_jobs']!=len(jobs) or summary['status_counts']!=states:raise ValueError('Analysis outcome coverage mismatch')
        for model,u in usage.items():
            a=summary['usage_accounting'][model]
            for left,right in [('reported_prompt_tokens','prompt_tokens'),('reported_completion_tokens','completion_tokens'),('reported_cached_prompt_tokens','cached_prompt_tokens'),('reported_reasoning_tokens','reasoning_tokens'),('receipts_with_usage','receipts_with_usage')]:
                if a[left]!=u[right]:raise ValueError('Analysis/independent usage disagreement')
        seen=set()
        with (ANALYSIS/'observations.csv').open(newline='',encoding='utf-8') as f:
            for row in csv.DictReader(f):
                jid=row['job_id'];o=observed[jid]
                if jid in seen or any(row[k]!=(str(o[k]) if o[k] is not None else '') for k in ['state','label','returned_model','attempt_directories']):raise ValueError('Analysis observation disagreement/duplicate')
                seen.add(jid)
        if seen!=set(by_id):raise ValueError('Analysis observation rows missing')
        for section,reps in [('first_pass',[1]),('repeat_representative',[1,2,3])]:
            if summary[section]['claims']!=10000:raise ValueError('Analysis claim denominator mismatch')
            for m in common.MODELS:
                for c in 'ABC':
                    subset=[o for o in observed.values() if o['model']==m and o['condition']==c and o['repetition'] in reps]
                    d=summary[section]['details'][m+'/'+c+'/accuracy_ITT']
                    if d['assigned_calls']!=len(subset) or d['correct']!=sum(o['correct'] for o in subset) or d['valid_calls']!=sum(o['state']=='valid' for o in subset):raise ValueError('Analysis accuracy numerator/denominator disagreement')
        sqlite_supervisor.verify()
        common.write_new(REPORT/'ANALYSIS_VERIFICATION.json',{'at_utc':common.now(),'status':'PASS','analysis_output':str(ANALYSIS),
            'observations_verified':len(seen),'usage_accounting_agreement':True,'accuracy_numerator_denominator_agreement':True,
            'raw_provenance_files_verified':len(responses),'all_seals':'PASS','output_files':{f.name:common.digest(f) for f in ANALYSIS.iterdir() if f.is_file()}})
        print(json.dumps({'phase':'analysis_verified','status':'PASS','recorded_cost_usd':known,'at_utc':common.now()}),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        common.write_new(REPORT/'ERROR.json',{'at_utc':common.now(),'error_type':type(exc).__name__,'reason':str(exc),'traceback':traceback.format_exc()})
        raise
