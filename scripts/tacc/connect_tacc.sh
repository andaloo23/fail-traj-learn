#!/bin/bash
# Interactive local authentication, followed by a read-only allocation inventory.
# Run in a real WSL terminal so SSH reads password/MFA directly from the terminal.
set -euo pipefail
username=${1:?Usage: bash scripts/tacc/connect_tacc.sh USERNAME HOSTNAME}
host=${2:?Missing TACC hostname}
if [[ ! "$username" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ || ! "$host" =~ ^[a-z0-9.-]+\.tacc\.utexas\.edu$ ]]; then
    echo 'Use the TACC username and a hostname ending in .tacc.utexas.edu.' >&2
    exit 2
fi
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
socket="$HOME/.ssh/tacc-flora-%C"
target="$username@$host"
out="$repo/outputs/tacc_access"
mkdir -p "$HOME/.ssh" "$out"
chmod 700 "$HOME/.ssh"
report="$out/$username-$host.txt"
receipt="$out/$username-$host.ready"
if [[ -e "$receipt" ]]; then
    stamp=$(date -u +%Y%m%dT%H%M%S)
    mv -- "$receipt" "$receipt.$stamp.previous"
    if [[ -f "$report" ]]; then cp -- "$report" "$report.$stamp.previous"; fi
fi
printf 'TACC allocation check for %s\n' "$target"
echo 'Enter your password and MFA at the SSH prompts. Do not enter them in chat.'
echo 'A failed login does not establish that you have no allocation.'
if ! ssh -S "$socket" -O check "$target" 2>/dev/null; then
    ssh -M -S "$socket" -o ControlPersist=4h -o ConnectTimeout=20 -fN "$target"
fi
echo 'Authenticated. Reading project balances and available queues...'
partial=$(mktemp "$out/.inventory-XXXXXX")
trap 'rm -f -- "$partial"' EXIT
if ssh -S "$socket" -o BatchMode=yes "$target" bash -s < "$repo/scripts/tacc/probe.sh" > "$partial" 2>&1; then
    mv -- "$partial" "$report"
    printf 'Authenticated: %s\nUTC: %s\nReport: %s\n' "$target" "$(date -u +%FT%TZ)" "$report" > "$receipt"
    cat "$report"
    printf '\nAllocation inventory saved to %s\nThe authenticated connection is ready for Codex.\n' "$report"
else
    cat "$partial"
    echo 'Login succeeded, but the inventory command failed. No ready receipt was written.' >&2
    exit 1
fi
