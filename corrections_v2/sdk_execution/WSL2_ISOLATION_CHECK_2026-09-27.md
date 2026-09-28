# WSL2 Linux SDK sandbox isolation check — 2026-09-27

Windows attempt `p01_C_j1_b01/attempt-01` remains archived as blocked
(`not_launched:windows_sdk_sandbox_unsupported`). Sandbox was not disabled.
This check is not a correction judgment.

## Result

`sandbox_initialized: true` on Ubuntu WSL2 as user `evidex`.

- Helper: `/home/evidex/sdk_execution/node_modules/@cursor/sdk-linux-x64/bin/cursorsandbox`
- Bubblewrap: 0.11.1
- Workspace: `/home/evidex/isolated/_sandbox_probe/workspace` (Linux home, not `/mnt/c`)
- Packet resolved to POSIX `/home/evidex/isolated/_sandbox_probe/workspace/corrections_v2/blind_io/p00/packet.json`
- Output resolved to POSIX `/home/evidex/isolated/_sandbox_probe/workspace/corrections_v2/blind_io/p00/packet.output.json`
- Fail-closed hook CLI: packet read allow, output write allow, outside read deny, `/mnt/c` repo read deny, packet overwrite deny, shell deny
- `agent.send` with `local.sandboxOptions.enabled=true` finished; `sandboxUnsupported=false`; `sendError=null`
- Probe model selection: `grok-4.6` effort=high fast=true
- Probe prompt was a non-judgment PONG dry run, not a correction packet

Raw report: `wsl/linux_sandbox_probe_report.json`.
