"""Preserve explicit credit rejections so the unchanged Sol-only run can resume.

No API calls. Refuses response-bearing, in-flight, unknown or other failed attempts.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import compare_v8_v9 as runner
import oopsie_common as common


def prepare_resume(root):
    root=Path(root).resolve()
    if not root.is_relative_to(common.ROOT.resolve()):
        raise ValueError('Run must remain inside the workspace')
    if (root/'collection.lock').exists():
        raise ValueError('A collector lock exists; do not move active attempts')
    m=runner.verify(root)
    if m['protocol']!=runner.ENRICHED_PROTOCOL or m['config']['teachers']!={'sol':'gpt-6.1-sol'}:
        raise ValueError('Only the frozen Sol-only V8.1 run is supported')
    successful=[];rejections=[]
    for e in m['episodes']:
        for repeat in range(1,m['config']['repeats']+1):
            folder=root/'traces'/runner.binary.trace_name(e['id'],'sol',repeat)
            if not folder.exists():continue
            state=common.read(folder/'attempt.json')
            if state['status']=='validated':
                if runner.load_rich(root,m,e,repeat) is None:raise ValueError('Missing validated trace')
                successful.append(folder)
            else:
                if state['status']!='stopped' or 'HTTP 429 [credit_balance_exhausted]' not in state.get('error',''):
                    raise ValueError('Cannot resume an in-flight or unknown/other failed submission')
                if sorted(p.name for p in folder.iterdir())!=['attempt.json']:
                    raise ValueError('Credit rejection has response-bearing or unexpected files; inspect manually')
                rejections.append(folder)
    if not rejections:raise ValueError('No explicit credit rejections to archive')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    receipt=root/('resume_'+stamp+'.json')
    if receipt.exists():raise ValueError('Resume receipt already exists')
    paths=[root/p for p in ('manifest.json','prompt.md','config.json','token_preflight.json','matched_request_audit.json')]
    paths+=list((root/'requests').glob('*.json'))
    paths+=[p for f in successful for p in f.iterdir() if p.is_file()]
    preserved={p.relative_to(root).as_posix():common.sha(p) for p in paths}
    moves=[]
    for folder in rejections:
        destination=root/'stopped_attempts'/(folder.name+'_credit_rejection_'+stamp)
        if not folder.resolve().is_relative_to(root) or not destination.resolve().is_relative_to(root):
            raise ValueError('Archive path escapes the verified run directory')
        if destination.exists():raise ValueError('Archive destination already exists')
        moves.append(dict(source=folder.relative_to(root).as_posix(),destination=destination.relative_to(root).as_posix(),attempt_sha256=common.sha(folder/'attempt.json')))
    common.write(receipt,dict(status='planned',preserved_files=preserved,credit_rejections=moves,
                             completed_responses_reused=len(successful),remaining_responses=len(m['episodes'])*m['config']['repeats']-len(successful)))
    for move in moves:
        destination=common.inside(root,move['destination']);destination.parent.mkdir(exist_ok=True)
        common.inside(root,move['source']).rename(destination)
        if common.sha(destination/'attempt.json')!=move['attempt_sha256']:raise ValueError('Archived attempt changed')
    for name,digest in preserved.items():
        if common.sha(common.inside(root,name))!=digest:raise ValueError('Preserved artifact changed during resume')
    result=common.read(receipt);result['status']='archived_verified'
    runner.transport.atomic_json(receipt,result)
    (root/('resume_'+stamp+'.md')).write_text(
        '# Resume unchanged Sol-only V8.1 collection\n\n'
        f'{len(successful)} completed responses are preserved and will be reused. '
        f'{len(moves)} explicit HTTP credit rejections were archived with their exact attempt hashes. '
        'No model output, frozen prompt, input, request or preflight receipt was changed. '
        'This preparation made no API calls.\n',encoding='utf-8')
    return dict(receipt=str(receipt),completed_responses_reused=len(successful),archived_credit_rejections=len(moves),
                remaining_responses=result['remaining_responses'],api_calls=0)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    print(json.dumps(prepare_resume(p.parse_args().run),indent=2))
