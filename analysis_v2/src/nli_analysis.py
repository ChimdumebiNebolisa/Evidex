"""Research question E: independent local NLI diagnostic.

Runs a local NLI model over (evidence -> claim) pairs, compares the predicted
relationship with the FEVER gold label, and flags high-disagreement cases.
The NLI model is a diagnostic signal only, never ground truth.

Caches probabilities; degrades gracefully if the model cannot be downloaded.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

# cross-encoder/nli-deberta-v3-small label order: contradiction, neutral, entailment
LABEL_MAP = {"contradiction": 0, "neutral": 1, "entailment": 2}
FEVER_TO_NLI = {"Supported": "entailment", "Refuted": "contradiction"}


def nli_analysis() -> pd.DataFrame:
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET if config.ENRICHED_PARQUET.exists()
                         else config.PAIRED_PARQUET)
    cache = config.CACHE_DIR / "nli_probs.npy"
    try:
        if cache.exists():
            probs = np.load(cache)
        else:
            from transformers import pipeline
            nli = pipeline("text-classification",
                           model=config.NLI_MODEL,
                           top_k=None, device=-1)
            pairs = list(zip(df["gold_evidence"].fillna(""), df["claim_text"].fillna("")))
            raw = nli([{"text": e, "text_pair": c} for e, c in pairs], batch_size=64)
            probs = np.zeros((len(df), 3))
            for i, scores in enumerate(raw):
                for s in scores:
                    probs[i, LABEL_MAP[s["label"]]] = s["score"]
            np.save(cache, probs)
    except Exception as e:
        print(f"NLI model unavailable ({type(e).__name__}: {e}); skipping NLI stage")
        df["nli_available"] = False
        df.to_parquet(config.ENRICHED_PARQUET, index=False)
        return df

    df["nli_entailment"] = probs[:, 2]
    df["nli_contradiction"] = probs[:, 0]
    df["nli_neutral"] = probs[:, 1]
    df["nli_pred"] = np.array(["contradiction", "neutral", "entailment"])[probs.argmax(axis=1)]
    df["nli_expected"] = df["gold_label"].map(FEVER_TO_NLI)
    df["nli_disagrees_with_fever"] = df["nli_pred"] != df["nli_expected"]
    df["nli_margin"] = probs.max(axis=1) - np.sort(probs, axis=1)[:, 1]
    # Weak warrant: expected class probability low and margin small.
    df["weakly_warranted"] = (
        df.apply(lambda r: probs[r.name, LABEL_MAP[r["nli_expected"]]], axis=1) < 0.35
    )
    df["nli_available"] = True

    df.to_parquet(config.ENRICHED_PARQUET, index=False)

    # Agreement summary by transition class.
    if "gpt-5.4_transition" in df.columns:
        tab = df.groupby("gpt-5.4_transition")["nli_disagrees_with_fever"].agg(["mean", "size"])
        tab.to_csv(config.TABLES_DIR / "nli_disagreement_by_transition.csv")
        print(tab.to_string())
    print(f"NLI diag available; overall disagreement with FEVER label: "
          f"{df['nli_disagrees_with_fever'].mean():.3f}")
    return df


if __name__ == "__main__":
    nli_analysis()
