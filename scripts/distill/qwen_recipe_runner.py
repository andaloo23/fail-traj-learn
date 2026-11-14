"""Auditable Qwen recipe benchmark, bounded SFT and binary student evaluation."""
import argparse
from collections import Counter,defaultdict
import copy
import gc
import importlib.metadata
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import time

import oopsie_common as common
import annotation_runtime as transport
import qwen_oopsie_sft as core
import oopsie_recipe_data as data
from oopsie_bulk_v8_1 import write_once

ROOT=common.ROOT/common.read(data.CONFIG)['out']


def load(folder):
    folder=Path(folder);s=common.read(folder.parent/'study.json');index=common.read(folder/'index.json')
    if common.sha(folder.parent/'study.json')!=index['study_sha256'] or common.sha(folder/'records.jsonl')!=index['records_sha256']:
        raise ValueError('Frozen study/export changed')
    if common.sha(folder/'adapter.json')!=index['adapter_sha256']:raise ValueError('Evidence adapter changed')
    source=common.ROOT/s['config']['source_run']
    if common.sha(source/'manifest.json')!=s['source_manifest_sha256']:raise ValueError('Teacher source changed')
    rows=[json.loads(x) for x in (folder/'records.jsonl').read_text(encoding='utf-8').splitlines()]
    if any(r['split']=='test' for r in rows):raise ValueError('Final test must stay sealed')
    return s,source,rows


def cfg_for(study):
    return dict(study['config']['student'],local_files_only=True)


@lru_cache(maxsize=2)
def image_dimensions(source):
    manifest=common.read(Path(source)/'manifest.json');sizes={}
    for episode in manifest['episodes']:
        for image in episode['images']:
            panels=image.get('panels',[])
            if panels:
                sizes[image['path']]=(max(p['x']+p['width'] for p in panels),max(p['y']+p['height'] for p in panels))
    return sizes


