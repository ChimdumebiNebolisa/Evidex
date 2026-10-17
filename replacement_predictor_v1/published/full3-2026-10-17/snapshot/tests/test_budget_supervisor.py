"""Cost-guard tests use synthetic ledgers/transports only."""
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import budget_supervisor as guard
import common
import coordination
import runner
from test_operations import fixture, config, response


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.path = Path(self.temp.name)
        self.rows,self.jobs = fixture(2)
        self.store = runner.Store(self.path,self.jobs,{'synthetic_only':True})
        self.c = coordination.Coordinator(self.store,config(),clock=lambda:1000,jitter=lambda:.001)
        features = {j['job_id']:(j['model'],100) for j in self.jobs}
        priors = {m:{'calls':6,'prompt':600,'completion':12,'estimate':600} for m in common.MODELS}
        self.p = guard.Projection(features,priors)

    def tearDown(self):
        self.store.db.close(); self.temp.cleanup()

    def insert(self,jid='0',attempt=1,state='valid',usage=None,status=200):
        self.store.db.execute('INSERT INTO op_attempts(job_id,attempt,model,started,ended,reserved,http_status,state,usage) VALUES(?,?,?,?,?,?,?,?,?)',
            (jid,attempt,self.jobs[int(jid)]['model'],1000,1001 if state else None,200,status,state,json.dumps(usage)))
        if state not in (None,'pending'):self.store.state(jid,state)

    def test_prepared_baseline_matches_preserved_smoke_without_calls(self):
        p = guard.Projection.prepared()
        self.assertEqual(sum(t['calls'] for t in p.totals.values()),180000)
        self.assertEqual(p.totals['gpt-5.4']['prompt'],6534021)
        estimate = sum(guard.cost(m,t['prompt']*p.priors[m]['prompt']/p.priors[m]['estimate'],
            t['calls']*p.priors[m]['completion']/p.priors[m]['calls']) for m,t in p.totals.items())
        self.assertAlmostEqual(estimate,29.678725076763484)

    def test_known_usage_and_remaining_cost_are_separate(self):
        self.insert(usage={'prompt_tokens':100,'completion_tokens':2})
        s = self.p.snapshot(self.store.db,clock=1002)
        self.assertEqual(s['completed_jobs'],1)
        self.assertAlmostEqual(s['known_usage_cost_usd'],guard.cost('gpt-5.4',100,2))
        self.assertAlmostEqual(s['remaining_forecast_usd'],guard.cost('gpt-5.4-mini',100,2))
        self.assertEqual(s['successful_http_calls_last_60_seconds'],1)

    def test_missing_usage_and_inflight_are_reserved_not_free(self):
        self.insert(state=None,status=None)
        s = self.p.snapshot(self.store.db)
        self.assertGreater(s['unreported_and_inflight_reservation_usd'],0)
        self.assertEqual(s['attempts_without_reported_usage'],1)
        self.assertAlmostEqual(s['remaining_forecast_usd'],guard.cost('gpt-5.4-mini',100,2))
        self.store.db.execute("UPDATE op_attempts SET state='uncertain',ended=1002")
        self.store.state('0','uncertain')
        self.assertEqual(self.p.snapshot(self.store.db)['attempts_without_reported_usage'],1)

    def test_retry_costs_and_multiplier_are_retained(self):
        self.insert(state='pending',usage=None,status=503)
        self.insert(attempt=2,usage={'prompt_tokens':100,'completion_tokens':2})
        s = self.p.snapshot(self.store.db)
        self.assertEqual(s['admissions'],2)
        self.assertAlmostEqual(s['per_model']['gpt-5.4']['attempt_multiplier'],8/7)
        self.assertGreater(s['unreported_and_inflight_reservation_usd'],0)

    def test_invalid_terminal_output_is_charged_without_replacement(self):
        self.insert(state='invalid',usage={'prompt_tokens':100,'completion_tokens':32})
        s = self.p.snapshot(self.store.db)
        self.assertEqual(s['failures'],1)
        self.assertGreater(s['known_usage_cost_usd'],0)
        self.assertEqual(s['per_model']['gpt-5.4']['remaining_projected_usd'],0)

    def test_strict_ceiling_and_existing_stop_are_preserved(self):
        self.assertIsNone(guard.enforce(self.store.db,{'projected_total_cost_usd':35}))
        self.store.db.execute("INSERT INTO meta VALUES('stop_requested','Original stop')")
        guard.enforce(self.store.db,{'projected_total_cost_usd':35.01})
        self.assertEqual(self.c.stop_reason(),'Original stop')

    def test_budget_stop_blocks_admissions_and_drains_saved_response(self):
        job,n,lock = self.store.claim()
        try:
            self.c.acquire(job,n,200)
            guard.enforce(self.store.db,{'projected_total_cost_usd':35.01})
            with self.assertRaises(coordination.Stopped):
                self.c.admission({'job_id':'new','model':'gpt-5.4-mini'},1,200)
            result = runner.run_attempt(self.store,self.rows[0],job,n,
                lambda _: (200,response(job['model']),{},False))
            self.assertEqual(result['state'],'valid')
            self.assertEqual(len(list(self.path.rglob('response.bin'))),1)
            self.assertEqual(len(list(self.path.rglob('request.json'))),1)
            self.assertIsNone(self.store.claim())
        finally:lock.__exit__(None,None,None)

    def test_monitor_failure_stops_admissions_and_signals_drain(self):
        class Broken:
            def snapshot(self,db):raise RuntimeError('Synthetic monitor failure')
        self.store.db.execute("INSERT INTO meta VALUES('op_owner','new')")
        directory = self.path/'monitor'
        with patch.object(guard._thread,'interrupt_main') as interrupt:
            guard.watch(self.path,Broken(),directory,threading.Event())
            interrupt.assert_called_once()
        self.assertIn('Cost monitor failed',self.c.stop_reason())
        self.assertEqual(common.load(directory/'monitor-error.json')['error_type'],'RuntimeError')

    def test_resume_waits_for_new_launcher_owner_before_monitoring(self):
        self.store.db.execute("INSERT INTO meta VALUES('op_owner','old')")
        self.store.db.execute("INSERT INTO meta VALUES('stop_requested','Reviewed previous stop')")
        class OverBudget:
            def snapshot(self,db):return {'projected_total_cost_usd':36,'completed_jobs':0}
        done = threading.Event()
        with patch.object(guard._thread,'interrupt_main') as interrupt:
            thread = threading.Thread(target=guard.watch,args=(self.path,OverBudget(),self.path/'monitor',done,'old'))
            thread.start(); time.sleep(.1)
            self.assertEqual(self.c.stop_reason(),'Reviewed previous stop')
            self.store.db.execute("DELETE FROM meta WHERE key='stop_requested'")
            self.store.db.execute("UPDATE meta SET value='new' WHERE key='op_owner'")
            thread.join(timeout=5); done.set()
            self.assertFalse(thread.is_alive()); interrupt.assert_not_called()
        self.assertIn('Budget forecast exceeds',self.c.stop_reason())

    def test_thousand_job_milestone_is_written_before_budget_stop(self):
        self.store.db.execute("INSERT INTO meta VALUES('op_owner','new')")
        class Milestone:
            def snapshot(self,db):return {'projected_total_cost_usd':36,'completed_jobs':1000}
        directory = self.path/'monitor'
        guard.watch(self.path,Milestone(),directory,threading.Event())
        record = common.load(directory/'first-1000-completed.json')
        self.assertEqual(record['completed_jobs'],1000)
        self.assertIn('Budget forecast exceeds',record['stop_reason'])
