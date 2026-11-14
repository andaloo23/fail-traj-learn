"""Build a local video review of native dense FLORA predictions; never edits labels.

Requires PyAV/numpy only for browser-compatible video previews. Run in the WSL
LeRobot environment after downloading the dense output. Serve the output with
python -m http.server --directory OUTPUT_DIRECTORY.
"""
import argparse
import json
from pathlib import Path

from check_flora_results import check


PAGE = r'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FLORA · LIBERO review</title>
<style>
body{font:16px system-ui;background:#10151c;color:#e4eaf2;margin:32px auto;max-width:1150px;padding:0 20px}
h1{font-size:28px}select,button{font:inherit;background:#263346;color:inherit;border:1px solid #617089;border-radius:6px;padding:8px}
.videos{display:flex;gap:16px;flex-wrap:wrap}video{width:min(45vw,480px);background:#05080b}
.muted{color:#aab6c8}table{width:100%;border-collapse:collapse;margin:20px 0}td,th{text-align:left;padding:10px;border-bottom:1px solid #344054}
tr{cursor:pointer}.failure{color:#ff8c96}.suboptimal{color:#f8ce7d}.normal{color:#8ce0b3}
.active{background:#263346}#timeline{display:flex;width:100%;height:30px;margin-top:18px}
#timeline{position:relative}#timeline button{border:0;border-radius:0;padding:0;min-width:0;overflow:hidden;color:#fff;font-size:11px}
#head{position:absolute;top:0;bottom:0;width:3px;background:white;box-shadow:0 0 4px #000;pointer-events:none}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:12px 0}.player,.current{background:#192533;border:1px solid #34485e;border-radius:10px;padding:16px}
.videos{justify-content:center}.videos video{width:min(40vw,330px)}.videos p{margin:0 0 6px}.current{border-left:5px solid #8ce0b3;margin-top:16px}
.current h3{margin:0 0 8px;font-size:23px;text-transform:capitalize}.current p{margin:8px 0;line-height:1.5}#scrub{width:100%;margin:4px 0}
.axis{display:flex;justify-content:space-between;color:#aab6c8;font-size:12px}#clock{font-variant-numeric:tabular-nums}button{cursor:pointer}
details{margin:18px 0}pre{white-space:pre-wrap}@media(max-width:650px){body{padding:0 12px;margin:16px auto}.player{padding:10px}.videos{gap:8px}.videos video{width:40vw}}
@media(min-width:651px) and (max-height:850px){body{margin:16px auto}h1{margin:0 0 8px}h2{font-size:20px;margin:12px 0}.videos video{width:200px}.bar{margin:8px 0}.current{margin-top:12px;padding:12px}.current p{margin:6px 0}}
</style><h1>FLORA · LIBERO review</h1>
<p class="muted">Model predictions awaiting human review. 1 = failure · 2 = suboptimal · 3 = normal.
Click a span to seek both cameras. Times are retrospective; segment end frames are exclusive.</p>
<label>Episode <select id="episode"></select></label>
<h2 id="task"></h2><p id="status" class="muted"></p>
<section class="player">
<div class="videos"><div><p>Agent camera</p><video id="agent" controls preload="metadata"></video></div>
<div><p>Wrist camera</p><video id="wrist" muted preload="metadata"></video></div></div>
<div class="bar"><button id="back">Previous frame</button><button id="play">Play</button><button id="forward">Next frame</button>
<label>Speed <select id="speed"><option value="0.25">0.25x</option><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option></select></label><span id="clock"></span></div>
<input id="scrub" type="range" min="0" value="0" step="1" aria-label="Source frame">
</section>
<div class="bar"><button id="prevSegment">Previous segment</button><button id="nextSegment">Next segment</button>
<span class="normal">Normal</span><span class="suboptimal">Suboptimal</span><span class="failure">Failure</span></div>
<div id="timeline" aria-label="FLORA segment timeline"></div><div class="axis"><span>0 s</span><span id="duration"></span></div>
<section id="current" class="current"><h3 id="liveLabel"></h3><p id="liveRange" class="muted"></p><p id="liveRationale"></p></section>
<details><summary>Show all segments</summary><table><thead><tr><th>Seconds</th><th>Frames</th><th>Label</th><th>Model rationale</th></tr></thead><tbody id="spans"></tbody></table></details>
<details><summary>Raw clip answers and validity</summary><pre id="raw"></pre></details>
<script>
const data=__DATA__, colors={1:'#d45c6a',2:'#c59542',3:'#4a9f7b'};
const $=id=>document.getElementById(id), select=$('episode'), agent=$('agent'), wrist=$('wrist');
let current, frame=0, segmentIndex=-1, bars=[], rows=[];
for(const row of data){const o=document.createElement('option');o.value=row.id;o.textContent=row.id;select.append(o)}
function pause(){agent.pause();wrist.pause();$('play').textContent='Play'}
function paint(t){
 if(!current)return;
 frame=Math.max(0,Math.min(current.num_frames-1,Math.floor(t*current.fps+1e-4)));
 $('scrub').value=frame;$('clock').textContent=`Frame ${frame} / ${current.num_frames-1} | ${(frame/current.fps).toFixed(2)} s`;
 $('head').style.left=`${100*frame/current.num_frames}%`;
 const index=current.segments.findIndex(s=>s.start_frame<=frame&&frame<s.end_frame);
 if(index!==segmentIndex){segmentIndex=index;
  rows.forEach((row,i)=>row.classList.toggle('active',i===index));
  bars.forEach((bar,i)=>bar.setAttribute('aria-current',String(i===index)));
  const s=current.segments[index];
  $('liveLabel').textContent=s?`${s.score} | ${s.label}`:'No segment at this frame';
  $('liveLabel').className=s?s.label:'';$('current').style.borderLeftColor=s?colors[s.score]:'#aab6c8';
  $('liveRange').textContent=s?`Segment ${index+1} / ${current.segments.length} | frames [${s.start_frame}, ${s.end_frame}) | ${s.start_s.toFixed(2)}-${s.end_s.toFixed(2)} s`:'';
  $('liveRationale').textContent=s?(s.rationale||'No rationale provided for this segment.'):'';
 }
}
// Seek inside the target frame; browsers can round its exact start backwards.
function seekFrame(f){pause();const bounded=Math.max(0,Math.min(current.num_frames-1,Math.round(f))),t=(bounded+.5)/current.fps;agent.currentTime=t;wrist.currentTime=t;paint(t)}
function toggle(){if(!agent.paused){pause();return}if(agent.ended)seekFrame(0);agent.play().catch(e=>$('status').textContent=e.message)}
function show(){current=data.find(x=>x.id===select.value);agent.pause();wrist.pause();
 $('task').textContent=current.task;agent.src=current.previews[0];wrist.src=current.previews[1];
 $('status').textContent=`${current.num_frames} frames · ${current.fps} FPS · invalid clips: ${current.invalid_clips} · human verified: no`;
 $('raw').textContent=JSON.stringify(current.clips,null,2);$('spans').replaceChildren();$('timeline').replaceChildren();
 frame=0;segmentIndex=-1;rows=[];bars=[];$('scrub').max=current.num_frames-1;$('duration').textContent=`${(current.num_frames/current.fps).toFixed(2)} s`;
 for(const [index,s] of current.segments.entries()){const tr=document.createElement('tr');tr.className=s.label;
  for(const value of [`${s.start_s.toFixed(2)}–${s.end_s.toFixed(2)}`,`${s.start_frame}–${s.end_frame}`,`${s.score} · ${s.label}`,s.rationale||'—']){
   const td=document.createElement('td');td.textContent=value;tr.append(td)}
  tr.onclick=()=>seekFrame(s.start_frame);$('spans').append(tr);rows.push(tr);
  const bar=document.createElement('button');bar.style.flex=String(s.end_frame-s.start_frame);bar.style.background=colors[s.score];
  bar.title=`Segment ${index+1}: ${s.label}, frames [${s.start_frame}, ${s.end_frame})`;bar.setAttribute('aria-label',bar.title);
  bar.textContent=index+1;bar.onclick=()=>seekFrame(s.start_frame);$('timeline').append(bar);bars.push(bar)}
 const head=document.createElement('div');head.id='head';$('timeline').append(head);agent.playbackRate=Number($('speed').value);wrist.playbackRate=agent.playbackRate;paint(0);
}
select.onchange=show;$('play').onclick=toggle;
$('back').onclick=()=>seekFrame(frame-1);$('forward').onclick=()=>seekFrame(frame+1);$('scrub').oninput=()=>seekFrame(Number($('scrub').value));
$('prevSegment').onclick=()=>seekFrame(current.segments[Math.max(0,segmentIndex-1)].start_frame);
$('nextSegment').onclick=()=>seekFrame(current.segments[Math.min(current.segments.length-1,segmentIndex+1)].start_frame);
$('speed').onchange=()=>{agent.playbackRate=Number($('speed').value);wrist.playbackRate=agent.playbackRate};
agent.onseeking=()=>{wrist.currentTime=agent.currentTime;paint(agent.currentTime)};
agent.onseeked=()=>paint(agent.currentTime);
agent.onplay=()=>{wrist.currentTime=agent.currentTime;wrist.playbackRate=agent.playbackRate;wrist.play().catch(()=>{});$('play').textContent='Pause'};
agent.onpause=()=>{wrist.pause();$('play').textContent='Play'};agent.onended=pause;
agent.ontimeupdate=()=>{if(Math.abs(wrist.currentTime-agent.currentTime)>.1)wrist.currentTime=agent.currentTime;paint(agent.currentTime)};
if(agent.requestVideoFrameCallback){const tick=(_,metadata)=>{paint(metadata.mediaTime);agent.requestVideoFrameCallback(tick)};agent.requestVideoFrameCallback(tick)}
document.onkeydown=e=>{if(['INPUT','SELECT','TEXTAREA','BUTTON'].includes(e.target.tagName))return;
 if(e.code==='Space'){e.preventDefault();toggle()}if(e.key==='ArrowLeft'){e.preventDefault();seekFrame(frame-1)}if(e.key==='ArrowRight'){e.preventDefault();seekFrame(frame+1)}};
show();</script></html>'''


def preview(source, target):
    import av
    with av.open(str(source)) as src, av.open(str(target), 'w') as dst:
        input_stream = src.streams.video[0]
        output = dst.add_stream('libx264', rate=input_stream.average_rate)
        output.width, output.height = input_stream.width, input_stream.height
        output.pix_fmt = 'yuv420p'
        output.options = {'crf': '18', 'preset': 'fast'}
        for frame in src.decode(input_stream):
            image = av.VideoFrame.from_ndarray(frame.to_ndarray(format='rgb24'), format='rgb24')
            for packet in output.encode(image):
                dst.mux(packet)
        for packet in output.encode():
            dst.mux(packet)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dense', type=Path, required=True)
    p.add_argument('--jobs', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--page-only', action='store_true', help='Update an existing review page using its saved previews')
    a = p.parse_args()
    report = check(a.dense, a.jobs)
    rows = [json.loads(s) for s in a.dense.read_text(encoding='utf-8').splitlines() if s.strip()]
    jobs = {r['id']: r for r in (json.loads(s) for s in a.jobs.read_text(encoding='utf-8').splitlines() if s.strip())}
    if not report['structurally_valid']:
        raise ValueError(report['issues'])
    if a.page_only:
        if not a.out.is_dir():
            raise ValueError('--page-only requires an existing review directory')
    else:
        a.out.mkdir(parents=True, exist_ok=False)
        (a.out/'videos').mkdir()
    for index, row in enumerate(rows):
        row['previews'] = []
        for cam, rel in enumerate(jobs[row['id']]['videos']):
            name = f'videos/episode_{index:03d}_camera_{cam}.mp4'
            if a.page_only:
                if not (a.out/name).is_file():
                    raise ValueError(f'Missing preview: {name}')
            else:
                preview((a.jobs.parent/rel).resolve(), a.out/name)
            row['previews'].append(name)
    content = json.dumps(rows, ensure_ascii=True).replace('<', r'\u003c')
    (a.out/'index.html').write_text(PAGE.replace('__DATA__', content), encoding='utf-8')
    (a.out/'validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(a.out/'index.html')


if __name__ == '__main__':
    main()
