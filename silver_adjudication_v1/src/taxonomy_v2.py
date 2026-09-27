"""Proposed descriptive taxonomy v2; requires coauthor review.

    This describes judge observations, not GPT mechanisms or new FEVER labels.
    Applying it to v1 judgments is a rule-only sensitivity analysis, never a
    result for corrected evidence. C may add sentences as well as structure.
"""
VERSION = "proposed_v2_coauthor_review"
DECISIVE = {"Supported", "Refuted"}
VALID = DECISIVE | {"Ambiguous", "Unresolved"}


def classify(a, b, c, gold, cohort, *, c_adds_text, input_version):
    if gold not in DECISIVE or any(x not in VALID for x in (a, b, c)):
        raise ValueError("invalid label or missing consensus")
    labels = {"A": a, "B": b, "C": c}
    out = {"taxonomy_version": VERSION, "judgment_input_version": input_version}
    for stage, verdict in labels.items():
        out[f"decisive_{stage}"] = verdict in DECISIVE
        out[f"agrees_fever_{stage}"] = verdict == gold if verdict in DECISIVE else None
    out["first_decisive_stage"] = next((s for s, v in labels.items() if v in DECISIVE), "none")
    out["first_gold_agreeing_stage"] = next((s for s, v in labels.items() if v == gold), "none")
    out["title_resolution"] = a not in DECISIVE and b in DECISIVE
    out["c_resolution"] = b not in DECISIVE and c in DECISIVE
    out["reversal_A_B"] = a in DECISIVE and b in DECISIVE and a != b
    out["reversal_B_C"] = b in DECISIVE and c in DECISIVE and b != c
    out["decisiveness_lost"] = any(x in DECISIVE and y not in DECISIVE
                                     for x, y in ((a, b), (b, c)))
    out["c_disclosure"] = "additional_sentence_text_and_structure" if c_adds_text else "structure_without_new_sentence_text"
    # A-only field remains usable even if C is superseded, with no C sufficiency inference.
    out["sentence_only_utilization_compatible"] = cohort in ("regression", "resistant") and a == gold
    if c not in DECISIVE:
        category = "final_nondecisive"
    elif c != gold:
        category = "decisive_judge_fever_disagreement"
    elif out["reversal_A_B"] or out["reversal_B_C"] or out["decisiveness_lost"]:
        category = "nonmonotonic_judge_path"
    elif a == gold:
        category = "sentence_only_gold_agreeing"
    elif out["title_resolution"]:
        category = "title_disclosure_gold_agreeing"
    else:
        category = ("additional_evidence_gold_agreeing" if c_adds_text
                    else "structured_disclosure_gold_agreeing")
    out["category"] = category
    return out
