import { appendFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

function canonical(value, env = process.env) {
  if (typeof value !== "string" || !value.trim()) return null;
  const workspace = env.EVIDEX_WORKSPACE_PATH;
  const resolved = path.isAbsolute(value)
    ? path.resolve(value)
    : path.resolve(workspace || process.cwd(), value);
  return resolved.replaceAll("\\", "/").toLowerCase();
}

function candidatePath(input) {
  if (!input || typeof input !== "object") return null;
  for (const key of ["file_path", "path", "target_file", "target_path"]) {
    if (typeof input[key] === "string") return input[key];
  }
  return null;
}

function allowRead(requested, packet, output) {
  if (requested === packet) return { permission: "allow", reason: "designated packet read" };
  if (requested === output) return { permission: "allow", reason: "designated output read" };
  return { permission: "deny", reason: "read outside designated packet/output" };
}

function decision(payload, env = process.env) {
  const packet = canonical(env.EVIDEX_PACKET_PATH, env);
  const output = canonical(env.EVIDEX_OUTPUT_PATH, env);
  if (!packet || !output) return { permission: "deny", reason: "policy paths unavailable" };

  const event = payload?.hook_event_name;
  if (event === "beforeReadFile") {
    const requested = canonical(payload.file_path, env);
    const attachments = Array.isArray(payload.attachments) ? payload.attachments : [];
    const attachmentsAllowed = attachments.every((item) => {
      const attachment = canonical(item?.file_path, env);
      return attachment === packet || attachment === output;
    });
    if (!attachmentsAllowed) {
      return { permission: "deny", reason: "read outside designated packet/output" };
    }
    return allowRead(requested, packet, output);
  }

  if (event === "preToolUse") {
    const tool = String(payload.tool_name ?? "").toLowerCase();
    const requested = canonical(candidatePath(payload.tool_input), env);
    if (tool === "read" || tool === "piread") {
      return allowRead(requested, packet, output);
    }
    if (tool === "write" || tool === "piwrite" || tool === "edit" || tool === "piedit") {
      return requested === output
        ? { permission: "allow", reason: "designated output write" }
        : { permission: "deny", reason: "write outside designated output" };
    }
    return { permission: "deny", reason: `tool not allowlisted: ${tool || "unknown"}` };
  }

  return { permission: "deny", reason: `hook event denied: ${event || "unknown"}` };
}

function audit(payload, result, env = process.env) {
  const log = env.EVIDEX_HOOK_AUDIT_PATH;
  if (!log) throw new Error("EVIDEX_HOOK_AUDIT_PATH is required");
  const record = {
    at_utc: new Date().toISOString(),
    hook_event_name: payload?.hook_event_name ?? null,
    tool_name: payload?.tool_name ?? null,
    requested_path: candidatePath(payload?.tool_input) ?? payload?.file_path ?? null,
    permission: result.permission,
    reason: result.reason,
  };
  appendFileSync(log, `${JSON.stringify(record)}\n`, { encoding: "utf8" });
}

export { decision };

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  let payload;
  try {
    payload = JSON.parse(await new Promise((resolve, reject) => {
      let value = "";
      process.stdin.setEncoding("utf8");
      process.stdin.on("data", (chunk) => { value += chunk; });
      process.stdin.on("end", () => resolve(value));
      process.stdin.on("error", reject);
    }));
    const result = decision(payload);
    audit(payload, result);
    console.log(JSON.stringify({
      permission: result.permission,
      user_message: result.permission === "deny" ? result.reason : undefined,
    }));
    if (result.permission === "deny") process.exitCode = 2;
  } catch (error) {
    console.log(JSON.stringify({
      permission: "deny",
      user_message: `isolation policy failed closed: ${error.message}`,
    }));
    process.exitCode = 2;
  }
}
