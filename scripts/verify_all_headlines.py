"""Run every Level 1 headline check, including GLM Stage A.

Each verifier is a subprocess so panel ``src/`` modules cannot collide.
This script only reads the research record. It does not write reports,
tables, or judgment files, and it does not run git.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "silver_adjudication_v1"


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    print(f"\n=== {' '.join(args)}  (cwd={cwd.relative_to(ROOT)}) ===")
    return subprocess.run(args, cwd=str(cwd), text=True)


def main() -> int:
    jobs = [
        ([sys.executable, "src/verify_headlines.py"], ROOT / "analysis_v2"),
        ([sys.executable, "src/verify_headlines.py", "--panel", "cursor"], SILVER),
        ([sys.executable, "src/verify_glm_stage_a.py"], SILVER),
        ([sys.executable, "src/verify_headlines.py"], SILVER / "claude_residual_panel"),
        ([sys.executable, "src/verify_headlines.py"], SILVER / "claude_full_regression_panel"),
    ]
    failed = []
    for args, cwd in jobs:
        proc = run(args, cwd)
        if proc.returncode != 0:
            failed.append(" ".join(args))
    if failed:
        print("\nFAILED:", ", ".join(failed))
        return 1
    print("\nALL LEVEL-1 CHECKS PASSED (including GLM Stage A)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
