import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Agent } from "@cursor/sdk";
import { decision } from "./isolation-policy.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const hook = path.join(here, "isolation-policy.mjs");
const root = await mkdtemp(path.join(os.tmpdir(), "evidex-sdk-isolation-"));
const packet = path.join(root, "corrections_v2", "blind_io", "p00", "packet.json");
const output = path.join(root, "corrections_v2", "blind_io", "p00", "packet.output.json");
const outside = path.join(path.dirname(root), "forbidden.txt");
const audit = path.join(path.dirname(root), `${path.basename(root)}.audit.jsonl`);
const hookCommand = `node "${hook}"`;

const env = {
  ...process.env,
  EVIDEX_PACKET_PATH: packet,
  EVIDEX_OUTPUT_PATH: output,
  EVIDEX_HOOK_AUDIT_PATH: audit,
  EVIDEX_WORKSPACE_PATH: root,
};

function preToolUse(tool_name, target) {
  return {
    hook_event_name: "preToolUse",
    tool_name,
    tool_input: target ? { path: target } : {},
  };
}

function invoke(payload) {
  return spawnSync(process.execPath, [hook], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    env,
  });
}

try {
  await mkdir(path.dirname(packet), { recursive: true });
  await mkdir(path.join(root, ".cursor"), { recursive: true });
  await writeFile(packet, '{"fixture":true}\n', "utf8");
  await writeFile(outside, "forbidden\n", "utf8");
  await writeFile(path.join(root, ".cursor", "hooks.json"), `${JSON.stringify({
    version: 1,
    hooks: {
      preToolUse: [{ command: hookCommand, matcher: "*", failClosed: true }],
      beforeReadFile: [{ command: hookCommand, matcher: "Read", failClosed: true }],
      beforeShellExecution: [{ command: hookCommand, matcher: "*", failClosed: true }],
      beforeMCPExecution: [{ command: hookCommand, matcher: "*", failClosed: true }],
      subagentStart: [{ command: hookCommand, matcher: "*", failClosed: true }],
    },
  }, null, 2)}\n`, "utf8");

  const cases = [
    ["packet read", preToolUse("Read", packet), "allow"],
    ["output read", preToolUse("Read", output), "allow"],
    ["outside read", preToolUse("Read", outside), "deny"],
    ["traversal read", preToolUse("Read", path.join(root, "..", path.basename(outside))), "deny"],
    ["output write", preToolUse("piWrite", output), "allow"],
    ["output edit", preToolUse("edit", output), "allow"],
    ["packet overwrite", preToolUse("piWrite", packet), "deny"],
    ["packet edit", preToolUse("edit", packet), "deny"],
    ["outside write", preToolUse("piWrite", outside), "deny"],
    ["shell", preToolUse("Shell"), "deny"],
    ["web search", preToolUse("webSearch"), "deny"],
    ["MCP", preToolUse("MCP:filesystem"), "deny"],
    ["subagent", preToolUse("Task"), "deny"],
    ["delete", preToolUse("Delete", output), "deny"],
    ["missing path", preToolUse("Read"), "deny"],
    ["beforeReadFile packet", { hook_event_name: "beforeReadFile", file_path: packet, attachments: [] }, "allow"],
    ["beforeReadFile output", { hook_event_name: "beforeReadFile", file_path: output, attachments: [] }, "allow"],
    ["beforeReadFile outside", { hook_event_name: "beforeReadFile", file_path: outside, attachments: [] }, "deny"],
    ["attachment outside", {
      hook_event_name: "beforeReadFile",
      file_path: packet,
      attachments: [{ type: "rule", file_path: outside }],
    }, "deny"],
    ["shell hook", { hook_event_name: "beforeShellExecution" }, "deny"],
    ["MCP hook", { hook_event_name: "beforeMCPExecution" }, "deny"],
    ["subagent hook", { hook_event_name: "subagentStart" }, "deny"],
  ];

  for (const [name, payload, expected] of cases) {
    assert.equal(decision(payload, env).permission, expected, name);
    const result = invoke(payload);
    assert.equal(result.status, expected === "allow" ? 0 : 2, `${name} process status`);
    assert.equal(JSON.parse(result.stdout).permission, expected, `${name} process response`);
  }

  const invalid = spawnSync(process.execPath, [hook], {
    input: "{invalid",
    encoding: "utf8",
    env,
  });
  assert.equal(invalid.status, 2, "invalid JSON fails closed");
  assert.equal(JSON.parse(invalid.stdout).permission, "deny");

  const missingAudit = spawnSync(process.execPath, [hook], {
    input: JSON.stringify(preToolUse("Read", packet)),
    encoding: "utf8",
    env: { ...env, EVIDEX_HOOK_AUDIT_PATH: "" },
  });
  assert.equal(missingAudit.status, 2, "audit failure fails closed");
  assert.equal(JSON.parse(missingAudit.stdout).permission, "deny");

  const agent = await Agent.create({
    name: "evidex-offline-isolation-fixture",
    model: {
      id: "grok-4.6",
      params: [
        { id: "effort", value: "high" },
        { id: "fast", value: "true" },
      ],
    },
    tools: ["read", "edit", "piWrite"],
    disallowedTools: ["shell", "mcp", "task", "webSearch"],
    mcpServers: {},
    local: {
      cwd: root,
      settingSources: ["project"],
      sandboxOptions: { enabled: true },
      enableAgentRetries: false,
    },
  });
  await agent[Symbol.asyncDispose]();

  const auditLines = (await readFile(audit, "utf8")).trim().split(/\r?\n/);
  assert.equal(auditLines.length, cases.length, "one audit record per valid hook invocation");

  console.log(JSON.stringify({
    fixture_only: true,
    inference_calls: 0,
    policy_cases_passed: cases.length,
    invalid_json_failed_closed: true,
    audit_failure_failed_closed: true,
    sandbox_agent_create_without_send: "passed",
    offered_tools: ["read", "edit", "piWrite"],
    denied_tools: ["shell", "mcp", "task", "webSearch"],
  }));
} finally {
  await rm(root, { recursive: true, force: true });
  await rm(outside, { force: true });
  await rm(audit, { force: true });
}
