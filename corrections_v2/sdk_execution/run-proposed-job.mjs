import {
  appendFile,
  copyFile,
  lstat,
  mkdir,
  readFile,
  readdir,
  writeFile,
} from "node:fs/promises";
import { createHash } from "node:crypto";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Agent, Cursor } from "@cursor/sdk";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(process.env.EVIDEX_REPO || path.join(here, "..", ".."));
const manifestPath = path.join(repo, "corrections_v2", "generated", "rerun_manifest.json");
const policyPath = path.resolve(process.env.EVIDEX_POLICY_PATH || path.join(here, "isolation-policy.mjs"));
const selections = {
  grok: {
    locked: "cursor-grok-4.6-high-fast",
    selection: {
      id: "grok-4.6",
      params: [
        { id: "effort", value: "high" },
        { id: "fast", value: "true" },
      ],
    },
  },
  claude_full: {
    locked: "claude-opus-5-thinking-high",
    selection: {
      id: "claude-opus-5",
      params: [
        { id: "cyber", value: "false" },
        { id: "thinking", value: "true" },
        { id: "context", value: "1m" },
        { id: "effort", value: "high" },
        { id: "fast", value: "false" },
      ],
    },
  },
};

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

function normalizedSelection(value) {
  return {
    id: value?.id,
    params: [...(value?.params ?? [])].sort((a, b) => a.id.localeCompare(b.id)),
  };
}

function sameSelection(left, right) {
  return JSON.stringify(normalizedSelection(left)) === JSON.stringify(normalizedSelection(right));
}

