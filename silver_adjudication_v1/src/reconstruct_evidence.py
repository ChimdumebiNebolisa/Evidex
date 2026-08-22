"""Reconstruct Stage B (page titles) and Stage C (structured FEVER evidence).

Stage B: per-evidence-sentence page titles, recovered by identifying the
chosen (shortest complete) evidence set in the FEVER raw_evidence annotation
whose sentence count and page set match the stored resolver output.

Stage C: full annotation structure — chosen set with per-sentence (page, line)
and text, plus alternative complete evidence sets with their sentence texts
looked up from the official FEVER wiki archive (repo-external download,
read-only; see METHODS). Where a page is missing from the archive, the
alternative-set sentence is shown as its (page, line) pointer only and the
claim's Stage C availability is flagged.

The FEVER wiki download uses a fixed https URL with host validation
(https only; host must match the official FEVER data host; localhost/loopback/
private/reserved addresses rejected) per environment security policy.
"""
import ipaddress
import json
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

WIKI_ZIP = config.CACHE_DIR / "wiki-pages.zip"
WIKI_PAGES_CACHE = config.CACHE_DIR / "wiki_pages_needed.json"
ALLOWED_HOSTS = {"fever.ai"}


def validate_download_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme != "https":
        raise ValueError("only https URLs are allowed")
    if p.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"host not allowed: {p.hostname}")
    try:
        ip = ipaddress.ip_address(p.hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            raise ValueError("private/reserved address rejected")
    except ValueError:
        pass  # hostname form; host allow-list already applied


def chosen_evidence_set(raw_evidence_json: str, n_sentences: int, pages: list):
    """Return the annotation set matching the resolver's chosen set."""
    sets = json.loads(raw_evidence_json) if isinstance(raw_evidence_json, str) else raw_evidence_json
    candidates = []
    for s in sets:
        tuples = [t for t in s if len(t) >= 4]
        sp = sorted({t[2] for t in tuples})
        candidates.append((len(tuples), sp, tuples))
    exact = [c for c in candidates if c[0] == n_sentences and c[1] == sorted(set(pages))]
    if exact:
        return exact[0][2]
    # fallback: first shortest set
    shortest = min(candidates, key=lambda c: c[0])
    return shortest[2]


def parse_wiki_line(lines_str: str, line_no: int):
    for chunk in lines_str.split("\n"):
        parts = chunk.split("\t")
        if parts and parts[0] == str(line_no):
            return parts[-1]
    return None


def load_needed_pages(needed_pages):
    if WIKI_PAGES_CACHE.exists():
        return json.loads(WIKI_PAGES_CACHE.read_text(encoding="utf-8"))
    pages = {}
    with zipfile.ZipFile(WIKI_ZIP) as z:
        for name in z.namelist():
            if not name.endswith(".jsonl"):
                continue
            with z.open(name) as f:
                for raw in f:
                    try:
                        rec = json.loads(raw)
                    except (ValueError, UnicodeDecodeError):
                        continue
                    if not isinstance(rec, dict):
                        continue
                    if rec.get("id") in needed_pages:
                        pages[rec["id"]] = rec.get("lines", "")
                        if len(pages) == len(needed_pages):
                            break
            if len(pages) == len(needed_pages):
                break
    WIKI_PAGES_CACHE.write_text(json.dumps(pages), encoding="utf-8")
    return pages


def build_stage_b():
    cohort = pd.read_parquet(config.COHORT_PARQUET)
    id_map = pd.read_csv(config.ID_MAP_CSV)
    fever = pd.read_csv(config.FEVER_SOURCE, dtype={"claim_id": int}).set_index("claim_id")

    stage_a = {json.loads(l)["item_id"]: json.loads(l)
               for l in (config.BLINDED_DIR / "stage_a.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

    out = config.BLINDED_DIR / "stage_b.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for _, m in id_map.iterrows():
            row = cohort.set_index("claim_id").loc[m["claim_id"]]
            raw = fever.loc[m["claim_id"], "raw_evidence"]
            pages = json.loads(row["evidence_pages_json"])
            chosen = chosen_evidence_set(raw, int(row["n_evidence_sentences"]), pages)
            titles = [t[2].replace("_", " ") for t in chosen]
            rec = dict(stage_a[m["item_id"]])
            rec["page_titles"] = titles
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Stage B blinded file: {len(id_map)} items -> {out}")


def build_stage_c():
    cohort = pd.read_parquet(config.COHORT_PARQUET).set_index("claim_id")
    id_map = pd.read_csv(config.ID_MAP_CSV)
    fever = pd.read_csv(config.FEVER_SOURCE, dtype={"claim_id": int}).set_index("claim_id")

    # Collect every page referenced by any evidence set of any cohort claim.
    all_sets = {}
    needed = set()
    for _, m in id_map.iterrows():
        raw = fever.loc[m["claim_id"], "raw_evidence"]
        sets = json.loads(raw)
        all_sets[m["claim_id"]] = sets
        for s in sets:
            for t in s:
                if len(t) >= 4 and t[2]:
                    needed.add(t[2])
    print(f"Stage C: {len(needed)} distinct wiki pages needed")
    pages = load_needed_pages(needed)

    stage_b = {json.loads(l)["item_id"]: json.loads(l)
               for l in (config.BLINDED_DIR / "stage_b.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

    out = config.BLINDED_DIR / "stage_c.jsonl"
    n_alt_text = n_alt_pointer = 0
    with out.open("w", encoding="utf-8") as f:
        for _, m in id_map.iterrows():
            cid = m["claim_id"]
            row = cohort.loc[cid]
            rec = dict(stage_b[m["item_id"]])
            sets = all_sets[cid]
            chosen_pages = json.loads(row["evidence_pages_json"])
            chosen = chosen_evidence_set(sets, int(row["n_evidence_sentences"]), chosen_pages)

            def sentence_text(page, line):
                lines = pages.get(page)
                if lines is None:
                    return None
                return parse_wiki_line(lines, line)

            chosen_struct = []
            for t in chosen:
                page, line = t[2], t[3]
                chosen_struct.append({
                    "page_title": page.replace("_", " "),
                    "line_index": line,
                    "sentence": sentence_text(page, line),
                })
            alternatives = []
            for s in sets:
                tuples = [t for t in s if len(t) >= 4]
                key = json.dumps([[t[2], t[3]] for t in tuples])
                if key == json.dumps([[t[2], t[3]] for t in chosen]):
                    continue  # this IS the chosen set (or exact duplicate)
                alt = []
                for t in tuples:
                    page, line = t[2], t[3]
                    txt = sentence_text(page, line)
                    if txt is None:
                        n_alt_pointer += 1
                    else:
                        n_alt_text += 1
                    alt.append({"page_title": page.replace("_", " "),
                                "line_index": line, "sentence": txt})
                alternatives.append(alt)

            rec["structured_evidence"] = {
                "chosen_set": chosen_struct,
                "alternative_sets": alternatives,
                "n_annotation_sets": len(sets),
                "full_text_available": all(s["sentence"] is not None for s in chosen_struct),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Stage C blinded file -> {out} "
          f"(alternative-set sentences with text: {n_alt_text}, pointer-only: {n_alt_pointer})")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("b", "all"):
        build_stage_b()
    if which in ("c", "all"):
        if not WIKI_ZIP.exists():
            validate_download_url("https://fever.ai/download/fever/wiki-pages.zip")
            sys.exit("wiki-pages.zip not downloaded yet; run the download step first")
        build_stage_c()
