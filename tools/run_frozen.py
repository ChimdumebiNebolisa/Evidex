"""Run an original repository command from the preserved pre-layout commit.

Usage: python tools/run_frozen.py -- python scripts/verify_all_headlines.py
The temporary Git worktree is removed even when the command fails.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from verify_layout import ROOT, SOURCE_COMMIT, main as verify_layout


READ_ONLY_COMMANDS = {
    ("corrections_v2/verify_outputs.py",),
    ("scripts/verify_all_headlines.py",),
    ("scripts/run_all_tests.py",),
    ("corrections_v2/rerun.py", "validate", "--scope", "required"),
    ("corrections_v2/amendment_2026-09-28/amended_analysis.py", "status"),
    ("corrections_v2/amendment_2026-09-28/amended_analysis.py", "verify"),
}


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        print("Usage: python tools/run_frozen.py -- <command> [args...]", file=sys.stderr)
        return 2
    if not Path(args[0]).name.startswith("python") or tuple(args[1:]) not in READ_ONLY_COMMANDS:
        print("Only documented read-only verification commands are allowed here. "
              "Use a separate historical checkout for reproduction or inference.", file=sys.stderr)
        return 2
    verify_layout()
    with tempfile.TemporaryDirectory(prefix="evidex-frozen-") as tmp:
        checkout = Path(tmp) / "repo"
        subprocess.run(
            ["git", "worktree", "add", "--detach", "--quiet", str(checkout), SOURCE_COMMIT],
            cwd=ROOT, check=True,
        )
        try:
            return subprocess.run(args, cwd=checkout).returncode
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(checkout)],
                cwd=ROOT, check=True,
            )


if __name__ == "__main__":
    sys.exit(main())
