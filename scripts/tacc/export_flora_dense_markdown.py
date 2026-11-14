"""Readable derived tables from preserved native FLORA dense results."""
import argparse
import json
from pathlib import Path


def cell(value):return str(value).replace('|','\\|').replace('\n',' ')


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    path=a.root/'flora_oopsie_ten_reference_dense_3533752/dense.jsonl'
    rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
    lines=['# FLORA dense annotations: ten real OopsieData episodes','',
        'Derived readable conversion of preserved native FLORA output. Not a new model generation. Structural validation passed; human verification and training readiness remain false. Source-frame ends are exclusive. Native labels are failure, suboptimal and normal; no binary relabeling has been applied.','']
    for row in rows:
        lines+=['## '+row['id']+' · '+row['task'],'',f"Source: {row['num_frames']} frames at {row['fps']} FPS; {row['duration_s']:.3f} seconds.",'',
            '| Start (s) | End (s) | Source frames | Native label | Model rationale |','|---:|---:|---|---|---|']
        for s in row['segments']:
            lines.append(f"| {s['start_s']:.3f} | {s['end_s']:.3f} | [{s['start_frame']}, {s['end_frame']}) | {cell(s['label'])} ({s['score']}) | {cell(s.get('rationale',''))} |")
        lines+=['']
    (a.root/'dense_annotations_derived.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(dict(episodes=len(rows),segments=sum(len(r['segments']) for r in rows),native_outputs_modified=False)),flush=True)


if __name__=='__main__':main()
