"""Bounded retries for individual SQLite statements, never for API transport."""
import json
import os
import random
import sqlite3
import time
import uuid
from pathlib import Path

Row = sqlite3.Row


class Connection(sqlite3.Connection):
    retry_seconds = 45.0
    retry_attempts = 200

    def __init__(self, database, *args, **kwargs):
        super().__init__(database,*args,**kwargs)
        self.log_path = Path(database).parent/'sqlite-runtime'/(str(os.getpid())+'-'+uuid.uuid4().hex+'.jsonl')
        self.stats = {'transactions':0,'busy_retries':0,'max_wait_seconds':0,'max_transaction_seconds':0}
        self.transaction_start = None; self.last_summary = time.monotonic()

    def log(self, event, **details):
        try:
            self.log_path.parent.mkdir(parents=True,exist_ok=True)
            with self.log_path.open('a',encoding='utf-8') as f:
                f.write(json.dumps({'at':time.time(),'event':event,**details})+'\n')
        except OSError:
            pass  # Diagnostics cannot replace or invalidate a durable response.

    def execute(self, sql, parameters=()):
        began = time.monotonic(); tries = 0; verb = sql.lstrip().split()[0].upper()
        while True:
            try:
                cursor = super().execute(sql,parameters)
                break
            except sqlite3.OperationalError as exc:
                code = getattr(exc,'sqlite_errorcode',0) & 255
                if code not in (sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED):raise
                elapsed = time.monotonic()-began
                if elapsed>=self.retry_seconds or tries>=self.retry_attempts:
                    self.log('database_retry_exhausted',verb=verb,tries=tries,elapsed=elapsed)
                    raise
                tries += 1; self.stats['busy_retries'] += 1
                self.log('database_busy',verb=verb,try_number=tries,elapsed=elapsed)
                time.sleep(min(random.uniform(.005,.05),max(0,self.retry_seconds-elapsed)))
        elapsed = time.monotonic()-began
        self.stats['max_wait_seconds'] = max(self.stats['max_wait_seconds'],elapsed)
        if verb=='BEGIN':
            self.transaction_start = time.monotonic(); self.stats['transactions'] += 1
        elif verb in ('COMMIT','ROLLBACK') and self.transaction_start is not None:
            held = time.monotonic()-self.transaction_start; self.transaction_start = None
            self.stats['max_transaction_seconds'] = max(self.stats['max_transaction_seconds'],held)
            if held>.1:self.log('slow_transaction',held_seconds=held)
        if time.monotonic()-self.last_summary>=60:
            self.log('summary',**self.stats); self.last_summary = time.monotonic()
        return cursor

    def executescript(self, script):
        # The inherited Store/Coordinator schemas contain only independent,
        # idempotent CREATE ... IF NOT EXISTS statements; retry each, not a body.
        statements = [s.strip() for s in script.split(';') if s.strip()]
        if not all(s.upper().startswith('CREATE ') and 'IF NOT EXISTS' in s.upper() for s in statements):
            return super().executescript(script)
        if self.in_transaction:self.execute('COMMIT')
        cursor = None
        for statement in statements:cursor = self.execute(statement)
        return cursor

    def close(self):
        self.log('connection_closed',**self.stats)
        return super().close()


def connect(database, timeout=30, **kwargs):
    # Short busy waits yield between attempts instead of one unfair 30-second
    # busy wait. Only SQLITE_BUSY/LOCKED statements are retried, within bounds.
    return sqlite3.connect(database,timeout=.1,factory=Connection,**kwargs)
