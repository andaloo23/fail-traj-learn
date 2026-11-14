"""Preflight, freeze, queue and collect the one-call Sol V8.1 OopsieData batch.

No generation is retried automatically. Ambiguous submissions stop the queue.
Native requests, responses and Markdown are preserved; review data is derived.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

import requests
import oopsie_common as common
import annotation_runtime as transport
import batch_trajectories as batch_io
import failure_enrichment_v8_1 as enrichment
from oopsie_bulk_v8_1 import write_once, CONFIG

DEFAULT_ROOT=common.ROOT/common.read(CONFIG)['out']
TERMINAL={'completed','failed','expired','cancelled'}
MAX_LINE_BYTES=185_000_000
TEMPLATE=Path(__file__).with_name('oopsie_bulk_review.html')


def verify(root, evidence=False):
    m=common.read(root/'manifest.json'); c=m['config']
    if c['teachers']!={'sol':'gpt-6.1-sol'} or c['repeats']!=1 or len(m['episodes'])!=500:
        raise ValueError('Expected exactly 500 episodes, one Sol response each')
    for file,key in [('prompt.md','prompt_sha256'),('selection.json','selection_sha256'),('selection_plan.json','selection_plan_sha256')]:
        if common.sha(root/file)!=m[key]:raise ValueError('Frozen collection input changed: '+file)
    if common.sha(root/'prompt.md')!=c['prompt_sha256'] or m['source_annotations_used_as_model_input']:
        raise ValueError('Wrong prompt or leaked source annotations')
    if Counter(e['split'] for e in m['episodes'])!=c['split_counts']:raise ValueError('Split counts changed')
    labs={s:{e['lab'] for e in m['episodes'] if e['split']==s} for s in c['split_counts']}
    for a,b in [('train','development'),('train','test'),('development','test')]:
        if labs[a]&labs[b]:raise ValueError('Lab leakage across splits')
    if len({e['release_path'] for e in m['episodes']})!=500:raise ValueError('Duplicate episodes')
    if c.get('exclude_previous_runs'):
        prior=common.read(root/'selection_plan.json').get('previous_collections',[])
        if [p['run'] for p in prior]!=c['exclude_previous_runs']:
            raise ValueError('Previous-collection exclusion provenance changed')
        for p in prior:
            previous=common.inside(common.ROOT,p['run'])
            if (common.sha(previous/'selection.json')!=p['selection_sha256'] or
                    common.sha(previous/'config.json')!=p['config_sha256']):
                raise ValueError('Previous collection selection or configuration changed')
            old=common.read(previous/'selection.json')['episodes']
            old_paths={e['release_path'] for e in old};old_ids={e['id'] for e in old}
            old_hashes={e['hdf5_sha256'] for e in old}
            if any(e['release_path'] in old_paths or e['id'] in old_ids or e['hdf5_sha256'] in old_hashes
                    for e in m['episodes']):
                raise ValueError('Expansion includes a previously collected episode')
    if evidence:
        for e in m['episodes']:
            if common.sha(root/e.get('hdf5_file','source/'+e['release_path']))!=e['hdf5_sha256']:raise ValueError('Changed HDF5 source')
            for x in e['videos']+e['images']:
                if common.sha(common.inside(root,x.get('path',x.get('url'))))!=x['sha256']:raise ValueError('Changed visual evidence')
    return m


def payload(root,m,e):
    info=(f"\n\n## Episode input\n\n- Episode: {e['id']}\n- Task: {e['task']}\n"
          f"- Source frame count: {e['n_frames']}\n- Frames per second: {e['fps']}\n"
          '- Every recorded frame from every listed camera is supplied, in time order.\n\n### Cameras\n\n'
          +'\n'.join(f"- {c['camera']}: {c['description']}" for c in e['cameras']))
    text=(root/'prompt.md').read_text(encoding='utf-8')+info+(
        '\n\nEach supplied image is one original source frame with synchronized camera panels '
        'placed side by side. Read panels from left to right in the listed Cameras order. '
        'Each panel retains its per-camera resolution; black padding is not scene content. '
        'All recorded timestamps and all listed views are included; no temporal sampling is applied.')
    content=[dict(type='input_text',text=text)]
    for x in e['images']:
        p=common.inside(root,x['path'])
        if common.sha(p)!=x['sha256']:raise ValueError('Frozen image changed')
        content.extend([dict(type='input_text',text=f"Frame {x['frame']} | {x['seconds']:.6f} seconds | camera {x['camera']}"),
                        dict(type='input_image',image_url='data:image/webp;base64,'+base64.b64encode(p.read_bytes()).decode(),detail='high')])
    return dict(model='gpt-6.1-sol',input=[dict(role='user',content=content)],reasoning=dict(effort='low'),
        max_output_tokens=m['config']['max_output_tokens'],text=dict(format=dict(type='text')),truncation='disabled',store=False)


def compact(value):return json.dumps(value,separators=(',',':'),ensure_ascii=True).encode()


def overflow_files(root,e,body,key):
    """Keep every exact image, replacing only enough oversized inline bytes with IDs."""
    size=len(compact(body)); content=body['input'][0]['content']
    images=[(len(content[2+2*i]['image_url']),i) for i in range(len(e['images']))]
    for _,i in sorted(images,reverse=True):
        if size<MAX_LINE_BYTES-2048:break
        x=e['images'][i]; log=root/'image_uploads'/f"{e['id']}_{i:06d}.json"; log.parent.mkdir(exist_ok=True)
        if log.exists():upload=common.read(log)
        else:
            with (root/x['path']).open('rb') as f:
                response=requests.post('https://api.openai.com/v1/files',headers={'Authorization':'Bearer '+key},
                    data={'purpose':'vision'},files={'file':(Path(x['path']).name,f,'image/webp')},timeout=180)
            if response.status_code!=200:raise ValueError('Image upload failed: HTTP '+str(response.status_code))
            upload=dict(response=response.json(),image_sha256=x['sha256']);write_once(log,upload)
        if upload['image_sha256']!=x['sha256']:raise ValueError('Uploaded image changed')
        old=content[2+2*i]
        content[2+2*i]=dict(type='input_image',file_id=upload['response']['id'],detail=old['detail'])
        size=len(compact(body))
    if size>=MAX_LINE_BYTES:raise ValueError('Oversized request after lossless file-ID transport')
    return body


def ceiling(tokens,cfg):
    long=tokens>272000
    return (tokens*1.25*(2 if long else 1)+cfg['max_output_tokens']*5*(1.5 if long else 1))/1e6


def preflight_one(root,m,e,key):
    path=root/'requests'/f"{e['id']}_sol.json"; receipt=root/'preflight'/f"{e['id']}.json"
    if receipt.exists():
        row=common.read(receipt)
        if row['request_sha256']!=common.sha(path):raise ValueError('Changed preflight request')
        return row
    if path.exists():body=common.read(path)
    else:
        body=overflow_files(root,e,payload(root,m,e),key)
        with path.open('xb') as f:f.write(compact(body))
    response=transport.post('https://api.openai.com/v1/responses/input_tokens','openai',
        {k:body[k] for k in ('model','input','reasoning','text','truncation')},{'openai':key})
    tokens=response['input_tokens']
    if type(tokens)is not int or not 0<tokens<=m['config']['max_input_tokens']:raise ValueError('Input token limit exceeded; no truncation')
    row=dict(episode=e['id'],input_tokens=tokens,image_count=len(e['images']),request_bytes=path.stat().st_size,
        request_sha256=common.sha(path),per_call_ceiling_usd=ceiling(tokens,m['config']))
    write_once(receipt,row);return row


def preflight(root,workers=3):
    m=verify(root); key=transport.credentials()['openai']
    (root/'requests').mkdir(exist_ok=True); (root/'preflight').mkdir(exist_ok=True)
    rows=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(preflight_one,root,m,e,key) for e in m['episodes']]):
            rows.append(future.result())
            if len(rows)%10==0:print(json.dumps(dict(preflight_complete=len(rows),planned=500)),flush=True)
    order={e['id']:i for i,e in enumerate(m['episodes'])}; rows.sort(key=lambda r:order[r['episode']])
    result=dict(complete=True,manifest_sha256=common.sha(root/'manifest.json'),requests=rows,
        input_tokens=sum(r['input_tokens'] for r in rows),run_total_ceiling_usd=sum(r['per_call_ceiling_usd'] for r in rows),
        budget_usd=m['config']['budget_usd'],generation_calls=0)
    write_once(root/'token_preflight.json',result)
    if result['run_total_ceiling_usd']>result['budget_usd']:raise ValueError('Preflight exceeds authorized $75 budget; nothing submitted')
    print(json.dumps({k:v for k,v in result.items() if k!='requests'}),flush=True)
    freeze(root,m,result)


def run_pipeline(root,workers=3):
    """Overlap non-generating preflights with preparation, then queue frozen work."""
    lock=root/'pipeline_worker.lock'
    with lock.open('x',encoding='utf-8') as f:json.dump(dict(pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat()),f)
    try:
        cfg=common.read(root/'config.json');plan=common.read(root/'selection_plan.json');key=transport.credentials()['openai']
        (root/'requests').mkdir(exist_ok=True);(root/'preflight').mkdir(exist_ok=True)
        while not (root/'manifest.json').exists():
            ready=[]
            for split,count in cfg['split_counts'].items():
                accepted=0
                for e in plan['candidates'][split]:
                    p=root/'prepared'/f"{e['id']}.json"
                    if not p.exists():break
                    try:prepared=common.read(p)
                    except json.JSONDecodeError:break
                    if prepared['status']=='prepared':
                        accepted+=1
                        if not (root/'preflight'/f"{e['id']}.json").exists():ready.append(prepared)
                    if accepted==count:break
            if ready:
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    for future in as_completed([pool.submit(preflight_one,root,{'config':cfg},e,key) for e in ready]):
                        row=future.result();print(json.dumps(dict(preflight_episode=row['episode'],input_tokens=row['input_tokens'])),flush=True)
            time.sleep(10)
        # Preparation publishes the complete JSON once; tolerate its short write interval.
        for _ in range(10):
            try:common.read(root/'manifest.json');break
            except json.JSONDecodeError:time.sleep(1)
        preflight(root,workers)
        queue(root)
    except Exception as exc:
        transport.atomic_json(root/'pipeline_failure.json',dict(message=str(exc),utc=datetime.now(timezone.utc).isoformat()))
        raise
    finally:lock.unlink(missing_ok=True)


def freeze(root,m,pf):
    if (root/'batch_manifest.json').exists():return
    folder=root/'batch_inputs'; folder.mkdir(exist_ok=True)
    if list(folder.glob('*.jsonl')):raise ValueError('Incomplete freeze requires inspection; no overwrite')
    shards=[]; stream=None; size=tokens=0; ids=[]; costs=0
    def close():
        if stream:
            stream.close()
            shards.append(dict(path=path.relative_to(root).as_posix(),sha256=common.sha(path),bytes=size,
                               input_tokens=tokens,custom_ids=list(ids),cost_ceiling_usd=costs))
    try:
        for row in pf['requests']:
            body=(root/'requests'/f"{row['episode']}_sol.json").read_bytes()
            line=(b'{"custom_id":'+compact(row['episode']+'_sol_r01')+b',"method":"POST","url":"/v1/responses","body":'+body+b'}\n')
            if len(line)>MAX_LINE_BYTES:raise ValueError('Batch request exceeds transport ceiling')
            if stream is None or size+len(line)>190_000_000 or tokens+row['input_tokens']>1_000_000:
                close();path=folder/f'batch_{len(shards)+1:03d}.jsonl';stream=path.open('xb');size=tokens=0;ids=[];costs=0
            stream.write(line);size+=len(line);tokens+=row['input_tokens'];ids.append(row['episode']+'_sol_r01');costs+=row['per_call_ceiling_usd']
        close();stream=None
    finally:
        if stream:stream.close()
    value=dict(protocol=m['protocol'],run_id=uuid.uuid4().hex,model='gpt-6.1-sol',planned=500,
        endpoint='/v1/responses',completion_window='24h',manifest_sha256=common.sha(root/'manifest.json'),
        preflight_sha256=common.sha(root/'token_preflight.json'),shards=shards,
        generation_retries=0,max_enqueued_input_tokens=2_500_000,cost_ceiling_usd=pf['run_total_ceiling_usd'])
    write_once(root/'batch_manifest.json',value)
    print(json.dumps(dict(frozen_shards=len(shards),planned_calls=500,cost_ceiling_usd=value['cost_ceiling_usd'])),flush=True)


def usage_cost(raw):
    u=raw['usage']; d=u.get('input_tokens_details') or {}; n=u['input_tokens']; out=u['output_tokens']
    cached=d.get('cached_tokens',0); writes=d.get('cache_write_tokens',0)
    if min(n,out,cached,writes)<0 or cached+writes>n:raise ValueError('Invalid usage accounting')
    return ((n-cached-writes)+cached*.05+writes*1.25)*(2 if n>272000 else 1)/1e6+out*5*(1.5 if n>272000 else 1)/1e6


def ingest(root,m,shard,raw_bytes):
    episodes={e['id']:e for e in m['episodes']}; seen=set()
    for line in raw_bytes.splitlines():
        if not line.strip():continue
        record=json.loads(line); cid=record['custom_id']
        if cid not in shard['custom_ids'] or cid in seen:raise ValueError('Unknown or duplicate Batch output custom ID')
        seen.add(cid); eid=cid.removesuffix('_sol_r01'); e=episodes[eid]
        folder=root/'traces'/cid;folder.mkdir(parents=True,exist_ok=True)
        original=folder/'batch_record.jsonl'
        if original.exists():
            if original.read_bytes()!=line+b'\n':raise ValueError('Native Batch record changed')
            if (folder/'attempt.json').exists():continue
        else:
            with original.open('xb') as f:f.write(line+b'\n')
        state=dict(episode=eid,teacher='sol',repeat=1,model='gpt-6.1-sol',
            manifest_sha256=common.sha(root/'manifest.json'),request_sha256=common.sha(root/'requests'/f'{eid}_sol.json'),
            native_batch_record_sha256=common.sha(original),status='stopped')
        response=record.get('response') or {}; raw=response.get('body')
        if isinstance(raw,dict):
            write_once(folder/'response.json',raw);state['response_sha256']=common.sha(folder/'response.json')
            if raw.get('usage'):state.update(usage=raw['usage'],generation_estimate_usd=usage_cost(raw))
            answer,complete=transport.extract_answer('openai',raw)
            if answer:
                annotation_path=folder/'annotation.md'
                if annotation_path.exists():
                    if annotation_path.read_bytes().decode('utf-8')!=answer:raise ValueError('Native annotation changed')
                else:
                    with annotation_path.open('x',encoding='utf-8',newline='') as f:f.write(answer)
                state['annotation_sha256']=common.sha(folder/'annotation.md')
            try:
                if response.get('status_code')!=200 or not complete:raise ValueError('API response not completed successfully')
                if raw.get('model')!='gpt-6.1-sol':raise ValueError('Unexpected teacher model')
                enrichment.parse(answer,e);state['status']='validated'
            except ValueError as exc:state.update(status='invalid',error=str(exc))
        else:state['error']=record.get('error') or 'No model response'
        write_once(folder/'attempt.json',state)


def publish(root,m,status=None):
    if (root/'review_check.lock').exists():return
    data=dict(protocol=m['protocol'],prompt_revision='V8.1',manifest_sha256=common.sha(root/'manifest.json'),
        review_ui_version=common.sha(TEMPLATE),side_labels={'v8':'V8.1 - Sol'},side_repeats={'v8':1},
        planned_responses=500,repeats=1,episodes=[],status_message=(status or {}).get('message','Sol Batch collection'),
        rich_prompt_description='One independent Sol annotation per episode. V8.1 failure labels, categories and visible explanations.')
    costs=0;valid=0;invalid=[]
    for e in m['episodes']:
        traces=[];folder=root/'traces'/f"{e['id']}_sol_r01";p=folder/'attempt.json'
        if p.exists():
            state=common.read(p);costs+=state.get('generation_estimate_usd',0)
            if state['status']=='validated':
                text=(folder/'annotation.md').read_bytes().decode('utf-8')
                if common.sha(folder/'annotation.md')!=state['annotation_sha256']:raise ValueError('Native annotation changed')
                annotation=enrichment.parse(text,e)
                traces=[dict(annotation,repeat=1,native_markdown=text,markdown=(folder/'annotation.md').relative_to(root).as_posix())];valid+=1
            else:invalid.append(e['id'])
        data['episodes'].append({k:e[k] for k in ('id','task','split','lab','fps','n_frames','videos')})
        data['episodes'][-1].update(teachers={'v8':traces},source_run=root.name)
    template=TEMPLATE.read_text(encoding='utf-8')
    embedded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    temp=root/'review.html.tmp';temp.write_text(template.replace('__DATA__',embedded),encoding='utf-8');temp.replace(root/'review.html')
    transport.atomic_json(root/'review_data.json',data)
    report=['# Sol V8.1: 500 real OopsieData episodes','',
        f'- Native validated annotations: **{valid}/500**; invalid/stopped outputs: {len(invalid)}.',
        '- One Sol request per episode; no Astra requests or automatic generation retries.',
        '- Split: 400 training / 50 development / 50 final test; contributing labs do not overlap across splits.',
        '- All original frames and all distinct native camera views are included. No temporal sampling or truncation.',
        '- The V8.1 prompt is unchanged. Each Yes interval includes taxonomy categories and a short visible-evidence explanation.',
        '- The saved pilot episodes are excluded; source annotations were never supplied to the teacher.',
        '- Inputs use the pilot JPEG95 per-camera preprocessing, packed in lossless WebP strips. Lossless file-ID transport is used only if necessary to fit a Batch file.',
        f'- Estimated consumed Batch generation cost: **${costs:.6f}**. Authorized budget: $75.',
        '- These are teacher proposals; parser validation is not human verification or accuracy measurement.',
        '- No student training has started. No repeat agreement can be measured with one call per episode.','',
        '## Episode annotations','', '| Episode | Split | Lab | Seconds | Annotation |','|---|---|---|---:|---|']
    for e in data['episodes']:
        ts=e['teachers']['v8']; link=f"[Native Markdown]({ts[0]['markdown']})" if ts else 'Pending or unavailable'
        report.append(f"| {e['id']} | {e['split']} | {e['lab']} | {e['n_frames']/e['fps']:.2f} | {link} |")
    temp=root/'report.md.tmp';temp.write_text('\n'.join(report)+'\n',encoding='utf-8');temp.replace(root/'report.md')
    transport.atomic_json(root/'collection_summary.json',dict(planned=500,validated=valid,invalid=invalid,generation_estimate_usd=costs))


def jobs(root,bm):
    return [(s,root/'batch_jobs'/(Path(s['path']).stem+'.json')) for s in bm['shards']]


def submit_shard(root,bm,s,path,key):
    stem=Path(s['path']).stem
    if path.exists():raise ValueError('A submission journal already exists; no resend')
    if common.sha(root/s['path'])!=s['sha256']:raise ValueError('Frozen batch input changed')
    upload_path=path.with_name(stem+'_upload.json')
    if upload_path.exists():uploaded=common.read(upload_path)
    else:
        uploaded=batch_io.upload(root/s['path'],key);write_once(upload_path,uploaded)
    state=dict(status='submitting',input_file_id=uploaded['id'],run_id=bm['run_id'],custom_ids=s['custom_ids'],
        request_id=str(uuid.uuid4()),started_utc=datetime.now(timezone.utc).isoformat())
    with path.open('x',encoding='utf-8') as f:json.dump(state,f,indent=2)
    try:
        state['batch']=batch_io.api('POST','/v1/batches',key,dict(input_file_id=uploaded['id'],endpoint='/v1/responses',
            completion_window='24h',metadata=dict(run_id=bm['run_id'],shard=stem,protocol=bm['protocol'])),request_id=state['request_id'])
        state['status']='submitted'
    except Exception as exc:
        state.update(status='submission_unresolved',error=str(exc));raise
    finally:transport.atomic_json(path,state)
    print(json.dumps(dict(submitted=stem,episodes=len(s['custom_ids']),batch_id=state['batch']['id'])),flush=True)


def collect(root,m,bm,key):
    for s,p in jobs(root,bm):
        if not p.exists():continue
        state=common.read(p)
        if not state.get('batch'):raise ValueError('Submission outcome unresolved; no automatic resend')
        remote=state['batch']
        if remote['status'] not in TERMINAL:
            remote=batch_io.api('GET','/v1/batches/'+remote['id'],key);state['batch']=remote;transport.atomic_json(p,state)
        if remote['status'] in TERMINAL:
            for role in ('output','error'):
                fid=remote.get(role+'_file_id')
                if fid:
                    dest=root/'batch_outputs'/(p.stem+'_'+role+'.jsonl');dest.parent.mkdir(exist_ok=True)
                    if not dest.exists():
                        raw=batch_io.api('GET','/v1/files/'+fid+'/content',key,raw=True)
                        with dest.open('xb') as f:f.write(raw)
                    ingest(root,m,s,dest.read_bytes())


def queue(root,interval=30):
    m=verify(root,True);bm=common.read(root/'batch_manifest.json')
    pf=common.read(root/'token_preflight.json')
    if bm['manifest_sha256']!=common.sha(root/'manifest.json') or bm['preflight_sha256']!=common.sha(root/'token_preflight.json'):
        raise ValueError('Frozen batch provenance changed')
    if bm['cost_ceiling_usd']>m['config']['budget_usd'] or not pf['complete']:raise ValueError('Budget/preflight not authorized')
    ids=[x for s in bm['shards'] for x in s['custom_ids']]
    if len(set(ids))!=500 or set(ids)!={e['id']+'_sol_r01' for e in m['episodes']}:raise ValueError('Batch request coverage mismatch')
    (root/'batch_jobs').mkdir(exist_ok=True)
    lock=root/'queue_worker.lock'
    with lock.open('x',encoding='utf-8') as f:json.dump(dict(pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat()),f)
    key=transport.credentials()['openai']
    try:
        while True:
            collect(root,m,bm,key)
            active=pending=complete=failed=0;queued_tokens=0
            for s,p in jobs(root,bm):
                if not p.exists():pending+=len(s['custom_ids']);continue
                state=common.read(p);r=state.get('batch')
                if not r:raise ValueError('Unresolved submission; no automatic resend')
                if r['status'] not in TERMINAL:active+=len(s['custom_ids']);queued_tokens+=s['input_tokens']
                elif r['status']=='completed':complete+=len(s['custom_ids'])
                else:failed+=len(s['custom_ids'])
            if failed:
                # Preserve all rejection records; diagnose instead of purchasing retries.
                raise ValueError('A batch stopped or failed; no further submissions until diagnostics reviewed')
            for s,p in jobs(root,bm):
                if not p.exists() and queued_tokens+s['input_tokens']<=bm['max_enqueued_input_tokens']:
                    submit_shard(root,bm,s,p,key);queued_tokens+=s['input_tokens'];active+=len(s['custom_ids']);pending-=len(s['custom_ids'])
            status=dict(planned=500,active_requests=active,queued_locally=pending,completed_batch_requests=complete,
                message=f'{active} requests active; {pending} queued locally; {complete} returned from completed batches.',
                updated_utc=datetime.now(timezone.utc).isoformat(),controller_pid=os.getpid())
            transport.atomic_json(root/'queue_status.json',status);publish(root,m,status)
            print(json.dumps(status),flush=True)
            if not active and not pending:return
            time.sleep(interval)
    except Exception as exc:
        failure=dict(message='Collection stopped: '+str(exc),updated_utc=datetime.now(timezone.utc).isoformat())
        transport.atomic_json(root/'queue_failure.json',failure);publish(root,m,failure)
        raise
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('run','preflight','queue','collect','review','verify'))
    parser.add_argument('--run',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args();root=args.run.resolve()
    if args.command=='run':run_pipeline(root,args.workers)
    elif args.command=='preflight':preflight(root,args.workers)
    elif args.command=='queue':queue(root)
    elif args.command=='collect':
        m=verify(root);collect(root,m,common.read(root/'batch_manifest.json'),transport.credentials()['openai']);publish(root,m)
    elif args.command=='review':publish(root,verify(root))
    else:verify(root,True);print('All source evidence and frozen inputs verified.')
