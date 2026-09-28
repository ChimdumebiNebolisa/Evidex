# Operational execution amendment — 2026-09-27

Status: prepared before fresh correction-v2 inference. This amendment does not
authorize a model call. It preserves
`analysis_spec_2026-09-27.md` and its freeze unchanged and changes no model lock,
packet, rubric, cohort, denominator, retry rule, consensus rule, taxonomy, or
analysis rule.

## Reason and scope

The frozen handoff requires exact model routing evidence and packet-only
isolation. Preflight established that Cursor exposes a selected/resolved model
identifier and run identifiers, but does not expose a provider-signed backend
version or routing attestation. It also established that an ordinary child
subagent shares the parent workspace and tools and can fall back under documented
plan or policy conditions. No fresh judgment existed when this amendment was
prepared.

This amendment replaces only the operational interpretation of the routing and
isolation gate. It does not relax blinding or permit a replacement model.

## 1. Provider and backend version metadata

Record provider/backend version metadata exactly when exposed. Otherwise record:

- `provider_model_version: null`
- `version_metadata_status: "not_exposed"`
- a note naming the catalog, dispatch, run, result, hook, transcript, and usage
  records that were inspected

Unavailable or opaque backend-version metadata is an explicit unknown and is not,
by itself, an execution failure. It must not be inferred from model
self-identification, marketing names, or output style.

## 2. Fixed model selection and fallback detection

Use a fresh top-level local Cursor SDK agent, not Auto, inherit, a resumed agent,
or a child subagent. Before each run:

1. Query the authenticated account model catalog and require the job's exact
   locked slug.
2. Dispatch that exact slug in `model.id` and again as the per-run model.
3. Record the catalog entry, dispatch object, SDK init event, immutable
   `run.model`, terminal `result.model`, agent ID, run ID, request ID, Cursor SDK
   version, and Cursor application/runtime version when exposed.
4. Fail before acceptance if the exact locked slug is absent, the dispatch is
   rejected, any recorded model identifier differs, Auto/inherit appears, or a
   routing/fallback warning appears.

Cursor documents `run.model` and `result.model` as the resolved model selection
used by a run. For this amended execution profile, an exact match across catalog,
dispatch, init, run, and result is the required operational evidence for
`resolved_model`. This is selection/runtime evidence, not a provider-signed
attestation of the downstream host, weights, snapshot, or backend build.
Undisclosed downstream substitution therefore remains an explicit residual
uncertainty.

## 3. Packet-only judge isolation

For each attempt, create a new non-repository workspace outside the source
repository and extract exactly that job's one-packet ZIP into it. Do not copy the
manifest, handoff, protocol, mappings, labels, prior outputs, prior transcripts,
repository rules, skills, memories, or other jobs.

Create a new SDK agent; never resume. Use all of these controls:

- `local.cwd` is the per-attempt workspace; no additional directories.
- `local.settingSources` is empty; no user, team, project, plugin, or MDM settings
  are loaded.
- Inline MCP configuration is empty.
- The built-in tool allowlist contains only file read and file write. Shell,
  web search/fetch, MCP, browser, Git, and task/subagent tools are not offered.
- The local sandbox is enabled. Shell-spawned outbound network remains denied
  even though shell is not offered. Hosted model transport is necessarily
  external and is not described as offline inference.
- Fail-closed project hooks allow reading only the exact packet path and writing
  only the exact designated output path. They deny all other tool names and paths
  and append their inputs and decisions to an operator audit log outside the
  judge-visible workspace.
- Before dispatch, inventory the workspace and hash the packet. After completion,
  inventory it again and require that only the designated output was added.
- Send exactly `job.launch_prompt`. Do not add coordinator findings or scientific
  context.

The hook and SDK allowlist are enforced application controls. The isolated
workspace is an observable filesystem boundary. Prompt restrictions are retained
as defense in depth, not treated as access control. Tool and hook logs establish
observed access; they do not prove the absence of undisclosed service-side
context. Cursor's hosted inference transport also prevents claiming a total
machine-level network air gap.

Archive the complete SDK event stream and hook audit. When the model writes the
JSON array through the write tool, preserve the exact generated file bytes as the
raw response before any fence removal or parsing, and require equality with the
delivered output. Record denied tool attempts as part of routing/isolation
evidence; any successful non-allowlisted access blocks acceptance.

## 4. Authorization and usage gate

Historical predictions and valid A/B judgments remain reused. Never rerun a
completed valid job.

No batch execution is authorized by this amendment. After environment setup and
model-catalog confirmation, report the first required Grok and Claude jobs,
available pricing/usage terms, and packet sizes. Wait for explicit authorization
to run those two jobs only. Do not launch optional historical-residual, newly
selected residual, resolver, ablation, or other required jobs.

After those two jobs, report actual SDK token usage and billed usage when exposed,
plus duration and output size. Estimate remaining work separately by locked model
and packet-size distribution, with uncertainty for output length, reasoning
tokens, cache behavior, retries, rate limits, plan terms, and routing overhead.
Do not estimate cost from job count alone. Stop before any further launch.

## 5. Remaining setup gate and disclosure

The execution route is not ready until the local SDK is installed, authenticated,
and confirms both locked judge slugs in its account-specific model catalog, and a
non-judgment dry run confirms that the fail-closed hooks, tool allowlist, sandbox,
event capture, and exact-output archival operate as specified. A missing slug,
unavailable sandbox/helper, unavailable fail-closed path control, model mismatch,
or absent authenticated SDK route makes this execution profile unsuitable.

Every accepted execution record and any separately named result version must cite
this amendment and preserve its hash with the routing evidence. The original
frozen protocol remains the scientific specification of record.

## Documentation basis

- Cursor SDK: https://cursor.com/docs/sdk/typescript
- Cursor subagent model behavior: https://cursor.com/docs/subagents
- Cursor hooks: https://cursor.com/docs/hooks
- Cursor model and usage terms: https://cursor.com/docs/models-and-pricing
