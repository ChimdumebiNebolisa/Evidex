"""Generate the silver-adjudication figures (1-8 from the protocol).

Every figure: clear title with sample sizes, source table in caption file
tables/figure_sources.csv, uncertainty where appropriate.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight", "font.size": 9})
SOURCES = []


def src(fig, table):
    SOURCES.append({"figure": fig, "source_table": str(table)})


def fig_agreement_by_stage():
    df = pd.read_csv(config.TABLES_DIR / "agreement_all_stages.csv")
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    x = range(len(df))
    ax.bar([i - 0.17 for i in x], df["pairwise_agreement_mean"] * 100, width=0.34,
           label="pairwise % agreement")
    ax.bar([i + 0.17 for i in x], df["fleiss_kappa"], width=0.34, label="Fleiss' kappa")
    ax.set_xticks(list(x)); ax.set_xticklabels([f"Stage {s}" for s in df["stage"]])
    ax.set_title(f"{config.AGREEMENT_FAMILY_LABEL} agreement by stage "
                 f"(n={int(df['n_items'].iloc[0])} items, 5 judges)")
    ax.legend(fontsize=8)
    fig.savefig(config.FIGURES_DIR / "fig1_agreement_by_stage.png")
    plt.close(fig)
    src("fig1", "tables/agreement_all_stages.csv")


def fig_ambiguity_by_cohort():
    df = pd.read_parquet(config.UNBLINDED_PARQUET)
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    order = ["regression", "resistant", "rescue", "robust"]
    for stage, color in zip(["A", "C"], ["#c44e52", "#4c72b0"]):
        rates = [((df[df["cohort"] == c][f"consensus_{stage}"]
                   .isin(["Ambiguous", "Unresolved"])).mean() * 100) for c in order]
        ax.bar([i - 0.17 if stage == "A" else i + 0.17 for i in range(4)], rates,
               width=0.34, color=color, label=f"Stage {stage}")
    ax.set_xticks(range(4)); ax.set_xticklabels(order)
    counts = df["cohort"].value_counts()
    ax.set_title("Ambiguous/Unresolved consensus rate by cohort\n"
                 + ", ".join(f"{c} n={counts[c]}" for c in order))
    ax.set_ylabel("% ambiguous or unresolved")
    ax.legend()
    fig.savefig(config.FIGURES_DIR / "fig2_ambiguity_by_cohort.png")
    plt.close(fig)
    src("fig2", "tables/statistical_tests.csv")


def fig_resolution_flow():
    df = pd.read_parquet(config.UNBLINDED_PARQUET)
    reg = df[df["cohort"] == "regression"]
    n = len(reg)
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    stages = ["Stage A", "+ titles (B)", "+ structure (C)"]
    amb = [(reg[f"consensus_{s}"].isin(["Ambiguous", "Unresolved"])).mean() * 100
           for s in ["A", "B", "C"]]
    dec = [100 - a for a in amb]
    ax.barh(stages, dec, color="#55a868", label="decisive (Supported/Refuted)")
    ax.barh(stages, amb, left=dec, color="#c44e52", label="Ambiguous/Unresolved")
    for i, (d, a) in enumerate(zip(dec, amb)):
        ax.text(d / 2, i, f"{d:.1f}%", ha="center", va="center", fontsize=8, color="white")
        ax.text(d + a / 2, i, f"{a:.1f}%", ha="center", va="center", fontsize=8, color="white")
    ax.set_title(f"Progressive disclosure: consensus verdict flow, regression cohort (n={n})")
    ax.set_xlabel("% of regression cohort")
    ax.legend(loc="lower right", fontsize=8)
    fig.savefig(config.FIGURES_DIR / "fig3_resolution_flow.png")
    plt.close(fig)
    src("fig3", "data/derived/consensus_changes.parquet")


def fig_sensitivity_by_cohort():
    df = pd.read_parquet(config.UNBLINDED_PARQUET)
    order = ["regression", "resistant", "rescue", "robust"]
    feats = [("resolved_by_titles", "resolved by titles"),
             ("resolved_only_by_structure", "resolved only by structure"),
             ("still_ambiguous_after_C", "still ambiguous after C")]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    w = 0.26
    for k, (f, label) in enumerate(feats):
        rates = [df[df["cohort"] == c][f].mean() * 100 for c in order]
        ax.bar([i + (k - 1) * w for i in range(4)], rates, width=w, label=label)
    ax.set_xticks(range(4)); ax.set_xticklabels(order)
    ax.set_title("Representation-sensitivity rates by cohort (consensus level)")
    ax.set_ylabel("% of cohort")
    ax.legend(fontsize=8)
    fig.savefig(config.FIGURES_DIR / "fig4_sensitivity_by_cohort.png")
    plt.close(fig)
    src("fig4", "tables/representation_sensitivity.csv")


def fig_verdict_change_rates():
    vc = pd.read_parquet(config.DERIVED_DIR / "verdict_changes.parquet")
    df = pd.read_parquet(config.UNBLINDED_PARQUET)[["item_id", "cohort"]]
    vc = vc.merge(df, on="item_id")
    order = ["regression", "resistant", "rescue", "robust"]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for k, (f, label) in enumerate([("change_A_to_B", "verdict change A→B"),
                                    ("change_B_to_C", "verdict change B→C")]):
        rates = [vc[vc["cohort"] == c].groupby("item_id")[f.lower() if False else f]
                 .first().mean() * 100 for c in order]
        ax.bar([i + (k - 0.5) * 0.36 for i in range(4)], rates, width=0.36, label=label)
    ax.set_xticks(range(4)); ax.set_xticklabels(order)
    ax.set_title("Per-judge verdict change rates by cohort (judge-observations pooled)")
    ax.set_ylabel("% of judge-item judgments")
    ax.legend(fontsize=8)
    fig.savefig(config.FIGURES_DIR / "fig5_verdict_change_rates.png")
    plt.close(fig)
    src("fig5", "data/derived/verdict_changes.parquet")


def fig_glm_vs_nli():
    df = pd.read_parquet(config.UNBLINDED_PARQUET)
    glm_dis = df["rule_A"] != "high_consensus"
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    cats = ["both NLI agree w/ FEVER", "one disagrees", "both disagree"]
    masks = [(~df["nli_disagrees"]) & (~df["nli2_disagrees"]),
             (df["nli_disagrees"] ^ df["nli2_disagrees"]),
             df["nli_disagrees"] & df["nli2_disagrees"]]
    rates = [glm_dis[m].mean() * 100 for m in masks]
    ns = [int(m.sum()) for m in masks]
    ax.bar(cats, rates, color=["#55a868", "#dd8452", "#c44e52"])
    for i, (r, n) in enumerate(zip(rates, ns)):
        ax.text(i, r + 1, f"{r:.1f}% (n={n})", ha="center", fontsize=8)
    ax.set_title(f"{config.AGREEMENT_FAMILY_LABEL} disagreement (Stage A) vs local NLI disagreement")
    ax.set_ylabel("% items without high consensus")
    fig.savefig(config.FIGURES_DIR / "fig6_glm_vs_nli_disagreement.png")
    plt.close(fig)
    src("fig6", "tables/statistical_tests.csv")


def fig_taxonomy_distribution():
    df = pd.read_parquet(config.UNBLINDED_PARQUET)
    order = ["regression", "resistant", "rescue", "robust"]
    tax = df["silver_taxonomy"].value_counts().index.tolist()
    fig, ax = plt.subplots(figsize=(6.5, 4))
    bottom = [0] * len(order)
    colors = plt.cm.tab20.colors
    for k, t in enumerate(tax):
        vals = [df[(df["cohort"] == c) & (df["silver_taxonomy"] == t)]
                .shape[0] / max(1, (df["cohort"] == c).sum()) * 100 for c in order]
        ax.bar(order, vals, bottom=bottom, label=t, color=colors[k % 20])
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_title("Silver diagnostic taxonomy distribution by cohort (derived, cautious)")
    ax.set_ylabel("% of cohort")
    ax.legend(fontsize=7, bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.savefig(config.FIGURES_DIR / "fig7_taxonomy_distribution.png")
    plt.close(fig)
    src("fig7", "tables/silver_by_cohort_full.csv")


def generate_figures():
    config.ensure_dirs()
    for fn in (fig_agreement_by_stage, fig_ambiguity_by_cohort, fig_resolution_flow,
               fig_sensitivity_by_cohort, fig_verdict_change_rates, fig_glm_vs_nli,
               fig_taxonomy_distribution):
        try:
            fn()
        except Exception as e:
            print(f"[warn] {fn.__name__} failed: {e}")
    pd.DataFrame(SOURCES).to_csv(config.TABLES_DIR / "figure_sources.csv", index=False)
    print("figures:", sorted(p.name for p in config.FIGURES_DIR.glob("*.png")))


if __name__ == "__main__":
    generate_figures()
