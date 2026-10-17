"""Seal the dated worker operational revision once; never overwrite either seal."""
from common import HERE, digest, load, now, verify_freeze, write_new

REVISION = HERE/'operational-revisions/2026-10-16-workers20'


def main():
    path = REVISION/'revision.json'
    if path.exists():
        verify_freeze(); print('Existing operational revision verifies; no seal changed'); return
    original = load(HERE/'protocol-freeze.json')
    replaced = {name:(REVISION/'original'/name).relative_to(HERE).as_posix() for name in ('common.py','runner.py')}
    for name, expected in original['files'].items():
        if digest(HERE/replaced.get(name,name)) != expected:
            raise ValueError('Original frozen bytes differ: '+name)
    if any((HERE/'runs').rglob('request.json')):
        raise ValueError('Cannot claim a prospective operational revision after generation requests exist')
    names = ['common.py','runner.py','coordination.py','launcher.py','smoke_projection.py','seal_operational.py',
             'tests/test_operations.py', 'OPERATIONAL_LAUNCH.md', 'README.md']
    names += [(REVISION/name).relative_to(HERE).as_posix() for name in ('limits.json','CHANGE_RECORD.md','TEST_RESULTS.txt','ACCESS_CHECK.json')]
    record = {'revision':'2026-10-16-workers20','sealed_at_utc':now(),
              'kind':'OPERATIONAL_ONLY_SCIENTIFIC_PROTOCOL_UNCHANGED',
              'original_freeze_sha256':digest(HERE/'protocol-freeze.json'),
              'original_files':replaced,'files':{name:digest(HERE/name) for name in names},
              'generation_calls_before_revision':0}
    write_new(path,record); verify_freeze()
    print('Sealed operational revision: '+digest(path))


if __name__=='__main__':
    main()
