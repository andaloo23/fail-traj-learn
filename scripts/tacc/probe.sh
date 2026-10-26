#!/bin/bash
# Read-only login-node inventory. No GPU work, downloads, or job submissions.
set -uo pipefail
hostname -f
uname -m
command -v python3 && python3 --version
printf 'WORK=%s\nSCRATCH=%s\n' "${WORK:-unset}" "${SCRATCH:-unset}"
if [[ -x /usr/local/etc/taccinfo ]]; then /usr/local/etc/taccinfo; fi
command -v show_accounts >/dev/null && show_accounts
command -v qlimits >/dev/null && qlimits
command -v sinfo >/dev/null && sinfo -o '%P %a %l %D %G'
command -v module >/dev/null && module -t list 2>&1
command -v module >/dev/null && module -t avail python3 cuda 2>&1
df -h "${SCRATCH:-.}"
