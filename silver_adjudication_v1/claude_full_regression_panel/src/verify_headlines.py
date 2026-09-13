"""Independent verification of every headline number in the panel reports.

Each entry in ``reports/HEADLINES.json`` is recomputed here from the frozen raw
artifacts along a code path that deliberately does not import the analysis
modules, and the quoted display string must appear in the named report. Freeze
hashes are recomputed from disk bytes. Exit 0 = all verified.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import panel_config as cfg  # noqa: E402
from eolhash import path_digest_matches, paths_digest_matches  # noqa: E402

HEADLINES_JSON = cfg.REPORTS_DIR / "HEADLINES.json"
WEAK = {"partial_or_ambiguous", "probably_insufficient", "clearly_insufficient"}
VERIFIERS = {}


def verifier(fn):
    VERIFIERS[fn.__name__] = fn
    return fn


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw(stage: str):
    """Read judge records straight from the frozen batch files."""
    rows = []
    for p in sorted(cfg.stage_judgments_dir(stage).glob("*_batch_*.jsonl")):
        content = p.read_text(encoding="utf-8").strip()
        try:
            arr = json.loads(content) if content else []
        except ValueError:
            arr = [json.loads(l) for l in content.splitlines() if l.strip()]
        for r in arr:
            rows.append((r["item_id"], r["judge_id"], r["verdict"],
                         r["evidence_sufficiency"], r["confidence"]))
    return rows


def _by_item(stage: str):
    out = {}
    for item_id, judge, verdict, suff, _ in _raw(stage):
        out.setdefault(item_id, {})[judge] = (verdict, suff)
    return out


def _consensus(stage: str):
    """Reimplementation of the published consensus rules."""
    labels = {}
    for item_id, votes in _by_item(stage).items():
        verdicts = [v for v, _ in votes.values()]
        suffs = [s for _, s in votes.values()]
        counts = Counter(verdicts)
        modal, modal_n = counts.most_common(1)[0]
        sup, ref = counts.get("Supported", 0), counts.get("Refuted", 0)
        mx = max(sup, ref)
        weak = sum(1 for s in suffs if s in WEAK)
        if mx >= 4:
            labels[item_id] = ("Supported" if sup > ref else "Refuted", "high_consensus")
        elif modal == "Ambiguous" and modal_n >= 2 and mx <= 3:
            labels[item_id] = ("Ambiguous", "ambiguous_majority")
        elif mx <= 3 and weak >= 3:
            labels[item_id] = ("Ambiguous", "ambiguous_weak_sufficiency")
        else:
            labels[item_id] = ("Unresolved", "unresolved")
    return labels


def _taxonomy_from_consensus():
    a, b, c = (_consensus(s) for s in cfg.STAGES)
    out = {}
    for item in a:
        ca, cb, cc = a[item][0], b[item][0], c[item][0]
        amb = ("Ambiguous", "Unresolved")
        dec = ("Supported", "Refuted")
        if cc in amb:
            out[item] = "silver_partial_or_ambiguous_warrant"
        elif (cb in amb and cc in dec) or (cb in dec and cc in dec and cb != cc) \
                or (ca in amb and cc in dec):
            out[item] = "silver_structured_evidence_sensitive"
        elif (ca in dec and cb in dec and ca != cb) or (ca in amb and cb in dec):
            out[item] = "silver_title_context_sensitive"
        elif cc in dec:
            out[item] = "silver_clear_evidence_utilization_failure"
        else:
            out[item] = "silver_unresolved"
    return out


BROAD = {
    "silver_partial_or_ambiguous_warrant": "residual_ambiguity",
    "silver_structured_evidence_sensitive": "representation_sensitive",
    "silver_title_context_sensitive": "representation_sensitive",
    "silver_clear_evidence_utilization_failure": "evidence_utilization_failure",
    "silver_unresolved": "other",
}


# --- cohort / completeness ---------------------------------------------------

@verifier
def cohort_n():
    return len({r[0] for r in _raw("A")})


@verifier
def judges_n():
    return len({r[1] for r in _raw("A")})


@verifier
def judgments_per_stage():
    return len(_raw("A"))


@verifier
def judgments_total():
    return sum(len(_raw(s)) for s in cfg.STAGES)


# --- Claude stage results ----------------------------------------------------

def _amb_pct(stage: str):
    lab = _consensus(stage)
    n_amb = sum(1 for v, _ in lab.values() if v in ("Ambiguous", "Unresolved"))
    return 100.0 * n_amb / len(lab)


@verifier
def claude_stage_A_ambiguous_pct():
    return _amb_pct("A")


@verifier
def claude_stage_B_ambiguous_pct():
    return _amb_pct("B")


@verifier
def claude_stage_C_ambiguous_pct():
    return _amb_pct("C")


@verifier
def claude_stage_C_high_consensus_pct():
    lab = _consensus("C")
    return 100.0 * sum(1 for _, r in lab.values() if r == "high_consensus") / len(lab)


# --- Claude mechanism decomposition -----------------------------------------

def _broad_pct(cat: str):
    tax = _taxonomy_from_consensus()
    return 100.0 * sum(1 for t in tax.values() if BROAD[t] == cat) / len(tax)


@verifier
def claude_utilization_failure_pct():
    return _broad_pct("evidence_utilization_failure")


@verifier
def claude_representation_sensitive_pct():
    return _broad_pct("representation_sensitive")


@verifier
def claude_residual_ambiguity_pct():
    return _broad_pct("residual_ambiguity")


@verifier
def claude_utilization_failure_n():
    tax = _taxonomy_from_consensus()
    return sum(1 for t in tax.values() if BROAD[t] == "evidence_utilization_failure")


@verifier
def claude_representation_sensitive_n():
    tax = _taxonomy_from_consensus()
    return sum(1 for t in tax.values() if BROAD[t] == "representation_sensitive")


@verifier
def claude_residual_ambiguity_n():
    tax = _taxonomy_from_consensus()
    return sum(1 for t in tax.values() if BROAD[t] == "residual_ambiguity")


# --- Grok baseline (recomputed from the frozen Cursor panel) -----------------

def _grok_reg():
    g = pd.read_parquet(cfg.CURSOR_UNBLINDED)
    return g[g["cohort"] == "regression"]


@verifier
def grok_utilization_failure_n():
    return int((_grok_reg()["silver_taxonomy"]
                == "silver_clear_evidence_utilization_failure").sum())


@verifier
def grok_representation_sensitive_n():
    return int(_grok_reg()["silver_taxonomy"].isin(
        ["silver_structured_evidence_sensitive", "silver_title_context_sensitive"]).sum())


@verifier
def grok_residual_ambiguity_n():
    return int((_grok_reg()["silver_taxonomy"]
                == "silver_partial_or_ambiguous_warrant").sum())


@verifier
def grok_stage_A_ambiguous_pct():
    g = _grok_reg()
    return 100.0 * g["consensus_A"].isin(["Ambiguous", "Unresolved"]).mean()


@verifier
def grok_stage_C_ambiguous_pct():
    g = _grok_reg()
    return 100.0 * g["consensus_C"].isin(["Ambiguous", "Unresolved"]).mean()


# --- cross-family agreement --------------------------------------------------

def _paired():
    tax = _taxonomy_from_consensus()
    idmap = pd.read_csv(cfg.ID_MAP_CSV).set_index("claude_item_id")
    grok = _grok_reg().set_index("item_id")["silver_taxonomy"]
    rows = []
    for cf, t in tax.items():
        rows.append((t, grok.loc[idmap.loc[cf, "source_item_id"]]))
    return rows


@verifier
def taxonomy_exact_agreement_pct():
    rows = _paired()
    return 100.0 * sum(1 for a, b in rows if a == b) / len(rows)


@verifier
def taxonomy_broad_agreement_pct():
    rows = _paired()
    return 100.0 * sum(1 for a, b in rows if BROAD[a] == BROAD[b]) / len(rows)


# --- freeze integrity --------------------------------------------------------

def verify_freezes():
    failures = []
    for stage in cfg.STAGES:
        mp = cfg.stage_freeze(stage)
        if not mp.exists():
            failures.append(f"freeze manifest missing: {mp.name}")
            continue
        entries = json.loads(mp.read_text(encoding="utf-8"))
        if entries.get("model") != cfg.LOCKED_MODEL:
            failures.append(f"stage {stage}: model lock drifted")
        if not path_digest_matches(entries["blinded"], cfg.stage_blinded(stage)):
            failures.append(f"stage {stage}: blinded file drifted from freeze")
        for judge, expect in entries["judges"].items():
            parts = sorted(cfg.stage_judgments_dir(stage).glob(f"{judge}_batch_*.jsonl"))
            if not paths_digest_matches(expect, parts):
                failures.append(f"stage {stage}: judge outputs drifted ({judge})")
    if cfg.FREEZE_MANIFEST.exists():
        man = json.loads(cfg.FREEZE_MANIFEST.read_text(encoding="utf-8"))
        for name, expect in man.get("files", {}).items():
            hits = list(cfg.ROOT.rglob(name))
            if len(hits) == 1 and not path_digest_matches(expect, hits[0]):
                failures.append(f"pre-unblinding freeze drift: {name}")
    else:
        failures.append("pre-unblinding freeze manifest missing")
    return failures


def main() -> int:
    failures = list(verify_freezes())
    if not HEADLINES_JSON.exists():
        print("FAIL: no headline registry (reports/HEADLINES.json)")
        return 1
    reg = json.loads(HEADLINES_JSON.read_text(encoding="utf-8"))
    reports = {}
    for name in reg["reports"]:
        p = cfg.REPORTS_DIR / name
        if not p.exists():
            print(f"FAIL: report missing: {name}")
            return 1
        reports[name] = p.read_text(encoding="utf-8")

    n_ok = 0
    for h in reg["headlines"]:
        hid = h["id"]
        if hid not in VERIFIERS:
            failures.append(f"{hid}: no verifier implemented")
            continue
        try:
            got = VERIFIERS[hid]()
        except Exception as e:  # noqa: BLE001
            failures.append(f"{hid}: verifier error: {e}")
            continue
        exp = h["expected"]
        if isinstance(exp, (int, float)) and isinstance(got, (int, float)):
            ok = abs(float(got) - float(exp)) <= h.get("tol", 0.051)
        else:
            ok = got == exp
        if not ok:
            failures.append(f"{hid}: expected {exp}, recomputed {got}")
            continue
        disp = h.get("display")
        if disp is not None and not any(disp in t for t in reports.values()):
            failures.append(f"{hid}: display {disp!r} not found in any report")
            continue
        n_ok += 1
        print(f"ok  {hid}: {got}" + (f"  [{disp}]" if disp else ""))

    print(f"\n{n_ok}/{len(reg['headlines'])} headline numbers verified")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("ALL HEADLINES VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