def estimated_tokens(processor,source,row):
    from PIL import Image
    from transformers.models.qwen2_vl.image_processing_qwen2_vl import smart_resize
    full=processor.apply_chat_template(row['messages'],tokenize=False,add_generation_prompt=False)
    text_tokens=len(processor.tokenizer(full,add_special_tokens=False)['input_ids'])
    ip=processor.image_processor
    dimensions=image_dimensions(str(source))
    for item in row['messages'][0]['content']:
        if item['type']!='image':continue
        if item['image'] in dimensions:w,h=dimensions[item['image']]
        else:
            with Image.open(source/item['image']) as image:w,h=image.size
        h,w=smart_resize(h,w,factor=ip.patch_size*ip.merge_size,min_pixels=ip.min_pixels,max_pixels=ip.max_pixels)
        text_tokens+=(h//ip.patch_size)*(w//ip.patch_size)//(ip.merge_size**2)-1
    return text_tokens


def audit(folder,processor=None):
    s,source,rows=load(folder);cfg=cfg_for(s);processor=processor or core.processor_for(cfg)
    output=[]
    for i,r in enumerate(rows):
        n=estimated_tokens(processor,source,r)
        output.append(dict(id=r['id'],episode=r['episode'],split=r['split'],task=r['task'],tokens=n,within_cap=n<=cfg['max_length']))
        if (i+1)%250==0:print(json.dumps(dict(audited=i+1,total=len(rows))),flush=True)
    result=dict(model=cfg['model'],revision=cfg['revision'],max_length=cfg['max_length'],rows=output,
        overlength=sum(not x['within_cap'] for x in output),max_tokens=max(x['tokens'] for x in output),
        adapter_sha256=common.sha(Path(folder)/'adapter.json'),method='Exact tokenizer plus pinned native image-grid resizing formula; representative sequences checked with the full processor')
    write_once(Path(folder)/'token_audit.json',result)
    return result


def benchmark(root,max_seconds=120):
    import torch
    s=common.read(root/'study.json');cfg=cfg_for(s);processor=core.processor_for(cfg)
    model=core.load_model(cfg,trainable=True)
    print(json.dumps(dict(stage='model_loaded',gpu=torch.cuda.get_device_name(),
        allocated_gpu_gib=torch.cuda.memory_allocated()/1024**3,
        trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad))),flush=True)
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=cfg['learning_rate'])
    results=[]
    for candidate in s['config']['candidate_adapters']:
        folder=root/f"evidence_c{candidate['core_frames']}_x{candidate['context_frames']}_v2"
        _,source,rows=load(folder)
        # Benchmark on training evidence only, using the widest visual context.
        eligible=[r for r in rows if r['split']=='train' and r['task']=='binary']
        ranked=sorted(((estimated_tokens(processor,source,r),r) for r in eligible),key=lambda x:x[0])
        n,row=ranked[-1];entry=dict(candidate,estimated_tokens=n,example=row['id'])
        if n>cfg['max_length']:
            results.append(dict(entry,status='over_context_cap'));continue
        try:
            print(json.dumps(dict(stage='encode_benchmark_candidate',candidate=candidate,estimated_tokens=n)),flush=True)
            t=time.monotonic();batch=core.encode_train(processor,source,row,cfg['max_length'])
            entry['processor_seconds']=time.monotonic()-t;entry['actual_tokens']=int(batch['input_ids'].shape[1])
            if entry['actual_tokens']!=n:raise ValueError('Native processor token count differs from exact audit formula')
            model.train();optimizer.zero_grad(set_to_none=True);torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats()
            print(json.dumps(dict(stage='forward_backward_benchmark',candidate=candidate,actual_tokens=n)),flush=True)
            torch.cuda.synchronize();t=time.monotonic();batch={k:v.to('cuda') for k,v in batch.items()}
            with torch.autocast('cuda',dtype=torch.bfloat16):loss,count=core.sft_loss(model,batch)
            (loss/count).backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1,error_if_nonfinite=True)
            optimizer.step();optimizer.zero_grad(set_to_none=True);torch.cuda.synchronize()
            entry.update(status='passed',forward_backward_optimizer_seconds=time.monotonic()-t,
                loss=float(loss.detach())/count,supervised_tokens=count,grad_norm=float(norm),
                peak_gpu_gib=torch.cuda.max_memory_allocated()/1024**3)
            del batch,loss
        except torch.cuda.OutOfMemoryError:
            entry.update(status='gpu_oom');optimizer.zero_grad(set_to_none=True)
        results.append(entry);gc.collect();torch.cuda.empty_cache()
        transport.atomic_json(root/'gpu_benchmark.json',dict(gpu=torch.cuda.get_device_name(),candidates=results,complete=False))
        print(json.dumps(entry),flush=True)
    usable=[r for r in results if r['status']=='passed' and r['peak_gpu_gib']<21.5 and r['forward_backward_optimizer_seconds']<=max_seconds]
    if not usable:raise ValueError('No full-frame adapter fits the bounded local benchmark; use a larger GPU or a new explicit input adapter')
    selected=usable[-1]
    adapter=f"evidence_c{selected['core_frames']}_x{selected['context_frames']}_v2"
    write_once(root/'selected_adapter.json',dict(folder=adapter,selection_basis='Largest predeclared context fitting training-only memory/speed benchmark; no development/test scores used',benchmark=selected))
    transport.atomic_json(root/'gpu_benchmark.json',dict(gpu=torch.cuda.get_device_name(),candidates=results,complete=True,selected=adapter))
    return adapter


def sample_primary(rows,seed):
    # Round-robin episodes prevents the first short sweep from seeing only long videos.
    rng=random.Random(seed);groups=defaultdict(list)
    for r in rows:groups[r['episode']].append(r)
    keys=sorted(groups);rng.shuffle(keys)
    for key in keys:rng.shuffle(groups[key])
    order=[]
    for i in range(max(map(len,groups.values()))):
        for key in keys:
            if i<len(groups[key]):order.append(groups[key][i])
    return order


