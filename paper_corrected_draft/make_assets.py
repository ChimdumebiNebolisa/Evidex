"""Generate the corrected draft's adjudication tables and figures from the amendment A1 results.

Reads corrections_v2/amendment_2026-09-28/results/ (primary = accepted outputs, sensitivity =
first-valid outputs) and writes tables/tab_{diagnostic,stage,shared}_v2.tex and
figures/fig_{stage_nondecisive,categories}.pdf. Prints the numbers quoted in the text.

  python paper_corrected_draft/make_assets.py
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "corrections_v2/amendment_2026-09-28/results"
SETS = {"accepted": RESULTS / "primary_accepted", "first_valid": RESULTS / "sensitivity_first_valid"}
CATEGORIES = [
    ("sentence_only_gold_agreeing", "Sentence-only gold-agreeing"),
    ("title_disclosure_gold_agreeing", "Title-disclosure gold-agreeing"),
    ("structured_disclosure_gold_agreeing", "Structured-disclosure gold-agreeing"),
    ("additional_evidence_gold_agreeing", "Additional-evidence gold-agreeing"),
    ("nonmonotonic_judge_path", "Nonmonotonic judge path"),
    ("decisive_judge_fever_disagreement", "Decisive judge--FEVER disagreement"),
    ("final_nondecisive", "Final nondecisive"),
]
WITH_CI = set()


def wilson(k, n, z=1.959963984540054):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * (centre - half), 100 * (centre + half)


def load(name):
    base = SETS[name]
    grok = pd.read_csv(base / "tables/grok_claims.csv")
    return {
        "grok": grok[grok.cohort.eq("regression")].reset_index(drop=True),
        "claude": pd.read_csv(base / "tables/claude_full_claims.csv"),
        "tests": pd.read_csv(base / "tables/cross_family_tests.csv").set_index("analysis"),
        "summary": json.loads((base / "cross_family_summary.json").read_text("utf-8")),
    }


def pct(k, n=226):
    return f"{100 * k / n:.1f}\\%"


def cell(k, n=226, ci=False):
    if not ci:
        return f"{k} ({pct(k, n)})"
    lo, hi = wilson(k, n)
    return f"{k} ({pct(k, n)}; {lo:.1f}--{hi:.1f})"


def fmt_p(p):
    if p < 1e-3:
        mantissa, exponent = f"{p:.1e}".split("e")
        return f"${mantissa}\\times 10^{{{int(exponent)}}}$"
    return f"{p:.2g}" if p < 0.1 else f"{p:.2f}"


def fmt_delta(d):
    return f"${d:+.1f}$".replace("+0.0", "0.0").replace("-0.0", "0.0")


def count(frame, column):
    return int(frame[column].sum())


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def diagnostic_table(acc, fv):
    rows = []
    for key, label in CATEGORIES:
        g = int(acc["grok"].category.eq(key).sum())
        c = int(acc["claude"].category.eq(key).sum())
        c_fv = int(fv["claude"].category.eq(key).sum())
        test = acc["tests"].loc[f"category_{key}"]
        rows.append(f"{label} & {cell(g, ci=key in WITH_CI)} & {cell(c, ci=key in WITH_CI)} & "
                    f"{c_fv if c_fv != c else '='} & {fmt_delta(test.delta_right_minus_left_pp)} & {fmt_p(test.p_bh)} \\\\")
    agree, agree_fv = acc["summary"]["exact_taxonomy_agreement"], fv["summary"]["exact_taxonomy_agreement"]
    return rf"""\begin{{table}}[t]
