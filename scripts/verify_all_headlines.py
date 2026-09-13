"""Run every Level 1 headline check, including GLM Stage A.

Each verifier is a subprocess so panel ``src/`` modules cannot collide.
``cross_panel_stage_a.py`` may rewrite supporting GLM comparison files;
those three paths are restored from git after the numeric check so a
verification run does not dirty frozen-adjacent reports.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "silver_adjudication_v1"
CURSOR = SILVER / "cursor_panel"
GLM_OUTPUTS = [
    CURSOR / "tables" / "cross_panel_stage_a_replication.csv",
    CURSOR / "tables" / "cross_panel_stage_a_consensus_crosstab.csv",
    CURSOR / "reports" / "CROSS_PANEL_STAGE_A_REPLICATION.md",
]


def run(args: list[str], cwd: Path, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"\n=== {' '.join(args)}  (cwd={cwd.relative_to(ROOT)}) ===")
    if capture:
        proc = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True)
        if proc.stdout:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.stderr:
            print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n")
        return proc
    return subprocess.run(args, cwd=str(cwd), text=True)


def restore_glm_outputs() -> None:
    rels = [str(p.relative_to(ROOT)).replace("\\", "/") for p in GLM_OUTPUTS]
    subprocess.run(
        ["git", "checkout", "--", *rels],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )


def check_glm(proc: subprocess.CompletedProcess) -> None:
    text = proc.stdout or ""
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        raise SystemExit("GLM Stage A: no JSON object on stdout")
    rows = json.loads(text[start : end + 1])
    checks = [
        ("n_items_compared", 1060, 0),
        ("verdict_modal_agreement", 0.8622641509433963, 0.0005),
        ("consensus_agreement", 0.8311320754716981, 0.0005),
        ("glm_ambiguous_rate", 0.22264150943396217, 0.0005),
    ]
    # consensus_agreement expected is 0.831 when printed to 3 decimals.
    # If the live value drifts only in the 4th decimal, still accept 0.831±0.0005.
    failures = []
    for key, expected, tol in checks:
        got = float(rows[key])
        if abs(got - expected) > tol:
            failures.append(f"{key}: expected {expected}, got {got}")
        else:
            print(f"ok  glm_{key}: {got}")
    if failures:
        raise SystemExit("GLM Stage A numeric check failed:\n  " + "\n  ".join(failures))
    print("ok  GLM Stage A replication numbers match the supporting report")


def main() -> int:
    jobs = [
        ([sys.executable, "src/verify_headlines.py"], ROOT / "analysis_v2"),
        ([sys.executable, "src/verify_headlines.py", "--panel", "cursor"], SILVER),
        ([sys.executable, "src/verify_headlines.py"], SILVER / "claude_residual_panel"),
        ([sys.executable, "src/verify_headlines.py"], SILVER / "claude_full_regression_panel"),
    ]
    failed = []
    for args, cwd in jobs:
        proc = run(args, cwd)
        if proc.returncode != 0:
            failed.append(" ".join(args))

    glm = run([sys.executable, "src/cross_panel_stage_a.py"], SILVER, capture=True)
    try:
        if glm.returncode != 0:
            failed.append("src/cross_panel_stage_a.py")
        else:
            check_glm(glm)
    finally:
        restore_glm_outputs()

    if failed:
        print("\nFAILED:", ", ".join(failed))
        return 1
    print("\nALL LEVEL-1 CHECKS PASSED (including GLM Stage A)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
