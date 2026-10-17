"""Continue offline work after the confirmed Windows update restart; no inference."""
import collections
import csv
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import traceback

HERE=Path(__file__).resolve().parent
REPORT=HERE.parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
import common
import runner
import sqlite_supervisor

RUN=ROOT/'runs/full3'
PLAN=ROOT/'prepared/full3'
PRECHECK=common.load(HERE/'PRECHECK.json')
OUTPUT=Path(PRECHECK['new_analysis_output'])
SOURCE=PRECHECK['frozen_analysis_source_sha256']


def main():
    with runner.job_lock(RUN/'finalization.lock') as owned:
        if not owned:raise ValueError('Another offline finalizer owns full3')
        sqlite_supervisor.verify()
        integrity=common.load(REPORT/'INTEGRITY.json')
        if common.digest(REPORT/'INTEGRITY.json')!=PRECHECK['old_integrity_report_sha256'] or integrity['status']!='PASS':
            raise ValueError('Completed integrity record changed')
        if common.digest(ROOT/'analyze.py')!=SOURCE:raise ValueError('Frozen analysis source changed')
        if OUTPUT.exists() or (REPORT/'ANALYSIS_VERIFICATION.json').exists():raise ValueError('Existing output requires inspection; no duplicate analysis')
        db=sqlite3.connect((RUN/'jobs.sqlite').as_uri()+'?mode=ro',uri=True)
        try:
            if dict(db.execute('SELECT state,count(*) FROM jobs GROUP BY state'))!={'valid':180000}:raise ValueError('Terminal queue changed')
            if list(db.execute("SELECT * FROM meta WHERE key IN ('stop_requested','halt_reason')")):raise ValueError('Stop/halt found')
            if db.execute('SELECT count(*) FROM op_attempts WHERE ended IS NULL').fetchone()[0]:raise ValueError('Admission recording remains active')
        finally:db.close()
        for filename,key in [('ARTIFACT_INVENTORY.jsonl','inventory_sha256'),('OUTCOMES.jsonl','outcomes_sha256')]:
            if common.digest(REPORT/filename)!=integrity[key]:raise ValueError('Independent reconciliation artifact changed')
        command=[sys.executable,'-B',str(ROOT/'analyze.py'),'--plan',str(PLAN),'--run-dir',str(RUN),'--output',str(OUTPUT)]
        env=os.environ.copy();env.pop('OPENAI_API_KEY',None)
        with (HERE/'analysis.stdout.txt').open('x',encoding='utf-8') as stdout,(HERE/'analysis.stderr.txt').open('x',encoding='utf-8') as stderr:
            child=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            common.write_new(HERE/'ANALYSIS_PROCESS.json',{'at_utc':common.now(),'pid':child.pid,'parent_pid':os.getpid(),'command':command,'analysis_source_sha256':SOURCE,'output':str(OUTPUT),'bootstrap_draws':2000,'reason':'Prior offline attempt interrupted by planned Windows update restart','recovery_source_sha256':common.digest(Path(__file__))})
            print(json.dumps({'phase':'frozen_analysis_restarted_offline','at_utc':common.now(),'pid':child.pid,'output':str(OUTPUT)}),flush=True)
            code=child.wait()
        common.write_new(HERE/'ANALYSIS_EXIT.json',{'at_utc':common.now(),'exit_code':code})
        if code:raise ValueError('Frozen analysis failed; retained diagnostics and outputs')
        summary=common.load(OUTPUT/'summary.json');provenance=common.load(OUTPUT/'provenance.json')
        expected_raw=common.load(REPORT/'RESPONSE_HASHES.json');plan=common.load(PLAN/'plan.json')
        if provenance['analysis_source_sha256']!=SOURCE or provenance['plan_sha256']!=common.digest(PLAN/'plan.json') or provenance['inputs_sha256']!=plan['inputs_sha256']:
            raise ValueError('Analysis provenance identity mismatch')
        if {k.replace('\\','/'):v for k,v in provenance['raw_response_files'].items()}!=expected_raw:raise ValueError('Raw provenance differs from complete independent inventory')
        if summary['planned_jobs']!=180000 or summary['status_counts']!=integrity['states']:raise ValueError('Analysis status/coverage mismatch')
        for model,u in integrity['usage'].items():
            a=summary['usage_accounting'][model]
            for left,right in [('reported_prompt_tokens','prompt_tokens'),('reported_completion_tokens','completion_tokens'),('reported_cached_prompt_tokens','cached_prompt_tokens'),('reported_reasoning_tokens','reasoning_tokens'),('receipts_with_usage','receipts_with_usage')]:
                if a[left]!=u[right]:raise ValueError('Analysis/independent usage disagreement')
        observed={}
        with (REPORT/'OUTCOMES.jsonl').open() as f:
            for line in f:
                x=json.loads(line);observed[x['job_id']]=x
        seen=set()
        with (OUTPUT/'observations.csv').open(newline='',encoding='utf-8') as f:
            for row in csv.DictReader(f):
                jid=row['job_id'];o=observed[jid]
                if jid in seen or any(row[k]!=(str(o[k]) if o[k] is not None else '') for k in ['claim_id','model','condition','repetition','state','label','returned_model','attempt_directories']):
                    raise ValueError('Analysis observation differs from independent outcome')
                seen.add(jid)
        if len(seen)!=180000 or seen!=set(observed):raise ValueError('Analysis observation coverage/uniqueness mismatch')
        for section,reps in [('first_pass',[1]),('repeat_representative',[1,2,3])]:
            if summary[section]['claims']!=10000:raise ValueError('Analysis claim denominator mismatch')
            for m in common.MODELS:
                for c in 'ABC':
                    subset=[o for o in observed.values() if o['model']==m and o['condition']==c and o['repetition'] in reps]
                    d=summary[section]['details'][m+'/'+c+'/accuracy_ITT']
                    if d['assigned_calls']!=len(subset) or d['correct']!=sum(o['correct'] for o in subset) or d['valid_calls']!=sum(o['state']=='valid' for o in subset):
                        raise ValueError('Analysis numerator/denominator mismatch')
        sqlite_supervisor.verify()
        common.write_new(REPORT/'ANALYSIS_VERIFICATION.json',{'at_utc':common.now(),'status':'PASS','analysis_output':str(OUTPUT),'analysis_attempt':'Offline recovery after Windows update; original interrupted attempt preserved','recovery_directory':str(HERE),
            'observations_verified':len(seen),'usage_accounting_agreement':True,'accuracy_numerator_denominator_agreement':True,'raw_provenance_files_verified':len(expected_raw),'all_seals':'PASS',
            'output_files':{f.name:common.digest(f) for f in OUTPUT.iterdir() if f.is_file()},'recovery_source_sha256':common.digest(Path(__file__))})
        print(json.dumps({'phase':'analysis_verified','status':'PASS','at_utc':common.now()}),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        common.write_new(HERE/'ERROR.json',{'at_utc':common.now(),'error_type':type(exc).__name__,'reason':str(exc),'traceback':traceback.format_exc()})
        raise
