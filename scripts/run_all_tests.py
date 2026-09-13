"""Run each Evidex test suite in its own process.

Several experiment directories contain a differently-shaped ``src/run_judges.py``.
Collecting them in one pytest process imports the wrong module. Isolation here
avoids changing any experiment code.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JOBS = [
    ([sys.executable, "-m", "pytest", "tests", "-q"], ROOT / "analysis_v2"),
    ([sys.executable, "-m", "unittest", "discover", "-s", "tests"], ROOT / "silver_adjudication_v1"),
    (
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        ROOT / "silver_adjudication_v1" / "claude_residual_panel",
    ),
    (
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        ROOT / "silver_adjudication_v1" / "claude_full_regression_panel",
    ),
]


def main() -> int:
    failed = []
    for args, cwd in JOBS:
        print(f"\n=== {' '.join(args)}  (cwd={cwd.relative_to(ROOT)}) ===")
        proc = subprocess.run(args, cwd=str(cwd))
        if proc.returncode != 0:
            failed.append(str(cwd.relative_to(ROOT)))
    if failed:
        print("\nFAILED suites:", ", ".join(failed))
        return 1
    print("\nALL TEST SUITES PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
