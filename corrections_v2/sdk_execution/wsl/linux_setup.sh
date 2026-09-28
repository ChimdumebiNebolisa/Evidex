#!/usr/bin/env bash
set -euo pipefail
export HOME=/home/evidex
export USER=evidex
umask 022
NODE_VERSION=v22.20.0
PREFIX=/home/evidex/node
if [ ! -x "$PREFIX/bin/node" ]; then
  mkdir -p /tmp/node-dist "$PREFIX"
  curl -fsSL "https://nodejs.org/dist/${NODE_VERSION}/node-${NODE_VERSION}-linux-x64.tar.xz" -o /tmp/node-dist/node.tar.xz
  tar -xJf /tmp/node-dist/node.tar.xz -C /tmp/node-dist
  rm -rf "$PREFIX"
  mv /tmp/node-dist/node-${NODE_VERSION}-linux-x64 "$PREFIX"
fi
export PATH="$PREFIX/bin:$PATH"
node -v
npm -v
# bubblewrap smoke as unprivileged user
bwrap --unshare-user --unshare-pid --unshare-uts --unshare-ipc --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /bin /bin \
  --proc /proc --dev /dev --tmpfs /tmp /bin/echo bwrap_ok
echo "linux_sdk_dir_prep=start"
SDK=/home/evidex/sdk_execution
mkdir -p "$SDK"
cp -f /mnt/c/Users/Chimdumebi/evidex/corrections_v2/sdk_execution/package.json "$SDK/"
cp -f /mnt/c/Users/Chimdumebi/evidex/corrections_v2/sdk_execution/package-lock.json "$SDK/"
cd "$SDK"
npm ci --ignore-scripts --no-audit --no-fund
# optional linux binary should now be present
ls -la node_modules/@cursor/sdk-linux-x64 2>/dev/null | head
ls node_modules/@cursor/sdk-linux-x64 | head
node -e "const p=require('./node_modules/@cursor/sdk/package.json'); console.log('sdk', p.version)"
echo "auth_copy"
mkdir -p /home/evidex/.cursor/sdk
if [ -f /mnt/c/Users/Chimdumebi/.cursor/sdk/auth.json ]; then
  cp -f /mnt/c/Users/Chimdumebi/.cursor/sdk/auth.json /home/evidex/.cursor/sdk/auth.json
  chmod 600 /home/evidex/.cursor/sdk/auth.json
  echo "auth_copied=yes"
else
  echo "auth_copied=no"
  exit 1
fi
chown -R evidex:evidex /home/evidex
echo "setup_ok"
