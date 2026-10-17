"""Read-only reconciliation of the stopped real run before authorized resumption."""
import collections
import concurrent.futures
import json
import os
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import budget_supervisor
import common
import runner

ROOT=common.HERE
REVISION=Path(__file__).resolve().parent
RUN=ROOT/'runs/full3'


def inspect_job(args):
    path,job,ledger=args
    files=[];results=[];ids=[];raw_hashes=[];errors=[];requests=0
    try:
        for directory in sorted(path.iterdir(),key=lambda p:int(p.name.split('-')[-1])):
            if not directory.is_dir():raise ValueError('Unexpected file at job level')
            for artifact in sorted(directory.iterdir()):
                if artifact.is_file():
                    files.append({'path':artifact.relative_to(RUN).as_posix(),'sha256':common.digest(artifact),'bytes':artifact.stat().st_size})
            if not (directory/'request.json').exists():
                if not (directory/'recovery.json').exists():raise ValueError('Attempt without request or recovery')
                continue
            requests+=1
            if requests>runner.MAX_ATTEMPTS:raise ValueError('Request-bearing attempt limit exceeded')
            if results and results[-1]['state']!='pending':raise ValueError('Submission after terminal outcome')
            saved=common.load(directory/'request.json');receipt=common.load(directory/'receipt.json')
            raw=(directory/'response.bin').read_bytes();result=common.load(directory/'result.json')
            if saved['job']!=job or common.value_hash(saved['body'])!=job['request_sha256']:raise ValueError('Request provenance mismatch')
            if saved['endpoint']!=common.ENDPOINT:raise ValueError('Endpoint changed')
            if any(saved['body'].get(k)!=v for k,v in common.SETTINGS.items()):raise ValueError('Scientific settings changed')
            if common.digest(directory/'response.bin')!=receipt['raw_sha256']:raise ValueError('Raw response hash mismatch')
            replay=runner.interpret(job,receipt,raw,saved['attempt'],request_count=requests)
            if replay!=result:raise ValueError('Saved interpretation differs from frozen parser')
            key=job['job_id'],saved['attempt']
            if key not in ledger:raise ValueError('Request missing from admission ledger')
            row=ledger[key]
            if row['ended'] is None or row['state']!=result['state'] or row['http_status']!=receipt['http_status']:raise ValueError('Ledger result mismatch')
            if json.loads(row['usage'] or 'null')!=result.get('usage'):raise ValueError('Ledger usage mismatch')
            obj=json.loads(raw)
            if obj.get('id'):ids.append(obj['id'])
            raw_hashes.append(receipt['raw_sha256']);results.append(result)
    except Exception as exc:
        errors.append({'job_id':job['job_id'],'error_type':type(exc).__name__,'reason':str(exc) if isinstance(exc,ValueError) else 'Saved artifact missing or unreadable'})
    return {'job_id':job['job_id'],'files':files,'results':results,'request_count':requests,'response_ids':ids,'raw_hashes':raw_hashes,'errors':errors}


