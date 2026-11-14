#!/bin/bash
# Add the supported CPU video reader without changing model or Torch versions.
set -euo pipefail
: "${SCRATCH:?}"
runtime=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export PIP_CACHE_DIR="$runtime/pip-cache"
py="$runtime/venv-rewarder/bin/python"
"$py" -m pip install --no-deps \
  'https://download.pytorch.org/whl/cpu/torchcodec-0.17.0%2Bcpu-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl#sha256=de8e58e5f30692ee7cf92b1b313d0ffdeaac95148525ef2a865067fca0255246'
"$py" - "$runtime" <<'PY'
from pathlib import Path
import importlib.metadata
import json
import re
import sys
root = Path(sys.argv[1])
assert importlib.metadata.version('av') == '19.0.2', 'Revalidate FFmpeg shared libraries if PyAV changes'
libs = root/'venv-rewarder/lib/python3.12/site-packages/av.libs'
aliases = root/'ffmpeg-pyav19'
aliases.mkdir(exist_ok=True)
linked = []
for path in libs.iterdir():
    match = re.match(r'^(lib(?:avcodec|avformat|avutil|avfilter|avdevice|swscale|swresample))-[^.]+\.so\.(\d+)', path.name)
    if not match:
        continue
    alias = aliases/(match.group(1)+'.so.'+match.group(2))
    if alias.is_symlink():
        assert alias.resolve() == path.resolve()
    else:
        alias.symlink_to(path)
    linked.append(dict(alias=str(alias), target=str(path)))
assert len(linked) == 7 and (aliases/'libavcodec.so.63').is_file()
(root/'rubric_decoder.json').write_text(json.dumps(dict(torchcodec='0.17.0+cpu',
    wheel_sha256='de8e58e5f30692ee7cf92b1b313d0ffdeaac95148525ef2a865067fca0255246',
    ffmpeg_libraries=linked), indent=2)+'\n')
print('TorchCodec decoder setup recorded; actual media preflight remains required.')
PY
