import { Agent } from "@cursor/sdk";
import { mkdir, writeFile, rm } from "node:fs/promises";
import path from "node:path";

const root = "/home/evidex/isolated/_tool_visibility/workspace";
const packet = path.join(root, "corrections_v2/blind_io/p00/packet.json");
const output = path.join(root, "corrections_v2/blind_io/p00/packet.output.json");
const policy = "/home/evidex/sdk_execution/isolation-policy.mjs";
const audit = "/home/evidex/records/_tool_visibility/hooks.jsonl";
await rm(root, { recursive: true, force: true });
await rm("/home/evidex/records/_tool_visibility", { recursive: true, force: true });
await mkdir(path.dirname(packet), { recursive: true });
await mkdir(path.join(root, ".cursor"), { recursive: true });
await mkdir("/home/evidex/records/_tool_visibility", { recursive: true });
await writeFile(packet, '{"fixture":true}\n', "utf8");
await writeFile(audit, "", "utf8");
await writeFile(path.join(root, ".cursor/hooks.json"), `${JSON.stringify({
  version: 1,
  hooks: {
    preToolUse: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
    beforeReadFile: [{ command: `node "${policy}"`, matcher: "Read", failClosed: true }],
    beforeShellExecution: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
    beforeMCPExecution: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
    subagentStart: [{ command: `node "${policy}"`, matcher: "*", failClosed: true }],
  },
}, null, 2)}\n`);

process.env.EVIDEX_PACKET_PATH = packet;
process.env.EVIDEX_OUTPUT_PATH = output;
process.env.EVIDEX_HOOK_AUDIT_PATH = audit;

const selection = {
  id: "grok-4.6",
  params: [
    { id: "effort", value: "high" },
    { id: "fast", value: "true" },
  ],
};
const agent = await Agent.create({
  name: "evidex-tool-visibility",
  model: selection,
  tools: ["read", "piWrite"],
  disallowedTools: ["shell", "mcp", "task", "webSearch"],
  mcpServers: {},
  agents: {},
  local: {
    cwd: root,
    settingSources: ["project"],
    sandboxOptions: { enabled: true },
    enableAgentRetries: false,
  },
});
const run = await agent.send(
  "Do not judge any claims. Reply with the exact names of tools currently available to you, then stop. Do not read files unless required to answer that question.",
  { model: selection, mcpServers: {} },
);
const events = [];
for await (const event of run.stream()) events.push(event);
const result = await run.wait();
await agent[Symbol.asyncDispose]();
const { readFile } = await import("node:fs/promises");
const hooks = await readFile(audit, "utf8");
console.log(JSON.stringify({
  status: result.status,
  model: result.model,
  tools: events.filter((e) => e.type === "tool_call").map((e) => ({ name: e.name, status: e.status })),
  assistant: events.filter((e) => e.type === "assistant").map((e) => e.text).join(""),
  hook_bytes: hooks.length,
  hook_lines: hooks.trim() ? hooks.trim().split(/\n/).length : 0,
}, null, 2));
