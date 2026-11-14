"""Frozen target views and full-coverage visual windows for recipe comparisons.

Native teacher annotations stay read-only. All derived assistant targets are
Markdown. Test references cannot be exported without explicit final-test access.
"""
from collections import defaultdict, Counter
import copy
import json
from pathlib import Path
import random
import re

import oopsie_common as common
import annotation_runtime as transport
import failure_enrichment_v8_1 as enrichment
from oopsie_bulk_v8_1 import write_once

CONFIG=common.ROOT/'configs/oopsie_distillation_recipes_v1.json'
RECIPES={
 'base':dict(kind='pretrained',requires=[]),
 'binary':dict(kind='sft',target='binary',requires=[]),
 'joint':dict(kind='sft',target='joint',requires=[]),
 'categories_aux':dict(kind='sft',target='categories_aux',requires=[]),
 'evidence_aux':dict(kind='sft',target='evidence_aux',requires=[]),
 'both_aux':dict(kind='sft',target='both_aux',requires=[]),
 'binary_compute_control':dict(kind='sft',target='binary_compute_control',requires=[]),
 'joint_then_binary':dict(kind='sft',target='joint_then_binary',requires=[]),
 'failure_balanced':dict(kind='sft',target='binary',sampling='failure_balanced',requires=[]),
 'self_review':dict(kind='inference_revision',requires=['binary']),
 'fixed_teacher_error_replay':dict(kind='training_feedback',requires=['binary','training_drafts']),
 'self_revision_distill':dict(kind='training_feedback',requires=['binary','self_review_training']),
 'sol_review':dict(kind='teacher_assisted_inference',requires=['binary','training_drafts','teacher_review_budget']),
 'sol_correction_distill':dict(kind='training_feedback',requires=['sol_review']),
 'preference_dpo':dict(kind='preference_training',requires=['binary','validated_preference_pairs']),
 'reward_grpo':dict(kind='reward_training',requires=['binary','verified_reward_and_rollouts'])
}


def table(eid,segments):
    return '# Episode: '+eid+'\n\n| Start frame | End frame | Failure |\n| --- | --- | --- |\n'+''.join(
        f"| {s['start_frame']} | {s['end_frame']} | {'Yes' if s['failure'] else 'No'} |\n" for s in segments)


def clip(segments,start,end):
    result=[]
    for s in segments:
        a,b=max(start,s['start_frame']),min(end,s['end_frame'])
        if a<b:
            if result and result[-1]['failure']==s['failure']:result[-1]['end_frame']=b
            else:result.append(dict(start_frame=a,end_frame=b,failure=s['failure']))
    if not result or result[0]['start_frame']!=start or result[-1]['end_frame']!=end:
        raise ValueError('Clipped teacher timeline has a coverage gap')
    return result


def windows(n,core,context):
    if n<1 or core<1 or context<0:raise ValueError('Invalid coverage parameters')
    return [dict(core_start=s,core_end=min(s+core,n),context_start=max(0,s-context),context_end=min(n,s+core+context))
            for s in range(0,n,core)]


def parse_prediction(text,eid,start,end):
    """Parse the binary prefix, preserving invalid outputs as abstentions."""
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    if len(lines)<4 or lines[0]!='# Episode: '+eid or lines[1]!='| Start frame | End frame | Failure |':
        raise ValueError('Missing required Markdown heading/table')
    if not re.fullmatch(r'\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|',lines[2]):raise ValueError('Invalid table separator')
    result=[];cursor=start
    for line in lines[3:]:
        if line.startswith('## '):break
        m=re.fullmatch(r'\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(Yes|No)\s*\|',line)
        if not m:raise ValueError('Unexpected binary output content')
        a,b,yes=int(m[1]),int(m[2]),m[3]=='Yes'
        if a!=cursor or not a<b<=end:raise ValueError('Gap, overlap or out-of-core boundary')
        if result and result[-1]['failure']==yes:raise ValueError('Adjacent equal labels must be merged')
        result.append(dict(start_frame=a,end_frame=b,failure=yes));cursor=b
    if cursor!=end:raise ValueError('Incomplete core coverage')
    return result


def citation_bounds(text):
    found=[]
    for m in re.finditer(r'\bframes?\s+(\d+(?:\s*(?:[-–]|to|,|and)\s*\d+)*)',text,re.I):
        found.extend(int(n) for n in re.findall(r'\d+',m[1]))
    return found


def supported_details(value,window):
    # Avoid supervising statements referring to unseen parts of a long failure.
    out=[]
    for a in value['failure_annotations']:
        if not a['start_frame']<window['core_end'] or not a['end_frame']>window['core_start']:continue
        refs=citation_bounds(a['explanation'])
        if (a['start_frame']>=window['context_start'] and a['end_frame']<=window['context_end']
                and refs and all(window['context_start']<=f<window['context_end'] for f in refs)):
            out.append(a)
    return out


