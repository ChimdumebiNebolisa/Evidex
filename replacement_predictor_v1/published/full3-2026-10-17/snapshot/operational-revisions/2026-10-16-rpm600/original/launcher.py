"""One launcher for twenty workers on one durable queue. No inference without run --live."""
import argparse
import json
import multiprocessing
import os
import signal
import time
import uuid
from pathlib import Path
import runner
from common import HERE, digest, load, now, read_inputs, verify_freeze, write_new
from coordination import Coordinator, Stopped, reservation, validate_limits

REVISION = HERE/'operational-revisions/2026-10-16-workers20'
DEFAULT_LIMITS = REVISION/'limits.json'
WORKERS = 20


def worker(run_dir, config, cap, event, session_id, mock=False):
    # Ctrl+C belongs to the launcher; let already submitted requests finish recording.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    store = runner.Store(run_dir)
    def cancelled():
        owner = store.db.execute("SELECT value FROM meta WHERE key='op_owner'").fetchone()
        parent = multiprocessing.parent_process()
        return event.is_set() or (parent is not None and not parent.is_alive()) or not owner or owner[0] != session_id
    coord = Coordinator(store, config, cap, cancelled=cancelled)
    try:
        if mock:
            # Only used by local tests; never selected by the CLI or environment.
            inputs = {r['claim_id']:r for r in load(Path(run_dir)/'mock-inputs.json')}
            def transport(payload):
                time.sleep(.15)
                return 200, runner.encoded({'id':'synthetic', 'model':payload['model'],
                    'choices':[{'finish_reason':'stop','message':{'content':'Supported'}}],
                    'usage':{'prompt_tokens':30,'completion_tokens':2}}), {}, False
        else:
            inputs = {r['claim_id']:r for r in read_inputs()}; transport = runner.Transport()
        while not cancelled() and not coord.stop_reason():
            item = store.claim()
            if item is None:
                counts = store.counts()
                if not counts.get('pending') and not counts.get('inflight'):
                    break
                event.wait(.2); continue
            job, attempt, lock = item
            try:
                coord.acquire(job, attempt, reservation(runner.request(inputs[job['claim_id']], job['model'], job['condition'])))
                runner.run_attempt(store, inputs[job['claim_id']], job, attempt, transport)
            except Stopped:
                # No request file means recovery will safely reschedule with a new ordinal.
                break
            finally:
                lock.__exit__(None,None,None)
    except BaseException as exc:
        coord.stop('Worker failed: '+type(exc).__name__+'; inspect artifacts before resuming')
        event.set()
        raise
    finally:
        store.db.close()


