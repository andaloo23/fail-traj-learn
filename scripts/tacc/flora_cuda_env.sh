#!/bin/bash
# Source on Lonestar6. Avoid the inherited module function: its Lmod path can
# differ between login and compute nodes. Fail before loading model weights.
export CUDA_HOME=${FLORA_CUDA_HOME:-/opt/apps/cuda/12.8}
export CUDA_PATH="$CUDA_HOME"
flora_gcc_root=${FLORA_GCC_ROOT:-/scratch/tacc/apps/gcc/13.2.0}
for flora_tool in "$CUDA_HOME/bin/nvcc" "$flora_gcc_root/bin/gcc" "$flora_gcc_root/bin/g++"; do
    if [[ ! -x "$flora_tool" ]]; then
        printf 'Required FLORA compiler is unavailable: %s\n' "$flora_tool" >&2
        return 1
    fi
done
if [[ ! -f "$CUDA_HOME/include/cuda_runtime.h" ]]; then
    printf 'CUDA headers are unavailable in %s\n' "$CUDA_HOME" >&2
    return 1
fi
export PATH="$flora_gcc_root/bin:$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$flora_gcc_root/lib64:$flora_gcc_root/lib:$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CC="$flora_gcc_root/bin/gcc"
export CXX="$flora_gcc_root/bin/g++"
export NVCC_CCBIN="$CXX"
unset flora_gcc_root flora_tool
