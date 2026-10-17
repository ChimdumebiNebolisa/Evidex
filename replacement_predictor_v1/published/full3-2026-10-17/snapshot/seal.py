"""Fingerprint the local prospective protocol and implementation; never redate a seal."""
import json
import subprocess
from common import HERE, ROOT, digest, now, load, verify_freeze, write_new

def main():
    if (HERE/'protocol-freeze.json').exists():
        verify_freeze(); print('Existing freeze verifies; no new freeze written'); return
    if (HERE/'runs').exists() and any((HERE/'runs').rglob('request.json')):
        raise SystemExit('Cannot create a prospective freeze after inference requests exist')
    names = ['PROTOCOL.md', 'common.py', 'prepare.py', 'runner.py', 'analyze.py', 'seal.py',
             'requirements.txt', 'official-sources.json', 'COST_ESTIMATE.json',
             'prepared/inputs.jsonl', 'prepared/input-verification.json', 'MESSAGE_EXAMPLES.json']
    names += [p.relative_to(HERE).as_posix() for p in (HERE/'prepared').rglob('*') if p.is_file() and p.name in ('plan.json','jobs.jsonl')]
    names += [p.relative_to(HERE).as_posix() for p in (HERE/'tests').glob('*.py')]
    names += [p.relative_to(HERE).as_posix() for p in HERE.glob('*.py')]
    files = {name:digest(HERE/name) for name in sorted(set(names))}
    value = {'frozen_at_utc':now(), 'local_protocol_date':'2026-10-16',
             'status':'LOCAL_PROSPECTIVE_PROTOCOL_NOT_EXTERNALLY_PREREGISTERED',
             'generation_calls_before_freeze':0,
             'historical_branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
             'historical_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'files':files}
    write_new(HERE/'protocol-freeze.json',value); verify_freeze()
    print(json.dumps({'frozen_at_utc':value['frozen_at_utc'],'files':len(files),'freeze_sha256':digest(HERE/'protocol-freeze.json')}))

if __name__=='__main__':main()
