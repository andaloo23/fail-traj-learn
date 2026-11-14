"""Publish a readable local status page without making model or API requests."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

import oopsie_common as common
import annotation_runtime as transport
from oopsie_bulk_v8_1 import CONFIG


def read_optional(path):
    try:return common.read(path)
    except (FileNotFoundError,json.JSONDecodeError):return None


def status(root, review_url='http://127.0.0.1:8800/review.html'):
    prepared=[read_optional(p) for p in (root/'prepared').glob('*.json')]
    prepared=[x for x in prepared if x]
    preflight=[read_optional(p) for p in (root/'preflight').glob('*.json')]
    preflight=[x for x in preflight if x]
    q=read_optional(root/'queue_status.json') or {}
    summary=read_optional(root/'collection_summary.json') or {}
    failure=read_optional(root/'pipeline_failure.json') or read_optional(root/'queue_failure.json')
    frozen=(root/'manifest.json').exists()
    if failure:stage='Stopped; preserved diagnostics require review'
    elif q:stage='Batch collection complete' if not q.get('active_requests') and not q.get('queued_locally') else 'Sol Batch collection running'
    elif (root/'batch_manifest.json').exists():stage='Batch requests frozen; queue starting'
    elif frozen:stage='500 episodes frozen; finishing token preflight'
    else:stage='Downloading and preparing whole-episode evidence'
    value=dict(stage=stage,updated_utc=datetime.now(timezone.utc).isoformat(),
        prepared_candidate_episodes=sum(x['status']=='prepared' for x in prepared),
        technical_exclusions=sum(x['status']!='prepared' for x in prepared),
        token_preflights_complete=len(preflight),planned_episodes=500,
        validated_annotations=summary.get('validated',0),
        active_batch_requests=q.get('active_requests',0),queued_locally=q.get('queued_locally',500),
        completed_batch_requests=q.get('completed_batch_requests',0),
        generation_estimate_usd=summary.get('generation_estimate_usd',0),selection_frozen=frozen,
        failure=failure)
    pf=read_optional(root/'token_preflight.json')
    lines=['# 500-episode Sol V8.1 run status','',f"**{stage}.**",'',
        '- Scope: 500 real OopsieData episodes, one Sol V8.1 annotation per episode; no Astra calls.',
        '- Planned split: 400 training / 50 development / 50 final test; contributing labs kept separate.',
        '- Every source frame and distinct native camera view is retained. The V8.1 prompt is unchanged.',
        '- Authorized maximum generation budget: $75. Submission requires the full preflight ceiling to fit.',
        f"- Candidate episodes prepared: {value['prepared_candidate_episodes']}; technical exclusions: {value['technical_exclusions']}.",
        '- Candidates with incompatible native video/state clocks or frame counts are replaced in frozen, label-blind reserve order.',
        f"- Token preflights complete: {len(preflight)}.",
        f"- Episodes in active remote batches: {value['active_batch_requests']}.",
        f"- Episodes awaiting local preparation/submission: {value['queued_locally']}.",
        f"- Episodes returned from completed batches: {value['completed_batch_requests']}.",
        f"- Validated native Markdown annotations: {value['validated_annotations']}/500.",
        f"- Estimated consumed generation cost: ${value['generation_estimate_usd']:.6f}.",
        f"- Last update: {value['updated_utc']}.",'']
    if pf:lines.append(f"Full-run cost ceiling, including maximum output allowance and cache writes: ${pf['run_total_ceiling_usd']:.6f}.\n")
    if failure:lines.extend(['## Stopped diagnostics','',failure.get('message','See preserved diagnostic records.'),''])
    if (root/'review.html').exists():lines.extend([f'[Video and time-aligned labels]({review_url}) · [Annotation report](report.md)',''])
    lines.extend(['Preparation, token preflight, queuing and result collection run automatically. Completed or uncertain generation requests are never automatically resent. No student training is launched by this run.',''])
    p=root/'status.md.tmp';p.write_text('\n'.join(lines),encoding='utf-8');p.replace(root/'status.md')
    transport.atomic_json(root/'pipeline_status.json',value)
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path)
    parser.add_argument('--url',default='http://127.0.0.1:8800/review.html')
    args=parser.parse_args()
    cfg=common.read(CONFIG);root=args.run.resolve() if args.run else common.ROOT/cfg['out']
    while True:
        result=status(root,args.url)
        if result['failure']:break
        summary=read_optional(root/'collection_summary.json') or {}
        if result['completed_batch_requests']==500 and result['active_batch_requests']==0 and summary.get('validated',0)+len(summary.get('invalid',[]))==500:
            # Run the required real-data browser regression on the ordinary URL.
            # It covers every episode and all available labels, never posting notes.
            if summary.get('validated'):
                check=subprocess.run([str(common.ROOT/'.venv-review/Scripts/python.exe'),
                    str(common.ROOT/'scripts/distill/check_binary_review_browser.py'),
                    '--url',args.url,
                    '--browser','C:/Program Files/Google/Chrome/Application/chrome.exe',
                    '--out',str(root/'browser_checks')],cwd=common.ROOT,
                    stdout=(root/'browser.stdout.log').open('w'),stderr=(root/'browser.stderr.log').open('w'),
                    creationflags=subprocess.CREATE_NO_WINDOW)
                transport.atomic_json(root/'browser_status.json',dict(returncode=check.returncode,
                    all_available_episodes_and_repeats_checked=check.returncode==0))
            break
        time.sleep(15)
