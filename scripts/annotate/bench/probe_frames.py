"""Dump per-frame oracle signals for a frame range: probe_frames.py <dataset> <episode> <f0> <f1>
Columns: frame chunk cmd aperture_cm eef_z target: gripper_contact left right grasped support resting z_cm | other slots touched"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import Episode, open_dataset  # noqa: E402

name, ep_i, f0, f1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
ep = Episode(open_dataset(name), name, ep_i)
slots = ep.meta["object_slots"]
tm = ep.col("priv.target_mask")[0]
t = int(np.flatnonzero(tm)[0])
gc = ep.col("priv.obj_gripper_contact")
lf = ep.col("priv.obj_left_finger_contact")
rf = ep.col("priv.obj_right_finger_contact")
gr = ep.col("priv.obj_grasped")
sup = ep.col("priv.obj_support_contact")
rest = ep.col("priv.obj_resting")
pos = ep.col("priv.obj_pos").reshape(ep.n, -1, 3)
eef = ep.eef_xyz
ap = ep.gripper_aperture
cmd = ep.gripper_cmd
print(f"{name} ep{ep_i} target={slots[t]} chunks={ep.n_chunks}")
gst = ep.col("priv.gripper_static_contacts").reshape(-1)
gfx = ep.col("priv.gripper_fixture_contacts").reshape(-1)
armc = ep.col("priv.arm_contacts").reshape(-1)
print("frame ch  cmd  ap_cm eef_z | tgt: gc L R grasp sup rest z_cm  dxy_cm | others touched | gstat gfix arm")
for i in range(max(0, f0), min(ep.n, f1 + 1)):
    others = [slots[s] for s in range(len(slots)) if s != t and gc[i, s] > 0]
    dxy = np.linalg.norm(eef[i, :2] - pos[i, t, :2]) * 100
    print(f"{i:5d} {ep.chunk_of_frame(i):2d} {cmd[i]:+4.0f} {ap[i]*100:5.2f} {eef[i,2]*100:5.1f} | "
          f"{int(gc[i,t])} {int(lf[i,t])} {int(rf[i,t])} {int(gr[i,t])}     {int(sup[i,t])}   {int(rest[i,t])}  {pos[i,t,2]*100:5.1f}  {dxy:5.1f} | {','.join(others):18s} | {int(gst[i])} {int(gfx[i])} {int(armc[i])}")