def study(config=CONFIG):
    cfg=common.read(config);root=common.ROOT/cfg['out'];source=common.ROOT/cfg['source_run']
    root.mkdir(parents=True,exist_ok=True)
    m=common.read(source/'manifest.json')
    if m['config']['teachers']!={'sol':'gpt-6.1-sol'}:raise ValueError('Expected Sol-only source')
    rows=[];quarantine=[]
    for e in m['episodes']:
        folder=source/'traces'/f"{e['id']}_sol_r01";state=common.read(folder/'attempt.json')
        if state['status']!='validated':quarantine.append(dict(episode=e['id'],split=e['split'],reason=state.get('error')));continue
        if common.sha(folder/'annotation.md')!=state['annotation_sha256'] or common.sha(folder/'response.json')!=state['response_sha256']:
            raise ValueError('Native source response changed')
        value=enrichment.parse((folder/'annotation.md').read_bytes().decode('utf-8'),e)
        rows.append(dict(episode=e['id'],split=e['split'],lab=e['lab'],n_frames=e['n_frames'],fps=e['fps'],
            annotation_sha256=state['annotation_sha256'],response_sha256=state['response_sha256'],
            has_failure=any(s['failure'] for s in value['segments'])))
    train=[r for r in rows if r['split']=='train']
    # Nested lab/positive strata use training labels only; development/test do not choose the training subset.
    groups=defaultdict(list)
    for r in train:groups[(r['lab'],r['has_failure'])].append(r['episode'])
    rng=random.Random(cfg['student']['seed']);keys=sorted(groups)
    for key in keys:groups[key].sort();rng.shuffle(groups[key])
    rng.shuffle(keys);order=[]
    for index in range(max(map(len,groups.values()))):
        for key in keys:
            if index<len(groups[key]):order.append(groups[key][index])
    value=dict(protocol=cfg['protocol'],config=cfg,source_manifest_sha256=common.sha(source/'manifest.json'),
        source_prompt_sha256=common.sha(source/'prompt.md'),episodes=rows,quarantined=quarantine,
        training_order=order,screening_train_ids=order[:cfg['screening_training_episodes']],
        development_ids=[r['episode'] for r in rows if r['split']=='development'],
        sealed_test_ids=[r['episode'] for r in rows if r['split']=='test'],recipes=RECIPES,
        test_evaluation_enabled=False,new_teacher_calls_authorized_by_controller=False)
    write_once(root/'study.json',value)
    print(json.dumps(dict(study=str(root),available_splits=dict(Counter(r['split'] for r in rows)),
        screening_training_episodes=len(value['screening_train_ids']),quarantined=len(quarantine),recipes=len(RECIPES))),flush=True)
    return root,source,m,value


def prompt_prefix(source):
    # Exact shared V9.1 recognition/boundary rules; only the student output scope changes.
    original=(source/'prompt.md').read_text(encoding='utf-8')
    return original.split('Partition every source frame',1)[0]


