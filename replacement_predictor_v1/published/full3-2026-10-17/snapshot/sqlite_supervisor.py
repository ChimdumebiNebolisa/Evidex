"""Select the separately sealed SQLite operational revision for the same run."""
import json
import sqlite3
import sys
import budget_supervisor
import common
import coordination
import launcher
import runner
import sqlite_coordination
import sqlite_runtime

REVISION = common.HERE/'operational-revisions/2026-10-17-sqlite-recovery'


def install():
    # The frozen Store/transport/parser are reused. Only its SQLite connection
    # factory and the selected operational coordinator are substituted.
    runner.sqlite3 = sqlite_runtime
    coordination.Coordinator = sqlite_coordination.Coordinator
    launcher.Coordinator = sqlite_coordination.Coordinator


def verify():
    budget_supervisor.verify()
    record = common.load(REVISION/'revision.json')
    for name,expected in record['files'].items():
        if common.digest(common.HERE/name)!=expected:raise ValueError('SQLite revision changed: '+name)
    for name,expected in record['previous_seals'].items():
        if common.digest(common.HERE/name)!=expected:raise ValueError('Previous seal changed: '+name)


install()  # Spawned workers import this entry point before calling the old worker.


if __name__=='__main__':
    verify()
    if '--resume' not in sys.argv:raise SystemExit('This revision requires --resume on the existing full3 queue')
    reconciliation = common.load(REVISION/'RECONCILIATION.json')
    if reconciliation['status']!='PASS':raise SystemExit('Reconciliation did not pass; remain stopped')
    with sqlite3.connect(common.HERE/'runs/full3/jobs.sqlite') as db:
        stops = dict(db.execute("SELECT key,value FROM meta WHERE key IN ('stop_requested','halt_reason')"))
        states = dict(db.execute('SELECT state,count(*) FROM jobs GROUP BY state'))
    if 'halt_reason' in stops or stops.get('stop_requested')!=reconciliation['resolved_operational_stop']:
        raise SystemExit('Only the reconciled SQLite operational stop may be cleared')
    if states!=reconciliation['states']:raise SystemExit('Queue changed since reconciliation; remain stopped')
    common.write_new(common.HERE/'runs/full3'/('sqlite-resume-'+common.now().replace(':','-')+'.json'),
        {'at_utc':common.now(),'revision_sha256':common.digest(REVISION/'revision.json'),
         'prior_recorded_cost_usd':reconciliation['recorded_cost_usd'],'prior_states':states,
         'resolved_operational_stop':stops['stop_requested'],'entry_point':__file__})
    budget_supervisor.main()
