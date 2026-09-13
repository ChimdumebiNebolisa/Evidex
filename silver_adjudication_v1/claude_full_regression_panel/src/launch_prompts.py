"""Emit the exact isolation wrapper prompt used for every judge subagent.

One fresh Cursor Task subagent per ``(judge, batch, stage)``, model locked to
``claude-opus-5-thinking-high``. The wrapper carries no scientific content: the
rubric and the items live in the packet. Every path handed to a judge is inside
the neutrally named ``silver_adjudication_v1/blind_io/`` tree so that no path
component can reveal how the cohort was selected.

Prompts are written to ``blind_io/launch_prompts/stage_<s>/`` so the exact text
each judge received is auditable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel_config as cfg  # noqa: E402

TEMPLATE = """You are an independent fact-checking adjudicator. You work only \
from one self-contained packet file.

Read exactly this one file and nothing else:
{packet}

The packet has fields: judge_id, stage, output_path, n_items, item_ids, items, \
rubric, disclosure_note. Follow the `rubric` text exactly. Judge every item \
using ONLY the fields inside that item.

Hard rules:
- Do NOT read any other file. Do NOT search or grep the codebase. Do NOT browse \
the web or look anything up. Do NOT run git.
- Judge only from the supplied claim and evidence; do not use outside knowledge \
to decide the verdict.
- If the evidence alone does not settle the claim, answer Ambiguous. That is a \
valid, useful answer.
- Do not speculate about hidden labels, why these items were selected, other \
judges, or any other model.
- Produce exactly one JSON object per item, in packet order, for every one of \
the item_ids. Never skip or merge items.
- Copy item_id, judge_id and stage exactly from the packet.
- verdict is one of: Supported, Refuted, Ambiguous
- evidence_sufficiency is one of: clearly_sufficient, probably_sufficient, \
partial_or_ambiguous, probably_insufficient, clearly_insufficient
- confidence is an integer 0-100
- issue_flags is a non-empty JSON array drawn from: none, \
possible_missing_title_context, possible_coreference_or_entity_resolution, \
possible_missing_surrounding_context, multi_sentence_integration, \
numerical_or_temporal_reasoning, negation_or_scope, \
entity_or_attribute_confusion, partial_warrant, \
apparent_internal_contradiction, other
- brief_reason is one short sentence grounded in the provided evidence.

Write your answer as a single JSON array (no prose before or after) to exactly \
this path, creating it:
{output}

Then reply with only one line: WROTE <count> records
"""


def build(stage: str) -> list[dict]:
    cfg.ensure_dirs()
    outdir = cfg.BLIND_IO / "launch_prompts" / f"stage_{stage.lower()}"
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for packet in sorted(cfg.stage_packets_dir(stage).glob("*_batch_*.json")):
        name = packet.stem
        prompt = TEMPLATE.format(
            packet=packet.resolve(),
            output=(cfg.stage_inbox_dir(stage) / f"{name}.jsonl").resolve(),
        )
        leaks = cfg.blinding_text_errors(prompt)
        if leaks:
            raise SystemExit(f"launch prompt for {name} would leak {leaks}")
        (outdir / f"{name}.txt").write_text(prompt, encoding="utf-8")
        written.append({"stage": stage, "batch": name,
                        "prompt_file": (outdir / f"{name}.txt").as_posix()})
    (outdir / "index.json").write_text(json.dumps(written, indent=2), encoding="utf-8")
    print(f"stage {stage}: wrote {len(written)} launch prompts -> {outdir}")
    return written


if __name__ == "__main__":
    for s in ([sys.argv[1].upper()] if len(sys.argv) > 1 else cfg.STAGES):
        if cfg.stage_packets_dir(s).exists():
            build(s)
