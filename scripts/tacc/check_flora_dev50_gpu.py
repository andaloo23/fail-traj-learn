"""Run the actual sampler on every selected GPU before loading FLORA's weights."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert not a.out.exists()
    import torch
    from flashinfer.jit.cpp_ext import get_cuda_path
    from flashinfer.sampling import top_k_top_p_sampling_from_logits
    cuda = Path(get_cuda_path())
    nvcc = subprocess.check_output([str(cuda / 'bin/nvcc'), '--version'], text=True)
    assert 'release 12.8,' in nvcc, nvcc
    ninja = shutil.which('ninja')
    assert ninja, f'ninja executable absent from PATH: {os.environ.get("PATH")}'
    ninja_version = subprocess.check_output([ninja, '--version'], text=True).strip()
    assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    devices = []
    for index in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(index)
        assert 'H100' in props.name or 'A100' in props.name
        assert props.total_memory >= 39 * 1024**3
        with torch.cuda.device(index):
            logits = torch.full((2, 128), -100., device=f'cuda:{index}', dtype=torch.float32)
            logits[:, 17] = 100.
            sample = top_k_top_p_sampling_from_logits(logits, 1, 1.)
            torch.cuda.synchronize()
            assert sample.tolist() == [17, 17], sample
        devices.append(dict(index=index, name=props.name, memory=props.total_memory))
    if 'H100' in devices[0]['name']:
        assert len(devices) == 1 and devices[0]['memory'] >= 79 * 1024**3
    else:
        assert len(devices) == 2
    a.out.write_text(json.dumps(dict(passed=True, devices=devices, nvcc=nvcc,
                                   ninja=ninja, ninja_version=ninja_version,
                                   python=sys.executable, torch=torch.__version__,
                                   cc=os.environ['CC'], cxx=os.environ['CXX']), indent=2) + '\n')
    print('Actual FlashInfer GPU sampling passed on all selected GPUs', flush=True)


if __name__ == '__main__':
    main()
