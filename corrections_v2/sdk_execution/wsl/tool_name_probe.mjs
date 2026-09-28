import { Agent } from "@cursor/sdk";
import { mkdtemp, rm } from "node:fs/promises";

const cwd = await mkdtemp("/home/evidex/isolated/_tool_probe_");
const model = {
  id: "grok-4.6",
  params: [
    { id: "effort", value: "high" },
    { id: "fast", value: "true" },
  ],
};

async function tryTools(tools) {
  try {
    const agent = await Agent.create({
      name: "evidex-tool-name-probe",
      model,
      tools,
      disallowedTools: ["shell", "mcp", "task", "webSearch"],
      mcpServers: {},
      agents: {},
      local: {
        cwd,
        settingSources: [],
        sandboxOptions: { enabled: true },
        enableAgentRetries: false,
      },
    });
    await agent[Symbol.asyncDispose]();
    return { tools, ok: true };
  } catch (error) {
    return {
      tools,
      ok: false,
      name: error?.name,
      message: String(error?.message || error).slice(0, 2000),
    };
  }
}

const results = [];
for (const tools of [
  ["not-a-real-tool"],
  ["read", "write"],
  ["read", "edit"],
  ["read", "piWrite"],
  ["read", "Write"],
]) {
  results.push(await tryTools(tools));
}
console.log(JSON.stringify(results, null, 2));
await rm(cwd, { recursive: true, force: true });
