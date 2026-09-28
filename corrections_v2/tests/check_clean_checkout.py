"""Integration regression test in a clean, locally committed candidate clone.

Creates only a temporary Git index/unreferenced commit and local clone. Does
not change the working branch/index, push, or fabricate active judgments.
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autocrlf", choices=["true", "false"], required=True)
    args = parser.parse_args()
    scratch = Path(tempfile.mkdtemp(prefix="evidex-clean-checkout-"))
    env = dict(os.environ, GIT_INDEX_FILE=str(scratch / "candidate-index"),
               GIT_AUTHOR_NAME="Evidex local verification", GIT_AUTHOR_EMAIL="verification@localhost",
               GIT_COMMITTER_NAME="Evidex local verification", GIT_COMMITTER_EMAIL="verification@localhost")

    def git(*argv, cwd=ROOT, candidate=False, data=None):
        return subprocess.check_output(["git", *argv], cwd=cwd, env=env if candidate else None,
                                       input=data, stderr=subprocess.PIPE).decode().strip()

    branch_before = git("rev-parse", "HEAD")
    index_before = git("diff", "--cached", "--binary")
    git("read-tree", "HEAD", candidate=True)
    git("-c", "core.autocrlf=false", "add", "-A", "--", "corrections_v2", candidate=True)
    tree = git("write-tree", candidate=True)
    commit = git("commit-tree", tree, "-p", branch_before, candidate=True,
                 data=b"Local reproduction verification candidate; not published\n")
    checkout = scratch / "checkout"
    git("clone", "--shared", "--no-checkout", str(ROOT), str(checkout))
    git("config", "core.autocrlf", args.autocrlf, cwd=checkout)
    git("checkout", "--detach", commit, cwd=checkout)
    # A preserved legacy test resolves a local 'main', not origin/main.
    if subprocess.run(["git", "show-ref", "--verify", "--quiet", "refs/heads/main"], cwd=checkout).returncode:
        git("branch", "main", "refs/remotes/origin/main", cwd=checkout)
    assert not git("status", "--porcelain", cwd=checkout), "candidate checkout not clean"
    tracked = git("ls-files", "corrections_v2", cwd=checkout).splitlines()
    assert "corrections_v2/generated/output_hashes.json" in tracked
    results = []

    def run(name, command, expected=0):
        proc = subprocess.run(command, cwd=checkout, capture_output=True)
        (scratch / f"{name}.log").write_bytes(proc.stdout + proc.stderr)
        results.append({"name": name, "command": command, "exit_code": proc.returncode})
        if expected is not None and proc.returncode != expected:
            raise AssertionError(f"{name}: exit {proc.returncode}; inspect {scratch / (name + '.log')}")
        return proc

    print(f"Clean checkout {checkout}; candidate {commit}; {len(tracked)} tracked correction files", flush=True)
    fingerprints = []
    for repeat in (1, 2):
        run(f"reproduce-{repeat}", [sys.executable, "corrections_v2/reproduce.py"])
        run(f"verify-{repeat}", [sys.executable, "corrections_v2/verify_outputs.py"])
        fingerprints.append((checkout / "corrections_v2/generated/output_hashes.json").read_bytes())
        print(f"Round {repeat}: reproduced and verified", flush=True)
    assert fingerprints[0] == fingerprints[1], "repeat reproduction changed output byte identities"
    run("correction-tests", [sys.executable, "-m", "unittest", "discover", "-s", "corrections_v2/tests", "-v"])
    run("required-incomplete", [sys.executable, "corrections_v2/rerun.py", "validate", "--scope", "required"], expected=1)
    run("all-incomplete", [sys.executable, "corrections_v2/rerun.py", "validate", "--scope", "all"], expected=1)
    # Historical verifiers are intentionally preserved. Record raw-byte failures
    # separately; audit_freezes explains EOL-only equivalence without a rewrite.
    run("historical-headlines", [sys.executable, "scripts/verify_all_headlines.py"], expected=None)
    run("existing-tests", [sys.executable, "scripts/run_all_tests.py"], expected=None)
    source = checkout / "experiment_tracker_with_evidence_balanced_10000_v1.csv"
    original = source.read_bytes()
    output_before = {p.relative_to(checkout).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (checkout / "corrections_v2/generated").glob("*") if p.is_file()}
    source.write_bytes(original.replace(b"Black Canary", b"Black Canarz", 1))
    run("historical-drift-rejected", [sys.executable, "corrections_v2/reproduce.py"], expected=1)
    source.write_bytes(original)
    assert output_before == {p.relative_to(checkout).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (checkout / "corrections_v2/generated").glob("*") if p.is_file()}
    assert git("rev-parse", "HEAD") == branch_before
    assert git("diff", "--cached", "--binary") == index_before
    historical = json.loads((checkout / "corrections_v2/generated/historical_integrity.json").read_text())
    report = {"platform": platform.platform(), "python": sys.version, "core_autocrlf": args.autocrlf,
              "candidate_commit": commit, "tracked_correction_files": len(tracked),
              "clean_at_start": True, "two_rounds_byte_identical": True,
              "historical_drift_rejected_before_writes": True,
              "historical_exact_recorded_bytes": historical["exact_recorded_bytes"],
              "historical_eol_only_equivalent": historical["eol_only_equivalent"],
              "commands": results, "logs": str(scratch), "model_calls": 0}
    (scratch / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
