"""Compile the actual FlashInfer sampler before model loading; optionally run it."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compile-only', action='store_true', help='Build for H100 on a CPU node')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('CUDA preflight receipt must be new')
    if args.compile_only:
        os.environ['FLASHINFER_CUDA_ARCH_LIST'] = '9.0a'
    import torch
    from flashinfer.jit.cpp_ext import get_cuda_path
    from flashinfer.sampling import gen_sampling_module, top_k_top_p_sampling_from_logits

    cuda = Path(get_cuda_path())
    nvcc = cuda / 'bin/nvcc'
    assert nvcc.is_file() and shutil.which('ninja'), 'nvcc and ninja are required'
    version = subprocess.check_output([str(nvcc), '--version'], text=True)
    assert 'release 12.8,' in version, version
    # Compile the same JIT specification used by vLLM's startup sampler. CPU
    # nodes lack libcuda.so.1, so loading/execution belongs to the GPU check.
    spec = gen_sampling_module()
    spec.build(verbose=True)
    assert spec.get_library_path().is_file(), 'FlashInfer library was not built'
    sampled = False
    if not args.compile_only:
        assert torch.cuda.is_available(), 'GPU preflight requires CUDA'
        assert 'H100' in torch.cuda.get_device_name(0)
        logits = torch.full((2, 128), -100.0, device='cuda', dtype=torch.float32)
        logits[:, 17] = 100.0
        result = top_k_top_p_sampling_from_logits(logits, 1, 1.0)
        torch.cuda.synchronize()
        assert result.tolist() == [17, 17], result
        sampled = True
    receipt = dict(compilation_passed=True, gpu_sampling_passed=sampled,
                   compile_only=args.compile_only, cuda_home=str(cuda), nvcc_version=version,
                   cc=os.environ['CC'], cxx=os.environ['CXX'], python=sys.executable,
                   torch=torch.__version__, torch_cuda=torch.version.cuda,
                   sampling_library=str(spec.get_library_path()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    main()
