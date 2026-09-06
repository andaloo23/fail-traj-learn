#!/usr/bin/env bash
# Schema v3 smoke recording: 4 shifted-init episodes on the butter task (goal-region container keeps its yaw,
# gripper_cmd in the sidecar, lag-free privileged poses). Dataset: data/v3_test__t6.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export PROJ SCRIPTS
NAME=v3_test SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS='[6]' N_EP=4 INIT=shifted SXY=0.08 SYAW=60 SEED=4300 \
  NOTES="schema v3 smoke: shifted init 8cm/60deg, container yaw locked" \
  bash "$SCRIPTS/record/record_config.sh"
