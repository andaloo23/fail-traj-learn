#!/usr/bin/env bash
# Smoke test: MolmoAct2-LIBERO on one LIBERO task. Optionally recorded to a LeRobotDataset (RECORD=true).
# All paths are absolute on purpose. Never call this through wsl.exe with inline variables.
set -euo pipefail
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
cd "$PROJ/lerobot"
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

SUITE=${SUITE:-libero_object}
TASK_IDS=${TASK_IDS:-[0]}
N_EP=${N_EP:-5}
RECORD=${RECORD:-false}
NAME=${NAME:-smoke_${SUITE}}
OUT="$PROJ/outputs/eval_$NAME"

echo "suite=$SUITE task_ids=$TASK_IDS n_episodes=$N_EP record=$RECORD out=$OUT"
mkdir -p "$PROJ/outputs"
if [ -d "$OUT" ]; then
  echo "output dir exists: $OUT"
  echo "remove it manually if you want to rerun"
  exit 2
fi

"$PROJ/lerobot/.venv/bin/lerobot-eval" \
  --policy.type=molmoact2 \
  --policy.checkpoint_path=allenai/MolmoAct2-LIBERO \
  --policy.norm_tag=libero \
  --policy.inference_action_mode=continuous \
  --policy.dtype=bfloat16 \
  --policy.enable_inference_cuda_graph=true \
  --policy.device=cuda \
  --policy.per_episode_seed=true \
  --policy.eval_seed=1000 \
  --env.type=libero \
  --env.task="$SUITE" \
  --env.task_ids="$TASK_IDS" \
  --env.camera_name_mapping='{"agentview_image":"image","robot0_eye_in_hand_image":"wrist_image"}' \
  --eval.batch_size=1 \
  --eval.n_episodes="$N_EP" \
  --eval.recording="$RECORD" \
  --seed=1000 \
  --output_dir="$OUT"
