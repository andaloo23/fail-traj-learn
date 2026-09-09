"""Montage of the object gallery: montage.py <glob> <out.png> [cols]  (paths relative to outputs/annot_preview)"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WIN_OUT  # noqa: E402

base = WIN_OUT / "annot_preview"
files = sorted(base.glob(sys.argv[1]))
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
ims = [Image.open(f).convert("RGB").resize((768, 384)) for f in files]
rows = (len(ims) + cols - 1) // cols
m = Image.new("RGB", (cols * 768, rows * 384), (0, 0, 0))
for k, im in enumerate(ims):
    m.paste(im, ((k % cols) * 768, (k // cols) * 384))
m.save(base / sys.argv[2])
print(len(files), "->", base / sys.argv[2])
for f in files:
    print(" ", f.name)