def record(source,e,value,window,task='binary'):
    a,b=window['core_start'],window['core_end'];c,d=window['context_start'],window['context_end']
    segments=clip(value['segments'],a,b);details=supported_details(value,window)
    contract=(f"\n\n## Student window input\nEpisode: {e['id']}\nTask: {e['task']}\n"
        f"Original episode: {e['n_frames']} frames at {e['fps']} FPS.\n"
        f'Visible source frames: [{c}, {d}). Label only the scored core [{a}, {b}).\n'
        'The visible clip is a window, so its beginning and end are not episode termination. '
        'All source frames within this window and all listed camera panels are provided. '
        'Use surrounding visible frames as context. Use original frame indices, start inclusive, end exclusive. '
        'Partition the scored core without gaps or overlaps; merge adjacent equal labels.\n'
        +'Camera panels, left to right: '+', '.join(x['camera'] for x in e['cameras'])+'.\n')
    target=table(e['id'],segments)
    if task in ('binary','binary_compute_control'):
        instruction='Return only the Markdown episode heading and table with Start frame, End frame, Failure (Yes or No). No explanations or other fields.'
    elif task=='joint':
        instruction=('First return the binary Markdown episode heading and Start frame / End frame / Failure table for the scored core. '
            'Then under ## Visible failure evidence describe any entire failure intervals wholly visible in this context. '
            'Give Frames, Categories and Explanation with camera/frame references. These evidence intervals may extend outside the scored core; the primary table must not. Write None if no complete interval can be described.')
        target+='\n## Visible failure evidence\n\n'+detail_markdown(details,'both_aux')
    else:
        instruction=('This is an auxiliary visual supervision task. Describe complete, visibly supported failure intervals overlapping the scored core. '
            'Use only the images; return Markdown under # Visible failure evidence. Include '+
            ('Frames and Categories.' if task=='categories_aux' else 'Frames and Explanation with source camera/frame references.' if task=='evidence_aux' else 'Frames, Categories and Explanation with source camera/frame references.'))
        target='# Visible failure evidence\n\n'+detail_markdown(details,task)
        if not details:raise ValueError('Auxiliary target has no fully visible, grounded failure interval')
    if task in ('binary','binary_compute_control','joint'):
        instruction+=('\n\nRequired primary format (replace placeholders):\n# Episode: '+e['id']+
            '\n\n| Start frame | End frame | Failure |\n| --- | --- | --- |\n| START | END | Yes or No |\n')
    content=[dict(type='text',text=prompt_prefix(source)+contract+'\n'+instruction)]
    for x in e['images'][c:d]:
        content.extend([dict(type='text',text=f"Frame {x['frame']} | {x['seconds']:.6f} seconds"),
                        dict(type='image',image=x['path'])])
    return dict(id=f"{e['id']}_{a:06d}_{b:06d}_{task}",episode=e['id'],split=e['split'],task=task,
        **window,source_n_frames=e['n_frames'],fps=e['fps'],
        messages=[dict(role='user',content=content),dict(role='assistant',content=target)],
        target_origin='derived from preserved native Sol V8.1; no new teacher generation',
        has_failure=any(s['failure'] for s in segments),eligible_aux_annotations=len(details),
        supervision=dict(assistant_excluded_char_ranges=[],has_eligible_segment_targets=True))


def detail_markdown(details,task):
    if not details:return 'None\n'
    blocks=[]
    for index,a in enumerate(details,1):
        block=f"## Failure {index}\n\n- Frames: {a['start_frame']}-{a['end_frame']}\n"
        if task in ('categories_aux','both_aux'):block+='- Categories: '+', '.join(a['categories'])+'\n'
        if task in ('evidence_aux','both_aux'):block+='- Explanation: '+a['explanation']+'\n'
        blocks.append(block)
    return '\n'.join(blocks)


def export(root,core,context,version=2):
    s=common.read(root/'study.json');source=common.ROOT/s['config']['source_run'];m=common.read(source/'manifest.json')
    if common.sha(source/'manifest.json')!=s['source_manifest_sha256']:raise ValueError('Source manifest changed')
    folder=root/f'evidence_c{core}_x{context}_v{version}';folder.mkdir(exist_ok=True)
    adapter=dict(version='full_timestamp_overlapping_windows_v1',core_frames=core,context_frames=context,
        all_frames_retained=True,cameras='all native nonduplicate panels',student=s['config']['student'],
        limitation='Windowed student cannot observe distant episode context. Teacher evidence unavailable inside a window is omitted from auxiliary targets.')
    write_once(folder/'adapter.json',adapter)
    ids=set(s['screening_train_ids'])|set(s['development_ids']);metadata=[];counts=Counter()
    output=folder/'records.jsonl'
    if output.exists():raise ValueError('Derived records already frozen; choose another adapter version')
    with output.open('x',encoding='utf-8') as f:
        for e in m['episodes']:
            if e['id'] not in ids:continue
            native=source/'traces'/f"{e['id']}_sol_r01"/'annotation.md'
            value=enrichment.parse(native.read_bytes().decode('utf-8'),e)
            coverage=0
            for w in windows(e['n_frames'],core,context):
                coverage+=w['core_end']-w['core_start']
                tasks=['binary'] if e['split']!='train' else ['binary','joint']
                if supported_details(value,w) and e['split']=='train':tasks+=['categories_aux','evidence_aux','both_aux']
                for task in tasks:
                    r=record(source,e,value,w,task);f.write(json.dumps(r,separators=(',',':'))+'\n')
                    counts[e['split']+'_'+task]+=1
                    metadata.append({k:r[k] for k in ('id','episode','split','task','core_start','core_end','context_start','context_end','has_failure','eligible_aux_annotations')})
            if coverage!=e['n_frames']:raise ValueError('Student scored-core coverage is incomplete')
    index=dict(protocol=s['protocol'],study_sha256=common.sha(root/'study.json'),adapter_sha256=common.sha(folder/'adapter.json'),
        records_sha256=common.sha(output),counts=dict(counts),records=metadata,sealed_test_exported=False)
    write_once(folder/'index.json',index)
    print(json.dumps(dict(export=str(folder),counts=dict(counts),all_source_frames_covered=True)),flush=True)
    return folder
