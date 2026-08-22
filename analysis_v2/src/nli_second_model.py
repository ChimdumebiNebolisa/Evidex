"""Second independent local NLI model (robustness check for the NLI finding).

Runs typeform/distilbert-base-uncased-mnli (local, CPU, free) over the same
(evidence -> claim) pairs as the primary diagnostic, caches probabilities,
adds nli2_* columns to the enriched dataset, and writes a side-by-side
comparison of disagreement rates by transition class for both NLI models.
Diagnostic signal only; never ground truth.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

# typeform/distilbert-base-uncased-mnli id2label: 0 ENTAILMENT, 1 NEUTRAL, 2 CONTRADICTION
LABEL_IDX = {"entailment": 0, "neutral": 1, "contradiction": 2}
FEVER_TO_NLI = {"Supported": "entailment", "Refuted": "contradiction"}


def run_second_nli() -> pd.DataFrame:
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    cache = config.CACHE_DIR / "nli2_probs.npy"
    try:
        if cache.exists():
            probs = np.load(cache)
        else:
            from transformers import pipeline
            nli = pipeline("text-classification",
                           model="typeform/distilbert-base-uncased-mnli",
                           top_k=None, device=-1)
            pairs = list(zip(df["gold_evidence"].fillna(""), df["claim_text"].fillna("")))
            raw = nli([{"text": e, "text_pair": c} for e, c in pairs], batch_size=64)
            probs = np.zeros((len(df), 3))
            for i, scores in enumerate(raw):
                for s in scores:
                    probs[i, LABEL_IDX[s["label"].lower()]] = s["score"]
            np.save(cache, probs)
    except Exception as e:
        print(f"Second NLI model unavailable ({type(e).__name__}: {e}); skipping")
        return df

    df["nli2_entailment"] = probs[:, 0]
    df["nli2_neutral"] = probs[:, 1]
    df["nli2_contradiction"] = probs[:, 2]
    df["nli2_pred"] = np.array(["entailment", "neutral", "contradiction"])[probs.argmax(axis=1)]
    df["nli2_expected"] = df["gold_label"].map(FEVER_TO_NLI)
    df["nli2_disagrees_with_fever"] = df["nli2_pred"] != df["nli2_expected"]
    df["nli2_margin"] = probs.max(axis=1) - np.sort(probs, axis=1)[:, 1]
    df["nli2_weakly_warranted"] = pd.Series(
        probs[np.arange(len(df)), [LABEL_IDX[x] for x in df["nli2_expected"]]] < 0.35)

    df.to_parquet(config.ENRICHED_PARQUET, index=False)

    # Side-by-side comparison by transition class for each experiment model.
    rows = []
    for m in config.MODELS:
        for t in ["correct_to_correct", "wrong_to_correct", "wrong_to_wrong", "correct_to_wrong"]:
            sub = df[df[f"{m}_transition"] == t]
            rows.append({
                "model": m, "transition": t, "n": len(sub),
                "nli1_disagree": sub["nli_disagrees_with_fever"].mean(),
                "nli2_disagree": sub["nli2_disagrees_with_fever"].mean(),
                "nli1_weak": sub["weakly_warranted"].mean(),
                "nli2_weak": sub["nli2_weakly_warranted"].mean(),
            })
    comp = pd.DataFrame(rows)
    comp.to_csv(config.TABLES_DIR / "nli_model_comparison.csv", index=False)
    print(comp.to_string(index=False))
    # Correlation between the two diagnostics on the same claims.
    both = df[df["nli_available"] & df.get("nli2_available", True)]
    agree_diag = (both["nli_disagrees_with_fever"] == both["nli2_disagrees_with_fever"]).mean()
    print(f"\nTwo NLI models agree on disagreement flag for {agree_diag:.3f} of claims "
          f"(overall disagreement nli1={df['nli_disagrees_with_fever'].mean():.3f}, "
          f"nli2={df['nli2_disagrees_with_fever'].mean():.3f})")
    return df


if __name__ == "__main__":
    run_second_nli()