def main():
    budget_supervisor.verify()
    backup=common.load(REVISION/'BACKUP.json')
    if common.digest(REVISION/'backup/jobs.sqlite')!=backup['backup_sha256']:raise ValueError('Consistent backup changed')
    plan=common.load(ROOT/'prepared/full3/plan.json')
    if common.digest(ROOT/'prepared/full3/jobs.jsonl')!=plan['jobs_sha256']:raise ValueError('Prepared plan changed')
    if common.digest(ROOT/'prepared/inputs.jsonl')!=plan['inputs_sha256']:raise ValueError('Prepared inputs changed')
    if common.load(RUN/'run.json')['plan_sha256']!=common.digest(ROOT/'prepared/full3/plan.json'):raise ValueError('Run identity mismatch')
    jobs=[json.loads(line) for line in (ROOT/'prepared/full3/jobs.jsonl').read_text().splitlines()]
    by_id={j['job_id']:j for j in jobs}
    if len(jobs)!=len(by_id) or len(jobs)!=180000:raise ValueError('Prepared job count/duplicates')
    db=sqlite3.connect((RUN/'jobs.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failed')
        rows=list(db.execute('SELECT * FROM jobs ORDER BY ordinal'))
        if len(rows)!=180000:raise ValueError('Queue job coverage mismatch')
        for row,job in zip(rows,jobs):
            if row['id']!=job['job_id'] or row['ordinal']!=job['order'] or json.loads(row['payload'])!=job:raise ValueError('Queue payload/order mismatch')
        states=dict(db.execute('SELECT state,count(*) FROM jobs GROUP BY state'))
        if states!={'pending':138554,'valid':41446}:raise ValueError('Stopped queue state changed')
        stops=dict(db.execute("SELECT key,value FROM meta WHERE key IN ('halt_reason','stop_requested')"))
        if stops!={'stop_requested':'Worker process exited unexpectedly; inspect before --resume'}:raise ValueError('Unresolved or different halt')
        ledger={(r['job_id'],r['attempt']):dict(r) for r in db.execute('SELECT * FROM op_attempts')}
        if len(ledger)!=41446 or any(r['ended'] is None for r in ledger.values()):raise ValueError('Unfinished or changed ledger')
        if len({k[0] for k in ledger})!=len(ledger):raise ValueError('Multiple admissions for a stopped job')
        latest=max((RUN/'launches').glob('*'),key=lambda p:p.stat().st_mtime)
        recovery=common.load(latest/'finished.json')['recovery']
        returned=[]
        for item in recovery:
            row=db.execute('SELECT state,attempt FROM jobs WHERE id=?',(item['job_id'],)).fetchone()
            directory=RUN/'attempts'/item['job_id']/('attempt-'+str(row['attempt']).zfill(2))
            if item['action']=='no_request_created_safe_to_schedule':
                if row['state']!='pending' or (directory/'request.json').exists():raise ValueError('Returned job has transmission ambiguity')
                if common.load(directory/'recovery.json')['reason']!=item['action']:raise ValueError('Returned job recovery mismatch')
                returned.append({'job_id':item['job_id'],'state':row['state'],'attempt_ordinal':row['attempt'],'request_files':0})
        if len(returned)!=8:raise ValueError('Expected eight returned jobs')
        physical=list((RUN/'attempts').iterdir())
        if any(p.name not in by_id for p in physical):raise ValueError('Orphan attempt directory')
        issues=[];usage={m:{'prompt_tokens':0,'completion_tokens':0,'cached_prompt_tokens':0,'reasoning_tokens':0,'receipts':0} for m in common.MODELS}
        ids=collections.Counter();hashes=collections.Counter();counts=collections.Counter();observed=set();file_count=0
        with (REVISION/'ARTIFACT_INVENTORY.jsonl').open('x',encoding='utf-8') as inventory:
            with concurrent.futures.ThreadPoolExecutor(8) as pool:
                tasks=((p,by_id[p.name],ledger) for p in physical)
                for i,info in enumerate(pool.map(inspect_job,tasks),1):
                    issues.extend(info['errors']);ids.update(info['response_ids']);hashes.update(info['raw_hashes'])
                    for artifact in info['files']:inventory.write(json.dumps(artifact,separators=(',',':'))+'\n');file_count+=1
                    for result in info['results']:
                        model=by_id[info['job_id']]['model'];u=result.get('usage')
                        if not isinstance(u,dict) or any(k not in u for k in ('prompt_tokens','completion_tokens')):
                            issues.append({'job_id':info['job_id'],'reason':'Unreported usage; preserve rather than assume zero'});continue
                        s=usage[model];s['receipts']+=1;s['prompt_tokens']+=u['prompt_tokens'];s['completion_tokens']+=u['completion_tokens']
                        s['cached_prompt_tokens']+=(u.get('prompt_tokens_details') or {}).get('cached_tokens',0)
                        s['reasoning_tokens']+=(u.get('completion_tokens_details') or {}).get('reasoning_tokens',0)
                        counts[result['state']]+=1;observed.add(info['job_id'])
                    if i%5000==0:print(json.dumps({'inspected_job_directories':i,'issues':len(issues)}),flush=True)
            inventory.flush();os.fsync(inventory.fileno())
        if observed!={r['id'] for r in rows if r['state']=='valid'}:issues.append({'reason':'Completed queue and saved response coverage differ'})
        if any(n>1 for n in ids.values()):issues.append({'reason':'Duplicate provider response IDs'})
        if any(n>1 for n in hashes.values()):issues.append({'reason':'Duplicate raw response hashes'})
        cost=sum((u['prompt_tokens']*common.RATES[m]['input']+u['completion_tokens']*common.RATES[m]['output'])/1e6 for m,u in usage.items())
        if abs(cost-6.86945225)>1e-8:issues.append({'reason':'Cumulative recorded cost mismatch'})
        common.write_new(REVISION/'RECONCILIATION.json',{'at_utc':common.now(),'status':'FAIL' if issues else 'PASS','issues':issues,
            'states':states,'planned_unique_jobs':180000,'ledger_admissions':len(ledger),'duplicate_admissions':0,
            'saved_response_counts':dict(counts),'artifact_files_hashed':file_count,'inventory_sha256':common.digest(REVISION/'ARTIFACT_INVENTORY.jsonl'),
            'duplicate_response_ids':sum(n-1 for n in ids.values() if n>1),'duplicate_raw_response_hashes':sum(n-1 for n in hashes.values() if n>1),
            'usage':usage,'recorded_cost_usd':cost,'returned_jobs':returned,'recovered_response':'51856_gpt-5.4_C_r03',
            'recovered_response_frozen_reparse_and_provenance_verified':'51856_gpt-5.4_C_r03' in observed,
            'resolved_operational_stop':stops['stop_requested'],'seals_verified':True,'original_artifacts_modified':False})
        print(json.dumps({'status':'FAIL' if issues else 'PASS','issues':issues,'artifact_files':file_count,'cost':cost},indent=2))
        if issues:raise SystemExit(1)
    finally:db.close()


if __name__=='__main__':main()
