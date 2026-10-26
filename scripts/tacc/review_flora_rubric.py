"""Build a local multi-camera viewer for native FLORA rubric explanations."""
import argparse
import json
from pathlib import Path
import re
import shutil

from check_flora_results import check_rubric, rubric_samples_from_manifest
from review_flora import preview


def timed_cues(text, duration):
    """Quote explicit timestamps in Video Analysis; do not invent local scores.

    A point statement remains visible up to the next timestamp for that camera.
    Those display intervals are derived and are not native dense predictions.
    """
    cues, inside, camera = [], False, 'Video analysis'
    timestamp = re.compile(r'(?<![\d:])(\d{1,2}):([0-5]\d)(?!\d|:\d)')
    for line_number, line in enumerate(text.splitlines(), 1):
        if '**Video Analysis:**' in line:
            inside = True
            continue
        if not inside:
            continue
        if re.match(r'^\s*\*\*(Evaluation|Synthesis|Scoring|Conclusion):\*\*', line):
            break
        header = re.search(r'\*\*Video\s+\d+\s*\(([^)]+)\):\*\*', line)
        if header:
            camera = header.group(1)
        matches = list(timestamp.finditer(line))
        if not matches:
            continue
        start = int(matches[0][1])*60 + int(matches[0][2])
        if not 0 <= start < duration:
            continue
        end, kind = None, 'point_until_next_timestamp'
        if len(matches) > 1 and re.fullmatch(r'\s*(?:-|–|—|to)\s*', line[matches[0].end():matches[1].start()]):
            end = min(duration, int(matches[1][1])*60+int(matches[1][2]))
            kind = 'explicit_range'
            if end <= start:
                continue
        quote = re.sub(r'^\s*[*+-]\s+', '', line).strip()
        cues.append(dict(start_s=start, end_s=end, camera=camera, text=quote,
                         source_line=line_number, timing_kind=kind))
    for cue in cues:
        if cue['end_s'] is None:
            following = [c['start_s'] for c in cues if c['camera'] == cue['camera'] and c['start_s'] > cue['start_s']]
            cue['end_s'] = min(following, default=duration)
    return sorted(cues, key=lambda c: (c['start_s'], c['source_line']))


