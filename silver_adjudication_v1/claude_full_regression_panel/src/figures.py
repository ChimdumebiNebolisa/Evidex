"""Figures for the Claude full-regression panel (post-unblinding only)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze  # noqa: E402
import panel_config as cfg  # noqa: E402

LABELS = {
    "evidence_utilization_failure": "utilization\nfailure",
    "representation_sensitive": "representation-\nsensitive",
    "residual_ambiguity": "residual\nambiguity",
    "other": "other",
}


def fig_mechanism():
    df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
    n = len(df)
    cats = [c for c in analyze.BROAD_ORDER
            if ((df["grok_broad"] == c).any() or (df["claude_broad"] == c).any())]
    grok = [100.0 * (df["grok_broad"] == c).sum() / n for c in cats]
    claude = [100.0 * (df["claude_broad"] == c).sum() / n for c in cats]
    x = range(len(cats))
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar([i - 0.2 for i in x], grok, 0.4, label="Grok panel", color="#4C72B0")
    ax.bar([i + 0.2 for i in x], claude, 0.4, label="Claude panel", color="#C44E52")
    for i, (g, c) in enumerate(zip(grok, claude)):
        ax.text(i - 0.2, g + 1, f"{g:.1f}%", ha="center", fontsize=8)
        ax.text(i + 0.2, c + 1, f"{c:.1f}%", ha="center", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([LABELS[c] for c in cats], fontsize=9)
    ax.set_ylabel("% of 226 regressions")
    ax.set_title("Regression mechanism decomposition by judge family\n"
                 "(same cohort, same taxonomy rules; silver, not human ground truth)",
                 fontsize=10)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = cfg.FIGURES_DIR / "fig1_mechanism_by_family.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"-> {out.name}")


def fig_stage_ambiguity():
    df = pd.read_parquet(cfg.UNBLINDED_PARQUET)
    n = len(df)
    grok = [100.0 * df[f"grok_ambiguous_{s}"].sum() / n for s in cfg.STAGES]
    claude = [100.0 * df[f"ambiguous_{s}"].sum() / n for s in cfg.STAGES]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(cfg.STAGES, grok, "o-", label="Grok panel", color="#4C72B0")
    ax.plot(cfg.STAGES, claude, "s-", label="Claude panel", color="#C44E52")
    for s, g, c in zip(cfg.STAGES, grok, claude):
        ax.annotate(f"{g:.1f}%", (s, g), textcoords="offset points", xytext=(0, 8), fontsize=8)
        ax.annotate(f"{c:.1f}%", (s, c), textcoords="offset points", xytext=(0, -14), fontsize=8)
    ax.set_xlabel("disclosure stage (A sentences → B +titles → C +structure)")
    ax.set_ylabel("% Ambiguous or Unresolved")
    ax.set_ylim(0, max(grok + claude) * 1.25)
    ax.set_title("Consensus ambiguity across progressive disclosure", fontsize=10)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = cfg.FIGURES_DIR / "fig2_stage_ambiguity.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"-> {out.name}")


def fig_confusion():
    cm = pd.read_csv(cfg.TABLES_DIR / "taxonomy_confusion_broad.csv", index_col=0)
    keep = [c for c in cm.index if cm.loc[c].sum() or cm[c].sum()]
    cm = cm.loc[keep, keep]
    fig, ax = plt.subplots(figsize=(6.2, 5.0))
    im = ax.imshow(cm.to_numpy(), cmap="Blues")
    ax.set_xticks(range(len(cm.columns)))
    ax.set_xticklabels([LABELS[c].replace("\n", " ") for c in cm.columns],
                       rotation=25, ha="right", fontsize=8)
    ax.set_yticks(range(len(cm.index)))
    ax.set_yticklabels([LABELS[c].replace("\n", " ") for c in cm.index], fontsize=8)
    for i in range(len(cm.index)):
        for j in range(len(cm.columns)):
            v = int(cm.iloc[i, j])
            ax.text(j, i, v, ha="center", va="center", fontsize=9,
                    color="white" if v > cm.to_numpy().max() / 2 else "black")
    ax.set_xlabel("Claude mechanism")
    ax.set_ylabel("Grok mechanism")
    ax.set_title("Claim-level mechanism agreement (n=226)", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.7, label="claims")
    fig.tight_layout()
    out = cfg.FIGURES_DIR / "fig3_mechanism_confusion.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"-> {out.name}")


if __name__ == "__main__":
    cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_mechanism()
    fig_stage_ambiguity()
    fig_confusion()
