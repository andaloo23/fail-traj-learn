"""Visualize frozen teacher evidence timing on real OopsieData, without model calls.

This is a separate timing explainer, not a label reviewer or a training export.
The fork's fifth-frame rule is applied illustratively to the same real episode.
"""
import argparse
from collections import Counter
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import unquote,urlsplit

REPO=Path(__file__).resolve().parents[2]
SOURCE=REPO/'outputs/oopsie_rich_failure_v8_1_500_batch_v1'
OUT=REPO/'outputs/teacher_sampling_visualization_v1'
FORK_COMMIT='b9c08be774c749036a20205b1d842a0ee38b3bf3'


def build(source=SOURCE,out=OUT):
    m=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    if m['config']['evidence']!='all_recorded_frames_all_nonduplicate_native_cameras':
        raise ValueError('Expected all-recorded-frame teacher evidence')
    episodes=[]
    for e in m['episodes']:
        frames=[x['frame'] for x in e['images']]
        if frames!=list(range(e['n_frames'])):raise ValueError('Native teacher frame sequence is not complete: '+e['id'])
        expected=[f"images/{e['id']}/{f:06d}.webp" for f in frames]
        if [x['path'] for x in e['images']]!=expected:raise ValueError('Unexpected evidence paths')
        episodes.append({k:e[k] for k in ('id','task','lab','split','fps','n_frames','cameras')})
    counts=Counter(e['fps'] for e in episodes)
    value=dict(episodes=episodes,default_episode='O0006',
        native_rates=[dict(fps=f,episodes=n) for f,n in sorted(counts.items())],
        manifest_sha256=hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest(),
        source_run=str(source.relative_to(REPO).as_posix()),
        fork_commit=FORK_COMMIT,fork_teacher_stride=5,fork_student_teacher_stride=3,
        comparison_is_illustrative=True,new_teacher_calls=0)
    out.mkdir(parents=True,exist_ok=True)
    (out/'data.json').write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    template=Path(__file__).with_name('teacher_sampling_visualization.html')
    (out/'index.html').write_bytes(template.read_bytes())
    (out/'README.md').write_text('''# Teacher sampling visualization

Open http://127.0.0.1:8801/ while the local server is running.

Every episode in the frozen real OopsieData collection is selectable. The first
column shows exact preserved teacher image strips at their source timestamps.
The other columns apply the linked fork's every-fifth-frame teacher rule and
its default every-third-teacher-frame student rule to the same episode, for a
visual comparison. They are not claims about requests made on these episodes.
All schedules retain the final source frame, including short endpoint gaps.

FPS measures observations per second of source video, not API requests per
second, generation speed, or playback speed. Camera panels at one timestamp
are simultaneous observations, not additional time samples. Playback uses one
shared source-time clock; a sparse column holds its last supplied image.

The current collection retains every recorded source frame. Native rates vary
across its 500 episodes: 5, 7.5, 10, 12, 15, 20, 30 and 50 FPS. A native 5-FPS
recording cannot supply observations between its 200-ms timestamps.

Sources (fork pinned at b9c08be774c749036a20205b1d842a0ee38b3bf3):

- [Teacher selection](https://github.com/MohammadAlMasalmeh/fail-traj-learn/blob/b9c08be774c749036a20205b1d842a0ee38b3bf3/scripts/annotate/annotate_trajectories.py): range(0, n, 5), plus final frame.
- [Student image stride](https://github.com/MohammadAlMasalmeh/fail-traj-learn/blob/b9c08be774c749036a20205b1d842a0ee38b3bf3/scripts/distill/data.py): InputCfg.stride defaults to 3, applied to the teacher frame sequence, keeping first/last.
- [Fork viewer](https://github.com/MohammadAlMasalmeh/fail-traj-learn/blob/b9c08be774c749036a20205b1d842a0ee38b3bf3/scripts/annotate/review_trajectory_annotations.html): source-frame clock; sampled mode holds the most recent supplied image.
- Local source: outputs/oopsie_rich_failure_v8_1_500_batch_v1/manifest.json, validated against every episode's complete image index.

No labels, prompts, frozen evidence, model requests or queued training jobs are
changed by this visualization.

To rebuild and serve:

```powershell
python scripts/analysis/visualize_teacher_sampling.py --serve --port 8801
```
''',encoding='utf-8')
    print(json.dumps(dict(out=str(out),episodes=len(episodes),native_rates=value['native_rates'],teacher_frames=sum(e['n_frames'] for e in episodes))),flush=True)


class Handler(SimpleHTTPRequestHandler):
    source=SOURCE

    def translate_path(self,path):
        clean=unquote(urlsplit(path).path)
        if clean.startswith('/evidence/'):
            relative=clean.removeprefix('/evidence/')
            target=(self.source/relative).resolve()
            images=(self.source/'images').resolve()
            if target.is_relative_to(images) and target.suffix=='.webp':return str(target)
            return str(Path(self.directory)/'not-found')
        return super().translate_path(path)

    def end_headers(self):
        if not urlsplit(self.path).path.startswith('/evidence/'):
            self.send_header('Cache-Control','no-store')
        super().end_headers()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=SOURCE)
    p.add_argument('--out',type=Path,default=OUT);p.add_argument('--serve',action='store_true');p.add_argument('--port',type=int,default=8801)
    a=p.parse_args();build(a.source,a.out)
    if a.serve:
        Handler.source=a.source.resolve()
        server=ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(a.out.resolve())))
        print(f'Teacher sampling: http://127.0.0.1:{a.port}/',flush=True)
        server.serve_forever()
