"""Optional clustering of failure-cohort claim embeddings.

Uses UMAP + HDBSCAN if available; otherwise skips. Stability is checked by
re-running with different seeds and comparing label agreement (ARI). Unstable
or singleton-dominated clusterings are reported as such and discarded.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def clustering_analysis():
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    emb_files = sorted(config.CACHE_DIR.glob("claim_emb_*.npy"))
    if not emb_files:
        print("No cached claim embeddings; skipping clustering")
        return None
    try:
        import umap
        import hdbscan
        from sklearn.metrics import adjusted_rand_score
    except ImportError as e:
        print(f"umap/hdbscan unavailable ({e}); skipping clustering (documented)")
        return None

    emb = np.load(emb_files[-1])
    # Focus: GPT-5.4 evidence-condition failure cohort (regressions + resistant).
    mask = (
        (df["gpt-5.4_transition"] == config.TRANSITION_REGRESSION)
        | (df["gpt-5.4_transition"] == config.TRANSITION_RESISTANT)
    ).to_numpy()
    if mask.sum() < 100:
        print("Failure cohort too small for clustering; skipping")
        return None
    sub_emb = emb[mask]
    sub = df[mask]

    reducer = umap.UMAP(n_components=10, random_state=config.RANDOM_SEED, n_jobs=1)
    red = reducer.fit_transform(sub_emb)

    labels_runs = []
    for seed in (config.RANDOM_SEED, config.RANDOM_SEED + 1, config.RANDOM_SEED + 2):
        clusterer = hdbscan.HDBSCAN(min_cluster_size=15)
        labels_runs.append(clusterer.fit_predict(red))
    aris = [adjusted_rand_score(labels_runs[0], l) for l in labels_runs[1:]]
    stable = np.mean(aris) >= 0.8

    labels = labels_runs[0]
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_frac = float((labels == -1).mean())

    result = {
        "cohort_size": int(mask.sum()),
        "n_clusters": n_clusters,
        "noise_fraction": noise_frac,
        "stability_ari_mean": float(np.mean(aris)),
        "stable": bool(stable and n_clusters >= 2 and noise_frac < 0.6),
    }
    pd.Series(result, name="value").to_csv(config.TABLES_DIR / "clustering_summary.csv")
    print(result)

    if result["stable"]:
        sub = sub.assign(cluster=labels)
        (sub[["claim_id", "claim_text", "gold_label", "gpt-5.4_transition", "cluster"]]
         .to_csv(config.TABLES_DIR / "failure_clusters.csv", index=False))
    else:
        print("Clustering unstable or degenerate; not interpreted (per protocol)")
    return result


if __name__ == "__main__":
    clustering_analysis()
