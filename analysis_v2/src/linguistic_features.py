"""Research questions C (evidence structure) and D (linguistic characteristics).

Regex-based linguistic features plus optional spaCy entity features (cached).
Adds features to the paired dataset -> paired_enriched.parquet.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

NEG_RE = re.compile(r"\b(not|no|never|n't|neither|nor|without)\b", re.I)
CMP_RE = re.compile(r"\b(more|less|fewer|most|least|\w+er than|\w+est)\b", re.I)
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
DATE_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,4}\b"
    r"|\b\d{4}\b|\b(?:19|20)\d{2}s?\b"
)
PRON_RE = re.compile(r"\b(he|she|it|they|him|her|his|hers|its|their|them|this|that|these|those)\b", re.I)
MODAL_RE = re.compile(r"\b(can|could|may|might|must|shall|should|will|would)\b", re.I)
CONJ_RE = re.compile(r"\b(and|but|or|so|because|while|whereas|however|although)\b", re.I)
STOP = set("a an the is was are were be been of in on at to for with by from as that this it its "
           "he she they his her their and or but if then than so such not no nor do does did has "
           "have had will would can could may might must should".split())


def tokenize(t: str):
    return [w.lower() for w in re.findall(r"[A-Za-z0-9']+", t or "")]


def lex_features(claim: str, evidence: str) -> dict:
    ct, et = tokenize(claim), tokenize(evidence)
    cs, es = set(ct), set(et)
    csn, esn = cs - STOP, es - STOP
    overlap = len(csn & esn) / max(1, len(csn))
    jc = len(csn & esn) / max(1, len(csn | esn))
    cnums, enums = set(NUM_RE.findall(claim or "")), set(NUM_RE.findall(evidence or ""))
    return {
        "claim_len_words": len(ct),
        "evidence_len_words": len(et),
        "claim_evidence_len_ratio": len(ct) / max(1, len(et)),
        "claim_negation": len(NEG_RE.findall(claim or "")),
        "claim_comparative": len(CMP_RE.findall(claim or "")),
        "claim_numbers": len(NUM_RE.findall(claim or "")),
        "claim_dates": len(DATE_RE.findall(claim or "")),
        "claim_pronouns": len(PRON_RE.findall(claim or "")),
        "claim_modals": len(MODAL_RE.findall(claim or "")),
        "claim_conjunctions": len(CONJ_RE.findall(claim or "")),
        "evidence_negation": len(NEG_RE.findall(evidence or "")),
        "evidence_numbers": len(NUM_RE.findall(evidence or "")),
        "lexical_overlap": overlap,
        "jaccard_content": jc,
        "numerical_overlap": len(cnums & enums) / max(1, len(cnums)) if cnums else 1.0,
        "claim_has_date_evidence_no_date": int(bool(DATE_RE.findall(claim or ""))
                                                and not DATE_RE.findall(evidence or "")),
    }


def spacy_entities(df: pd.DataFrame) -> pd.DataFrame:
    """Entity counts and claim/evidence entity overlap via spaCy (nlp pipe, cached)."""
    cache = config.CACHE_DIR / "spacy_entities.parquet"
    if cache.exists():
        cached = pd.read_parquet(cache)
        if len(cached) == len(df):
            return pd.concat([df.reset_index(drop=True), cached.reset_index(drop=True)], axis=1)
    try:
        import spacy
        nlp = spacy.load(config.SPACY_MODEL, disable=["parser", "lemmatizer"])
    except Exception as e:  # graceful degradation
        print(f"spaCy unavailable ({e}); skipping entity features")
        return df

    docs_claim = list(nlp.pipe(df["claim_text"].fillna(""), batch_size=256))
    docs_ev = list(nlp.pipe(df["gold_evidence"].fillna(""), batch_size=256))
    rows = []
    for dc, de in zip(docs_claim, docs_ev):
        ec = {e.text.lower().strip() for e in dc.ents}
        ee = {e.text.lower().strip() for e in de.ents}
        rows.append({
            "claim_entity_count": len(ec),
            "evidence_entity_count": len(ee),
            "entity_overlap": len(ec & ee) / max(1, len(ec)),
            "claim_person_org_entities": sum(1 for e in dc.ents if e.label_ in ("PERSON", "ORG")),
        })
    ent = pd.DataFrame(rows)
    ent.to_parquet(cache, index=False)
    return pd.concat([df.reset_index(drop=True), ent], axis=1)


def enrich():
    config.ensure_dirs()
    df = pd.read_parquet(config.PAIRED_PARQUET)
    feats = pd.DataFrame([lex_features(c, e) for c, e in zip(df["claim_text"], df["gold_evidence"])])
    df = pd.concat([df.reset_index(drop=True), feats], axis=1)
    df = spacy_entities(df)
    df.to_parquet(config.ENRICHED_PARQUET, index=False)
    print(f"Enriched dataset: {df.shape} -> {config.ENRICHED_PARQUET}")
    return df


if __name__ == "__main__":
    enrich()