function isInside(parent, child) {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

async function filesUnder(root, current = root) {
  const found = [];
  for (const entry of await readdir(current, { withFileTypes: true })) {
    const full = path.join(current, entry.name);
    const stat = await lstat(full);
    if (stat.isSymbolicLink()) throw new Error(`symlink/junction not allowed: ${full}`);
    if (entry.isDirectory()) found.push(...await filesUnder(root, full));
    else if (entry.isFile()) found.push(path.relative(root, full).replaceAll("\\", "/"));
    else throw new Error(`unsupported filesystem entry: ${full}`);
  }
  return found.sort();
}

async function sha256(file) {
  return createHash("sha256").update(await readFile(file)).digest("hex");
}

function safeJson(value) {
  return JSON.stringify(value, (_key, item) => typeof item === "bigint" ? item.toString() : item);
}

function compactError(error) {
  return {
    name: error?.name ?? "Error",
    message: String(error?.message ?? error).slice(0, 2000),
    code: error?.code ?? null,
    operation: error?.operation ?? null,
    requestId: error?.requestId ?? null,
  };
}

function sandboxUnsupported(error) {
  return String(error?.message ?? error).includes("sandboxing is not supported");
}

const jobId = argument("--job");
const attempt = Number(argument("--attempt"));
const workspace = path.resolve(argument("--workspace") ?? "");
const recordDir = path.resolve(argument("--record-dir") ?? "");
if (!Number.isInteger(attempt) || attempt < 1 || attempt > 9) {
  throw new Error("--attempt must be 1 through 9");
}
const label = String(attempt).padStart(2, "0");
if (!jobId) throw new Error("--job is required");
if (process.env.EVIDEX_EXECUTION_AUTHORIZATION !== jobId) {
  throw new Error(`set EVIDEX_EXECUTION_AUTHORIZATION=${jobId} only after explicit authorization`);
}
if (!argument("--workspace") || !argument("--record-dir")) {
  throw new Error("--workspace and --record-dir are required");
}
if (isInside(repo, workspace)) throw new Error("judge workspace must be outside the repository");
if (isInside(workspace, recordDir)) throw new Error("record directory must be outside judge workspace");
if (os.platform() === "win32") {
  throw new Error("Windows SDK sandbox is unsupported; refuse unsandboxed Windows dispatch");
}

const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const optionalPanels = new Set(
  (manifest.panels ?? []).filter((panel) => panel.optional).map((panel) => panel.panel),
);
const job = manifest.jobs.find((item) => item.job_id === jobId);
if (!job) throw new Error(`unknown job: ${jobId}`);
if (optionalPanels.has(job.panel)) throw new Error("optional jobs are not authorized");
const config = selections[job.panel];
if (!config) throw new Error(`panel is not a required executable panel: ${job.panel}`);
if (job.model !== config.locked) {
  throw new Error("manifest job does not match the locked proposed configuration");
}

const packet = path.join(workspace, ...job.packet.split("/"));
const output = path.join(workspace, ...job.output.split("/"));
const initialFiles = await filesUnder(workspace);
if (JSON.stringify(initialFiles) !== JSON.stringify([job.packet])) {
  throw new Error(`workspace must initially contain exactly the packet: ${safeJson(initialFiles)}`);
}
if (await sha256(packet) !== job.packet_sha256) throw new Error("packet hash mismatch");
if (!packet.startsWith("/home/evidex/isolated/") || !output.startsWith("/home/evidex/isolated/")) {
  throw new Error("Linux packet and output paths must resolve under /home/evidex/isolated/");
}

const catalog = await Cursor.models.list();
const catalogModel = catalog.find((item) => item.id === config.selection.id);
if (!catalogModel?.variants?.some((variant) => sameSelection(
  { id: catalogModel.id, params: variant.params },
  config.selection,
))) {
  throw new Error("exact canonical model configuration is absent from account catalog");
}

await mkdir(recordDir, { recursive: false });
const hookAudit = path.join(recordDir, `attempt-${label}.hooks.jsonl`);
const eventLog = path.join(recordDir, `attempt-${label}.sdk-events.jsonl`);
const routingPath = path.join(recordDir, `attempt-${label}.routing.json`);
const routingTextPath = path.join(recordDir, `attempt-${label}.routing.txt`);
const rawPath = path.join(recordDir, `attempt-${label}.raw.txt`);
const errorPath = path.join(recordDir, "dispatch-error.json");
await writeFile(hookAudit, "", { encoding: "utf8", flag: "wx" });
await writeFile(eventLog, "", { encoding: "utf8", flag: "wx" });

await mkdir(path.join(workspace, ".cursor"), { recursive: false });
const hookCommand = `node "${policyPath}"`;
await writeFile(path.join(workspace, ".cursor", "hooks.json"), `${JSON.stringify({
  version: 1,
  hooks: {
    preToolUse: [{ command: hookCommand, matcher: "*", failClosed: true }],
    beforeReadFile: [{ command: hookCommand, matcher: "Read", failClosed: true }],
    beforeShellExecution: [{ command: hookCommand, matcher: "*", failClosed: true }],
    beforeMCPExecution: [{ command: hookCommand, matcher: "*", failClosed: true }],
    subagentStart: [{ command: hookCommand, matcher: "*", failClosed: true }],
  },
}, null, 2)}\n`, { encoding: "utf8", flag: "wx" });

process.env.EVIDEX_PACKET_PATH = packet;
process.env.EVIDEX_OUTPUT_PATH = output;
process.env.EVIDEX_HOOK_AUDIT_PATH = hookAudit;
process.env.EVIDEX_WORKSPACE_PATH = workspace;

async function recordDispatchError(stage, error) {
  await writeFile(errorPath, `${JSON.stringify({
    status: "blocked",
    stage,
    sandbox_unsupported: sandboxUnsupported(error),
    error: compactError(error),
    job_id: jobId,
    attempt,
    host: os.platform(),
    workspace,
    packet,
    output,
    at_utc: new Date().toISOString(),
  }, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
}

const started = new Date().toISOString();
let agent;
try {
  agent = await Agent.create({
    name: `evidex-${jobId}-attempt-${label}`,
    model: config.selection,
    tools: ["read", "edit", "piWrite"],
    disallowedTools: ["shell", "mcp", "task", "webSearch"],
    mcpServers: {},
    agents: {},
    local: {
      cwd: workspace,
      settingSources: ["project"],
      sandboxOptions: { enabled: true },
      enableAgentRetries: false,
    },
  });
} catch (error) {
  await recordDispatchError("Agent.create", error);
  console.error(JSON.stringify({ stage: "Agent.create", error: compactError(error) }));
  throw error;
}

let run;
let result;
let initModels = [];
let toolEvents = [];
let completed;
try {
  run = await agent.send(job.launch_prompt, { model: config.selection, mcpServers: {} });
  for await (const event of run.stream()) {
    await appendFile(eventLog, `${safeJson(event)}\n`, "utf8");
    if (event.type === "system" && event.model) initModels.push(event.model);
    if (event.type === "tool_call") {
      toolEvents.push({ name: event.name, status: event.status });
    }
  }
  result = await run.wait();
  completed = new Date().toISOString();
} catch (error) {
  await recordDispatchError("agent.send", error);
  console.error(JSON.stringify({ stage: "agent.send", error: compactError(error) }));
  try { await agent[Symbol.asyncDispose](); } catch {}
  throw error;
}

if (result.status !== "finished") throw new Error(`run status: ${result.status}`);
if (!sameSelection(run.model, config.selection) || !sameSelection(result.model, config.selection)) {
  throw new Error("run/result model selection mismatch");
}
if (initModels.length && initModels.some((model) => !sameSelection(model, config.selection))) {
  throw new Error("SDK init model selection mismatch");
}
if (toolEvents.some((event) => !["read", "piRead", "piWrite", "edit", "piEdit"].includes(event.name))) {
  throw new Error("non-allowlisted tool appeared in event stream");
}

const outputBytes = await readFile(output);
await copyFile(output, rawPath);
JSON.parse(outputBytes.toString("utf8"));
const finalFiles = await filesUnder(workspace);
const expectedFinal = [".cursor/hooks.json", job.output, job.packet].sort();
if (JSON.stringify(finalFiles) !== JSON.stringify(expectedFinal)) {
  throw new Error(`unexpected final workspace files: ${safeJson(finalFiles)}`);
}

let billedUsage = null;
try {
  billedUsage = await agent.getUsage();
} catch (error) {
  billedUsage = { unavailable: true, error_name: error.name };
}

await agent[Symbol.asyncDispose]();

const routing = {
  status: "pending_human_review",
  amendment: "corrections_v2/protocol/amendments/operational_amendment_2026-09-27-sdk-mapping.md",
  isolation_host: "wsl2-ubuntu",
  job_id: jobId,
  attempt,
  requested_model: config.locked,
  sdk_model_selection: config.selection,
  catalog_variant_verified: true,
  agent_id: agent.agentId,
  run_id: run.id,
  request_id: run.requestId ?? result.requestId ?? null,
  run_model: run.model ?? null,
  result_model: result.model ?? null,
  init_models: initModels,
  started_at_utc: started,
  completed_at_utc: completed,
  packet_path: job.packet,
  packet_sha256: job.packet_sha256,
  resolved_packet_path: packet,
  resolved_output_path: output,
  output_path: job.output,
  output_sha256: await sha256(output),
  raw_response_sha256: await sha256(rawPath),
  offered_tools: ["read", "edit", "piWrite"],
  sandbox_enabled: true,
  tool_events: toolEvents,
  sdk_usage: result.usage ?? run.usage ?? null,
  billed_usage: billedUsage,
  provider_model_version: null,
  version_metadata_status: "not_exposed",
};
await writeFile(routingPath, `${JSON.stringify(routing, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
await writeFile(routingTextPath, [
  `Linux WSL2 SDK run for ${jobId} attempt-${label}`,
  `started ${started} completed ${completed}`,
  `legacy lock: ${config.locked}`,
  `canonical selection: ${safeJson(config.selection)}`,
  `run.model: ${safeJson(run.model)}`,
  `result.model: ${safeJson(result.model)}`,
  `agent_id: ${agent.agentId}`,
  `run_id: ${run.id}`,
  `request_id: ${routing.request_id}`,
  `sandbox_enabled: true`,
  `resolved_packet: ${packet}`,
  `resolved_output: ${output}`,
  `packet_sha256: ${routing.packet_sha256}`,
  `output_sha256: ${routing.output_sha256}`,
  `raw_response_sha256: ${routing.raw_response_sha256}`,
  `offered_tools: read, edit, piWrite`,
  `tool_events: ${safeJson(toolEvents)}`,
  `sdk_usage: ${safeJson(routing.sdk_usage)}`,
  `billed_usage: ${safeJson(billedUsage)}`,
  `provider_model_version: not exposed; catalog, dispatch, init, run, result, hooks, transcript, and usage were inspected`,
  "",
].join("\n"), { encoding: "utf8", flag: "wx" });

console.log(JSON.stringify({
  status: routing.status,
  job_id: jobId,
  attempt,
  record_dir: recordDir,
  run_id: routing.run_id,
  request_id: routing.request_id,
  agent_id: routing.agent_id,
  sdk_usage: routing.sdk_usage,
  billed_usage: routing.billed_usage,
}));
