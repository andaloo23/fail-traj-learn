"""Build a fixed, separate r6 audit pack; never mutates corpus references or labels."""
import hashlib
import html
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle_reference import BENCH, REFERENCE_VERSION, _open_with_retry, build_reference
from common import Episode, WIN_OUT, dump_json
from review_oracle import decode_episode, ffmpeg_pipe
from oracle_labels import q_of

OUT = WIN_OUT / "oracle_audit_r6"
SAMPLE = [
    ("clean_success", "full_anchor__t0", 0),
    ("clean_success", "full_goals8__t1", 4),
    ("recovered_success", "full_shift16__t1", 18),
    ("recovered_success", "full_goals8__t9", 2),
    ("missed_grasp", "full_shift16__t1", 14),
    ("missed_grasp", "full_shift12__t3", 11),
    ("transport_drop", "full_goals8__t2", 2),
    ("transport_drop", "full_l90__t74", 7),
    ("timeout", "full_shift16__t2", 10),
    ("timeout", "full_l90__t74", 8),
    ("wrong_object", "full_l90__t47", 11),
    ("release_miss", "full_shift8__t6", 15),
]


def sheet(agent, wrist, frames, path):
    out = Image.new("RGB", (1152, 218 * ((len(frames) + 2) // 3)), "#eeeeee")
    draw = ImageDraw.Draw(out)
    for j, f in enumerate(frames):
        x, y = (j % 3) * 384, (j // 3) * 218
        pair = Image.fromarray(np.concatenate((agent[f], wrist[f]), axis=1)).resize((384, 192))
        out.paste(pair, (x, y + 24))
        draw.text((x + 5, y + 5), f"frame {f} / chunk {f // 10}", fill="black")
    out.save(path, quality=93)


def build_index():
    """Present authored findings beside frozen predictions, without changing either."""
    manifest = json.loads((OUT / "manifest.json").read_text())
    findings = json.loads((OUT / "findings.json").read_text())["episodes"]
    by_key = {(e["dataset"], e["episode_index"]): e for e in manifest["episodes"]}
    esc = html.escape
    parts = []
    for i, f in enumerate(findings):
        entry = by_key[(f["dataset"], f["episode_index"])]
        rel = f"{f['dataset']}/ep{f['episode_index']:04d}"
        ref = json.loads((OUT / rel / "reference.json").read_text())
        labels = ref["chunk_labels"]
        buttons = " ".join(f'<button onclick="seek({i},{ref["chunks"][c][0] / ref["fps"]})">c{c}</button>' for c in f["chunks"])
        links = " | ".join(f'<a href="{rel}/{esc(e)}">{esc(e)}</a>' for e in f["evidence"])
        rows = "".join(f'<tr><td><button onclick="seek({i},{ref["chunks"][c["chunk"]][0] / ref["fps"]})">{c["chunk"]}</button></td>'
                       f'<td>{esc(c["primary"])}</td><td>{esc(", ".join(c["allowed"]))}</td><td>{q_of(c["allowed"],c["rule"])}</td>'
                       f'<td>{esc(c["rule"])}</td></tr>' for c in labels)
        payload = json.dumps({"chunks": ref["chunks"], "labels": labels, "fps": ref["fps"]}).replace("<", "\\u003c")
        parts.append(f'''<article id="episode-{i}"><h2>{esc(f['dataset'])} / episode {f['episode_index']}</h2>
<p class="meta">{esc(entry['category'])} · {esc(entry['split'])} · frozen r6 · <strong>{esc(f['verdict'].replace('_',' '))}</strong></p>
<p>{esc(ref['task'])}</p><p class="finding">{esc(f['finding'])}</p>
<video id="v{i}" src="{rel}/raw.mp4" controls preload="metadata" ontimeupdate="show({i})"></video>
<p>Jump to reviewed chunks: {buttons or 'none flagged'} <button onclick="document.getElementById('v{i}').playbackRate=0.25">¼ speed</button>
<button onclick="document.getElementById('v{i}').playbackRate=1">Normal speed</button></p>
<details ontoggle="show({i})"><summary>Compare with r6 annotations</summary><p id="now{i}"></p>
<div class="scroll"><table><thead><tr><th>Chunk</th><th>Primary</th><th>Allowed</th><th>q</th><th>Rule</th></tr></thead><tbody>{rows}</tbody></table></div></details>
<p><a href="{rel}/overview.jpg">Unlabelled overview</a> | {links}</p>
<script type="application/json" id="data{i}">{payload}</script></article>''')
    content = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Frozen r6 annotation audit</title><style>
body{max-width:1050px;margin:40px auto;padding:0 22px;font:16px/1.55 system-ui;color:#17252b;background:#f5f6f5}
h1{font-size:34px;margin-bottom:8px}h2{font-size:21px}a{color:#005f78}article{background:white;border:1px solid #d7dfdf;border-radius:10px;padding:24px;margin:24px 0}
.meta{color:#526366;font-size:14px}.finding{border-left:4px solid #ad7947;padding-left:14px}video{width:100%;max-width:768px;background:#111}
button{padding:5px 10px;margin:3px;border:1px solid #b4c4c8;border-radius:4px;background:#f2f7f7;cursor:pointer}summary{cursor:pointer;font-weight:600}
.scroll{overflow:auto;max-height:380px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;padding:7px;border-bottom:1px solid #e2e7e8}
</style><h1>Frozen r6 annotation audit</h1>
<p><strong>4 clear disagreements · 4 semantic concerns · 4 with no issue found in inspected evidence.</strong></p>
<p>12 purposively selected episodes: 8 held-out failures and 4 supplemental successes. Assistant visual/telemetry review,
not human ground truth or a population accuracy estimate. Raw videos are unlabelled; expand the annotation table to compare.</p>
<p><a href="../../docs/oracle_r6_audit.md">Full report</a> · <a href="protocol.md">Protocol</a> ·
<a href="visual_first_pass.md">Visual first-pass notes</a> · <a href="manifest.json">Frozen manifest</a> · <a href="findings.json">Findings JSON</a></p>
''' + "\n".join(parts) + '''<script>
function seek(i,t){let v=document.getElementById('v'+i);v.currentTime=t;v.scrollIntoView({block:'center'});show(i)}
function show(i){const d=JSON.parse(document.getElementById('data'+i).textContent),v=document.getElementById('v'+i);
const f=Math.min(d.chunks.at(-1)[1]-1,Math.floor(v.currentTime*d.fps)),c=d.chunks.findIndex(b=>b[0]<=f&&f<b[1]);
if(c>=0){const l=d.labels[c];document.getElementById('now'+i).textContent='Frame '+f+' · chunk '+c+' · '+l.primary+' · allowed: '+l.allowed.join(', ')+' · '+l.rule}}
</script></html>'''
    (OUT / "index.html").write_text(content, encoding="utf-8")
    print("Audit review:", OUT / "index.html")


def main():
    assert REFERENCE_VERSION == "r6", "This pack is frozen to r6"
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name("oracle_reference.py").read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    snapshot = OUT / "oracle_reference_r6.py"
    if snapshot.exists():
        assert snapshot.read_bytes() == source, "r6 changed after audit started"
    else:
        snapshot.write_bytes(source)
    held = {(r["dataset"], r["episode_index"]) for r in json.loads((BENCH / "episodes.json").read_text())["episodes"]}
    dev = {(r["dataset"], r["episode_index"]) for r in json.loads((BENCH / "episodes_dev.json").read_text())["episodes"]}
    manifest = []
    for category, name, idx in SAMPLE:
        assert (name, idx) not in dev
        assert (name, idx) not in {("full_goals8__t6", 0), ("full_shift8__t1", 3)}
        if "success" not in category:
            assert (name, idx) in held
        manifest.append(dict(category=category, dataset=name, episode_index=idx,
                             split="heldout_failure" if (name, idx) in held else "supplemental_success"))
    dump_json(dict(version="r6", source_sha256=digest, selection="purposive strata using existing reference metadata; not random",
                   episodes=manifest), OUT / "manifest.json")
    ds_cache = {}
    for entry in manifest:
        name, idx = entry["dataset"], entry["episode_index"]
        folder = OUT / name / f"ep{idx:04d}"
        if (folder / "done.json").exists():
            print("SKIP", name, idx, flush=True)
            continue
        folder.mkdir(parents=True, exist_ok=True)
        ds = ds_cache.setdefault(name, None)
        if ds is None:
            ds = ds_cache[name] = _open_with_retry(name)
        ep = Episode(ds, name, idx)
        agent, wrist, _ = decode_episode(ds, ep)
        # The first-pass visual evidence uses uniform sampling, independent of r6 events/labels.
        frames = np.unique(np.linspace(0, ep.n - 1, 24).astype(int)).tolist()
        sheet(agent, wrist, frames, folder / "overview.jpg")
        np.savez_compressed(folder / "cameras.npz", agent=agent, wrist=wrist)
        proc = ffmpeg_pipe(folder / "raw.mp4", 512, 280, ep.fps)
        for i in range(ep.n):
            im = Image.new("RGB", (512, 280), "white")
            im.paste(Image.fromarray(np.concatenate((agent[i], wrist[i]), axis=1)), (0, 24))
            ImageDraw.Draw(im).text((5, 5), f"frame {i} / chunk {i // 10}", fill="black")
            proc.stdin.write(im.tobytes())
        proc.stdin.close()
        assert proc.wait() == 0
        ref = build_reference(ep)
        dump_json(ref, folder / "reference.json")
        np.savez_compressed(folder / "telemetry.npz", **ep._cols)
        dump_json(dict(task=ep.task, n_frames=ep.n, overview_frames=frames, **entry), folder / "done.json")
        print("READY", name, idx, ep.task, ep.n, flush=True)
    assert hashlib.sha256(Path(__file__).with_name("oracle_reference.py").read_bytes()).hexdigest() == digest


if __name__ == "__main__":
    if "--index-only" in sys.argv:
        build_index()
    else:
        main()