def launch(store, config, cap, resume=False, interval=10, mock=False):
    """Monitor processes, drain on interruption/halt/crash, then recover without inference."""
    with runner.job_lock(store.path/'launcher.lock') as locked:
        if not locked:
            raise ValueError('A launcher already owns this run directory')
        coord = Coordinator(store, config, cap)
        if store.db.execute("SELECT value FROM meta WHERE key='halt_reason'").fetchone():
            raise ValueError('Sticky global halt remains; inspect retained failure, never auto-clear it')
        prior_stop = coord.stop_reason()
        if coord.stop_reason() and not resume:
            raise ValueError('Prior operational stop remains; inspect it and use --resume')
        if resume:
            store.db.execute("DELETE FROM meta WHERE key='stop_requested'")
        session_id = uuid.uuid4().hex
        store.db.execute("INSERT OR REPLACE INTO meta VALUES('op_owner',?)", (session_id,))
        actions = runner.recover(store)
        if any(a['action']=='active_worker_skipped' for a in actions):
            raise ValueError('An earlier worker is still recording; wait for it before relaunching')
        if coord.stop_reason():
            raise ValueError('Recovery found a global halt; inspect retained failure')
        stamp = now().replace(':','-')+'-'+session_id
        record_dir = store.path/'launches'/stamp
        write_new(record_dir/'launch.json', {'at_utc':now(),'workers':WORKERS,'session_id':session_id,
                  'run_directory':str(store.path.resolve()),'limits':config,'max_cumulative_admissions':cap,
                  'operational_revision_sha256':digest(REVISION/'revision.json') if not mock else 'synthetic',
                  'generation_enabled':not mock,'recovery':actions,'resumed_stop_reason':prior_stop})
        ctx = multiprocessing.get_context('spawn'); event = ctx.Event(); processes = []
        interrupted = False; previous = signal.getsignal(signal.SIGINT)
        def stop_signal(signum, frame):
            nonlocal interrupted
            interrupted = True; event.set()
        signal.signal(signal.SIGINT, stop_signal)
        stop_at = None; next_report = 0
        try:
            for _ in range(WORKERS):
                p = ctx.Process(target=worker, args=(str(store.path),config,cap,event,session_id,mock))
                p.start(); processes.append(p)
            while any(p.is_alive() for p in processes):
                if interrupted:
                    coord.stop('User interruption; requests already in flight will finish recording')
                if any(p.exitcode not in (None,0) for p in processes):
                    coord.stop('Worker process exited unexpectedly; inspect before --resume')
                if coord.stop_reason() or event.is_set():
                    event.set(); stop_at = stop_at or time.monotonic()
                if time.monotonic() >= next_report:
                    progress = coord.progress(); progress['alive_workers'] = sum(p.is_alive() for p in processes)
                    print(json.dumps(progress),flush=True)
                    write_new(record_dir/('progress-'+str(time.time_ns())+'.json'),progress)
                    next_report = time.monotonic()+interval
                # Transport timeout is 120 seconds. Forced exits preserve uncertainty on recovery.
                if stop_at and time.monotonic()-stop_at > 160:
                    for p in processes:
                        if p.is_alive():
                            p.terminate()
                time.sleep(.1)
        finally:
            event.set()
            # Also drain partially started groups after launcher errors.
            for p in processes:
                p.join(timeout=130)
                if p.is_alive():
                    p.terminate(); p.join()
            signal.signal(signal.SIGINT,previous)
            recovery = runner.recover(store)
            progress = coord.progress()
            write_new(record_dir/'finished.json', {'progress':progress,'recovery':recovery,
                       'worker_exit_codes':[p.exitcode for p in processes]})
            print(json.dumps(progress),flush=True)
        return progress


def bind_revision(store):
    seal = verify_freeze()
    revision_hash = seal.get('operational_revision_sha256')
    if not revision_hash:
        raise ValueError('Operational revision has not been sealed')
    identity = {'operational_revision_sha256':revision_hash,
                'original_freeze_sha256':digest(HERE/'protocol-freeze.json')}
    path = store.path/'operational-revision.json'
    if path.exists():
        if load(path) != identity:
            raise ValueError('Run belongs to another operational revision')
    else:
        write_new(path,identity)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','status','recover','stop','run'])
    parser.add_argument('--plan',type=Path,default=HERE/'prepared/full3')
    parser.add_argument('--run-dir',type=Path,default=HERE/'runs/full3')
    parser.add_argument('--workers',type=int,choices=[WORKERS],default=WORKERS)
    parser.add_argument('--limits',type=Path,default=DEFAULT_LIMITS)
    parser.add_argument('--max-attempts',type=int)
    parser.add_argument('--live',action='store_true'); parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    if args.command=='run' and (not args.live or not args.max_attempts or args.max_attempts < 1):
        parser.error('run requires --live and an explicit positive --max-attempts; no inference made')
    config = load(args.limits); validate_limits(config)
    store, _ = runner.open_plan(args.plan,args.run_dir)
    try:
        bind_revision(store)
        planned = sum(store.counts().values())
        cap = args.max_attempts or planned*runner.MAX_ATTEMPTS
        if cap > planned*runner.MAX_ATTEMPTS:
            parser.error('Operational admission cap cannot exceed three per planned job')
        coord = Coordinator(store,config,cap)
        if args.command=='stop':
            coord.stop('Explicit stop requested; drain in-flight requests'); return
        if args.command=='recover':
            print(json.dumps(runner.recover(store),indent=2)); return
        if args.command in ('prepare','status'):
            print(json.dumps({'workers':WORKERS,'run_directory':str(store.path.resolve()),
                              'limits':config,'generation_calls':0,'progress':coord.progress()},indent=2)); return
        # Preflight is metadata-only and centralized: no 20-fold metadata traffic.
        result,path = runner.preflight()
        if result['status'] != 'model_metadata_access_verified':
            raise SystemExit('Account metadata access not verified; no generation made. See '+str(path))
        report = launch(store,config,cap,args.resume)
        if report['stop_reason'] or report['states'].get('pending') or report['states'].get('inflight'):
            raise SystemExit(2)
    finally:
        store.db.close()


if __name__=='__main__':
    main()