\centering
\caption{{Adjudication outcomes for the 226 unique regressions on repaired Stage~C inputs, as counts with percentages of 226. $\Delta$ is Claude minus Grok in percentage points with exact McNemar tests, Benjamini--Hochberg adjusted over 14 cross-family tests. ``FV'' gives the Claude count under the first-valid sensitivity selection (= unchanged); Grok regression-cohort values are identical under both selections. Categories describe blinded judge-panel verdicts; they are not causes of GPT errors or corrected FEVER labels.}}
\label{{tab:diagnostic}}
\small
\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{lrrrrr}}
\toprule
Category & Grok & Claude & FV & $\Delta$ (pp) & $p_{{\mathrm{{BH}}}}$ \\
\midrule
{chr(10).join(rows)}
\midrule
\multicolumn{{6}}{{@{{}}p{{0.97\linewidth}}@{{}}}}{{Exact per-claim category agreement: {agree['k']}/226, {agree['rate_pct']:.1f}\% (Wilson {agree['wilson_low']:.1f}--{agree['wilson_high']:.1f}), $\kappa={acc['summary']['fine_cohen_kappa']:.3f}$; first-valid {agree_fv['k']}/226, {agree_fv['rate_pct']:.1f}\%, $\kappa={fv['summary']['fine_cohen_kappa']:.3f}$}} \\
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def stage_table(acc, fv):
    def row(label, column, test):
        g, c, c_fv = count(acc["grok"], column), count(acc["claude"], column), count(fv["claude"], column)
        t, t_fv = acc["tests"].loc[test], fv["tests"].loc[test]
        claude = cell(c) + (f" [{c_fv}]" if c_fv != c else "")
        delta = fmt_delta(t.delta_right_minus_left_pp) + (
            f" [{fmt_delta(t_fv.delta_right_minus_left_pp)}]" if c_fv != c else "")
        p = fmt_p(t.p_bh) + (f" [{fmt_p(t_fv.p_bh)}]" if fmt_p(t_fv.p_bh) != fmt_p(t.p_bh) else "")
        return f"{label} & {cell(g)} & {claude} & {delta} & {p} \\\\"

    reversed_g = count(acc["grok"], "reversed_after_titles") + count(acc["grok"], "reversed_at_C")
    reversed_c = count(acc["claude"], "reversed_after_titles") + count(acc["claude"], "reversed_at_C")
    body = "\n".join([
        row("Nondecisive at Stage~A", "ambiguous_A", "ambiguous_A"),
        row("Nondecisive at Stage~B", "ambiguous_B", "ambiguous_B"),
        row("Nondecisive at Stage~C", "ambiguous_C", "ambiguous_C"),
        row("Resolved by titles (A$\\rightarrow$B)", "resolved_by_titles", "resolved_by_titles"),
        row("Resolved at Stage~C (B$\\rightarrow$C)", "resolved_at_C", "resolved_at_C"),
        f"Decisive verdict reversed & {reversed_g} & {reversed_c} & 0.0 & 1.0 \\\\",
    ])
    return rf"""\begin{{table}}[t]
\centering
\caption{{Stage-wise nondecisiveness and resolution for the 226 regressions (percentages of 226). Stage~A and~B verdicts are retained historical judgments on unchanged inputs; Stage~C verdicts are new judgments on repaired inputs. $\Delta$ is Claude minus Grok with exact McNemar tests, Benjamini--Hochberg adjusted over 14 tests. Brackets give the first-valid sensitivity selection where it differs.}}
\label{{tab:stage}}
\small
\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{lrrrr}}
\toprule
Measure & Grok & Claude & $\Delta$ (pp) & $p_{{\mathrm{{BH}}}}$ \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def shared_table(acc, fv):
    def subgroup(data, family):
        a, b, c, d = json.loads(data["tests"].loc[f"{family}_nondecisive_shared_vs_specific_OR"].cells)
        return a, a + b, c, c + d

    g, c, c_fv = subgroup(acc, "grok"), subgroup(acc, "claude"), subgroup(fv, "claude")
    tg, tc, tc_fv = (x["tests"].loc[f"{f}_nondecisive_shared_vs_specific_OR"]
                     for x, f in ((acc, "grok"), (acc, "claude"), (fv, "claude")))

    def claude_cell(i):
        base = cell(c[i], c[i + 1])
        return base + (f" [{c_fv[i]} ({pct(c_fv[i], c_fv[i + 1])})]" if c_fv[i] != c[i] else "")

    return rf"""\begin{{table}}[t]
