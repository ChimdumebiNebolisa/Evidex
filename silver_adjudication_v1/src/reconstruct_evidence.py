"""Corrected, local-only reconstruction; never writes frozen v1 files.

Run corrections_v2/reproduce.py for audited B/C outputs. Historical code is
preserved at evidex-artifact-v1 and commit 776d09b.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from fever_evidence import (canonicalize_wiki_title, evidence_set_id,
                            selected_evidence_set, sentence_text_from_lines)
from resolve_gold_evidence import parse_evidence_sets

parse_wiki_line = sentence_text_from_lines


def normalized_page(page):
    return canonicalize_wiki_title(page).replace(" ", "_")


def load_needed_pages(needed_pages, snapshot=None):
    """Read historical cache, then local shards for absent pages only.

    No network fallback or writes to historical cache. NFC collisions with
    different content are errors, not overwrites. Return paths for hashing.
    """
    needed = {normalized_page(p) for p in needed_pages}
    pages, sources = {}, []
    cache = ROOT / "silver_adjudication_v1/data/cache/wiki_pages_needed.json"
    if snapshot is not None:
        cache = Path(snapshot).resolve()
        if not cache.is_file():
            raise FileNotFoundError(cache)

    def add(page, lines):
        key = normalized_page(page)
        if key not in needed:
            return
        if key in pages and pages[key] != lines:
            raise ValueError(f"normalization_collision:{page}")
        pages[key] = lines

    if cache.exists():
        sources.append(cache)
        for page, lines in json.loads(cache.read_text(encoding="utf-8")).items():
            add(page, lines)
    remaining = needed - pages.keys()
    if snapshot is not None:
        return pages, sources
    for path in sorted((ROOT / "wiki-pages/wiki-pages").glob("wiki-*.jsonl")):
        if not remaining:
            break
        sources.append(path)
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                doc = json.loads(line)
                if not isinstance(doc, dict):
                    continue
                key = normalized_page(doc.get("id", ""))
                if key in remaining:
                    add(key, doc.get("lines", ""))
        remaining = needed - pages.keys()
    return pages, sources


def reconstruct(row, stage_a, pages):
    sets = parse_evidence_sets(row["raw_evidence"])
    sentences = json.loads(row["evidence_sentences_json"])
    titles = json.loads(row["evidence_pages_json"])
    selected = selected_evidence_set(sets, row["evidence_set_id"], titles, sentences)
    if stage_a["claim"] != row["claim_text"] or stage_a["evidence_sentences"] != row["gold_evidence"]:
        raise ValueError("stage_a_differs_from_original_input")
    if " ".join(sentences).strip() != row["gold_evidence"]:
        raise ValueError("original_sentence_array_differs_from_prompt")
    validation = []

    def build_set(es, canonical=None):
        records = []
        for position, (page, index) in enumerate(es["pointers"]):
            lines = pages.get(normalized_page(page))
            extracted = None if lines is None else parse_wiki_line(lines, index)
            status = "available" if extracted is not None else (
                "missing_page" if lines is None else "missing_sentence")
            text = extracted
            if canonical is not None:
                if extracted is not None and extracted != canonical[position]:
                    raise ValueError(f"canonical_text_conflict:{stage_a['item_id']}:{page}:{index}")
                text = canonical[position]
                if extracted is None:
                    status += "_using_original_selected_text"
            records.append({"page_title": page.replace("_", " "),
                            "line_index": index, "sentence": text})
            validation.append({"set_index": es["set_index"], "set_id": evidence_set_id(es),
                               "role": "chosen" if canonical is not None else "alternative",
                               "position": position, "page": page, "line_index": index,
                               "status": status, "archive_text": extracted, "text": text})
        return records

    chosen = build_set(selected, sentences)
    alternatives, indices = [], []
    # Keep all annotation boundaries, including duplicate pointer sets.
    for es in sets:
        if es["set_index"] != selected["set_index"]:
            alternatives.append(build_set(es))
            indices.append(es["set_index"])
    # Lookup keys use NFC; judge-visible historical titles keep their exact
    # original Unicode spelling. This avoids changing valid Stage B inputs.
    raw_selected = json.loads(row["raw_evidence"])[selected["set_index"]]
    stage_b = dict(stage_a, page_titles=[t[2].replace("_", " ") for t in raw_selected])
    stage_c = dict(stage_b, structured_evidence={
        "chosen_set": chosen, "alternative_sets": alternatives,
        "n_annotation_sets": len(json.loads(row["raw_evidence"])),
        "chosen_annotation_index": selected["set_index"],
        "alternative_annotation_indices": indices,
        "full_text_available": all(s["sentence"] is not None for s in chosen),
        "chosen_archive_text_available": all(v["archive_text"] is not None for v in validation if v["role"] == "chosen"),
        "alternative_full_text_available": [all(s["sentence"] is not None for s in alt) for alt in alternatives],
    })
    return stage_b, stage_c, validation


if __name__ == "__main__":
    raise SystemExit("Use python corrections_v2/reproduce.py; frozen v1 output paths are disabled.")
