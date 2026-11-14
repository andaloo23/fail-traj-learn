"""Build an offline, time-aligned development-only student prediction review."""
import json
import os
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/distill'))
import oopsie_recipe_data as data
import score_recipe_suite as scoring

OUT = REPO / 'outputs/oopsie_distillation_completed_audit_20261103_v1'


def main():
    study = json.loads((REPO / 'outputs/oopsie_distillation_full_v1/study.json').read_text())
    source = REPO / study['config']['source_run']
    manifest = json.loads((source / 'manifest.json').read_text())
    dev_ids = set(study['development_ids'])
    models = {'Local base': REPO / 'outputs/oopsie_distillation_local_sequential_v1/predictions/base',
              'Local binary': REPO / 'outputs/oopsie_distillation_local_sequential_v1/predictions/binary',
              'Local joint': REPO / 'outputs/oopsie_distillation_local_sequential_v1/predictions/joint',
              'TACC base': OUT / 'tacc_snapshot/predictions/base'}
    episodes = []
    for e in manifest['episodes']:
        if e['id'] not in dev_ids:
            continue
        native = (source / 'traces' / (e['id'] + '_sol_r01') / 'annotation.md').read_text(encoding='utf-8')
        ref = data.parse_prediction(native.split('## Failure annotations')[0], e['id'], 0, e['n_frames'])
        tracks = {'Sol reference': ref}
        for name, folder in models.items():
            for normalized in (False, True):
                values = [None] * e['n_frames']
                for path in sorted(folder.glob(e['id'] + '_*_binary.json')):
                    r = json.loads(path.read_text(encoding='utf-8'))
                    text = r['text'].strip()
                    if normalized:
                        m = re.fullmatch(r'```(?:markdown|md)?\s*\n([\s\S]*?)\n```', text, flags=re.I)
                        if m:
                            text = m[1]
                    try:
                        if r['hit_max']:
                            raise ValueError('Token cap')
                        for s in data.parse_prediction(text, e['id'], r['core_start'], r['core_end']):
                            values[s['start_frame']:s['end_frame']] = [int(s['failure'])] * (s['end_frame']-s['start_frame'])
                    except ValueError:
                        pass
                tracks[name + (' unwrapped' if normalized else '')] = scoring.segments(values)
        episodes.append(dict(id=e['id'], fps=e['fps'], frames=e['n_frames'], task=e['task'], lab=e['lab'],
            cameras=', '.join(c['camera'] for c in e['cameras']),
            images=[os.path.relpath(source / i['path'], OUT).replace('\\', '/') for i in e['images']],
            tracks=tracks, teacher=native))
    payload = json.dumps(episodes).replace('<', '\\u003c')
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Distillation development review</title>
<style>
body{font:16px system-ui;margin:24px auto;max-width:1250px;padding:0 18px;color:#18222e;background:#f5f7fa}
h1{font-size:25px}button,select{font:inherit;padding:7px;margin:3px}#controls{position:sticky;top:0;background:#f5f7fa;padding:8px 0;z-index:2}
#frameImage{display:block;max-width:100%;max-height:62vh;margin:auto;background:#111}#scrub{width:100%}
.track{display:grid;grid-template-columns:180px 120px 1fr;align-items:center;gap:10px;margin:7px 0}.bar{height:22px;position:relative;background:#b6beca;cursor:pointer}
.segment{position:absolute;top:0;height:100%}.cursor{position:absolute;top:0;height:100%;width:2px;background:#111;z-index:1}.current{font-weight:650}
pre{white-space:pre-wrap;background:white;padding:16px;line-height:1.5}.yes{color:#b52026}.no{color:#17683f}.unknown{color:#5b6270}
textarea{width:100%;height:85px;font:inherit}small{color:#536273}
</style><h1>Distillation development review</h1>
<p>50 development episodes. Sol labels are the imitation reference. Red = failure, green = non-failure, gray = invalid output.
The unwrapped diagnostic removes enclosing code fences only. Original predictions and review notes remain unchanged.</p>
<div id="controls"><button id="prevEpisode">Previous episode</button><select id="episode"></select><button id="nextEpisode">Next episode</button>
<br><button id="back">Previous frame</button><button id="play">Play</button><button id="forward">Next frame</button>
<select id="speed"><option value="1">1×</option><option value="4">4×</option><option value="10">10×</option></select>
<label><input type="checkbox" id="unwrap">Remove outer code fences</label> <span id="position"></span>
<input id="scrub" type="range" min="0" value="0"></div>
<p id="task"></p><small id="cameras"></small><img id="frameImage" alt="All native camera panels at the selected source frame">
<div id="tracks"></div><details><summary>Preserved Sol annotation and explanation</summary><pre id="teacher"></pre></details>
<p>Review the full episode and the student’s 32-frame scored core with up to eight surrounding frames.
For persistent stalling, distinguish visible failure in this local view from a conclusion requiring the whole episode.</p>
<label for="notes">Human review notes (saved only when downloaded)</label><textarea id="notes" placeholder="Describe the visible evidence, source frame range, and whether the teacher or student needs correction."></textarea>
<button id="download">Download Markdown review note</button>
<script>const episodes=PAYLOAD;
const $=id=>document.getElementById(id);const notesByEpisode=new Map();let current=0,frame=0,playing=false,anchor=0,anchorFrame=0;
const modelNames=['Sol reference','Local base','Local binary','Local joint','TACC base'];
for(const [i,e] of episodes.entries()){const o=new Option(e.id+' · '+e.lab,i);$('episode').add(o)}
function stop(){playing=false;$('play').textContent='Play'}
function selectedTrack(name){return episodes[current].tracks[name+(name!=='Sol reference'&&$('unwrap').checked?' unwrapped':'')]}
function valueAt(name){return selectedTrack(name).find(s=>s.start_frame<=frame&&frame<s.end_frame)}
function draw(){const e=episodes[current];$('scrub').value=frame;$('position').textContent=`Frame ${frame}/${e.frames-1} · ${(frame/e.fps).toFixed(2)} s · ${e.fps} FPS`;
$('frameImage').src=e.images[frame];for(const name of modelNames){const d=document.querySelector(`[data-model="${name}"]`),s=valueAt(name),label=s?(s.failure?'Failure':'Non-failure'):'Unknown';
d.querySelector('.current').textContent=label;d.querySelector('.current').className='current '+(s?(s.failure?'yes':'no'):'unknown');d.querySelector('.cursor').style.left=(100*frame/e.frames)+'%';}}
function buildTracks(){const e=episodes[current];$('tracks').replaceChildren();for(const name of modelNames){const d=document.createElement('div');d.className='track';d.dataset.model=name;
const title=document.createElement('span');title.textContent=name;const label=document.createElement('span');label.className='current';const bar=document.createElement('div');bar.className='bar';
for(const s of selectedTrack(name)){const b=document.createElement('span');b.className='segment';b.style.left=100*s.start_frame/e.frames+'%';b.style.width=100*(s.end_frame-s.start_frame)/e.frames+'%';b.style.background=s.failure?'#df777b':'#8bc9a5';bar.append(b)}
const cursor=document.createElement('span');cursor.className='cursor';bar.append(cursor);bar.onclick=ev=>{stop();frame=Math.min(e.frames-1,Math.max(0,Math.floor((ev.clientX-bar.getBoundingClientRect().left)/bar.clientWidth*e.frames)));draw()};d.append(title,label,bar);$('tracks').append(d)}draw()}
function choose(i){stop();notesByEpisode.set(episodes[current].id,$('notes').value);current=(i+episodes.length)%episodes.length;frame=0;$('episode').value=current;const e=episodes[current];$('notes').value=notesByEpisode.get(e.id)||'';$('scrub').max=e.frames-1;$('task').textContent=e.id+' — '+e.task;$('cameras').textContent='Camera panels: '+e.cameras;$('teacher').textContent=e.teacher;buildTracks()}
$('episode').onchange=()=>choose(Number($('episode').value));$('prevEpisode').onclick=()=>choose(current-1);$('nextEpisode').onclick=()=>choose(current+1);
$('scrub').oninput=()=>{stop();frame=Number($('scrub').value);draw()};$('back').onclick=()=>{stop();frame=Math.max(0,frame-1);draw()};$('forward').onclick=()=>{stop();frame=Math.min(episodes[current].frames-1,frame+1);draw()};$('unwrap').onchange=buildTracks;
function tick(time){if(!playing)return;frame=Math.min(episodes[current].frames-1,anchorFrame+Math.floor((time-anchor)/1000*episodes[current].fps*Number($('speed').value)));draw();if(frame>=episodes[current].frames-1)stop();else requestAnimationFrame(tick)}
$('play').onclick=()=>{if(playing){stop();return}if(frame===episodes[current].frames-1)frame=0;playing=true;anchor=performance.now();anchorFrame=frame;$('play').textContent='Pause';requestAnimationFrame(tick)};
$('speed').onchange=()=>{anchor=performance.now();anchorFrame=frame};
$('download').onclick=()=>{const e=episodes[current],text=`# Human development review\\n\\nEpisode: ${e.id}\\nFrame: ${frame} (${(frame/e.fps).toFixed(2)} seconds)\\nEvaluation: ${$('unwrap').checked?'Outer code fence removed':'Strict native outputs'}\\n\\n${$('notes').value}\\n`;
const url=URL.createObjectURL(new Blob([text],{type:'text/markdown'}));const a=document.createElement('a');a.href=url;a.download=e.id+'_development_review.md';a.click();URL.revokeObjectURL(url)};
choose(0);</script></html>'''
    (OUT / 'review.html').write_text(html.replace('PAYLOAD', payload), encoding='utf-8')
    print(f'Created development review for {len(episodes)} episodes: {OUT / "review.html"}')


if __name__ == '__main__':
    main()
