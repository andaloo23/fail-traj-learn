"""Build the pinned causal-conv1d source for the pilot's L40S architecture."""
import hashlib
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from urllib.request import urlopen

URL = (
    "https://files.pythonhosted.org/packages/f4/d1/"
    "eba27735f31bd5527d39a3c7f693e6ded7b844cab275db719a15ad37b6cd/causal_conv1d-1.7.0.tar.gz"
)
SHA256 = "3202758494eaa7b597ce1c282dfa188889506bfcb92cad3c407d26736bfcd32b"

with urlopen(URL, timeout=30) as response:
    source = response.read()
if hashlib.sha256(source).hexdigest() != SHA256:
    raise ValueError("Unexpected causal-conv1d source archive")

with TemporaryDirectory() as temporary:
    with tarfile.open(fileobj=BytesIO(source)) as archive:
        archive.extractall(temporary, filter="data")
    package = Path(temporary) / "causal_conv1d-1.7.0"
    setup = package / "setup.py"
    text = setup.read_text()
    start = text.index('        cc_flag.append("-gencode")')
    stop = text.index("    # HACK:", start)
    setup.write_text(text[:start] + '        cc_flag = ["-gencode", "arch=compute_89,code=sm_89"]\n\n'
                     + text[stop:])
    subprocess.run([sys.executable, "-m", "pip", "install", "--verbose", "--no-build-isolation",
                    "--no-deps", str(package)], check=True,
                   env=dict(os.environ, CC="/usr/bin/gcc", CXX="/usr/bin/g++",
                            CAUSAL_CONV1D_FORCE_BUILD="TRUE"))
