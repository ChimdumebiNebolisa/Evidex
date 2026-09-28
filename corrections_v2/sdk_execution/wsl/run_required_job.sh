#!/usr/bin/env bash
set -euo pipefail

JOB="${1:?job id}"
ATTEMPT="${2:?attempt number}"
LABEL="$(printf '%02d' "$ATTEMPT")"
REPO="${EVIDEX_REPO:-/mnt/c/Users/Chimdumebi/evidex}"
SDK="/home/evidex/sdk_execution"
NODE="/home/evidex/node/bin/node"
ZIP="$REPO/corrections_v2/handoff_jobs/${JOB}.zip"
WS="/home/evidex/isolated/${JOB}/attempt-${LABEL}/workspace"
RD="/home/evidex/records/${JOB}/attempt-${LABEL}"
STAGE="/mnt/c/Users/Chimdumebi/evidex_execution_records/${JOB}/attempt-${LABEL}"

if [[ ! -f "$ZIP" ]]; then
  echo "missing export: $ZIP" >&2
  exit 2
fi
if [[ -e "$WS" || -e "$RD" ]]; then
  echo "workspace or record dir already exists" >&2
  exit 2
fi

mkdir -p "/home/evidex/isolated/${JOB}/attempt-${LABEL}" "/home/evidex/records/${JOB}"
mkdir -p "$WS"
python3 - "$ZIP" "$WS" <<'PY'
import sys, zipfile
src, dest = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(src) as archive:
    names = archive.namelist()
    if len(names) != 1:
        raise SystemExit(f"export must contain exactly one packet, got {names}")
    archive.extractall(dest)
PY
chown -R evidex:evidex "/home/evidex/isolated/${JOB}" "/home/evidex/records/${JOB}"
find "$WS" -print | sed "s|^|workspace: |"

set +e
sudo -u evidex env \
  HOME=/home/evidex \
  USER=evidex \
  PATH=/home/evidex/node/bin:/usr/bin:/bin \
  EVIDEX_REPO="$REPO" \
  EVIDEX_POLICY_PATH="$SDK/isolation-policy.mjs" \
  EVIDEX_EXECUTION_AUTHORIZATION="$JOB" \
  "$NODE" "$SDK/run-proposed-job.mjs" \
    --job "$JOB" \
    --attempt "$ATTEMPT" \
    --workspace "$WS" \
    --record-dir "$RD"
NODE_EXIT=$?
set -e

mkdir -p "$STAGE"
if [[ -d "$RD" ]]; then
  cp -a "$RD"/. "$STAGE"/ || true
fi

if [[ $NODE_EXIT -ne 0 ]]; then
  echo "run-proposed-job exited with code $NODE_EXIT" >&2
  exit $NODE_EXIT
fi

mkdir -p "$STAGE"
cp -a "$RD"/. "$STAGE"/
python3 - "$RD" "$WS" "$STAGE" "$REPO" "$JOB" <<'PY'
import json, shutil, sys
from pathlib import Path
rd, ws, stage, repo, job = map(Path, sys.argv[1:6])
routing = json.loads((rd / sorted(rd.glob('attempt-*.routing.json'))[0]).read_text())
src = ws / routing['output_path']
dst = stage / 'workspace.output.json'
shutil.copy2(src, dst)
print(json.dumps({
    'copied_output': str(dst),
    'bytes': dst.stat().st_size,
    'job_id': str(job),
}))
PY
