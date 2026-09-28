#!/usr/bin/env bash
# Run fresh three-turn Codex CLI conversations for R002--R012, serially.
#
# Each initial `codex exec` creates one new conversation. Turns 2 and 3 use
# `codex exec resume <thread-id>` so context is shared only within that R ID.
# This script deliberately refuses to overwrite any existing v3 artifact.
set -euo pipefail

# On WSL, `pwd` may normalize this mount to an uppercase path that a sandbox treats
# as outside its writable root. Callers can override it, while the default is the
# workspace spelling used by this project.
ROOT="${WORKSPACE_ROOT:-/mnt/c/users/localpc/dev/fail-traj-learn}"
if [[ ! -d "$ROOT" ]]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
CODEX_BIN="${CODEX_BIN:-codex}"
MODEL="${CODEX_MODEL:-gpt-6-astra}"
PYTHON_BIN="${PYTHON_BIN:-/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python}"
PROMPTS="$ROOT/outputs/gpt6_human_review_v1/fewshot_v3/prompts"
EPISODES="$ROOT/outputs/gpt6_human_review_v1/episodes"
RUNS="$ROOT/outputs/gpt6_human_review_v1/fewshot_v3/codex_runs"
IDS=(R002 R003 R004 R005 R006 R007 R008 R009 R010 R011 R012)

extract_thread_id() {
  local jsonl="$1"
  node - "$jsonl" <<'NODE'
const fs = require("fs");
const lines = fs.readFileSync(process.argv[2], "utf8").split(/\r?\n/).filter(Boolean);
const keys = new Set(["thread_id", "threadId", "session_id", "sessionId"]);
function find(value) {
  if (!value || typeof value !== "object") return null;
  if (Array.isArray(value)) {
    for (const child of value) { const found = find(child); if (found) return found; }
    return null;
  }
  for (const [key, child] of Object.entries(value)) {
    if (keys.has(key) && typeof child === "string" && child) return child;
    if (key === "thread" && child && typeof child.id === "string") return child.id;
    const found = find(child);
    if (found) return found;
  }
  return null;
}
for (const line of lines) {
  try {
    const found = find(JSON.parse(line));
    if (found) { process.stdout.write(found); process.exit(0); }
  } catch (_) {}
}
process.exit(1);
NODE
}

run_initial_turn() {
  local ident="$1" run_dir="$2"
  "$CODEX_BIN" exec --json -m "$MODEL" --approve-for-me \
    -C "$ROOT" "$(<"$PROMPTS/${ident}_turn1.md")" \
    >"$run_dir/turn1.jsonl" 2>"$run_dir/turn1.stderr"
}

run_resumed_turn() {
  local ident="$1" turn="$2" thread_id="$3" run_dir="$4"
  "$CODEX_BIN" exec resume --json -m "$MODEL" "$thread_id" \
    "$(<"$PROMPTS/${ident}_turn${turn}.md")" \
    >"$run_dir/turn${turn}.jsonl" 2>"$run_dir/turn${turn}.stderr"
}

mkdir -p "$RUNS"
for ident in "${IDS[@]}"; do
  episode="$EPISODES/$ident"
  run_dir="$RUNS/$ident"
  if [[ -e "$episode/gpt6_fewshot_v3_observation.json" || -e "$episode/gpt6_fewshot_v3_audit.json" || -e "$episode/gpt6_fewshot_v3_annotation.json" ]]; then
    echo "$ident: refusing to overwrite existing v3 artifact" >&2
    exit 1
  fi
  mkdir -p "$run_dir"
  echo "$ident: starting fresh Codex conversation"
  run_initial_turn "$ident" "$run_dir"
  thread_id="$(extract_thread_id "$run_dir/turn1.jsonl")" || {
    echo "$ident: could not extract a Codex thread ID; see $run_dir/turn1.jsonl" >&2
    exit 1
  }
  printf '%s\n' "$thread_id" >"$run_dir/thread_id.txt"
  echo "$ident: turn 1 complete; resuming $thread_id for turn 2"
  run_resumed_turn "$ident" 2 "$thread_id" "$run_dir"
  echo "$ident: turn 2 complete; resuming $thread_id for turn 3"
  run_resumed_turn "$ident" 3 "$thread_id" "$run_dir"
  "$PYTHON_BIN" "$ROOT/scripts/annotate/bench/gpt6_human_review_fewshot_v3.py" \
    validate-gpt --id "$ident" | tee "$run_dir/validation.txt"
  echo "$ident: valid"
done
