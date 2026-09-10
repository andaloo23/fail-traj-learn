#!/usr/bin/env bash
# Seed replication of the claims the sweep rests on: the sparse-event reward beating the terminal-only
# critic, and the actor-side modes beating it as well. One 150-episode evaluation carries about
# +-8 points, so the single-seed ordering in docs/rl_results.md is not yet significant on its own.
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
SEEDS=${SEEDS:-"1 2"}
bash "$R/seeds.sh" iql_events "$SEEDS" -- --algo iql --segments events --seg-use-q
bash "$R/seeds.sh" iql_mask   "$SEEDS" -- --algo iql --segments mask   --seg-use-q
bash "$R/seeds.sh" iql_terminal "$SEEDS" -- --algo iql
