#!/usr/bin/env bash
# General recorder wrapper. Everything is set through environment variables so a pilot script can
# chain several configurations. Defaults reproduce the MolmoAct2-LIBERO smoke test.
#
#   NAME      dataset name (data/<NAME>)                 SOURCE   policy family tag
#   CKPT      HF checkpoint (policy.checkpoint_path)      NORM_TAG MolmoAct2 norm tag (libero)
#   SUITE     libero suite(s), comma separated           TASK_IDS  e.g. '[0,1,2]' or '' for all
#   N_EP      episodes per task                           INIT      standard | shifted
#   SXY       shift in meters (shifted)                   SYAW      shift yaw in degrees (shifted)
#   NOISE     action noise std (0 = off)                  SEED      base seed
#   EXTRA     extra CLI flags, e.g. '--policy.num_inference_steps=2'
#   NOTES     free text stored in every sidecar
set -uo pipefail
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}

NAME=${NAME:-smoke_rec}
SOURCE=${SOURCE:-molmoact2_libero}
CKPT=${CKPT:-allenai/MolmoAct2-LIBERO}
NORM_TAG=${NORM_TAG:-libero}
SUITE=${SUITE:-libero_object}
TASK_IDS=${TASK_IDS-[0]}   # unset -> task 0 only; explicitly empty (TASK_IDS=) -> all tasks in the suite
N_EP=${N_EP:-2}
INIT=${INIT:-standard}
SXY=${SXY:-0.0}
SYAW=${SYAW:-0.0}
NOISE=${NOISE:-0.0}
SEED=${SEED:-2000}
EXTRA=${EXTRA:-}
NOTES=${NOTES:-}

cd "$PROJ/lerobot"
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$PROJ/logs"

# One recorder process per task: each process owns exactly one MuJoCo/EGL renderer and finalizes its own
# dataset (data/<NAME>__t<task>), so a native crash can lose at most the task in progress.
if [ -z "$TASK_IDS" ]; then
  case "$SUITE" in
    libero_90) LAST=89 ;;
    *) LAST=9 ;;
  esac
  TASK_LIST=$(seq 0 $LAST)
else
  TASK_LIST=$(echo "$TASK_IDS" | tr -d '[] ' | tr ',' ' ')
fi

FINAL_RC=0
for TID in $TASK_LIST; do
DSNAME="${NAME}__t${TID}"
LOG="$PROJ/logs/record_${DSNAME}.log"
echo "[record_config] NAME=$DSNAME SOURCE=$SOURCE CKPT=$CKPT SUITE=$SUITE TASK=$TID N_EP=$N_EP INIT=$INIT SXY=$SXY SYAW=$SYAW NOISE=$NOISE EXTRA=$EXTRA" | tee -a "$LOG"
.venv/bin/python "$SCRIPTS/record_rollouts.py" \
  --policy.type=molmoact2 \
  --policy.checkpoint_path="$CKPT" \
  --policy.norm_tag="$NORM_TAG" \
  --policy.inference_action_mode=continuous \
  --policy.dtype=bfloat16 \
  --policy.enable_inference_cuda_graph=true \
  --policy.device=cuda \
  --policy.per_episode_seed=true \
  --policy.eval_seed="$SEED" \
  --env.type=libero \
  --env.task="$SUITE" \
  --env.task_ids="[$TID]" \
  --env.observation_height=256 \
  --env.observation_width=256 \
  --env.camera_name_mapping='{"agentview_image":"image","robot0_eye_in_hand_image":"wrist_image"}' \
  --n_episodes="$N_EP" \
  --dataset_name="$DSNAME" \
  --source="$SOURCE" \
  --checkpoint_tag="$CKPT" \
  --init_mode="$INIT" \
  --shift_xy="$SXY" \
  --shift_yaw_deg="$SYAW" \
  --action_noise_std="$NOISE" \
  --seed="$SEED" \
  --notes="$NOTES" \
  $EXTRA \
  >> "$LOG" 2>&1
RC=$?
echo "EXIT=$RC" >> "$LOG"
grep -aE 'Finalized|Recording aborted|malloc|EXIT=' "$LOG" | tail -3 | cut -c1-200
if [ $RC -ne 0 ]; then FINAL_RC=$RC; echo "[record_config] task $TID exited rc=$RC"; fi
done
exit $FINAL_RC
