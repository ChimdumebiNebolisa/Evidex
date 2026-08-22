"""Publication-quality figures. Every figure answers a stated research question."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight", "font.size": 9})

T4 = [config.TRANSITION_ROBUST, config.TRANSITION_RESCUE,
      config.TRANSITION_RESISTANT, config.TRANSITION_REGRESSION]
T4_LABEL = {"correct_to_correct": "Robust\n(correct→correct)",
            "wrong_to_correct": "Rescue\n(wrong→correct)",
            "wrong_to_wrong": "Resistant\n(wrong→wrong)",
            "correct_to_wrong": "Regression\n(correct→wrong)"}


def fig_transition_matrices(df):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    for ax, m in zip(axes, config.MODELS):
        counts = df[f"{m}_transition"].value_counts().reindex(T4, fill_value=0)
        ax.bar(range(4), counts.values, color=["#4c72b0", "#55a868", "#c44e52", "#8172b2"])
        ax.set_xticks(range(4))
        ax.set_xticklabels([T4_LABEL[t] for t in T4], fontsize=7)
        for i, v in enumerate(counts.values):
            ax.text(i, v + 50, f"{v}\n({v/len(df)*100:.1f}%)", ha="center", fontsize=7)
        ax.set_title(m)
        ax.set_ylabel("claims")
        ax.set_ylim(0, counts.max() * 1.25)
    fig.suptitle("Q1: Four-way evidence transition classes per model (n=10,000 each)", y=1.05)
    fig.savefig(config.FIGURES_DIR / "fig1_transition_matrices.png")
    plt.close(fig)


def fig_transitions_by_label(df):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), sharey=True)
    for ax, m in zip(axes, config.MODELS):
        tab = (df.groupby(["gold_label", f"{m}_transition"]).size()
               .unstack().reindex(columns=T4, fill_value=0) / 5000 * 100)
        tab.T.plot.bar(ax=ax, color=["#4c72b0", "#c44e52"], legend=(m == config.MODELS[0]))
        ax.set_title(m)
        ax.set_xticklabels([T4_LABEL[t].replace("\n", " ") for t in T4], fontsize=7, rotation=20)
        ax.set_ylabel("% of label cohort")
    fig.suptitle("Q7/B: Transition rates by gold label (Supported vs Refuted)", y=1.05)
    fig.savefig(config.FIGURES_DIR / "fig2_transitions_by_label.png")
    plt.close(fig)


def fig_cross_model(df):
    ct = pd.crosstab(df["gpt-5.4_transition"], df["gpt-5.4-mini_transition"]).reindex(
        index=T4, columns=T4, fill_value=0)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    im = ax.imshow(ct.values, cmap="Blues")
    ax.set_xticks(range(4)); ax.set_yticks(range(4))
    ax.set_xticklabels([t.replace("_", "→") for t in T4], rotation=30, ha="right", fontsize=7)
    ax.set_yticklabels([t.replace("_", "→") for t in T4], fontsize=7)
    ax.set_xlabel("gpt-5.4-mini"); ax.set_ylabel("gpt-5.4")
    for i in range(4):
        for j in range(4):
            ax.text(j, i, ct.values[i, j], ha="center", va="center", fontsize=7,
                    color="white" if ct.values[i, j] > ct.values.max() / 2 else "black")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Q4/I: Cross-model transition concordance")
    fig.savefig(config.FIGURES_DIR / "fig3_cross_model_matrix.png")
    plt.close(fig)


def fig_similarity_by_transition(df):
    if "cosine_sim_claim_evidence" not in df.columns:
        return
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), sharey=True)
    for ax, m in zip(axes, config.MODELS):
        data = [df.loc[df[f"{m}_transition"] == t, "cosine_sim_claim_evidence"].dropna()
                for t in T4]
        ax.boxplot(data, tick_labels=[T4_LABEL[t].replace("\n", " ") for t in T4])
        ax.set_xticklabels([T4_LABEL[t].replace("\n", " ") for t in T4], rotation=20, fontsize=7)
        ax.set_title(m)
        ax.set_ylabel("cosine(claim, evidence)")
    fig.suptitle("QF: Semantic similarity distributions by transition class", y=1.05)
    fig.savefig(config.FIGURES_DIR / "fig4_similarity_by_transition.png")
    plt.close(fig)


def fig_evidence_set_size(df):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), sharey=True)
    for ax, m in zip(axes, config.MODELS):
        sub = df[df["evidence_set_size"] <= 3]
        tab = (sub.groupby(["evidence_set_size", f"{m}_transition"]).size()
               .unstack(fill_value=0)
               .reindex(columns=T4, fill_value=0))
        rates = tab.div(tab.sum(axis=1), axis=0) * 100
        rates[[config.TRANSITION_RESCUE, config.TRANSITION_REGRESSION,
               config.TRANSITION_RESISTANT]].plot(ax=ax)
        ax.set_title(m); ax.set_xlabel("evidence-set size (sentences)")
        ax.set_ylabel("% of claims")
    fig.suptitle("QC: Transition probability vs evidence-set size", y=1.05)
    fig.savefig(config.FIGURES_DIR / "fig5_evidence_set_size.png")
    plt.close(fig)


def fig_nli(df):
    if "nli_entailment" not in df.columns or not df.get("nli_available", False).all():
        return
    fig, ax = plt.subplots(figsize=(5, 3.5))
    for t, color in zip(T4, ["#4c72b0", "#55a868", "#c44e52", "#8172b2"]):
        vals = df.loc[df[f"gpt-5.4_transition"] == t, "nli_disagrees_with_fever"].mean() * 100
        ax.bar(T4_LABEL[t].replace("\n", " "), vals, color=color)
        ax.text(list(T4).index(t), vals + 0.5, f"{vals:.1f}%", ha="center", fontsize=7)
    ax.set_ylabel("% NLI prediction ≠ FEVER label")
    ax.set_xticklabels([T4_LABEL[t].replace("\n", " ") for t in T4], rotation=20, fontsize=7)
    ax.set_title("QE: Local NLI / FEVER disagreement by transition class (gpt-5.4)")
    fig.savefig(config.FIGURES_DIR / "fig6_nli_disagreement.png")
    plt.close(fig)


def generate_figures():
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET if config.ENRICHED_PARQUET.exists()
                         else config.PAIRED_PARQUET)
    fig_transition_matrices(df)
    fig_transitions_by_label(df)
    fig_cross_model(df)
    fig_similarity_by_transition(df)
    fig_evidence_set_size(df)
    fig_nli(df)
    print("Figures written:", sorted(p.name for p in config.FIGURES_DIR.glob("*.png")))


if __name__ == "__main__":
    generate_figures()
