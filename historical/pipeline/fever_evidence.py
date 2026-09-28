"""Shared interpretation of the archived FEVER line format and set identity."""
import hashlib
import json
import unicodedata


def canonicalize_wiki_title(title):
    return unicodedata.normalize("NFC", str(title).strip())


def sentence_text_from_lines(lines_str, idx):
    """A line is index<TAB>sentence[<TAB>anchor<TAB>target ...].

    Link fields are never sentence text. Preserve sentence bytes as decoded;
    normalize titles, not evidence prose. Empty/malformed lines are missing.
    """
    for raw_line in lines_str.split("\n"):
        parts = raw_line.rstrip("\r").split("\t")
        if len(parts) >= 2 and parts[0] == str(idx):
            return parts[1] or None
    return None


def evidence_set_id(evidence_set):
    payload = json.dumps({
        "set_index": evidence_set["set_index"],
        "pointers": [{"page": canonicalize_wiki_title(page), "sent_idx": idx}
                     for page, idx in evidence_set["pointers"]],
    }, ensure_ascii=False, separators=(",", ":"))
    return "fever_set_" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def selected_evidence_set(sets, set_id, pages, sentences):
    """Match the stored ID (annotation index + ordered, NFC pointers).

    Sentence count or page-set similarity alone cannot identify a selected set.
    Never fall back to the shortest set when historical identity is missing.
    """
    matches = [s for s in sets if evidence_set_id(s) == set_id]
    if len(matches) != 1:
        raise ValueError(f"selected_set_identity_unavailable:{set_id}")
    selected = matches[0]
    if ([p for p, _ in selected["pointers"]] !=
            [canonicalize_wiki_title(p) for p in pages] or
            len(selected["pointers"]) != len(sentences)):
        raise ValueError("selected_set_order_or_length_mismatch")
    return selected
