"""Frozen v1 decision rules. For historical reproduction only, not inference.

    Source: 776d09b, join_analysis_v2.unblind_join.taxonomy and Claude
    analyze.taxonomy_row. The redundant NLI branch returned the same label.
"""
VERSION = "legacy_v1"


def taxonomy_row(r, cohort="regression"):
    if r["still_ambiguous_after_C"]:
        return "silver_partial_or_ambiguous_warrant"
    if r["resolved_only_by_structure"] or r["reversed_after_structure"] or (
            r["consensus_A"] in ("Ambiguous", "Unresolved") and
            r["consensus_C"] in ("Supported", "Refuted")):
        return "silver_structured_evidence_sensitive"
    if r["reversed_after_titles"] or r["resolved_by_titles"]:
        return "silver_title_context_sensitive"
    if cohort in ("regression", "resistant") and r["consensus_C"] in ("Supported", "Refuted"):
        return "silver_clear_evidence_utilization_failure"
    return "silver_unresolved"
