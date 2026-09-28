#!/usr/bin/env bash
set -euo pipefail
echo "uid=$(id -u) user=$(id -un)"
echo "HOME=$HOME"
echo "PWD=$PWD"
echo "uname=$(uname -a)"
command -v bwrap
bwrap --version
echo "userns_clone=$(cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null || echo missing)"
echo "max_user_namespaces=$(cat /proc/sys/user/max_user_namespaces 2>/dev/null || echo missing)"
command -v node || echo "node=absent"
command -v npm || echo "npm=absent"
ls -ld /root /home /tmp
getent passwd | awk -F: '$3>=1000 {print $1,$3,$6,$7}'