def train(folder,recipe,out,updates=None,max_hours=None,init_adapter=None,replay_ids=None):
    import torch
    s,source,rows=load(folder);cfg=cfg_for(s)
    updates=updates or s['config'].get('optimizer_updates',s['config'].get('screening_optimizer_updates'));max_hours=max_hours or s['config'].get('train_max_hours',s['config'].get('screening_max_hours_per_arm'))
    if recipe not in data.RECIPES and recipe!='continuation_control':raise ValueError('Unknown training recipe')
    if out.exists():raise ValueError('Training output already exists; no silent restart')
    binary=[r for r in rows if r['split']=='train' and r['task']=='binary']
    base_order=sample_primary(binary,cfg['seed'])
    by_window={r['id'].removesuffix('_binary'):r for r in binary}
    joint={r['id'].removesuffix('_joint'):r for r in rows if r['split']=='train' and r['task']=='joint'}
    aux_kind=recipe if recipe in ('categories_aux','evidence_aux','both_aux') else 'both_aux'
    aux=[r for r in rows if r['split']=='train' and r['task']==aux_kind]
    aux_rng=random.Random(cfg['seed']+1);aux_rng.shuffle(aux)
    pos=[r for r in base_order if r['has_failure']];neg=[r for r in base_order if not r['has_failure']]
    if replay_ids is not None:
        accepted=set(replay_ids);hard=[r for r in base_order if r['id'] in accepted];easy=[r for r in base_order if r['id'] not in accepted]
        if not hard:raise ValueError('Feedback branch has no diagnosed training errors')
        base_order=[x for pair in zip(hard*max(1,math.ceil(len(easy)/len(hard))),easy) for x in pair]
    processor=core.processor_for(cfg);random.seed(cfg['seed']);torch.manual_seed(cfg['seed']);torch.cuda.manual_seed_all(cfg['seed'])
    model=core.load_model(cfg,trainable=True,adapter=init_adapter);model.train()
    parameters=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(parameters,lr=cfg['learning_rate'])
    out.mkdir(parents=True)
    write_once(out/'run.json',dict(recipe=recipe,student=cfg,study_sha256=common.sha(Path(folder).parent/'study.json'),
        adapter_sha256=common.sha(Path(folder)/'adapter.json'),records_sha256=common.sha(Path(folder)/'records.jsonl'),
        planned_updates=updates,max_hours=max_hours,init_adapter=str(init_adapter) if init_adapter else None,
        primary_examples_per_update=cfg['gradient_accumulation'],auxiliary_loss_weight=.3,
        auxiliary_examples_available=len(aux),seed=cfg['seed'],vision_tower_frozen=True,
        versions={n:importlib.metadata.version(n) for n in ('torch','transformers','peft','bitsandbytes')},
        warm_start_optimizer_reinitialized=bool(init_adapter),test_used=False))
    start=time.monotonic();step=0;seen=Counter();total_tokens=0;examples=0
    with (out/'train.jsonl').open('x',encoding='utf-8',buffering=1) as log:
        for step in range(1,updates+1):
            optimizer.zero_grad(set_to_none=True);group=[]
            for j in range(cfg['gradient_accumulation']):
                i=(step-1)*cfg['gradient_accumulation']+j
                r=base_order[i%len(base_order)]
                # Full-data balanced arm first sees every window, then balances
                # the second pass budget. Screening behavior stays unchanged.
                balanced_i=i-len(base_order) if s['config'].get('full_training_data') else i
                if recipe=='failure_balanced' and balanced_i>=0:
                    pool=pos if balanced_i%2==0 else neg
                    if not pool:raise ValueError('Both failure classes are required for balanced replay')
                    r=pool[(balanced_i//2)%len(pool)]
                if recipe=='joint' or recipe=='joint_then_binary' and step<=updates//2:r=joint[r['id'].removesuffix('_binary')]
                group.append((r,1/cfg['gradient_accumulation']))
            if recipe in ('categories_aux','evidence_aux','both_aux','binary_compute_control'):
                if not aux:raise ValueError('Auxiliary training requested without eligible visible evidence')
                r=aux[(step-1)%len(aux)]
                if recipe=='binary_compute_control':r=by_window[r['id'].removesuffix('_both_aux')]
                group=[(x,w/1.3) for x,w in group]+[(r,.3/1.3)]
            loss_sum=0.;t=time.monotonic();step_tokens=0;torch.cuda.reset_peak_memory_stats()
            for row,weight in group:
                batch=core.encode_train(processor,source,row,cfg['max_length']);n=int(batch['input_ids'].shape[1])
                batch={k:v.to('cuda') for k,v in batch.items()}
                with torch.autocast('cuda',dtype=torch.bfloat16):loss,count=core.sft_loss(model,batch)
                if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
                (loss/count*weight).backward();loss_sum+=float(loss.detach())/count*weight
                step_tokens+=n;examples+=1;seen[row['episode']]+=1;del batch,loss
            norm=torch.nn.utils.clip_grad_norm_(parameters,1,error_if_nonfinite=True)
            warmup=max(1,math.ceil(updates*.03));scale=step/warmup if step<=warmup else .1+.9*(1+math.cos(math.pi*(step-warmup)/max(1,updates-warmup)))/2
            for g in optimizer.param_groups:g['lr']=cfg['learning_rate']*scale
            optimizer.step();torch.cuda.synchronize();total_tokens+=step_tokens
            entry=dict(step=step,loss=loss_sum,grad_norm=float(norm),step_seconds=time.monotonic()-t,
                elapsed_seconds=time.monotonic()-start,input_tokens=step_tokens,peak_gpu_gib=torch.cuda.max_memory_allocated()/1024**3,
                unique_training_episodes_seen=len(seen))
            log.write(json.dumps(entry)+'\n');print(json.dumps(entry),flush=True)
            if step%s['config'].get('checkpoint_every_updates',10)==0 or step==updates or time.monotonic()-start>max_hours*3600:
                checkpoint=out/f'adapter_step_{step}';model.save_pretrained(checkpoint);processor.save_pretrained(checkpoint)
                if s['config'].get('save_optimizer_state'):
                    state=dict(step=step,optimizer=optimizer.state_dict(),python_rng=random.getstate(),
                        torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all(),
                        adapter=str(checkpoint.resolve()),planned_updates=updates,
                        records_sha256=common.sha(Path(folder)/'records.jsonl'),seen=dict(seen),
                        total_tokens=total_tokens,examples=examples)
                    temporary=out/'training_state.tmp';torch.save(state,temporary);temporary.replace(out/'training_state.pt')
            if time.monotonic()-start>max_hours*3600:break
    result=dict(recipe=recipe,steps=step,planned_updates=updates,completed_schedule=step==updates,
        adapter=str(checkpoint.resolve()),elapsed_seconds=time.monotonic()-start,input_tokens=total_tokens,
        examples=examples,unique_training_episodes_seen=len(seen),optimizer_resume_supported=False,
        optimizer_state_preserved=bool(s['config'].get('save_optimizer_state')))
    write_once(out/'completion.json',result);return result


def generate(folder,out,adapter=None,split='development',review=False,max_windows=None,max_hours=None):
    import torch
    s,source,rows=load(folder);cfg=cfg_for(s)
    if split=='test':raise ValueError('Final test is sealed until recipe selection')
    examples=[r for r in rows if r['split']==split and r['task']=='binary']
    if max_windows:examples=examples[:max_windows]
    out.mkdir(parents=True,exist_ok=True)
    spec=dict(model=cfg['model'],revision=cfg['revision'],adapter=str(adapter) if adapter else None,split=split,
        self_review=review,study_sha256=common.sha(Path(folder).parent/'study.json'),adapter_sha256=common.sha(Path(folder)/'adapter.json'),
        max_new_tokens=s['config']['max_new_tokens'],examples=len(examples),max_hours=max_hours,test_used=False)
    write_once(out/'generation.json',spec)
    processor=core.processor_for(cfg);model=core.load_model(cfg,adapter=adapter);model.eval()
    generation_start=time.monotonic();generated_now=0
    for i,row in enumerate(examples):
        path=out/(row['id']+'.json')
        if path.exists():continue
        messages=copy.deepcopy(row['messages'][:-1]);texts=[];started=time.monotonic()
        for turn in range(2 if review else 1):
            if turn:
                messages[0]['content'][0]['text']+='\n\nYour first draft was:\n'+texts[0]+'\n\nRecheck the visible images for missed failures, false alarms and boundaries. Return a corrected binary Markdown table only. Keep a correct draft unchanged.'
            batch=core.encoded_prompt(processor,source,messages);n=int(batch['input_ids'].shape[1])
            if n+s['config']['max_new_tokens']>cfg['max_length']:raise ValueError('Generation would exceed fixed context cap; no truncation')
            batch=batch.to('cuda')
            with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
                output=model.generate(**batch,do_sample=False,max_new_tokens=s['config']['max_new_tokens'],logits_to_keep=1)
            tokens=output[0,n:];text=processor.tokenizer.decode(tokens,skip_special_tokens=True)
            texts.append(text);del batch,output
        record=dict(window_id=row['id'],episode=row['episode'],core_start=row['core_start'],core_end=row['core_end'],
            text=texts[-1],draft=texts[0],output_tokens=len(tokens),hit_max=len(tokens)>=s['config']['max_new_tokens'],
            elapsed_seconds=time.monotonic()-started)
        try:
            record['segments']=data.parse_prediction(record['text'],row['episode'],row['core_start'],row['core_end']);record['schema_valid']=True
        except ValueError as exc:record.update(schema_valid=False,error=str(exc))
        write_once(path,record)
        generated_now+=1
        # User-facing generations and drafts are Markdown; transport/status stay internal.
        (out/(row['id']+'.md')).write_text(record['text'],encoding='utf-8')
        if review:(out/(row['id']+'_draft.md')).write_text(record['draft'],encoding='utf-8')
        print(json.dumps(dict(generated=i+1,total=len(examples),window=row['id'],valid=record['schema_valid'],seconds=record['elapsed_seconds'])),flush=True)
        if max_hours is not None and time.monotonic()-generation_start>=max_hours*3600:break
    complete=all((out/(r['id']+'.json')).exists() for r in examples)
    result=dict(out=str(out),windows=len(examples),generated_now=generated_now,complete=complete,elapsed_seconds=time.monotonic()-generation_start)
    transport.atomic_json(out/'completion.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['audit','benchmark','train','generate'])
    p.add_argument('--study',type=Path,default=ROOT);p.add_argument('--data',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--recipe',default='binary');p.add_argument('--adapter',type=Path);p.add_argument('--updates',type=int)
    p.add_argument('--max-hours',type=float);p.add_argument('--split',choices=['train','development'],default='development')
    p.add_argument('--self-review',action='store_true');p.add_argument('--max-windows',type=int)
    a=p.parse_args()
    if a.command=='benchmark':result=benchmark(a.study)
    elif a.command=='audit':result={k:v for k,v in audit(a.data).items() if k!='rows'}
    elif a.command=='train':result=train(a.data,a.recipe,a.out,a.updates,a.max_hours,a.adapter)
    else:result=generate(a.data,a.out,a.adapter,a.split,a.self_review,a.max_windows,a.max_hours)
    print(json.dumps(result),flush=True)
