import { mkdir, writeFile, rm } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { Agent } from "@cursor/sdk";
import { decision } from "./isolation-policy.mjs";

const root = "/home/evidex/isolated/_sandbox_probe/workspace";
const packet = path.join(root, "corrections_v2/blind_io/p00/packet.json");
const output = path.join(root, "corrections_v2/blind_io/p00/packet.output.json");
const audit = "/home/evidex/records/_sandbox_probe/hooks.jsonl";
const outside = "/tmp/evidex-forbidden.txt";
const policy = "/home/evidex/sdk_execution/isolation-policy.mjs";

await rm(root, { recursive: true, force: true });
await rm("/home/evidex/records/_sandbox_probe", { recursive: true, force: true });
await mkdir(path.dirname(packet), { recursive: true });
await mkdir(path.join(root, ".cursor"), { recursive: true });
await mkdir("/home/evidex/records/_sandbox_probe", { recursive: true });
await writeFile(packet, '{"fixture":true}\n', "utf8");
await writeFile(outside, "forbidden\n", "utf8");
await writeFile(audit, "", "utf8");
await writeFile(path.join(root, ".cursor/hooks.json"), JSON.stringify({
  version: 1,
  hooks: {
    preToolUse: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
    beforeReadFile: [{ command: `node "${policy}"`, matcher: "Read", failClosed: true }],
    beforeShellExecution: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
    beforeMCPExecution: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
    subagentStart: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
  },
}, null, 2) + "\n");

const env = {
  ...process.env,
  HOME: "/home/evidex",
  EVIDEX_PACKET_PATH: packet,
  EVIDEX_OUTPUT_PATH: output,
  EVIDEX_HOOK_AUDIT_PATH: audit,
};

function runHook(payload) {
  return spawnSync(process.execPath, [policy], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    env,
  });
}

const pathCases = [
  ["packet read", { hook_event_name: "preToolUse", tool_name: "Read", tool_input: { path: packet } }, "allow"],
  ["output write", { hook_event_name: "preToolUse", tool_name: "piWrite", tool_input: { path: output } }, "allow"],
  ["outside read", { hook_event_name: "preToolUse", tool_name: "Read", tool_input: { path: outside } }, "deny"],
  ["mntc repo read", { hook_event_name: "preToolUse", tool_name: "Read", tool_input: { path: "/mnt/c/Users/Chimdumebi/evidex/corrections_v2/generated/rerun_manifest.json" } }, "deny"],
  ["packet overwrite", { hook_event_name: "preToolUse", tool_name: "piWrite", tool_input: { path: packet } }, "deny"],
  ["shell", { hook_event_name: "preToolUse", tool_name: "Shell", tool_input: {} }, "deny"],
];

const policyResults = [];
for (const [name, payload, expected] of pathCases) {
  const decided = decision(payload, env).permission;
  const proc = runHook(payload);
  const permission = JSON.parse(proc.stdout || "{}").permission;
  const okStatus = expected === "allow" ? proc.status === 0 : proc.status === 2;
  if (decided !== expected || permission !== expected || !okStatus) {
    throw new Error(`policy failed: ${name} decided=${decided} proc=${permission}/${proc.status} stderr=${proc.stderr}`);
  }
  policyResults.push({ name, permission, resolved_packet: path.resolve(packet), resolved_output: path.resolve(output) });
}

process.env.EVIDEX_PACKET_PATH = packet;
process.env.EVIDEX_OUTPUT_PATH = output;
process.env.EVIDEX_HOOK_AUDIT_PATH = audit;

const started = new Date().toISOString();
const agent = await Agent.create({
  name: "evidex-linux-sandbox-probe",
  model: { id: "grok-4.6", params: [{ id: "effort", value: "high" }, { id: "fast", value: "true" }] },
  tools: ["read", "piWrite"],
  disallowedTools: ["shell", "mcp", "task", "webSearch"],
  mcpServers: {},
  agents: {},
  local: {
    cwd: root,
    settingSources: [],
    sandboxOptions: { enabled: true },
    enableAgentRetries: false,
  },
});

let sendError = null;
let result = null;
try {
  const run = await agent.send("Do not use tools. Reply with the single word PONG.", {
    model: { id: "grok-4.6", params: [{ id: "effort", value: "high" }, { id: "fast", value: "true" }] },
  });
  result = await run.wait();
} catch (error) {
  sendError = {
    name: error?.name,
    message: String(error?.message || error).slice(0, 800),
    operation: error?.operation ?? null,
  };
} finally {
  try { await agent[Symbol.asyncDispose](); } catch {}
}

const sandboxUnsupported = Boolean(sendError?.message?.includes("sandboxing is not supported"));
const report = {
  linux_ext4_workspace: root.startsWith("/home/evidex/"),
  resolved_packet: packet,
  resolved_output: output,
  packet_is_posix: packet.includes("/") && !packet.includes("\\"),
  policyResults,
  sendError,
  sandboxUnsupported,
  run_status: result?.status ?? null,
  run_model: result?.model ?? null,
  sandbox_initialized: !sandboxUnsupported && !sendError && result?.status === "finished",
  started,
  completed: new Date().toISOString(),
};
await writeFile("/home/evidex/records/_sandbox_probe/report.json", JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report, null, 2));
if (!report.sandbox_initialized) process.exit(2);
