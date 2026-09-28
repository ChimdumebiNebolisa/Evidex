# SDK model-selection implementation note — 2026-09-27

Status: prepared before fresh correction-v2 inference. This note preserves the
original protocol, freeze, and `operational_amendment_2026-09-27.md` unchanged.
It does not authorize a model call or alter a model family, reasoning setting,
speed setting, context, packet, rubric, or scientific rule.

## Observed SDK contract

The authenticated Cursor SDK 1.0.32 catalog did not list the manifest's legacy
configuration labels as literal model IDs:

- `cursor-grok-4.6-high-fast`
- `claude-opus-5-thinking-high`

Instead, the catalog represents those configurations as canonical model IDs plus
parameters. The matching account-catalog defaults were:

- `grok-4.6` with `effort=high`, `fast=true`
- `claude-opus-5` with `cyber=false`, `thinking=true`, `context=1m`,
  `effort=high`, `fast=false`

The original operational amendment said to put the locked legacy slug directly
in `model.id`. SDK 1.0.32 does not expose that form. Before inference, this note
changes that implementation detail to the catalog's canonical `ModelSelection`.
It is a serialization change, not a model substitution.

SDK 1.0.32 also rejects the documented generic `write` tool name and exposes the
installed file-write capability as `piWrite`. The enforced allowlist therefore
uses `read` and `piWrite`; the path policy treats `piWrite` only as the designated
output-file write capability. No shell, fetch, browser, MCP, task, edit, delete,
or additional file capability is offered.

## Acceptance evidence

For each proposed run:

1. `requested_model` remains the exact manifest lock.
2. Archive the account-catalog entry and the exact canonical `ModelSelection`.
3. Require the canonical parameters above to be present as a single catalog
   variant before dispatch.
4. Dispatch the complete canonical selection at agent creation and per run.
5. Require SDK init, `run.model`, and `result.model` to equal that complete
   selection. Any missing or different parameter, Auto, warning, or fallback
   blocks acceptance.
6. Record the manifest slug in `resolved_model` only when the archived evidence
   establishes the complete canonical mapping; preserve both representations in
   routing evidence.

The SDK record is still not a provider-signed backend or weight attestation.
Provider/backend version remains unknown when not exposed, as specified by the
earlier amendment.

## Account and billing observation

The account model catalog was retrieved read-only. The dashboard and exported
usage events for 2026-09-21 through 2026-09-27 showed included usage only and zero
on-demand events at inspection time. This does not guarantee that a future run
will remain included or that account limits and plan terms will not change.
On-demand usage must not be enabled by this procedure.
