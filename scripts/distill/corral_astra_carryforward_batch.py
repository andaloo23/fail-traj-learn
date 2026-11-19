"""Finish the frozen 1,000 episodes using reviewed all-frame parts and Batch only.

Reuse 936 validated native labels and two reviewed pilots. Each of the remaining
62 episodes advances only after its previous part validates. Immutable Batch
submission journals prevent unknown submissions being automatically repeated.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import time
import uuid

import corral_astra_v8_2_batch as batch
import corral_astra_window_pilot as window
import oopsie_common as common
import annotation_runtime as transport
import rich_failure_v8_2 as schema
from oopsie_bulk_v8_1 import write_once

SOURCE=batch.DEFAULT
PILOTS=[common.ROOT/'outputs/corral_astra_rich_failure_v8_2_carryforward_pilot_v1',
        common.ROOT/'outputs/corral_astra_rich_failure_v8_2_carryforward_pilot_v2']
DEFAULT=common.ROOT/'outputs/corral_astra_rich_failure_v8_2_carryforward_batch_v3'
MODEL=batch.MODEL
MAX_QUEUED_TOKENS=2_500_000
MAX_REPAIRS=2
_episodes={}


def episode(root,eid):
    key=(str(root),eid)
    if key not in _episodes:_episodes[key]=common.read(root/'prepared'/(eid+'.json'))
    return _episodes[key]


def canonical(root,key):return root/'canonical'/key


def verify(root):
    plan=common.read(root/'run_plan.json')
    identity=root/'plan_identity.json'
    if identity.exists() and common.sha(root/'run_plan.json')!=common.read(identity)['run_plan_sha256']:
        raise ValueError('Frozen run plan changed')
    if plan['model']!=MODEL or plan['generation_transport']!='batch_only' or plan['frame_stride']!=1:
        raise ValueError('Frozen all-frame, Astra, Batch-only policy changed')
    if len(plan['reused'])!=938 or len(plan['authorized_episode_ids'])!=62:
        raise ValueError('Unexpected authorized run scope')
    for name,digest in plan['frozen_hashes'].items():
        if common.sha(root/name)!=digest:raise ValueError('Changed frozen artifact: '+name)
    return plan


def initialize(root):
    if root.exists():raise ValueError('Version exists; resume instead of replacing it')
    selection=common.read(SOURCE/'selection.json')
    ids={e['id'] for e in selection['episodes']}
    reused={}
    for p in (SOURCE/'traces').glob('*/status.json'):
        status=common.read(p);eid=p.parent.name.removesuffix('_astra')
        if status.get('status')=='validated':reused[eid]=(p.parent,'whole_episode_native')
    if len(reused)!=936:raise ValueError('Original run state changed; inspect before collecting again')
    for pilot in PILOTS:
        pp,e=window.verify(pilot);eid=e['id'];folder=pilot/'traces'/f'{eid}_final'
        if eid in reused or not (folder/'status.json').exists():raise ValueError('Unexpected reviewed-pilot state')
        reused[eid]=(folder,'reviewed_carryforward_reconciliation')
    remaining=sorted(ids-set(reused))
    if len(remaining)!=62 or not set(remaining)<ids:raise ValueError('Unexpected remaining scope')
    root.mkdir(parents=True)
    for name in ('selection.json','prompt.md'):shutil.copyfile(SOURCE/name,root/name)
    for name in ('window_prompt.md','reconciliation_prompt.md'):
        if common.sha(PILOTS[0]/name)!=common.sha(PILOTS[1]/name):raise ValueError('Reviewed prompts differ')
        shutil.copyfile(PILOTS[0]/name,root/name)
    catalog=[]
    for eid in sorted(ids):
        source=SOURCE/'prepared'/(eid+'.json');e=common.read(source)
        batch.link_file(source,root/'prepared'/(eid+'.json'))
        for video in e['videos']:batch.link_file(SOURCE/video['url'],root/video['url'])
        catalog.append({k:e[k] for k in ('id','lab','split','task','n_frames','fps','videos','frame_times','duration_seconds') if k in e})
    imports=[]
    for eid,(source,kind) in sorted(reused.items()):
        e=episode(root,eid);raw=common.read(source/'response.json');status=common.read(source/'status.json')
        if raw['model']!=MODEL or status['model']!=raw['model']:raise ValueError('Teacher identity changed')
        schema.parse((source/'annotation.md').read_text(encoding='utf-8'),e)
        for name in ('response.json','annotation.md','parsed.json','status.json'):
            batch.link_file(source/name,canonical(root,eid+'_final')/name)
        imports.append(dict(episode=eid,kind=kind,source_trace=str(source),
            response_sha256=common.sha(source/'response.json'),recorded_model=raw['model']))
    historical_cost=0
    for p in (SOURCE/'traces').glob('*/response.json'):
        raw=common.read(p);eid=p.parent.name.removesuffix('_astra')
        historical_cost+=batch.usage_cost(raw['usage'],eid not in {f'C{i:04d}' for i in range(1,11)})
    historical_cost+=sum(window.cost_to_date(p) for p in PILOTS)
    write_once(root/'catalog.json',catalog)
    recipe={eid:window.windows(episode(root,eid)['n_frames'],episode_id=eid) for eid in remaining}
    write_once(root/'recipe.json',recipe)
    plan=dict(protocol='rich_failure_v8_2_carryforward_batch_v3',created_utc=batch.now(),
        authorization='User reviewed both pilots and explicitly approved finishing the dataset, Batch mode to minimize cost, all recorded frames; no every-other-frame sampling.',
        model=MODEL,generation_transport='batch_only',frame_stride=1,all_distinct_cameras=True,
        window_frames=350,preceding_context_frames=2,annotation_overlap_frames=0,
        max_part_output_tokens=8000,max_final_output_tokens=12000,max_request_input_tokens=240000,
        prompt_cache_options=dict(mode='explicit',ttl='30m'),cache_scope='shared prompt text only',
        completion_window='24h',budget_usd=250,historical_returned_usage_cost_usd=historical_cost,
        historical_gateway_error_charges='Unverified; no usage returned for preserved pilot HTTP 500 errors.',
        source_run=str(SOURCE),authorized_episode_ids=remaining,reused=imports,
        planned_new_parts=sum(len(v) for v in recipe.values()),planned_new_reconciliations=len(remaining),
        transport_generation_retries=0,max_completed_or_terminal_failure_repairs=MAX_REPAIRS,
        source_annotations_used_as_model_input=False,original_run_and_holds_unchanged=True,
        frozen_hashes={name:common.sha(root/name) for name in ('selection.json','prompt.md','window_prompt.md','reconciliation_prompt.md','catalog.json','recipe.json')})
    write_once(root/'run_plan.json',plan)
    write_once(root/'plan_identity.json',dict(run_plan_sha256=common.sha(root/'run_plan.json')))
    projection(root)
    publish(root)
    print('Initialized: reuse 938, finish 62 original episodes; Batch only; every frame.',flush=True)


def projection(root):
    plan=verify(root);recipe=common.read(root/'recipe.json');tokens=0;part_outputs=[];final_outputs=[];final_inputs=[]
    for pilot in PILOTS:
        for p in (pilot/'traces').glob('*/response.json'):
            u=common.read(p)['usage']
            if '_final' in p.parent.name:final_outputs.append(u['output_tokens']);final_inputs.append(u['input_tokens'])
            else:part_outputs.append(u['output_tokens'])
    for eid,spans in recipe.items():
        e=episode(root,eid);pan=e['images'][0]['panels']
        per=math.ceil(math.ceil(sum(p['width'] for p in pan)/32)*math.ceil(max(p['height'] for p in pan)/32)*1.2)+10
        tokens+=sum(2600+(w['end']-w['context_start'])*per+(800 if i else 0) for i,w in enumerate(spans))
    parts=plan['planned_new_parts'];count=len(recipe)
    components=dict(part_inputs_usd=tokens*5/1e6,
        part_outputs_usd=parts*statistics.mean(part_outputs)*25/1e6,
        reconciliation_inputs_usd=count*statistics.mean(final_inputs)*5/1e6,
        reconciliation_outputs_usd=count*statistics.mean(final_outputs)*25/1e6,
        shared_prefix_write_allowance_usd=(parts+count)*3000*1.25/1e6)
    added=sum(components.values())
    write_once(root/'initial_cost_projection.json',dict(remaining_episodes=count,planned_parts=parts,
        estimated_part_input_tokens=tokens,components=components,estimated_additional_usd=added,
        estimated_total_usd=plan['historical_returned_usage_cost_usd']+added,
        assumptions='Batch pricing, no cache-hit credit, pilot average output/reconciliation sizes. Future inputs depend on prior native labels. Excludes unknown historical gateway-error charges.'))


def apply_shared_cache(body,prompt):
    content=body['input'][0]['content'];first=content[0]['text']
    if not first.startswith(prompt):raise ValueError('Shared prompt mismatch')
    content[:1]=[dict(type='input_text',text=prompt,prompt_cache_breakpoint=dict(mode='explicit')),
                dict(type='input_text',text=first[len(prompt):])]
    body['prompt_cache_options']=dict(mode='explicit',ttl='30m')
    return body


def build_final(root,e,spans):
    parsed={w['id']:common.read(canonical(root,w['id'])/'parsed.json') for w in spans}
    draft=window.core_draft(dict(windows=spans),parsed);frames={0,e['n_frames']-1};last=-1
    for im in e['images']:
        second=math.floor(im['seconds'])
        if second!=last:frames.add(im['frame']);last=second
    for w in spans:
        for s in [dict(start_frame=w['start'],end_frame=w['end'])]+parsed[w['id']]['segments']:
            for f in (s['start_frame'],s['end_frame']-1):
                frames.update(i for i in (f-1,f,f+1) if 0<=i<e['n_frames'])
    extra='\n## Central-core draft (provisional)\n\n| Start frame | End frame | Failure | Source window |\n| --- | --- | --- | --- |\n'
    extra+='\n'.join(f'| {s["start_frame"]} | {s["end_frame"]} | {"Yes" if s["failure"] else "No"} | {s["source_window"]} |' for s in draft)
    for w in spans:extra+='\n\n## Native window report: '+w['id']+'\n\n'+(canonical(root,w['id'])/'annotation.md').read_text(encoding='utf-8')
    return [e['images'][i] for i in sorted(frames)],extra


def prepare_job(root,descriptor):
    plan=verify(root);eid=descriptor['episode'];key=descriptor['key'];attempt=descriptor['attempt'];identifier=f'{key}_A{attempt}'
    if eid not in plan['authorized_episode_ids']:raise ValueError('Episode outside authorized remaining scope')
    receipt=root/'preflight'/(identifier+'.json')
    if receipt.exists():return common.read(receipt)
    e=episode(root,eid);bounds=descriptor.get('bounds');prior=[]
    if bounds:
        previous=bounds['previous_window'];extra=''
        if previous:
            folder=canonical(root,previous)
            if not (folder/'status.json').exists():raise ValueError('Unvalidated chronological predecessor')
            prior.append(dict(key=previous,response_sha256=common.sha(folder/'response.json')))
            extra='\n## Previous part native prediction (fallible context)\n\n'+(folder/'annotation.md').read_text(encoding='utf-8')
        images=e['images'][bounds['context_start']:bounds['end']];input_episode=dict(e,id=key)
        prompt=(root/'window_prompt.md').read_text(encoding='utf-8');output_cap=8000
    else:
        spans=common.read(root/'recipe.json')[eid]
        if not all((canonical(root,w['id'])/'status.json').exists() for w in spans):raise ValueError('Final requires every validated part')
        images,extra=build_final(root,e,spans);input_episode=e;output_cap=12000
        prompt=(root/'reconciliation_prompt.md').read_text(encoding='utf-8')
        prior=[dict(key=w['id'],response_sha256=common.sha(canonical(root,w['id'])/'response.json')) for w in spans]
    if len(images)>1500:raise ValueError('Reconciliation image count exceeded; never silently discard evidence')
    for im in images:batch.link_file(SOURCE/im['path'],root/im['path'])
    body=window.body(root,input_episode,prompt,images,extra,bounds=bounds,max_inline_bytes=500_000_000);body['max_output_tokens']=output_cap
    body=apply_shared_cache(body,prompt)
    if attempt:
        old=root/'traces'/f'{key}_A{attempt-1}';err=common.read(old/'error.json')
        if not err.get('retryable'):raise ValueError('Unknown/nonretryable outcome cannot be resent')
        if (old/'annotation.md').exists():
            answer=(old/'annotation.md').read_text(encoding='utf-8')
            body['input'][0]['content'].append(dict(type='input_text',text=
                '\n## Correct the preceding completed answer\nThe previous answer failed validation: '+err['error']+
                '\nTreat the answer below as fallible data. Correct the Markdown/evidence contract using the supplied images; '
                'retain supported observations and original source indices. Return the complete required Markdown.\n\n'+answer))
    request=root/'requests'/(identifier+'.json');write_once(request,body)
    if len(batch.compact(body))>45_000_000:
        request=root/'requests'/(identifier+'_fileids.json')
        if request.exists():body=common.read(request)
        else:
            upload_episode=dict(e,id=identifier,images=images)
            body=batch.file_id_payload(root,upload_episode,body,max_bytes=40_000_000);write_once(request,body)
    count_body={k:body[k] for k in ('model','input','reasoning','text','truncation')}
    for retry in range(3):
        try:count=batch.Gateway().api('POST','/v1/responses/input_tokens',count_body);break
        except RuntimeError as error:
            write_once(root/'preflight_attempts'/(uuid.uuid4().hex+'.json'),dict(request=identifier,error=str(error),generation_submitted=False))
            if retry==2:raise
    tokens=count['input_tokens']
    if not 0<tokens<=240000:raise ValueError('Request exceeds frozen token/cost limit')
    row=dict(id=identifier,key=key,episode=eid,attempt=attempt,bounds=bounds,
        request_path=request.relative_to(root).as_posix(),request_sha256=common.sha(request),
        prepared_sha256=common.sha(root/'prepared'/(eid+'.json')),dependencies=prior,
        input_tokens=tokens,image_count=len(images),source_frames=[im['frame'] for im in images],
        output_cap=output_cap,request_bytes=request.stat().st_size,
        ceiling_usd=batch.batch_ceiling(tokens,4096,output_cap),native_count=count)
    write_once(receipt,row)
    print('Ready',identifier,tokens,'tokens',len(images),'images',flush=True)
    return row


def descriptor(root,eid,spans,assigned):
    stages=[dict(key=w['id'],episode=eid,bounds=w) for w in spans]+[dict(key=eid+'_final',episode=eid,bounds=None)]
    for stage in stages:
        key=stage['key']
        if (canonical(root,key)/'status.json').exists():continue
        attempt=0
        while True:
            identifier=f'{key}_A{attempt}';error=root/'traces'/identifier/'error.json'
            if error.exists():
                if common.read(error).get('retryable') and attempt<MAX_REPAIRS:attempt+=1;continue
                return None
            if identifier in assigned or (root/'preflight'/(identifier+'.json')).exists():return None
            return dict(stage,attempt=attempt,id=identifier)
    return None


def accounting(root):
    spent=0
    for p in (root/'traces').glob('*/response.json'):
        u=common.read(p).get('usage')
        if u:spent+=batch.usage_cost(u,True)
    reserved=sum(common.read(p)['ceiling_usd'] for p in (root/'batch_jobs').glob('*.json') if common.read(p)['status']!='collected')
    return spent,reserved


def submit(root,rows):
    plan=verify(root)
    if (root/'STOP_REQUESTED.json').exists():raise ValueError('Stop requested')
    for row in rows:
        if row['episode'] not in plan['authorized_episode_ids']:raise ValueError('Unauthorized batch episode')
        if common.sha(root/row['request_path'])!=row['request_sha256']:raise ValueError('Changed frozen request')
        for dep in row['dependencies']:
            if common.sha(canonical(root,dep['key'])/'response.json')!=dep['response_sha256']:raise ValueError('Changed predecessor response')
    ceiling=sum(r['ceiling_usd'] for r in rows);spent,reserved=accounting(root)
    if spent+reserved+ceiling>plan['budget_usd']:raise ValueError('Additional-run budget guard reached')
    name='batch_'+uuid.uuid4().hex;path=root/'batch_inputs'/(name+'.jsonl');path.parent.mkdir(exist_ok=True)
    with path.open('xb') as stream:
        for row in rows:stream.write(batch.compact(dict(custom_id=row['id'],method='POST',url='/v1/responses',body=common.read(root/row['request_path'])))+b'\n')
    if path.stat().st_size>185_000_000:raise ValueError('Frozen batch too large')
    state=dict(status='uploading',rows=rows,ceiling_usd=ceiling,input_tokens=sum(r['input_tokens'] for r in rows),
        path=path.relative_to(root).as_posix(),sha256=common.sha(path),created_utc=batch.now(),
        upload_request_id=uuid.uuid4().hex,submit_request_id=uuid.uuid4().hex,generation_post_started=False)
    journal=root/'batch_jobs'/(name+'.json');write_once(journal,state)
    finish_submission(root,journal,state)


def finish_submission(root,journal,state):
    plan=verify(root);path=root/state['path']
    if state.get('generation_post_started') or state.get('batch'):
        raise ValueError('Unknown or accepted generation submission must not be resent')
    if common.sha(path)!=state['sha256']:raise ValueError('Changed immutable Batch input')
    if not all(row['episode'] in plan['authorized_episode_ids'] for row in state['rows']):
        raise ValueError('Journal episode outside authorized scope')
    try:
        client=batch.Gateway()
        if 'upload' not in state:state['upload']=batch.upload_immutable_file(root,client,path,state['upload_request_id'],purpose='batch')
        if (root/'STOP_REQUESTED.json').exists():raise ValueError('Stop requested before generation submission')
        state['status']='submitting';state['generation_post_started']=True;transport.atomic_json(journal,state)
        state['batch']=client.api('POST','/v1/batches',dict(input_file_id=state['upload']['id'],endpoint='/v1/responses',
            completion_window='24h',metadata=dict(protocol=plan['protocol'],shard=journal.stem)),request_id=state['submit_request_id'])
        state['status']='submitted';state['submitted_utc']=batch.now()
    except Exception as error:
        state['status']='submission_unresolved' if state['generation_post_started'] else 'upload_failed_before_generation'
        state['error']=str(error);raise
    finally:transport.atomic_json(journal,state)
    print('Submitted',len(state['rows']),'Batch requests',state['batch']['id'],flush=True)


def ingest(root,row,envelope):
    folder=root/'traces'/row['id'];write_once(folder/'batch_envelope.json',envelope)
    if (folder/'status.json').exists() or (folder/'error.json').exists():return
    retryable=True
    try:
        result=envelope.get('response') or {}
        if result.get('status_code')!=200 or envelope.get('error'):
            code=(envelope.get('error') or {}).get('code')
            retryable=code in ('batch_expired','rate_limit_exceeded','server_error') or result.get('status_code') in (429,500,502,503,504)
            raise ValueError('Terminal Batch item error: '+str(envelope.get('error') or result)[:1200])
        raw=result['body'];write_once(folder/'response.json',raw)
        actual=raw.get('model','')
        if not (actual==MODEL or actual.startswith(MODEL+'-')):
            retryable=False;raise ValueError('Unexpected actual teacher model: '+actual)
        text,complete=transport.extract_answer('openai',raw);(folder/'annotation.md').write_text(text,encoding='utf-8')
        if not complete:raise ValueError('Native response incomplete; output preserved')
        e=episode(root,row['episode']);bounds=row['bounds']
        if bounds:e=dict(e,id=row['key'],images=[e['images'][i] for i in row['source_frames']])
        kwargs=dict(coverage_start=bounds['start'],coverage_end=bounds['end']) if bounds else {}
        parsed=schema.parse(text,e,**kwargs);write_once(folder/'parsed.json',parsed)
        write_once(folder/'status.json',dict(status='validated',model=actual,usage=raw['usage'],completed_utc=batch.now(),
            batch_mode=True,request_sha256=row['request_sha256'],original_episode=row['episode']))
        for name in ('response.json','annotation.md','parsed.json','status.json'):
            batch.link_file(folder/name,canonical(root,row['key'])/name)
        print('Validated',row['id'],flush=True)
    except Exception as error:
        write_once(folder/'error.json',dict(error=str(error),retryable=retryable,recorded_utc=batch.now(),
            unknown_submission_resent=False,native_output_preserved=True))


def collect(root):
    client=batch.Gateway();assigned=set();queued=0;unresolved=[]
    for path in sorted((root/'batch_jobs').glob('*.json')):
        state=common.read(path);assigned.update(r['id'] for r in state['rows'])
        if state['status']=='collected':continue
        if state['status'] in ('upload_failed_before_generation','upload_pending_verified_no_submit'):
            finish_submission(root,path,state)
        if 'batch' not in state:unresolved.append(path.name);continue
        state['batch']=client.api('GET','/v1/batches/'+state['batch']['id'])
        if state['batch']['status'] not in batch.TERMINAL:queued+=state['input_tokens']
        else:
            seen=set();expected={r['id']:r for r in state['rows']}
            for field in ('output_file_id','error_file_id'):
                file_id=state['batch'].get(field)
                if not file_id:continue
                dest=root/'batch_outputs'/(path.stem+'_'+field+'.jsonl');dest.parent.mkdir(exist_ok=True)
                if dest.exists():value=dest.read_bytes()
                else:
                    value=client.api('GET','/v1/files/'+file_id+'/content',raw=True)
                    with dest.open('xb') as f:f.write(value)
                for line in value.splitlines():
                    if not line.strip():continue
                    envelope=json.loads(line);cid=envelope['custom_id']
                    if cid not in expected or cid in seen:raise ValueError('Unknown/duplicate Batch result ID')
                    seen.add(cid);ingest(root,expected[cid],envelope)
            for cid,row in expected.items():
                if cid not in seen:ingest(root,row,dict(custom_id=cid,response=None,error=dict(code='batch_expired' if state['batch']['status']=='expired' else 'missing_output',message='No output returned')))
            state['status']='collected';state['collected_utc']=batch.now()
        transport.atomic_json(path,state)
    return assigned,queued,unresolved


def publish(root):
    plan=verify(root);catalog=common.read(root/'catalog.json');data_episodes=[];dataset=[];ready=0
    for item in catalog:
        eid=item['id'];folder=canonical(root,eid+'_final');traces=[]
        if (folder/'status.json').exists():
            parsed=common.read(folder/'parsed.json');text=(folder/'annotation.md').read_text(encoding='utf-8');status=common.read(folder/'status.json')
            traces=[dict(repeat=1,**parsed,native_markdown=text,markdown=f'canonical/{eid}_final/annotation.md')];ready+=1
            dataset.append(dict(episode_id=eid,task=item['task'],teacher_recorded_model=status['model'],
                response_sha256=common.sha(folder/'response.json'),native_response=f'canonical/{eid}_final/response.json',
                assistant_target=text,human_verified=eid in ('C0052','C0188'),
                label_origin='reused' if eid in {r['episode'] for r in plan['reused']} else 'carryforward_batch_reconciliation'))
        data_episodes.append(dict(item,teachers={'v8':traces},source_run=root.name))
    template=Path(window.pilot.__file__).with_name('corral_astra_v8_2_review.html').read_text(encoding='utf-8')
    helper='''function frameSeconds(f){const a=current.frame_times;if(!a)return f/current.fps;if(f<a.length)return a[f];return current.duration_seconds??a.at(-1)+1/current.fps}
function frameAtSeconds(t){const a=current.frame_times;if(!a)return Math.floor(t*current.fps+0.001);let lo=0,hi=a.length;while(lo<hi){const mid=(lo+hi)>>1;if(a[mid]<=t+0.00001)lo=mid+1;else hi=mid}return Math.max(0,lo-1)}
'''
    template=template.replace('Ten Astra pilot annotations from a fresh 1,000-episode Corral sample:','Frozen 1,000-episode sample; existing labels reused and remaining episodes processed with all-frame sequential parts:')
    template=template.replace('const time=f=>(f/current.fps).toFixed(2)',helper+'const time=f=>frameSeconds(f).toFixed(2)').replace('pendingSeek=frame/current.fps','pendingSeek=frameSeconds(frame)').replace('Math.floor(master.currentTime*current.fps+0.001)','frameAtSeconds(master.currentTime)')
    data=dict(protocol=plan['protocol'],prompt_revision='V8.2',manifest_sha256=common.sha(root/'run_plan.json'),
        review_ui_version=hashlib.sha256(template.encode()).hexdigest(),repeats=1,planned_responses=1000,
        side_labels={'v8':'Astra V8.2'},side_repeats={'v8':1},episodes=data_episodes,
        rich_prompt_description='Native labels retain actual teacher identity. Remaining labels use reviewed all-frame sequential parts and final reconciliation; previous labels are reused.')
    transport.atomic_json(root/'review_data.json',data)
    encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    temp=root/'review.html.tmp';temp.write_text(template.replace('__DATA__',encoded),encoding='utf-8');temp.replace(root/'review.html')
    spent,reserved=accounting(root)
    transport.atomic_json(root/'dataset_manifest.json',dict(updated_utc=batch.now(),complete=ready==1000,validated_episodes=ready,
        reused_episodes=938,newly_completed_episodes=ready-938,new_batch_returned_usage_usd=spent,
        prior_returned_usage_usd=plan['historical_returned_usage_cost_usd'],total_returned_usage_usd=spent+plan['historical_returned_usage_cost_usd'],
        unknown_historical_gateway_error_charges_excluded=True,training_launched=False))
    tmp=root/'dataset.jsonl.tmp';tmp.write_bytes(b''.join(batch.compact(r)+b'\n' for r in dataset));tmp.replace(root/'dataset.jsonl')
    estimate=common.read(root/'initial_cost_projection.json')
    lines=['# Astra all-frame carry-forward Batch completion','',f'**{ready}/1000 validated episodes.** 938 existing labels reused; {ready-938}/62 additional episodes completed.','',
        'Every recorded frame and all distinct cameras are retained. Disjoint 350-frame parts carry the previous two frames and previous native annotation; final reconciliation produces one episode label. All new generation uses Batch mode only.','',
        f'New returned-usage cost: **${spent:.2f}**. Prior returned-usage cost including pilots: **${plan["historical_returned_usage_cost_usd"]:.2f}**. '
        f'Initial projected full-run total: **${estimate["estimated_total_usd"]:.2f}**; output lengths and future predecessor text vary. Historical gateway-error charges are unverified and excluded.','',
        'Original frozen requests, native outputs, review notes and source videos remain preserved. No training is running. The two reviewed pilot responses are reused without new calls.','',
        '[Open video and time-aligned labels](review.html)','', '| Episode | Status | Native Markdown |','|---|---|---|']
    for e in data_episodes:
        traces=e['teachers']['v8'];lines.append(f'| {e["id"]} | '+(traces[0]['success_label'] if traces else 'Pending')+' | '+(f'[Markdown]({traces[0]["markdown"]})' if traces else 'Pending')+' |')
    (root/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return ready


def run(root,interval=20):
    plan=verify(root);recipe=common.read(root/'recipe.json');lock=root/'worker.lock'
    write_once(lock,dict(pid=os.getpid(),started_utc=batch.now()))
    futures={};cooldown={};last_publish=0
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            while True:
                if (root/'STOP_REQUESTED.json').exists():break
                try:
                    assigned,queued,unresolved=collect(root)
                    for identifier,future in list(futures.items()):
                        if future.done():
                            try:future.result()
                            except Exception as error:
                                (root/'preparation_errors').mkdir(parents=True,exist_ok=True)
                                transport.atomic_json(root/'preparation_errors'/(identifier+'.json'),dict(error=str(error),recorded_utc=batch.now(),generation_submitted=False))
                                cooldown[identifier]=time.monotonic()+120
                            del futures[identifier]
                    for eid,spans in recipe.items():
                        d=descriptor(root,eid,spans,assigned)
                        if d and d['id'] not in futures and time.monotonic()>cooldown.get(d['id'],0):
                            if len(futures)>=6:break
                            futures[d['id']]=pool.submit(prepare_job,root,d)
                    available=[]
                    for p in sorted((root/'preflight').glob('*.json')):
                        row=common.read(p)
                        if row['id'] not in assigned and not (canonical(root,row['key'])/'status.json').exists() and not (root/'traces'/row['id']/'error.json').exists():available.append(row)
                    group=[];size=tokens=0
                    for row in available:
                        if queued+tokens+row['input_tokens']>MAX_QUEUED_TOKENS:break
                        if group and (size+row['request_bytes']+1024>180_000_000 or tokens+row['input_tokens']>750000):
                            submit(root,group);queued+=tokens;group=[];size=tokens=0
                        group.append(row);size+=row['request_bytes']+1024;tokens+=row['input_tokens']
                    if group:submit(root,group);queued+=tokens
                    final_count=sum((canonical(root,eid+'_final')/'status.json').exists() for eid in recipe)
                    if time.monotonic()-last_publish>120 or final_count==62:
                        publish(root);last_publish=time.monotonic()
                    spent,reserved=accounting(root)
                    transport.atomic_json(root/'queue_status.json',dict(updated_utc=batch.now(),reused_episodes=938,new_completed_episodes=final_count,
                        validated_episodes=938+final_count,total_episodes=1000,preparing=len(futures),queued_input_tokens=queued,
                        submitted_requests=len(assigned),new_returned_usage_usd=spent,reserved_ceiling_usd=reserved,
                        unresolved_submissions=unresolved,worker_pid=os.getpid(),all_frames=True,batch_only=True))
                    if final_count==62:
                        write_once(root/'completion.json',dict(completed_utc=batch.now(),validated_episodes=1000,new_batch_usage_usd=spent));break
                except Exception as error:
                    transport.atomic_json(root/'worker_error.json',dict(error=str(error),recorded_utc=batch.now(),unknown_submissions_never_resent=True))
                    print('Worker attention:',str(error),flush=True)
                time.sleep(interval)
    finally:
        if lock.exists() and common.read(lock).get('pid')==os.getpid():lock.unlink()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['init','run','publish'])
    parser.add_argument('--run',type=Path,default=DEFAULT)
    args=parser.parse_args();root=args.run.resolve()
    if args.command=='init':initialize(root)
    elif args.command=='run':run(root)
    else:publish(root)
