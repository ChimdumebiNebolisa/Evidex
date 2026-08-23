"""Resumable orchestrator for the silver-adjudication pipeline.

Stages that need GLM subagent execution (judges, resolver) cannot be driven
from inside this script; the script validates their completeness and reports
gaps, and the session orchestrator launches the corresponding subagents.
Everything else runs end-to-end here. Completed valid judgments are cached
and never rerun; freeze manifests make prior outputs append-only.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

STAGES = [
    # (name, script, needs_subagents)
    ("validate_prerequisites", "src/validate_blinding.py", False),
    ("build_cohort", "src/build_cohort.py", False),
    ("blind_cohort", "src/blind_cohort.py", False),
    ("build_stage_b", None, False),  # handled by reconstruct_evidence.py b
    ("build_stage_c", None, False),
    ("validate_blinding", "src/validate_blinding.py", False),
    ("judge_status_A", None, False),
    ("freeze_A", None, False),
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


def run(args):
    return subprocess.run([sys.executable, str(HERE / args[0])] + args[1:], cwd=str(HERE)).returncode


def main():
    for name, script, _ in STAGES:
        print(f"\n=== {name} ===")
        rc = 0
        if name == "build_stage_b":
            rc = run(["src/reconstruct_evidence.py", "b"])
        elif name == "build_stage_c":
            rc = run(["src/reconstruct_evidence.py", "c"]) if \
                (config_cache_zip := HERE / "data/cache/wiki-pages.zip").exists() else 0
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
        elif script:
            rc = run([script])
        if rc != 0:
            print(f"[halt] stage {name} failed (rc={rc})")
            sys.exit(rc)
    print("\nPipeline pass complete (subagent stages validated, not executed).")


if __name__ == "__main__":
    main()
