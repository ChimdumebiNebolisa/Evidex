"""Resumable orchestrator for the silver-adjudication pipeline.

Judge/resolver subagent execution is driven by the session orchestrator.
This script validates completeness, freezes, and runs analyses. Completed
valid judgments are cached and never rerun.

Use ``--panel cursor`` to operate on the Cursor panel namespace. That path
never writes into the GLM ``judgments/`` directory and cannot unblind until
the Cursor pre-unblinding freeze manifest verifies.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Import after path setup so --panel is applied once for this process.
sys.path.insert(0, str(HERE))
import config  # noqa: E402

STAGES = [
    ("validate_prerequisites", "src/validate_blinding.py", False),
    ("build_cohort", "src/build_cohort.py", False),
    ("blind_cohort", "src/blind_cohort.py", False),
    ("build_stage_b", None, False),
    ("build_stage_c", None, False),
    ("validate_blinding", "src/validate_blinding.py", False),
    ("judge_status_A", None, False),
    ("freeze_A", None, False),
    ("cross_panel_stage_a", "src/cross_panel_stage_a.py", False),
    ("judge_status_B", None, False),
    ("freeze_B", None, False),
    ("judge_status_C", None, False),
    ("freeze_C", None, False),
    ("consensus", None, False),
    ("resolver_inputs", None, False),
    ("resolver_validate", None, False),
    ("agreement", "src/agreement_analysis.py", False),
    ("freeze_silver", None, False),
    ("representation", "src/representation_sensitivity.py", False),
    ("unblind_join", "src/join_analysis_v2.py", False),
    ("statistics", "src/statistical_analysis.py", False),
    ("figures", "src/generate_figures.py", False),
    ("verify_headlines", "src/verify_headlines.py", False),
]

# Cursor panel reuses the already-built cohort and blinded stages.
CURSOR_SKIP_REBUILD = {
    "build_cohort", "blind_cohort", "build_stage_b", "build_stage_c",
}


def panel_args():
    if config.PANEL == "cursor":
        return ["--panel", "cursor"]
    return []


def run(args):
    cmd = [sys.executable, str(HERE / args[0])] + args[1:] + panel_args()
    return subprocess.run(cmd, cwd=str(HERE)).returncode


def main():
    for name, script, _ in STAGES:
        if config.PANEL == "cursor" and name in CURSOR_SKIP_REBUILD:
            print(f"\n=== {name} (skipped: reuse existing cohort/blinded stages) ===")
            continue
        if config.PANEL != "cursor" and name == "cross_panel_stage_a":
            print(f"\n=== {name} (skipped: GLM panel is not the Cursor replication) ===")
            continue
        print(f"\n=== {name} ===")
        rc = 0
        if name == "build_stage_b":
            rc = run(["src/reconstruct_evidence.py", "b"])
        elif name == "build_stage_c":
            rc = run(["src/reconstruct_evidence.py", "c"]) if \
                (HERE / "data/cache/wiki-pages.zip").exists() else 0
        elif name.startswith("judge_status_"):
            stage = name[-1]
            rc = run(["src/run_judges.py", "status", stage])
        elif name.startswith("freeze_") and len(name) == 8:
            rc = run(["src/run_judges.py", "freeze", name[-1]])
        elif name == "consensus":
            for s in ("A", "B", "C"):
                rc = rc or run(["src/aggregate_consensus.py", s])
        elif name == "resolver_inputs":
            rc = run(["src/resolve_disagreements.py", "inputs"])
        elif name == "resolver_validate":
            for s in ("A", "B", "C"):
                rc = rc or run(["src/resolve_disagreements.py", "validate", s])
        elif name == "freeze_silver":
            rc = run(["src/join_analysis_v2.py", "--freeze-only"])
        elif name == "unblind_join":
            if not config.FREEZE_MANIFEST.exists():
                print("[halt] unblind refused: pre-unblinding freeze manifest missing")
                sys.exit(1)
            rc = run(["src/join_analysis_v2.py"])
        elif script:
            rc = run([script])
        if rc != 0:
            print(f"[halt] stage {name} failed (rc={rc})")
            sys.exit(rc)
    print("\nPipeline pass complete (subagent stages validated, not executed).")


if __name__ == "__main__":
    main()
