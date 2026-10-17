"""Preserve both prior seals and seal the prospective full3 throughput revision once."""
from common import HERE, digest, load, now, verify_freeze, write_new

REVISION = HERE/'operational-revisions/2026-10-16-rpm600'
PREVIOUS = HERE/'operational-revisions/2026-10-16-workers20'


def main():
    path = REVISION/'revision.json'
    if path.exists():
        verify_freeze(); print('Existing throughput revision verifies; no seal changed'); return
    baseline = load(REVISION/'BASELINE.json')
    if digest(HERE/'protocol-freeze.json') != baseline['original_freeze_sha256']:
        raise ValueError('Original seal changed')
    if digest(PREVIOUS/'revision.json') != baseline['previous_revision_sha256']:
        raise ValueError('Previous operational seal changed')
    previous = load(PREVIOUS/'revision.json')
    original = load(HERE/'protocol-freeze.json')
    replaced = {name:(REVISION/'original'/name).relative_to(HERE).as_posix()
                for name in ('common.py','coordination.py','launcher.py')}
    for name, expected in original['files'].items():
        if digest(HERE/previous['original_files'].get(name,name)) != expected:
            raise ValueError('Original experiment bytes changed: '+name)
    for name, expected in previous['files'].items():
        if expected != baseline['prior_files'][name] or digest(HERE/replaced.get(name,name)) != expected:
            raise ValueError('Previous operational bytes changed: '+name)
    if any((HERE/'runs/full3').rglob('request.json')):
        raise ValueError('Full3 already has generation requests')
    for filename,key in [('SMOKE_REPORT.json','smoke_report_sha256'),('RESPONSE_INVENTORY.json','smoke_inventory_sha256')]:
        if digest(HERE/'reports/2026-10-16-smoke'/filename) != baseline[key]:
            raise ValueError('Preserved smoke evidence changed')
    inventory = load(HERE/'reports/2026-10-16-smoke/RESPONSE_INVENTORY.json')
    for name, info in inventory['files'].items():
        if digest(HERE/name) != info['sha256']:
            raise ValueError('Preserved smoke artifact changed: '+name)
    data = (REVISION/'TEST_RESULTS.txt').read_bytes()
    tests = data.decode('utf-16' if data.startswith(b'\xff\xfe') else 'utf-8')
    if 'Ran 62 tests' not in tests or tests.strip().splitlines()[-1] != 'OK':
        raise ValueError('Expected complete passing 62-test suite')
    names = ['common.py','coordination.py','launcher.py','rate_policy.py','throughput_projection.py',
             'seal_throughput.py','tests/test_throughput.py']
    names += [(REVISION/name).relative_to(HERE).as_posix() for name in
              ('BASELINE.json','limits-600.json','CHANGE_RECORD.md','THROUGHPUT_600.md',
               'LIMIT_EVIDENCE.json','TEST_RESULTS.txt','MOCK_BENCHMARK.json')]
    record = {'revision':'2026-10-16-rpm600','sealed_at_utc':now(),
              'kind':'OPERATIONAL_ONLY_SCIENTIFIC_PROTOCOL_UNCHANGED',
              'original_freeze_sha256':baseline['original_freeze_sha256'],
              'previous_revision_sha256':baseline['previous_revision_sha256'],
              'previous_files':replaced,'files':{name:digest(HERE/name) for name in names},
              'full3_generation_calls_before_revision':0,'existing_preserved_smoke_calls':12}
    write_new(path,record); verify_freeze()
    print('Sealed throughput revision: '+digest(path))


if __name__=='__main__':
    main()
