# Superseded duplicate Stage B runs (judge 4, batches 01-03)

The first Stage B wave hit `Other Models usage limit reached` and left several
`(judge, batch)` units undelivered. Those units were relaunched, and — because
recovery work overlapped — three of them (`claude_full_judge_4` batches 01, 02
and 03) ended up being adjudicated twice by two independent
`claude-opus-5-thinking-high` subagent runs.

Both copies are legitimate Claude output. Only one may enter the panel, because
the design is one judgment per `(stage, judge_id, item_id)`.

**Tie-break rule: first ingested wins.** The copy already present in
`judgments/stage_b/` was kept; the later copy was discarded. This rule is
purely temporal and content-independent — the discarded files' verdicts were
never read, compared against the retained copy, or scored in any way, so the
choice cannot express a preference for one set of results over the other.
Selecting on content here would have been cherry-picking.

`run_judges.ingest` enforces this automatically: it refuses to overwrite an
already-ingested file whose bytes differ, which is how the duplication was
detected rather than silently absorbed.

The discarded bytes are preserved here with their sha256 hashes (see
`MANIFEST.json`) so an auditor can confirm both that a duplicate existed and
that the retained copy was not chosen for its content.

Note: `MANIFEST.json` in this directory was written by the shared
`src/quarantine.py` helper and therefore carries that script's default
model-substitution wording in its `reason` field. That wording does not apply
here; the operative reason for this directory is the duplicate-run tie-break
described above.