PAGE = r'''<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FLORA · OopsieData review</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#10151c;color:#e4eaf2;font:15px/1.55 system-ui,sans-serif}
main{max-width:1440px;margin:24px auto;padding:0 24px}header{display:flex;justify-content:space-between;gap:16px;align-items:center}
h1{font-size:26px;margin:0}h2{font-size:23px;margin:14px 0 5px}h3{margin:0 0 12px;font-size:18px}
.muted{color:#aab6c8}.tag{border:1px solid #8c7444;color:#f8ce7d;border-radius:20px;padding:5px 12px;font-size:13px}
select,button{font:inherit;color:inherit;background:#243247;border:1px solid #53647a;border-radius:7px;padding:7px 11px}
button{cursor:pointer}button:hover{background:#31445e}select{max-width:100%}a{color:#9cc7ff}
.choose{margin-top:18px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}.layout{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:20px;margin-top:18px;align-items:start}
.card{background:#192330;border:1px solid #344458;border-radius:12px;padding:18px;margin-bottom:16px}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.camera{min-width:0}.camera p{margin:0 0 6px;text-transform:capitalize;color:#b9c8da;font-size:13px}
video{display:block;width:100%;height:205px;background:#080c11;border-radius:6px;object-fit:contain}.controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:14px}
#scrub{width:100%;accent-color:#91baff;margin:14px 0 5px}#clock{font-variant-numeric:tabular-nums}.scoreline{display:flex;gap:18px;align-items:center}.score{font-size:35px;font-weight:650;color:#b8d5ff;white-space:nowrap}
#grade{margin:4px 0}.note{font-size:13px;margin:10px 0 0}.explanation{position:sticky;top:20px}.explanation .heading{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
#reasoning{max-height:calc(100vh - 260px);min-height:340px;overflow:auto;padding-right:14px;overflow-wrap:anywhere;scrollbar-color:#53647a #192330}
#reasoning p{margin:0 0 14px}#reasoning h3,#reasoning h4,#reasoning h5{margin:18px 0 10px}#reasoning ul,#reasoning ol{padding-left:24px;margin:0 0 16px}#reasoning li{margin:5px 0}
#reasoning code{font-size:13px;background:#10151c;padding:2px 4px;border-radius:3px}details{margin-top:12px}summary{cursor:pointer;color:#bfd2ed}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,monospace}
.grading{padding-left:22px}.grading li{margin:8px 0}.grading .selected{color:#bad7ff;font-weight:600}.footer{font-size:13px;margin:18px 0 30px}
.segmentbar{display:flex;position:relative;height:28px;margin-top:14px;border-radius:4px;overflow:hidden;background:#2c394a}.segmentbar button{padding:0;border:0;border-radius:0;min-width:0;opacity:.75}.segmentbar button.active{opacity:1;box-shadow:inset 0 0 0 2px #fff}.playhead{position:absolute;top:0;bottom:0;width:2px;background:#fff;pointer-events:none}
.segment-controls{display:flex;gap:8px;margin:12px 0;flex-wrap:wrap}.segment-title{font-size:21px;margin:0 0 6px}.cue{padding:12px;margin:10px 0;border-left:3px solid #8bbaff;background:#121d2a;border-radius:4px}.cue p{margin:6px 0 0}.cue small{color:#b4c4d9}.cue button{font-size:12px;padding:3px 7px;float:right}.live-body{max-height:calc(100vh - 330px);overflow:auto;padding-right:10px}.live-body:focus{outline:1px solid #8bbaff}.legend{font-size:12px;display:flex;gap:14px;flex-wrap:wrap}.normal{color:#8ce0b3}.suboptimal{color:#f8ce7d}.failure{color:#ff8c96}.segmenttable{width:100%;border-collapse:collapse;font-size:13px}.segmenttable td{padding:8px;border-bottom:1px solid #344458}.segmenttable tr{cursor:pointer}.segmenttable tr.active{background:#31445e}#denseStatus{margin-top:10px;font-size:13px}
@media(max-width:900px){.layout{grid-template-columns:1fr}.explanation{position:static}#reasoning{max-height:none;min-height:0}video{height:220px}}
@media(max-width:550px){main{padding:0 12px;margin:16px auto}header{align-items:start}h1{font-size:22px}.tag{font-size:11px}.gallery{grid-template-columns:1fr}video{height:210px}.scoreline{align-items:start}}
</style>
<main><header><h1>FLORA · OopsieData</h1><span class="tag">Awaiting human review</span></header>
<p class="muted" id="configurationNote"></p>
<div class="choose"><label for="episode">Episode</label><select id="episode"></select><a href="rubric.jsonl" download>Download raw results</a></div>
<h2 id="task"></h2><div class="muted" id="context"></div>
<div class="layout"><section>
<div class="card"><div id="gallery" class="gallery"></div>
<div class="controls"><button id="restart">Restart</button><button id="back">Previous frame</button><button id="play">Play</button><button id="forward">Next frame</button>
<label>Speed <select id="speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label></div>
<input id="scrub" type="range" min="0" value="0" step="1" aria-label="Video frame"><div class="muted" id="clock"></div><p id="mediaError" role="status"></p></div>
<div class="card"><h3>Segments</h3><div class="muted" id="segmentMode"></div><div id="segmentTimeline" class="segmentbar" aria-label="Segment timeline"></div>
<div class="segment-controls"><button id="previousSegment">Previous segment</button><button id="nextSegment">Next segment</button></div>
<div id="segmentLegend" class="legend"></div><p class="muted" id="denseStatus"></p>
<details><summary>All segments</summary><table class="segmenttable"><tbody id="segmentRows"></tbody></table></details></div>
<div class="card"><div class="scoreline"><div class="score" id="score"></div><div><strong>Overall task score</strong><p id="grade"></p></div></div>
<p class="muted note">Overall rubric score for the full episode, separate from the changing segment display.</p>
<details><summary>Scoring rubric</summary><p id="criterion"></p><ol id="grading" class="grading"></ol></details></div>
<details class="card"><summary>Native output and source details</summary><pre id="raw"></pre><pre id="source"></pre></details>
</section><section class="card explanation"><div class="heading"><h3>Reasoning at the playhead</h3><span class="muted" id="segmentCount"></span></div>
<div class="live-body" tabindex="0"><h4 id="segmentLabel" class="segment-title"></h4><div id="segmentRange" class="muted"></div><p id="segmentRationale"></p>
<div id="timedReasoning"></div><p class="muted note" id="timingNote"></p></div>
<details id="fullExplanation"><summary>Complete episode explanation · <span id="words"></span></summary><div id="reasoning" tabindex="0"></div></details>
<details><summary>Exact explanation text</summary><pre id="exact"></pre></details></section></div>
<p class="muted footer">Real-world videos · FLORA-Rewarder · native segment rationales and a separate episode rubric explanation · predictions require human review</p></main>
<script>
const data=__DATA__, $=id=>document.getElementById(id);
let current,videos=[],frame=0,segments=[],segmentIndex=-1,activeCueKey='',nativeDense=new Map(),denseState=null,bars=[],segmentRows=[];
const colors={1:'#c95766',2:'#b98b3e',3:'#438b6b'},labels={1:'Failure',2:'Suboptimal',3:'Normal'};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function inline(s){return esc(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*([^*\n]+)\*/g,'<em>$1</em>')}
function markdown(text){
 let html='',paragraph=[],list=null;
 const flush=()=>{if(paragraph.length){html+='<p>'+paragraph.map(inline).join('<br>')+'</p>';paragraph=[]}};
 const close=()=>{if(list){html+='</'+list+'>';list=null}};
 for(const line of text.split('\n')){
  const heading=line.match(/^\s*(#{1,6})\s+(.+)$/),bullet=line.match(/^\s*[-*+]\s+(.+)$/),number=line.match(/^\s*\d+[.)]\s+(.+)$/);
  if(!line.trim()){flush();close();continue}
  if(heading){flush();close();const level=Math.min(5,heading[1].length+2);html+='<h'+level+'>'+inline(heading[2])+'</h'+level+'>';continue}
  if(bullet||number){flush();const type=bullet?'ul':'ol';if(list!==type){close();html+='<'+type+'>';list=type}html+='<li>'+inline((bullet||number)[1])+'</li>';continue}
  close();paragraph.push(line)
 }flush();close();return html
}
function pause(){videos.forEach(v=>v.pause());$('play').textContent='Play'}
function paint(t){if(!current)return;frame=Math.max(0,Math.min(current.frames-1,Math.floor(t*current.fps+1e-4)));$('scrub').value=frame;
 $('clock').textContent=`${(frame/current.fps).toFixed(2)} / ${(current.frames/current.fps).toFixed(2)} s · frame ${frame+1} / ${current.frames}`;paintSegment()}
function rebuildSegments(){
 const dense=nativeDense.get(current.id);bars=[];segmentRows=[];segmentIndex=-1;activeCueKey='';
 if(dense){segments=dense.segments;$('segmentMode').textContent='Native FLORA action-quality segments';$('segmentLegend').innerHTML='<span class="failure">1 Failure</span><span class="suboptimal">2 Suboptimal</span><span class="normal">3 Normal</span>'}
 else{const boundaries=[...new Set([0,current.frames,...current.timed_cues.flatMap(c=>[Math.round(c.start_s*current.fps),Math.round(c.end_s*current.fps)])])].sort((a,b)=>a-b);
  segments=boundaries.slice(0,-1).map((start,i)=>({start_frame:start,end_frame:boundaries[i+1],start_s:start/current.fps,end_s:boundaries[i+1]/current.fps}));
  $('segmentMode').textContent='Intervals aligned to timestamps in the existing explanation';$('segmentLegend').textContent='Timing alignment only · native segment scores pending'}
 $('segmentTimeline').replaceChildren();$('segmentRows').replaceChildren();
 for(const [i,s] of segments.entries()){
  const button=document.createElement('button');button.style.flex=String(s.end_frame-s.start_frame);button.style.background=s.score?colors[s.score]:'#5378a8';button.title=`${s.start_s.toFixed(2)}–${s.end_s.toFixed(2)} s · ${s.score?labels[s.score]:'Timestamp-aligned interval'}`;button.setAttribute('aria-label',button.title);button.onclick=()=>seekFrame(s.start_frame);$('segmentTimeline').append(button);bars.push(button);
  const tr=document.createElement('tr');for(const text of [String(i+1),`${s.start_s.toFixed(2)}–${s.end_s.toFixed(2)} s`,s.score?labels[s.score]:'Timed excerpt',s.rationale||'']){const td=document.createElement('td');td.textContent=text;tr.append(td)}tr.onclick=()=>seekFrame(s.start_frame);$('segmentRows').append(tr);segmentRows.push(tr)
 }
 const head=document.createElement('div');head.id='segmentHead';head.className='playhead';$('segmentTimeline').append(head);updateDenseStatus();paintSegment()
}
function paintSegment(){
 if(!segments.length)return;const index=segments.findIndex(s=>s.start_frame<=frame&&frame<s.end_frame),s=segments[index];
 $('segmentHead').style.left=`${100*frame/current.frames}%`;
 if(index!==segmentIndex){segmentIndex=index;bars.forEach((b,i)=>b.classList.toggle('active',i===index));segmentRows.forEach((r,i)=>r.classList.toggle('active',i===index));
  $('segmentCount').textContent=`${index+1} / ${segments.length}`;$('segmentLabel').textContent=s.score?`${s.score} / 3 · ${labels[s.score]}`:'Timestamp-aligned explanation';$('segmentLabel').className='segment-title '+(s.label||'');
  $('segmentRange').textContent=`${s.start_s.toFixed(2)}–${s.end_s.toFixed(2)} s · frames [${s.start_frame}, ${s.end_frame})`;
  $('segmentRationale').textContent=s.score?(s.rationale||(s.score===3?'FLORA supplies no dense rationale for normal spans.':'No native rationale was supplied for this span.')):'Native action-quality scores will appear here when the dense run finishes.'}
 const time=frame/current.fps,cues=current.timed_cues.filter(c=>c.start_s<=time&&time<c.end_s),key=current.id+':'+cues.map(c=>c.source_line).join(',');
 if(key!==activeCueKey){activeCueKey=key;$('timedReasoning').replaceChildren();
  if(!cues.length){const p=document.createElement('p');p.className='muted';p.textContent=current.reference_batch_defaults?'The complete rubric explanation is episode-level and is available below. No segment timing is inferred from it.':'No explicit timestamped passage was supplied for this interval. The complete explanation is below.';$('timedReasoning').append(p)}
  for(const cue of cues){const card=document.createElement('div');card.className='cue';const meta=document.createElement('small');meta.textContent=cue.camera+' · quoted from the episode explanation';const jump=document.createElement('button');jump.textContent='Seek '+cue.start_s.toFixed(0)+'s';jump.onclick=()=>seekFrame(cue.start_s*current.fps);const quote=document.createElement('p');quote.textContent=cue.text;card.append(jump,meta,quote);$('timedReasoning').append(card)}
  document.querySelector('.live-body').scrollTop=0}
 $('timingNote').textContent=current.reference_batch_defaults?'Segment text above is the native dense rationale. The separate rubric explanation is not assigned segment timestamps.':'Quoted passages follow FLORA’s written timestamps. Point statements remain visible until the next timestamp for that camera. These are approximate text alignments, not independently inferred segment judgments.'
}
function updateDenseStatus(){if(!current)return;if(nativeDense.has(current.id)){$('denseStatus').textContent=`Native dense results loaded · job ${denseState?.job_id||''}. Labels are retrospective; brief switches can reflect overlap stitching.`;return}
 const state=denseState?.state||'PENDING';$('denseStatus').textContent=`Native dense pass ${state.toLowerCase()}${denseState?.job_id?' · job '+denseState.job_id:''}. This page checks automatically for results.`}
async function refreshDense(){try{const response=await fetch('dense_status.json?t='+Date.now(),{cache:'no-store'});if(!response.ok)return;const status=await response.json();denseState=status;
 if(status.available&&nativeDense.size===0){const payload=await fetch('dense.json?t='+Date.now(),{cache:'no-store'});if(!payload.ok)return;const rows=await payload.json();
  for(const row of rows){const source=data.find(x=>x.id===row.id);if(!source||row.task!==source.task||row.num_frames!==source.frames||Math.abs(row.fps-source.fps)>.001)throw new Error('Segment source mismatch');nativeDense.set(row.id,row)}
  if(current)rebuildSegments()}
 updateDenseStatus()}catch(e){$('denseStatus').textContent='Could not load segment update: '+e.message}}
function align(){if(!videos.length)return;const t=videos[0].currentTime;for(const v of videos.slice(1)){if(v.readyState&&Math.abs(v.currentTime-t)>.08)v.currentTime=t}}
function seekFrame(f){pause();const bounded=Math.max(0,Math.min(current.frames-1,Math.round(f))),t=(bounded+.5)/current.fps;for(const v of videos)v.currentTime=t;paint(t)}
function toggle(){const master=videos[0];if(!master.paused){pause();return}if(master.ended)seekFrame(0);master.play().catch(e=>$('mediaError').textContent=e.message)}
function show(){
 pause();current=data.find(x=>x.id===$('episode').value);videos=[];frame=0;$('gallery').replaceChildren();$('mediaError').textContent='';
 $('task').textContent=current.task;$('context').textContent=`${current.id} · ${current.lab} · ${(current.frames/current.fps).toFixed(2)} seconds · ${current.videos.length} camera views`;
 $('score').textContent=current.output.total.toFixed(2)+' / 1';const selected=current.output.samples[current.output.medoid_sample];
 $('configurationNote').textContent=current.configuration_note;
 $('grade').textContent=current.output.scores.map((s,i)=>`Step ${i+1}: ${s.toFixed(2)}`).join(' · ');
 $('criterion').textContent='Task rubric';$('grading').replaceChildren();
 for(const [i,criterion] of current.rubric.entries()){const li=document.createElement('li');
  const grade=criterion.grading.find(g=>Math.abs(g.points-current.output.scores[i])<1e-8);
  li.textContent=`${criterion.action} — ${current.output.scores[i].toFixed(2)}: ${grade?.label||'Unrecognized score'}`;$('grading').append(li)}
 $('exact').textContent=selected.thinking;$('reasoning').innerHTML=markdown(selected.thinking);$('reasoning').scrollTop=0;
 $('words').textContent=selected.thinking.trim().split(/\s+/).length.toLocaleString()+' words';
 $('raw').textContent=JSON.stringify(current.output,null,2);$('source').textContent=JSON.stringify(current.source,null,2);
 for(const [i,path] of current.videos.entries()){
  const card=document.createElement('div');card.className='camera';const label=document.createElement('p');label.textContent=current.cameras[i].replace(/^camera labeled /,'').replaceAll('_',' ');
  const v=document.createElement('video');v.muted=true;v.preload='auto';v.playsInline=true;v.src=path;v.playbackRate=Number($('speed').value);v.setAttribute('aria-label',label.textContent+' camera');
  v.onloadedmetadata=()=>{if(v===videos[0])paint(v.currentTime)};v.onerror=()=>{$('mediaError').textContent='Could not load '+label.textContent+' video.'};
  card.append(label,v);$('gallery').append(card);videos.push(v)
 }
 const master=videos[0];master.onplay=()=>{if(master!==videos[0])return;for(const v of videos.slice(1)){v.currentTime=master.currentTime;v.playbackRate=master.playbackRate;v.play().catch(()=>{})}$('play').textContent='Pause'};
 master.onpause=()=>{if(master!==videos[0])return;for(const v of videos.slice(1))v.pause();$('play').textContent='Play'};
 master.onseeking=()=>{if(master===videos[0]){align();paint(master.currentTime)}};master.onseeked=()=>{if(master===videos[0])paint(master.currentTime)};
 master.ontimeupdate=()=>{if(master===videos[0]){align();paint(master.currentTime)}};master.onended=()=>{if(master===videos[0])pause()};
 if(master.requestVideoFrameCallback){const tick=(_,m)=>{if(master!==videos[0])return;paint(m.mediaTime);master.requestVideoFrameCallback(tick)};master.requestVideoFrameCallback(tick)}
 $('scrub').max=current.frames-1;rebuildSegments();paint(0)
}
for(const row of data){const option=document.createElement('option');option.value=row.id;option.textContent=`${row.id} · ${row.task} · ${row.output.total.toFixed(2)}/1`;$('episode').append(option)}
$('episode').onchange=show;$('play').onclick=toggle;$('back').onclick=()=>seekFrame(frame-1);$('forward').onclick=()=>seekFrame(frame+1);$('restart').onclick=()=>seekFrame(0);
$('scrub').oninput=()=>seekFrame(Number($('scrub').value));$('speed').onchange=()=>videos.forEach(v=>v.playbackRate=Number($('speed').value));
$('previousSegment').onclick=()=>seekFrame(segments[Math.max(0,segmentIndex-1)].start_frame);$('nextSegment').onclick=()=>seekFrame(segments[Math.min(segments.length-1,segmentIndex+1)].start_frame);
document.onkeydown=e=>{if(['INPUT','SELECT','TEXTAREA','BUTTON','A'].includes(e.target.tagName)||e.target.closest('.explanation')||e.ctrlKey||e.metaKey||e.altKey)return;
 if(e.code==='Space'){e.preventDefault();toggle()}if(e.key==='ArrowLeft'){e.preventDefault();seekFrame(frame-1)}if(e.key==='ArrowRight'){e.preventDefault();seekFrame(frame+1)}};
show();refreshDense();setInterval(refreshDense,15000);
</script></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rubric', type=Path, required=True)
    parser.add_argument('--jobs', type=Path, required=True)
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--page-only', action='store_true')
    args = parser.parse_args()
    report = check_rubric(args.rubric, args.jobs, expected_samples=rubric_samples_from_manifest(args.rubric))
    if not report['structurally_valid']:
        raise ValueError(report['issues'])
    jobs = {r['id']: r for r in map(json.loads, args.jobs.read_text(encoding='utf-8').splitlines())}
    provenance = json.loads(args.provenance.read_text(encoding='utf-8'))
    episodes = {r['id']: r for r in provenance['episodes']}
    run = json.loads((args.rubric.parent/'run.json').read_text(encoding='utf-8'))
    reference = run.get('reference_batch_defaults') is True
    if not args.page_only:
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out/'videos').mkdir()
    data = []
    for row in map(json.loads, args.rubric.read_text(encoding='utf-8').splitlines()):
        job, source = jobs[row['id']], episodes[row['id']]
        by_hash = {c['sha256']: c for c in source['cameras'] if 'excluded_duplicate_of' not in c}
        from run_flora import digest
        included = [by_hash[digest((args.jobs.parent/name).resolve())] for name in job['videos']]
        assert len(included) == len(job['videos'])
        videos = []
        for index, relative in enumerate(job['videos']):
            target = f'videos/{row["id"]}_camera_{index}.mp4'
            if args.page_only:
                if not (args.out/target).is_file():
                    raise ValueError(f'Missing preview: {target}')
            else:
                print(f'Preparing {row["id"]} camera {index+1}', flush=True)
                preview((args.jobs.parent/relative).resolve(), args.out/target)
            videos.append(target)
        explanation = row['samples'][row['medoid_sample']]['thinking']
        cues = [] if reference else timed_cues(explanation, included[0]['frames']/included[0]['fps'])
        data.append(dict(id=row['id'], task=job['task'], rubric=job['rubric'],
                         cameras=job['cameras'], videos=videos,
                         timed_cues=cues,
                         reference_batch_defaults=reference,
                         configuration_note=(
                             'Reviewed camera mapping. Dense segment rationales and the separate rubric explanation are distinct model outputs.'
                             if source.get('reviewed_camera_mapping') else
                             'Historical pilot: dense camera ordering was not reviewed against NVIDIA instructions; rubric used reduced inference settings. These results are superseded for evaluating reference performance.'),
                         fps=included[0]['fps'], frames=included[0]['frames'],
                         lab=source['release_path'].split('/')[1], output=row,
                         source=dict(repo=provenance['repo'], revision=provenance['revision'],
                                     episode_path=source['release_path'], robot=job['robot'])))
    embedded = json.dumps(data, ensure_ascii=True).replace('<', r'\u003c')
    (args.out/'index.html').write_text(PAGE.replace('__DATA__', embedded), encoding='utf-8')
    shutil.copyfile(args.rubric, args.out/'rubric.jsonl')
    (args.out/'validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (args.out/'timed_alignment.json').write_text(json.dumps(
        dict(origin=('No derived timestamp alignment for reference evaluation; full rubric reasoning is episode-level' if reference else
                     'Display alignment of explicit timestamps in native explanation; not native dense output'),
             episodes={r['id']: r['timed_cues'] for r in data}), indent=2)+'\n', encoding='utf-8')
    if not (args.out/'dense_status.json').exists():
        (args.out/'dense_status.json').write_text(json.dumps(dict(state='PENDING', available=False))+'\n', encoding='utf-8')
    print(args.out/'index.html', flush=True)


if __name__ == '__main__':
    main()
