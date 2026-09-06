"""Build outputs/review/index.html: one local gallery page over every rendered episode (mp4 + contact sheet),
grouped by dataset, with the task language, outcome, length, target and shift info from the sidecar.
Open the file in a browser on Windows; videos play inline (h264). No server needed.

Usage: build_review_index.py [dataset_prefix ...]   (default: every full_* dataset with a review folder)
"""
import html
import json
import os
import re
import sys
from pathlib import Path

PROJ = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn"))
WIN_OUT = Path(os.environ.get("FTL_WIN_OUT", "/mnt/c/Users/LocalPC/dev/fail-traj-learn/outputs")) / "review"
NAME_RE = re.compile(r"ep(\d{4})_(ok|FAIL)_(.+)_(\d+)\.(mp4|png)$")

prefixes = sys.argv[1:] or ["full_"]
groups = []
for d in sorted(p for p in WIN_OUT.iterdir() if p.is_dir() and any(p.name.startswith(x) for x in prefixes)):
    eps = {}
    for f in sorted(d.iterdir()):
        m = NAME_RE.match(f.name)
        if not m:
            continue
        ep = int(m.group(1))
        eps.setdefault(ep, {})[m.group(5)] = f.name
    if not eps:
        continue
    cards = []
    for ep, files in sorted(eps.items()):
        meta = {}
        sc = PROJ / "data" / d.name / "sidecar" / f"episode_{ep:06d}.json"
        if sc.exists():
            meta = json.load(open(sc))
        shift = meta.get("shift_applied") or {}
        target = ", ".join(meta.get("target_objects") or [])
        goal = "; ".join(" ".join(map(str, g)) for g in (meta.get("goal_state") or []))
        shift_txt = ""
        if isinstance(shift, dict) and shift:
            parts = []
            for k, v in shift.items():
                if isinstance(v, dict) and "dxy" in v:
                    dx, dy = (list(v["dxy"]) + [0, 0])[:2]
                    parts.append(f"{k}: {100*dx:+.0f}/{100*dy:+.0f} cm, {57.2958*float(v.get('yaw_rad', 0)):+.0f} deg" + (" (yaw locked)" if v.get("yaw_locked") else ""))
                elif isinstance(v, dict):
                    parts.append(f"{k}: {json.dumps(v)}")
            shift_txt = "; ".join(parts)
        summ = {}
        if "json" in files:
            try:
                summ = json.load(open(d / files["json"]))
            except Exception:
                summ = {}
        badge = ""
        if summ.get("wrong_object") and not summ.get("target_grasped"):
            badge = " <span class='badge red'>WRONG OBJECT: " + html.escape(", ".join(summ["wrong_object"])) + "</span>"
        elif summ and not summ.get("target_grasped"):
            badge = " <span class='badge grey'>never grasped target</span>"
        elif summ.get("target_grasped"):
            badge = " <span class='badge green'>target grasped " + str(summ.get("grasp_frames", "")) + " frames</span>"
        if summ.get("arm_contact_frames"):
            badge += " <span class='badge red'>arm collision " + str(summ["arm_contact_frames"]) + " frames</span>"
        title = (f"ep {ep} | {'SUCCESS' if meta.get('success') else 'FAIL'} | len {meta.get('length', meta.get('n_frames', '?'))} | "
                 f"{meta.get('suite', '')}[{meta.get('task_id', '')}] {html.escape(str(meta.get('task_language', '')))}")
        touched_txt = (" &middot; touched: " + html.escape(", ".join(summ.get("touched") or []) or "none") + " &middot; moved: " + html.escape(", ".join(summ.get("moved") or []) or "none")) if summ else ""
        body = f"<div class='meta'>target: <b>{html.escape(str(target))}</b> &middot; goal: {html.escape(goal)}{touched_txt}" + (f" &middot; shift: {html.escape(shift_txt)}" if shift_txt else "") + \
               (f" &middot; notes: {html.escape(str(meta.get('notes', '')))}" if meta.get("notes") else "") + "</div>"
        vid = f"<video controls preload='metadata' loop src='{d.name}/{files['mp4']}'></video>" if "mp4" in files else "<i>no video</i>"
        img = f"<a href='{d.name}/{files['png']}' target='_blank'><img src='{d.name}/{files['png']}'></a>" if "png" in files else ""
        cards.append(f"<div class='card' id='{d.name}-{ep}'><h3>{title}{badge}</h3>{body}<div class='row'>{vid}</div>{img}</div>")
    groups.append((d.name, cards))

nav = " &middot; ".join(f"<a href='#{n}'>{n} ({len(c)})</a>" for n, c in groups)
sections = "".join(f"<section id='{n}'><h2>{n} <small>{len(c)} episodes</small></h2>{''.join(c)}</section>" for n, c in groups)
page = f"""<!doctype html><html><head><meta charset='utf-8'><title>Failure review</title>
<style>
body{{font-family:system-ui,sans-serif;background:#151515;color:#ddd;margin:0;padding:16px}}
a{{color:#8cf}} h2{{margin-top:32px;border-bottom:1px solid #333}} small{{color:#888;font-weight:normal}}
.card{{background:#202020;border-radius:8px;padding:12px;margin:12px 0}} .card h3{{margin:0 0 6px 0;font-size:15px}}
.meta{{color:#aaa;font-size:13px;margin-bottom:8px}}
video{{width:768px;max-width:100%;background:#000}} img{{display:block;max-width:100%;margin-top:8px}}
.nav{{position:sticky;top:0;background:#151515;padding:8px 0;border-bottom:1px solid #333;font-size:13px}}
.badge{{font-size:11px;padding:1px 6px;border-radius:9px;margin-left:6px;vertical-align:middle}} .red{{background:#7a2020}} .grey{{background:#444}} .green{{background:#1f5a2a}}
</style></head><body>
<div class='nav'>{nav} &nbsp; <span style='color:#888'>frame tags on the sheet: g=grasp s=support c=gripper-contact ARM=arm collision GST=gripper-static collision; strip: target_z red, eef_z blue, grasp green, support grey, gripper yellow, collision magenta. Videos are agentview | wrist at the recorded fps; use , and . to step frames while a video is focused.</span></div>
{sections}
<script>
document.querySelectorAll('video').forEach(v=>{{v.playbackRate=1.0}});
document.addEventListener('keydown',e=>{{const v=document.activeElement.closest?document.activeElement.closest('.card')?.querySelector('video'):null;if(!v)return;
if(e.key==='.'){{v.pause();v.currentTime+=0.1}}if(e.key===','){{v.pause();v.currentTime-=0.1}}}});
</script></body></html>"""
(WIN_OUT / "index.html").write_text(page, encoding="utf-8")
print(f"index: {sum(len(c) for _, c in groups)} episodes in {len(groups)} datasets -> {WIN_OUT / 'index.html'}")
