"""Simple figures and an issue-flag table from frozen Claude artifacts."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
})


def issue_flag_table(cons: pd.DataFrame, unb: pd.DataFrame) -> pd.DataFrame:
    m = cons.merge(
        unb[["claude_item_id", "claude_ambiguous"]],
        left_on="item_id", right_on="claude_item_id", how="left",
    )
    rows = []
    for scope, sub in (
        ("all", m),
        ("persistent", m[m["claude_ambiguous"] == True]),  # noqa: E712
        ("resolved", m[m["claude_ambiguous"] == False]),  # noqa: E712
    ):
        flags = Counter()
        for raw in sub["issue_flags"].fillna(""):
            for f in str(raw).split(";"):
                if f and f != "none":
                    flags[f] += 1
        for flag, n in flags.most_common():
            rows.append({"scope": scope, "issue_flag": flag, "n_items": n,
                         "pct": 100.0 * n / max(len(sub), 1)})
    out = pd.DataFrame(rows)
    out.to_csv(cfg.TABLES_DIR / "issue_flags.csv", index=False)
    return out


def fig1_consensus(cons: pd.DataFrame):
    order = ["Ambiguous", "Supported", "Refuted", "Unresolved"]
    counts = cons["consensus"].value_counts().reindex(order).fillna(0)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.bar(order, counts.to_numpy(), color=["#6b7280", "#2563eb", "#dc2626", "#92400e"])
    ax.set_ylabel("Items")
    ax.set_title("Raw Claude five-judge consensus (n=231)")
    for i, v in enumerate(counts):
        ax.text(i, v + 1.5, int(v), ha="center")
    fig.tight_layout()
    fig.savefig(cfg.FIGURES_DIR / "fig1_claude_consensus.png", dpi=140)
    plt.close(fig)


def fig2_taxonomy(unb: pd.DataFrame):
    order = [
        "cross_family_persistent_ambiguity",
        "cross_family_decisive_feversame",
        "cross_family_decisive_feverdifferent",
    ]
    labels = ["Persistent\nambiguity", "Claude decisive,\nFEVER-same",
              "Claude decisive,\nFEVER-different"]
    counts = unb["cross_family_taxonomy_fever"].value_counts().reindex(order).fillna(0)
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.bar(labels, counts.to_numpy(), color=["#6b7280", "#059669", "#d97706"])
    ax.set_ylabel("Items")
    ax.set_title("Cross-family taxonomy after FEVER unblinding")
    for i, v in enumerate(counts):
        ax.text(i, v + 1.5, int(v), ha="center")
    fig.tight_layout()
    fig.savefig(cfg.FIGURES_DIR / "fig2_cross_family_taxonomy.png", dpi=140)
    plt.close(fig)


def fig3_cohort(unb: pd.DataFrame):
    order = ["regression", "resistant", "rescue", "robust"]
    rates, ns = [], []
    for c in order:
        sub = unb[unb["cohort"] == c]
        ns.append(len(sub))
        rates.append(100.0 * sub["claude_ambiguous"].mean() if len(sub) else 0.0)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.bar([f"{c}\n(n={n})" for c, n in zip(order, ns)], rates, color="#4b5563")
    ax.set_ylabel("Persistent Ambiguous/Unresolved (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Claude residual persistence by residual cohort")
    for i, v in enumerate(rates):
        ax.text(i, v + 1.5, f"{v:.1f}%", ha="center")
    fig.tight_layout()
    fig.savefig(cfg.FIGURES_DIR / "fig3_persistent_by_cohort.png", dpi=140)
    plt.close(fig)


def main():
    cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cfg.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    cons = pd.read_parquet(cfg.FREEZES_DIR / "consensus_raw.parquet")
    unb = pd.read_parquet(cfg.UNBLINDED_PARQUET)
    issue_flag_table(cons, unb)
    fig1_consensus(cons)
    fig2_taxonomy(unb)
    fig3_cohort(unb)
    pd.DataFrame([
        {"figure": "fig1", "source": "freezes/consensus_raw.parquet"},
        {"figure": "fig2", "source": "freezes/claude_unblinded.parquet"},
        {"figure": "fig3", "source": "freezes/claude_unblinded.parquet"},
    ]).to_csv(cfg.TABLES_DIR / "figure_sources.csv", index=False)
    print("wrote figures and issue_flags.csv")


if __name__ == "__main__":
    main()
