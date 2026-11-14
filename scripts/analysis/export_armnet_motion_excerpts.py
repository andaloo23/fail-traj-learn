"""Find active ten-second Armnet excerpts and export student-rate MP4s."""
from concurrent.futures import ThreadPoolExecutor
import html
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image,ImageDraw,ImageFont

REPO=Path(__file__).resolve().parents[2]
OUT=REPO/'outputs/teacher_sampling_visualization_v1/armnet_10s'


def activity(source,e):
    step=max(1,round(e['fps']/4));frames=list(range(0,e['n_frames'],step));scores=[];last=None
    panels=[p for p in e['images'][0]['panels'] if p['camera'] in ('front','top')]
    if not panels:raise ValueError('Expected fixed Armnet front/top cameras')
    for f in frames:
        with Image.open(source/e['images'][f]['path']) as image:
            views=[]
            for p in panels:
                crop=image.crop((p['x'],p['y'],p['x']+p['width'],p['y']+p['height']))
                views.append(np.asarray(crop.convert('L').resize((96,54)),dtype=np.float32))
            value=np.stack(views)
        if last is not None:
            diff=value-last;diff-=np.median(diff,axis=(1,2),keepdims=True)
            scores.append((f,float(np.abs(diff).mean())))
        last=value
    width=round(10*e['fps']);choices=[]
    for start in range(0,e['n_frames']-width+1,step):
        amount=sum(score for f,score in scores if start<f<start+width)
        choices.append((amount,start))
    amount,start=max(choices)
    return dict(episode=e['id'],source_run=str(source),task=e['task'],fps=e['fps'],n_frames=e['n_frames'],
        start_frame=start,end_frame=start+width,start_seconds=start/e['fps'],end_seconds=(start+width)/e['fps'],
        activity_score=amount,release_path=e['release_path'])


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pilot=REPO/'outputs/oopsie_rich_failure_v8_1_twelve_v1'
    bulk=REPO/'outputs/oopsie_rich_failure_v8_1_500_batch_v1'
    pm=json.loads((pilot/'manifest.json').read_text(encoding='utf-8'))
    bm=json.loads((bulk/'manifest.json').read_text(encoding='utf-8'))
    original=next(e for e in pm['episodes'] if e['id']=='O004')
    candidates=[e for e in bm['episodes'] if e['lab']=='Armnet' and e['release_path']!=original['release_path']]
    original_rank=activity(pilot,original)
    with ThreadPoolExecutor(max_workers=4) as pool:ranked=list(pool.map(lambda e:activity(bulk,e),candidates))
    ranked.sort(key=lambda r:r['activity_score'],reverse=True)
    selected=[original_rank]+ranked[:2]
    (OUT/'selection.json').write_text(json.dumps(dict(selection_method='Largest ten-second sum of grayscale pixel changes in fixed front/top cameras, sampled at 4 Hz; median brightness change removed. Image activity is a heuristic, not a physical speed measurement.',episodes=selected),indent=2)+'\n',encoding='utf-8')
    sheet=Image.new('RGB',(1100,3*220),'#0c111b');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
    for i,r in enumerate(selected):
        source=Path(r['source_run']);m=pm if source==pilot else bm;e=next(e for e in m['episodes'] if e['id']==r['episode'])
        draw.text((10,i*220+3),f"{r['episode']} | {r['start_seconds']:.2f}-{r['end_seconds']:.2f} seconds",font=font,fill='white')
        panel=next(p for p in e['images'][0]['panels'] if p['camera']=='front')
        for j in range(5):
            f=r['start_frame']+round((j+.5)*2*e['fps'])
            with Image.open(source/e['images'][f]['path']) as image:
                crop=image.crop((panel['x'],panel['y'],panel['x']+panel['width'],panel['y']+panel['height'])).resize((210,118))
            sheet.paste(crop,(10+j*218,i*220+36))
            draw.text((10+j*218,i*220+158),f'{f/e["fps"]:.2f}s',font=font,fill='#b4c2d7')
    sheet.save(OUT/'selected_motion.jpg',quality=90)
    for r in selected:
        name=f"{r['episode']}_active10s_student_1.33fps.mp4"
        subprocess.run([sys.executable,str(REPO/'scripts/analysis/export_student_sampling_video.py'),
            '--source',r['source_run'],'--episode',r['episode'],'--sample-fps','4/3',
            '--start-seconds',str(r['start_seconds']),'--duration-seconds','10','--out',str(OUT/name)],check=True)
        r['file']=name
    cards=''.join(f'<section><h2>{html.escape(r["episode"])} · source {r["start_seconds"]:.2f}–{r["end_seconds"]:.2f}s</h2><video controls preload="metadata" src="{r["file"]}"></video><p><a href="{r["file"]}" download>Download MP4</a></p></section>' for r in selected)
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Armnet · active 10-second clips</title><style>body{background:#0c111b;color:#e8eef8;font:16px/1.5 system-ui;max-width:1150px;margin:auto;padding:24px}section{margin:25px 0;padding:15px;border:1px solid #304058;border-radius:8px}h2{font-size:19px}video{width:100%;max-height:550px;background:#000}a{color:#bda6ff}p{color:#b4c2d7}</style><h1>Armnet · active 10-second clips</h1><p>Three real excerpts, including the original O004 episode. Each lasts 10 seconds at original speed, with approximately 1.33 observations per second. Selected using image changes in the fixed cameras; this does not measure physical robot velocity.</p>'''+cards+'</html>'
    (OUT/'index.html').write_text(page,encoding='utf-8')
    (OUT/'selection.json').write_text(json.dumps(dict(episodes=selected,all_clips_seconds=10,sample_fps=4/3,original_speed=True),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(complete=True,clips=len(selected),url='http://127.0.0.1:8801/armnet_10s/')),flush=True)


if __name__=='__main__':main()
