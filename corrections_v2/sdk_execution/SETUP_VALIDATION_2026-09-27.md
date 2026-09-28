# Cursor SDK setup validation — 2026-09-27

No experimental judgment or inference probe was launched.

## SDK and authentication

- Node.js: 24.14.1
- Cursor SDK: `@cursor/sdk` 1.0.32, exact dependency and lockfile integrity
  recorded in this directory
- Authentication: supported `Cursor.auth.login()` stored credential
- Credential value: never printed or copied into the repository
- Stored-login expiry reported by the SDK: 2026-12-26T21:32:56.745Z
- Catalog operation: authenticated, read-only, 41 entries

## Locked configurations

Both locked configurations are present in the account catalog as canonical SDK
model selections:

- Manifest `cursor-grok-4.6-high-fast`:
  `grok-4.6` with `effort=high`, `fast=true`
- Manifest `claude-opus-5-thinking-high`:
  `claude-opus-5` with `cyber=false`, `thinking=true`, `context=1m`,
  `effort=high`, `fast=false`

The legacy labels are not literal SDK model IDs. The preserved pre-inference
implementation note is
`../protocol/amendments/operational_amendment_2026-09-27-sdk-mapping.md`.

## Billing evidence

The operator-supplied dashboard screenshot for 2026-09-21 through 2026-09-27
showed 8.6M total tokens, 8.6M included, and zero on-demand. The exported usage
CSV contained 2,442 events: every row had kind `Included`; 2,431 had cost
`Included`, 11 had cost `Free`, and none was on-demand.

Official SDK documentation states SDK runs use the same plan request pools and
pricing as IDE and Cloud Agent runs. The observed account source is therefore the
existing included Cursor allowance, not a separately verified SDK balance.

Unknown: the export does not show the remaining allowance, future plan state, or
whether an on-demand overage toggle is enabled. These must be checked immediately
before any authorized execution. Setup did not enable overages or change billing.

## Fixture-only isolation validation

`node validate-isolation.mjs` passed:

- 18 allow/deny policy cases;
- designated packet read allowed;
- outside and traversal reads denied;
- designated output write allowed;
- packet overwrite and outside writes denied;
- shell, web search, MCP, task/subagent, and delete denied;
- attachment-based outside read denied;
- invalid hook JSON failed closed;
- audit-log failure failed closed;
- SDK local agent creation with sandbox enabled and only `read`/`piWrite`
  succeeded without calling `send()` or making inference.

The SDK's installed tool name is `piWrite`, not the generic `write` shown in the
current documentation. That difference is recorded in the implementation note.
Offline fixtures establish local policy behavior only; they do not establish
live model routing or prove service-side isolation.

## Proposed execution

Exact, single-job, authorization-gated commands and the recording procedure are
in `PROPOSED_FIRST_JOBS.md`. The runner supports only `p01_C_j1_b01` and
`p02_C_j1_b01`, requires a job-specific authorization environment value, creates
no loop, and leaves every result `pending_human_review`.
