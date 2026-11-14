"""Export the original O001-O010 review set at a shared 4/3 observations/s."""
from concurrent.futures import ThreadPoolExecutor
import html
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO=Path(__file__).resolve().parents[2]
SOURCE=REPO/'outputs/oopsie_rich_failure_v8_1_twelve_v1'
OUT=REPO/'outputs/teacher_sampling_visualization_v1/first10_1.33fps'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    by_id={e['id']:e for e in m['episodes']}
    episodes=[by_id[f'O{i:03d}'] for i in range(1,11)]
    def export(e):
        path=OUT/(e['id']+'_student_1.33fps.mp4')
        command=[sys.executable,str(REPO/'scripts/analysis/export_student_sampling_video.py'),
            '--source',str(SOURCE),'--episode',e['id'],'--sample-fps','4/3','--out',str(path)]
        result=subprocess.run(command,capture_output=True,text=True)
        if result.returncode:raise RuntimeError(e['id']+': '+result.stderr[-2500:])
        report=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
        print(json.dumps(dict(episode=e['id'],seconds=report['duration_seconds'],observations=len(report['student_source_frames']),verified=True)),flush=True)
        return dict(report,task=e['task'],filename=path.name)
    with ThreadPoolExecutor(max_workers=2) as pool:reports=list(pool.map(export,episodes))
    cards=[]
    for r in reports:
        title=html.escape(r['episode']+' · '+r['task'])
        cards.append(f'<section><h2>{title}</h2><p>{r["duration_seconds"]:.2f} seconds · native {r["native_fps"]:g} FPS · sampled at ~1.33 observations/sec</p><video controls preload="metadata" playsinline src="{r["filename"]}"></video><p><a href="{r["filename"]}" download>Download MP4</a></p></section>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O001–O010 · student sampling examples</title><style>body{background:#0c111b;color:#e8eef8;font:16px/1.5 system-ui,sans-serif;max-width:1350px;margin:auto;padding:24px}h1{margin-bottom:8px}h2{font-size:19px}p{color:#b4c2d7}a{color:#bda6ff}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}section{background:#151e2b;border:1px solid #304058;border-radius:8px;padding:16px}video{width:100%;max-height:540px;background:#000}header{margin-bottom:24px}@media(max-width:800px){main{grid-template-columns:1fr}}</style><header><h1>O001–O010 · student sampling examples</h1><p>Original twelve-episode review set, first ten episodes. Every clip plays at its original speed and duration. Images update at about 1.33 observations/sec; the final source frame is retained. This is a fixed-rate visualization on preserved real OopsieData, with no new model calls.</p><p><a href="O001-O010_student_1.33fps.zip" download>Download all 10 MP4s as a ZIP</a></p></header><main>'''+''.join(cards)+'</main></html>'
    (OUT/'index.html').write_text(page,encoding='utf-8')
    (OUT/'README.md').write_text('# Original O001–O010 student-rate examples\n\nAll ten episodes retain their original speed and full duration. The observation schedule is uniformly spaced at a target 4/3 observations per video second, rounded to available source timestamps, with the final frame retained. This is a derived visualization and changes no native teacher evidence, labels, prompts, requests, review notes, or training runs.\n\n| Episode | Task | Duration |\n|---|---|---|\n'+''.join(f"| {r['episode']} | {r['task']} | {r['duration_seconds']:.2f} s |\n" for r in reports),encoding='utf-8')
    with zipfile.ZipFile(OUT/'O001-O010_student_1.33fps.zip','x',compression=zipfile.ZIP_STORED) as bundle:
        for r in reports:bundle.write(OUT/r['filename'],r['filename'])
        bundle.write(OUT/'README.md','README.md')
    (OUT/'export_manifest.json').write_text(json.dumps(dict(source_run=str(SOURCE),target_observations_per_second=4/3,episodes=reports),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(complete=True,episodes=len(reports),total_seconds=sum(r['duration_seconds'] for r in reports),url='http://127.0.0.1:8801/first10_1.33fps/')),flush=True)


if __name__=='__main__':main()