\centering
\caption{{Final Stage~C nondecisiveness among regressions shared by both GPT models versus regressions specific to one model. Odds ratios compare shared with model-specific regressions (two-test Benjamini--Hochberg family). Brackets give the Claude first-valid sensitivity selection.}}
\label{{tab:shared}}
\small
\begin{{tabular}}{{lrrr}}
\toprule
Subgroup & $n$ & Grok final nondecisive & Claude final nondecisive \\
\midrule
Shared by both GPT models & {g[1]} & {cell(g[0], g[1])} & {claude_cell(0)} \\
Exactly one GPT model & {g[3]} & {cell(g[2], g[3])} & {claude_cell(2)} \\
\midrule
Odds ratio (95\% CI) & & {tg.odds_ratio:.2f} ({tg.ci_low:.2f}--{tg.ci_high:.2f}) & {tc.odds_ratio:.2f} ({tc.ci_low:.2f}--{tc.ci_high:.2f}) [{tc_fv.odds_ratio:.2f}] \\
$p_{{\mathrm{{BH}}}}$ & & {fmt_p(tg.p_bh)} & {fmt_p(tc.p_bh)} [{fmt_p(tc_fv.p_bh)}] \\
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def figures(acc, fv):
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "pdf.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False})
    colours = {"Grok": "#4C72B0", "Claude": "#DD8452"}
    out = HERE / "figures"
    out.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    for name, frame in (("Grok", acc["grok"]), ("Claude", acc["claude"])):
        ks = [count(frame, f"ambiguous_{s}") for s in "ABC"]
        rates = [100 * k / 226 for k in ks]
        lows, highs = zip(*(wilson(k, 226) for k in ks))
        ax.errorbar(range(3), rates, yerr=[[r - lo for r, lo in zip(rates, lows)], [hi - r for r, hi in zip(rates, highs)]],
                    marker="o", capsize=3, color=colours[name], label=f"{name} (accepted)")
    k_fv = count(fv["claude"], "ambiguous_C")
    ax.plot([2.08], [100 * k_fv / 226], marker="D", mfc="white", color=colours["Claude"], linestyle="none",
            label="Claude C, first-valid")
    ax.set_xticks(range(3), ["A: sentences", "B: + titles", "C: structured\n(repaired)"])
    ax.set_ylabel("Nondecisive consensus (% of 226)")
    ax.set_ylim(0, 60)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "fig_stage_nondecisive.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    labels = [label.replace("--", "–") for _, label in CATEGORIES]
    y = range(len(CATEGORIES))
    g = [100 * acc["grok"].category.eq(k).sum() / 226 for k, _ in CATEGORIES]
    c = [100 * acc["claude"].category.eq(k).sum() / 226 for k, _ in CATEGORIES]
    c_fv = [100 * fv["claude"].category.eq(k).sum() / 226 for k, _ in CATEGORIES]
    ax.barh([i - 0.2 for i in y], g, height=0.38, color=colours["Grok"], label="Grok")
    ax.barh([i + 0.2 for i in y], c, height=0.38, color=colours["Claude"], label="Claude (accepted)")
    ax.scatter(c_fv, [i + 0.2 for i in y], marker="|", s=120, color="black", zorder=3, label="Claude, first-valid")
    ax.set_yticks(list(y), labels)
    ax.invert_yaxis()
    ax.set_xlabel("% of 226 regressions")
    handles, names = ax.get_legend_handles_labels()
    order = [names.index(n) for n in ("Grok", "Claude (accepted)", "Claude, first-valid")]
    ax.legend([handles[i] for i in order], [names[i] for i in order], frameon=False, fontsize=8,
              loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
    fig.tight_layout()
    fig.savefig(out / "fig_categories.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def quoted_numbers(acc, fv):
    out = {}
    for sel, data in (("accepted", acc), ("first_valid", fv)):
        for fam in ("grok", "claude"):
            f = data[fam]
            decisive_c = f[f.decisive_C.astype(bool)]
            out[f"{sel}/{fam}"] = {
                "nondecisive_ABC": [count(f, f"ambiguous_{s}") for s in "ABC"],
                "resolved_by_titles": count(f, "resolved_by_titles"),
                "resolved_at_C": count(f, "resolved_at_C"),
                "decisive_C_agree_fever": [int(decisive_c.agrees_fever_C.astype(bool).sum()), len(decisive_c)],
                "categories": {k: int(f.category.eq(k).sum()) for k, _ in CATEGORIES},
                "c_adds_sentence_text": int(f.c_disclosure.eq("additional_sentence_text_and_structure").sum()),
            }
        out[f"{sel}/tests"] = {i: {"delta": round(r.delta_right_minus_left_pp, 2), "p_bh": r.p_bh,
                                   "or": None if pd.isna(r.odds_ratio) else round(r.odds_ratio, 2)}
                               for i, r in data["tests"].iterrows()}
    return out


def main():
    acc, fv = load("accepted"), load("first_valid")
    write(HERE / "tables/tab_diagnostic_v2.tex", diagnostic_table(acc, fv))
    write(HERE / "tables/tab_stage_v2.tex", stage_table(acc, fv))
    write(HERE / "tables/tab_shared_v2.tex", shared_table(acc, fv))
    figures(acc, fv)
    print(json.dumps(quoted_numbers(acc, fv), indent=1, default=float))


if __name__ == "__main__":
    main()
