"""Research question H: data quality and benchmark diagnostics.

- exact/near duplicate claims (normalized text; near duplicates via char 3-gram Jaccard
  on minhash-style signature buckets to keep it dependency-light)
- evidence sufficiency proxies (very low lexical/semantic similarity)
- cases where both models fail in the same direction with evidence
- suspicious label/evidence relationship flags for manual review

Flags are diagnostic only; nothing is declared mislabeled without human review.
"""
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def normalize(t: str) -> str:
    return " ".join((t or "").lower().split())


def near_duplicate_buckets(texts, num_buckets=200, seed=config.RANDOM_SEED):
    """LSH-style bucketing of char 3-gram shingle sets; candidate pairs share a bucket."""
    import hashlib
    import random

    rnd = random.Random(seed)

    def shingles(t, k=3):
        t = normalize(t)
        return {t[i:i + k] for i in range(max(0, len(t) - k + 1))}

    def h(s):
        return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

    buckets = defaultdict(list)
    for idx, t in enumerate(texts):
        sh = shingles(t)
        if not sh:
            continue
        # one min-hash per bucket
        for b in range(num_buckets):
            m = min((h(s) ^ rnd.getrandbits(32)) for s in sh)
            buckets[(b, m)].append(idx)
    cand = set()
    for members in buckets.values():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                cand.add((members[i], members[j]))
    return cand


def jaccard(a: set, b: set) -> float:
    return len(a & b) / max(1, len(a | b))


def data_quality():
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET if config.ENRICHED_PARQUET.exists()
                         else config.PAIRED_PARQUET)
    texts = df["claim_text"].tolist()
    norm = [normalize(t) for t in texts]

    # Exact duplicates.
    dup_map = defaultdict(list)
    for i, t in enumerate(norm):
        dup_map[t].append(i)
    exact = [v for v in dup_map.values() if len(v) > 1]
    df["exact_duplicate_claim"] = False
    for grp in exact:
        df.loc[df.index[grp], "exact_duplicate_claim"] = True

    # Near duplicates among exact-duplicate-free claims.
    near_pairs = []
    seen_exact = set(i for grp in exact for i in grp)
    cand = near_duplicate_buckets([t for i, t in enumerate(norm) if i not in seen_exact])

    def sh(t, k=3):
        return {t[i:i + k] for i in range(max(0, len(t) - k + 1))}

    sh_cache = {}
    for i, j in cand:
        for k in (i, j):
            if k not in sh_cache:
                sh_cache[k] = sh(norm[k])
        score = jaccard(sh_cache[i], sh_cache[j])
        if score >= 0.85:
            near_pairs.append((i, j, score))
    df["near_duplicate_claim"] = False
    for i, j, _ in near_pairs:
        df.loc[df.index[i], "near_duplicate_claim"] = True
        df.loc[df.index[j], "near_duplicate_claim"] = True

    # Shared same-direction evidence-condition failures.
    same_dir = (
        (df["gpt-5.4_evidence_pred"] == df["gpt-5.4-mini_evidence_pred"])
        & (df["gpt-5.4_evidence_pred"] != df["gold_label"])
    )
    df["both_models_fail_same_direction"] = same_dir

    # Weak evidence-sufficiency flags (diagnostics, not verdicts).
    df["flag_low_lexical_overlap"] = df["lexical_overlap"] < 0.2
    if "cosine_sim_claim_evidence" in df.columns:
        df["flag_low_semantic_sim"] = df["cosine_sim_claim_evidence"] < (
            df["cosine_sim_claim_evidence"].quantile(0.02))
    if "nli_disagrees_with_fever" in df.columns and df["nli_available"].any():
        df["flag_nli_disagreement"] = df["nli_disagrees_with_fever"] & (df["nli_margin"] < 0.3)

    df.to_parquet(config.ENRICHED_PARQUET, index=False)

    summary = {
        "n_claims": len(df),
        "exact_duplicate_groups": len(exact),
        "claims_in_exact_duplicate_groups": int(df["exact_duplicate_claim"].sum()),
        "near_duplicate_pairs": len(near_pairs),
        "claims_in_near_duplicates": int(df["near_duplicate_claim"].sum()),
        "both_models_fail_same_direction_with_evidence": int(same_dir.sum()),
    }
    pd.Series(summary, name="value").to_csv(config.TABLES_DIR / "data_quality_summary.csv")
    for k, v in summary.items():
        print(f"{k}: {v}")
    return df


if __name__ == "__main__":
    data_quality()
