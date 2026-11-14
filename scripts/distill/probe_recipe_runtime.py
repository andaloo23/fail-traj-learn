"""Read-only runtime inventory; never loads weights or changes packages."""
import importlib.metadata
import json
import platform

versions={}
for name in ['torch','torchvision','transformers','peft','accelerate','bitsandbytes','Pillow','av','h5py']:
    try:versions[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:versions[name]=None
print(json.dumps(dict(platform=platform.platform(),versions=versions)),flush=True)
try:
    import torch
    print(json.dumps(dict(cuda=torch.cuda.is_available(),torch_cuda=torch.version.cuda,
        flash_compiled=torch.backends.cuda.is_flash_attention_available(),
        gpu=torch.cuda.get_device_name() if torch.cuda.is_available() else None)),flush=True)
except ImportError:pass
