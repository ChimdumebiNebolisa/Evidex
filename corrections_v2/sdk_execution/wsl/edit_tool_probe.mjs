import { Agent } from "@cursor/sdk";
import { mkdir, writeFile, rm, readFile } from "node:fs/promises";
import path from "node:path";

const root = "/home/evidex/isolated/_edit_probe/workspace";
const packet = path.join(root, "corrections_v2/blind_io/p00/packet.json");
const output = path.join(root, "corrections_v2/blind_io/p00/packet.output.json");
const policy = "/home/evidex/sdk_execution/isolation-policy.mjs";
const audit = "/home/evidex/records/_edit_probe/hooks.jsonl";
await rm(root, { recursive: true, force: true });
await rm("/home/evidex/records/_edit_probe", { recursive: true, force: true });
await mkdir(path.dirname(packet), { recursive: true });
await mkdir(path.join(root, ".cursor"), { recursive: true });
await mkdir("/home/evidex/records/_edit_probe", { recursive: true });
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
  name: "evidex-edit-probe",
  model: selection,
  tools: ["read", "edit"],
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
  "Read exactly corrections_v2/blind_io/p00/packet.json. Write the JSON object {\"ok\":true} to corrections_v2/blind_io/p00/packet.output.json using the file-write tool available to you. Return only WROTE 1 records.",
  { model: selection, mcpServers: {} },
);
const events = [];
for await (const event of run.stream()) events.push(event);
const result = await run.wait();
await agent[Symbol.asyncDispose]();
let outputText = null;
try { outputText = await readFile(output, "utf8"); } catch (error) { outputText = String(error.message); }
const hooks = await readFile(audit, "utf8");
const assistant = events
  .filter((e) => e.type === "assistant")
  .map((e) => (e.message?.content ?? []).map((c) => c.text ?? "").join(""))
  .join("");
console.log(JSON.stringify({
  status: result.status,
  tools: events.filter((e) => e.type === "tool_call").map((e) => ({ name: e.name, status: e.status, args: e.args })),
  assistant,
  outputText,
  hook_lines: hooks.trim() ? hooks.trim().split(/\n/).length : 0,
  hooks: hooks.slice(0, 4000),
}, null, 2));
