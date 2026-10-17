"""Run existing tests with the same SQLite wiring inherited by spawned workers."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import sqlite_supervisor

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(Path(__file__).parent),'test_*.py'))
    raise SystemExit(0 if result.wasSuccessful() else 1)
