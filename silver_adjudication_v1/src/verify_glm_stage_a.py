"""Read-only GLM Stage A replication check.

Recomputes frozen GLM-5.3 Stage A vs frozen Cursor Stage A and checks the
published supporting numbers. Does not write tables or reports.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cross_panel_stage_a import replicate_stage_a  # noqa: E402

EXPECTED = [
    ("n_items_compared", 1060, 0),
    ("verdict_modal_agreement", 0.8622641509433963, 0.0005),
    ("consensus_agreement", 0.8311320754716981, 0.0005),
    ("glm_ambiguous_rate", 0.22264150943396227, 0.0005),
]


def main() -> int:
    rows = replicate_stage_a(write=False)
    failures = []
    for key, expected, tol in EXPECTED:
        got = float(rows[key])
        if abs(got - expected) > tol:
            failures.append(f"{key}: expected {expected}, got {got}")
        else:
            print(f"ok  glm_{key}: {got}")
    if failures:
        print("FAIL: GLM Stage A read-only check")
        for line in failures:
            print(" -", line)
        return 1
    print("ALL GLM STAGE A HEADLINES VERIFIED (read-only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
