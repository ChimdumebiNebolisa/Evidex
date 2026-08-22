"""Research question F: semantic embeddings and similarity.

Uses a local SentenceTransformers model. Caches per-claim embeddings keyed by
(model name, row count, claim-id hash) so reruns reuse computation.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def _cache_key(df: pd.DataFrame) -> str:
    h = hashlib.sha256()
    h.update(config.EMBED_MODEL.encode())
    h.update(str(len(df)).encode())
    h.update(",".join(map(str, df["claim_id"].tolist()[:200])).encode())
    return h.hexdigest()[:16]


def embed_texts(texts, model_name=config.EMBED_MODEL):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return model.encode(texts, batch_size=128, show_progress_bar=False,
                         normalize_embeddings=True)


def semantic_features() -> pd.DataFrame:
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET if config.ENRICHED_PARQUET.exists()
                         else config.PAIRED_PARQUET)
    key = _cache_key(df)
    sim_cache = config.CACHE_DIR / f"semantic_sim_{key}.npy"
    ev_cache = config.CACHE_DIR / f"evidence_emb_{key}.npy"

    if sim_cache.exists() and ev_cache.exists():
        df["cosine_sim_claim_evidence"] = np.load(sim_cache)
        ev_emb = np.load(ev_cache)
    else:
        cl_emb = embed_texts(df["claim_text"].fillna("").tolist())
        ev_emb = embed_texts(df["gold_evidence"].fillna("").tolist())
        sims = (cl_emb * ev_emb).sum(axis=1)
        df["cosine_sim_claim_evidence"] = sims
        np.save(sim_cache, sims)
        np.save(ev_cache, ev_emb)
        np.save(config.CACHE_DIR / f"claim_emb_{key}.npy", cl_emb)

    # Outlier flag: low similarity relative to cohort.
    med = df["cosine_sim_claim_evidence"].median()
    mad = (df["cosine_sim_claim_evidence"] - med).abs().median()
    df["semantic_outlier"] = (med - df["cosine_sim_claim_evidence"]) > (3 * mad + 1e-9)

    df.to_parquet(config.ENRICHED_PARQUET, index=False)
    print(f"Semantic similarity: median={df['cosine_sim_claim_evidence'].median():.4f}, "
          f"outliers={int(df['semantic_outlier'].sum())}")
    return df


if __name__ == "__main__":
    semantic_features()
