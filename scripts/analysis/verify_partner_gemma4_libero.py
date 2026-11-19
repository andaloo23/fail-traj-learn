"""Reproduce the partner adapter's original LIBERO evaluation, at user request.

Whole episodes, original compact JSON contract, both cameras, native telemetry,
derived gripper events, stride three, 70 visual soft tokens. No training or APIs.
Native JSON remains internal; review Markdown is explicitly a derived conversion.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'scripts/distill'))
import oopsie_common as common
import annotation_runtime as transport
import data as native
import oopsie_markdown
import score_recipe_suite as binary_scoring

PRIOR=REPO/'outputs/partner_gemma4_archive_20261113_v1'
RUN=REPO/'outputs/partner_gemma4_libero_native_20261113_v1'
SOURCE=REPO/'outputs/sol_v8_distillation_500/export_v1'


def now():return datetime.now(timezone.utc).isoformat()


def legacy_module():
    spec=importlib.util.spec_from_file_location('partner_legacy_eval',REPO/'scripts/distill/eval.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def immutable(path,value):
    if path.exists():
        if common.read(path)!=value:raise ValueError('Changed frozen artifact: '+str(path))
    else:common.write(path,value)


def records():return {r['id']:r for r in native.load_records(str(SOURCE))}


def prepare():
    RUN.mkdir(parents=True,exist_ok=True)
    archived=[json.loads(line) for line in (PRIOR/'received/sft_v3_per_episode.jsonl').read_text().splitlines() if line.strip()]
    ids=[r['id'] for r in archived]
    logs=[json.loads(line) for line in (PRIOR/'received/train_log.jsonl').read_text().splitlines() if line.strip()]
    train={r['id'] for r in logs if r.get('event')=='example'}
    assert len(ids)==50 and len(set(ids))==50 and not set(ids)&train
    recs=records();assets=common.read(SOURCE/'assets.json');cfg=native.load_cfg(str(PRIOR/'received/input_cfg.json'))
    messages={};sizes={};files={};total_frames=0
    for eid in ids:
        record=recs[eid];info=native._task_info(record);total_frames+=info['n_frames']
        message=native.build_student_messages(record,str(SOURCE),cfg)
        messages[eid]=message;sizes[eid]=sum(x['type']=='image' for x in message[0]['content'])
        for item in message[0]['content']:
            if item['type']=='image':
                path=common.inside(SOURCE,item['image'])
                if common.sha(path)!=assets[item['image']]:raise ValueError('Changed source image')
                files[item['image']]=assets[item['image']]
        immutable(RUN/'requests'/f'{eid}.json',dict(episode=eid,user_messages=message))
    plan=dict(protocol='partner_gemma4_libero_native_reproduction_v1',created_scope='User explicitly requested testing on LIBERO after the OopsieData transfer test.',
        model='google/gemma-4-E4B-it',base_revision=common.read(PRIOR/'base_repository.json')['revision'],
        original_base_revision_supplied=False,adapter_sha256=common.sha(PRIOR/'received/adapter_model.safetensors'),
        export_manifest_sha256=common.sha(SOURCE/'manifest.json'),records_sha256=common.sha(SOURCE/'train.jsonl'),
        source='Preserved historical LIBERO export; real OopsieData test remains untouched.',episode_ids=ids,episodes=50,
        source_frames=total_frames,input_cfg=cfg.__dict__,image_counts=sizes,source_image_sha256=files,
        max_new_tokens=5120,do_sample=False,output_contract='Original whole-episode atomic JSON schema',
        source_teacher='gpt-6.1-sol',reference='Preserved teacher labels; agreement, not human-reference accuracy.',
        no_training=True,no_teacher_calls=True,training_id_overlap=[],
        limitations=['The original base-model commit and package lock were not supplied; the same declared base is pinned to the prior evaluation revision.',
            'Archived summaries omit raw predictions, so this reproduces metrics rather than exact old output bytes.',
            'Historical schema_valid checks field names/types, not complete timeline coverage; strict coverage is checked separately.'])
    immutable(RUN/'plan.json',plan)
    (RUN/'prompt.md').write_text('# Original student prompt\n\n'+__import__('prompt_short').SHORT_INSTRUCTIONS+'\n',encoding='utf-8')
    (RUN/'plan.md').write_text('# Native LIBERO reproduction\n\nEvaluate the exact 50 archived held-out IDs, disjoint from the adapter\'s 450 training IDs. Use the unchanged original whole-episode JSON instructions, two cameras, stride-three sampled images, all sampled telemetry and derived gripper events, 70 visual soft tokens per image, greedy decoding and a 5,120-token output limit.\n\nNo training, teacher API calls, or real OopsieData final-test evaluation. Outputs and readable Markdown conversions are saved in this new versioned run. Reproduce the historical metrics and independently validate full frame coverage.\n',encoding='utf-8')
    print(json.dumps(dict(episodes=50,frames=total_frames,input_images=sum(sizes.values()),training_overlap=0)),flush=True)


def timeline(value,eid,n):
    if not isinstance(value,dict) or value.get('episode_id')!=eid:raise ValueError('Wrong/missing episode ID')
    cursor=0;labels=[None]*n
    for seg in value.get('segments',[]):
        a,b,fail=seg.get('start_frame'),seg.get('end_frame'),seg.get('failure')
        if type(a) is not int or type(b) is not int or type(fail) is not bool:raise ValueError('Invalid boundary/label type')
        if a!=cursor or not a<b<=n:raise ValueError('Gap, overlap or out-of-range boundary')
        labels[a:b]=[fail]*(b-a);cursor=b
    if cursor!=n:raise ValueError('Incomplete episode coverage')
    return labels


def generate(batch_size=8):
    import torch
    import model as loader
    from transformers import StoppingCriteria,StoppingCriteriaList
    plan=common.read(RUN/'plan.json');recs=records();legacy=legacy_module()
    if common.sha(PRIOR/'received/adapter_model.safetensors')!=plan['adapter_sha256']:raise ValueError('Adapter changed')
    if common.sha(SOURCE/'train.jsonl')!=plan['records_sha256']:raise ValueError('Inputs changed')
    folder=RUN/'predictions';folder.mkdir(exist_ok=True)
    archived=[json.loads(line) for line in (PRIOR/'received/sft_v3_per_episode.jsonl').read_text().splitlines() if line.strip()]
    # Group by previously measured response length for throughput only: every
    # archived validation ID is retained, and these lengths are not model input.
    lengths={r['id']:r['n_tokens'] for r in archived}
    pending=sorted([eid for eid in plan['episode_ids'] if not (folder/f'{eid}.json').exists()],key=lambda eid:(lengths[eid],eid))
    if not pending:print('All 50 native predictions are already present.');return
    snapshot=common.read(PRIOR/'model_download.json')['snapshot']
    processor=loader.load_processor(snapshot);processor.image_processor.max_soft_tokens=70;processor.tokenizer.padding_side='left'
    loader.offload_ple=lambda model:None
    model=loader.load_model(base_id=snapshot,adapter_path=str(PRIOR/'received')).eval()
    from safetensors.torch import load_file
    saved=load_file(str(PRIOR/'received/adapter_model.safetensors'),device='cpu');params=dict(model.named_parameters())
    for name,value in saved.items():
        key=name.replace('.lora_A.weight','.lora_A.default.weight').replace('.lora_B.weight','.lora_B.default.weight')
        if key not in params or not torch.equal(params[key].detach().float().cpu(),value.float()):raise ValueError('Adapter load mismatch')
    del saved,params
    print('All 516 adapter tensors loaded exactly.',flush=True)
    transport.atomic_json(RUN/'runtime.json',dict(started_utc=now(),gpu=torch.cuda.get_device_name(),batch_size=batch_size,
        code_sha256=common.sha(Path(__file__)),base_revision=plan['base_revision'],adapter_tensors_matched=516,
        cache='default dynamic',quantization='NF4 double quantization, BF16 compute',per_layer_embedding_device='cuda'))
    start=time.monotonic()
    class Progress(StoppingCriteria):
        def __init__(self):self.step=0;self.started=time.monotonic()
        def __call__(self,input_ids,scores,**kwargs):
            self.step+=1
            if self.step%128==0:
                transport.atomic_json(RUN/'decoding_progress.json',dict(completed=len(list(folder.glob('D????.json'))),current_batch=group,generated_steps=self.step,batch_seconds=time.monotonic()-self.started,updated_utc=now()))
                print(f'Decoding batch: {self.step} token steps, {time.monotonic()-self.started:.1f}s',flush=True)
            return torch.zeros(input_ids.shape[0],dtype=torch.bool,device=input_ids.device)
    for offset in range(0,len(pending),batch_size):
        group=pending[offset:offset+batch_size];texts=[];image_batches=[]
        for eid in group:
            if (folder/f'{eid}.attempt.json').exists():raise ValueError('Unfinished attempt needs inspection: '+eid)
            immutable(folder/f'{eid}.attempt.json',dict(started_utc=now(),episode=eid))
            message=common.read(RUN/'requests'/f'{eid}.json')['user_messages']
            texts.append(native._prompt_text(processor,message));image_batches.append(native._load_images(message,str(SOURCE)))
        t0=time.monotonic();torch.cuda.reset_peak_memory_stats()
        inp=processor(text=texts,images=image_batches,padding=True,return_tensors='pt').to('cuda')
        inp['pixel_values']=inp['pixel_values'].to(torch.bfloat16);padded=int(inp['input_ids'].shape[1])
        eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos or [])
        if native.EOT_ID not in eos:eos.append(native.EOT_ID)
        print('Starting native batch '+', '.join(group)+f'; padded prompt {padded} tokens',flush=True)
        with torch.inference_mode():
            output=model.generate(**inp,max_new_tokens=5120,do_sample=False,eos_token_id=eos,stopping_criteria=StoppingCriteriaList([Progress()]))
        seconds=time.monotonic()-t0
        for i,eid in enumerate(group):
            tokens=output[i,padded:].tolist();stop=next((j+1 for j,t in enumerate(tokens) if t in eos),len(tokens));tokens=tokens[:stop]
            text=processor.tokenizer.decode(tokens,skip_special_tokens=True)
            value=legacy.parse_pred(text);info=native._task_info(recs[eid])
            row=dict(id=eid,text=text,n_tokens=len(tokens),n_prompt_tokens=int(inp['attention_mask'][i].sum()),hit_max=len(tokens)>=5120 and tokens[-1] not in eos,
                error=None,seconds=seconds/len(group),batch_size=len(group),batch_seconds=seconds,peak_gpu_gib=torch.cuda.max_memory_allocated()/1024**3,
                parsed=value is not None,schema_valid=legacy.schema_ok(value))
            try:timeline(value,eid,info['n_frames']);row['timeline_valid']=True
            except ValueError as error:row['timeline_valid']=False;row['timeline_error']=str(error)
            immutable(folder/f'{eid}.json',row)
            if value is not None:
                immutable(RUN/'parsed'/f'{eid}.json',value)
                if row['schema_valid']:
                    try:body=oopsie_markdown.render(value)
                    except (KeyError,TypeError,ValueError) as error:body='Readable conversion failed: '+str(error)+'\n\nSee the preserved native response.'
                    readable='# Derived readable conversion\n\nConverted from the preserved native JSON response; this was not a native Markdown generation.\n\n'+body
                    (RUN/'readable').mkdir(exist_ok=True);(RUN/'readable'/f'{eid}.md').write_text(readable,encoding='utf-8')
            print(eid+f': {len(tokens)} tokens; parsed={row["parsed"]}, schema={row["schema_valid"]}, timeline={row["timeline_valid"]}',flush=True)
        del inp,output
        transport.atomic_json(RUN/'progress.json',dict(completed=len(list(folder.glob('D????.json'))),expected=50,elapsed_seconds=time.monotonic()-start,updated_utc=now()))
        score()


def score():
    plan=common.read(RUN/'plan.json');recs=records();legacy=legacy_module();rows=[];strict=Counter();issues=[];per=[]
    for eid in plan['episode_ids']:
        path=RUN/'predictions'/f'{eid}.json'
        if not path.exists():continue
        prediction=common.read(path);teacher=legacy.teacher_info(recs[eid]);rows.append(legacy.score_episode(prediction,teacher))
        n=native._task_info(recs[eid])['n_frames'];truth=timeline(teacher['obj'],eid,n)
        try:
            if prediction['hit_max']:raise ValueError('Token cap reached')
            pred=timeline(legacy.parse_pred(prediction['text']),eid,n)
        except ValueError as error:pred=[None]*n;issues.append(dict(episode=eid,error=str(error)))
        c=binary_scoring.counts(pred,truth);strict.update(c);per.append(dict(episode=eid,metrics=binary_scoring.metrics(c)))
    if not rows:return
    actual=legacy.agg(rows);archived=common.read(PRIOR/'received/summary.json')['sft_v3']['all']
    result=dict(completed=len(rows),expected=50,legacy_metrics=actual,archived_metrics=archived,
        strict_complete_episodes=len(rows)-len(issues),strict_frame_metrics=binary_scoring.metrics(strict),
        issues=issues,per_episode=per,teacher='gpt-6.1-sol',test_is_original_adapter_holdout=True,real_oopsiedata_test_used=False)
    transport.atomic_json(RUN/'results.json',result)
    (RUN/'legacy_per_episode.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    lines=['# Gemma native LIBERO verification','',f'{len(rows)}/50 original held-out episodes completed. No training or teacher calls.','',
        'This restores the original whole-episode JSON output contract, sparse paired cameras, telemetry and derived gripper events. The earlier OopsieData test changed these conditions.','',
        '| Metric | Archived | Reproduced |','| --- | ---: | ---: |']
    for key in ['parse_rate','schema_valid_rate','fail_acc','fail_precision','fail_recall','fail_f1','frame_action_acc','boundary_f1_tol5','failure_iou','category_micro_f1']:
        a,b=archived.get(key),actual.get(key);fmt=lambda v:'N/A' if v is None else f'{100*v:.2f}%'
        lines.append(f'| {key} | {fmt(a)} | {fmt(b)} |')
    lines+=['',f'Strict complete episode timelines: {len(rows)-len(issues)}/{len(rows)}; valid-frame coverage after rejecting incomplete episode timelines: {100*result["strict_frame_metrics"]["coverage"]:.2f}%.','',
        'Episode-level detection F1 and mean temporal failure IoU are different metrics. Historical schema validity checked fields/types; the extra strict check validates the whole [0, source frame count) timeline. Teacher agreement is not human-ground-truth accuracy.','',
        'Native responses are preserved internally. [Readable annotations](readable/) are derived Markdown conversions, not native Markdown generations. Original base revision/package lock were not supplied; the same declared base and prior pinned revision are used.','']
    (RUN/'report.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','generate','score']);p.add_argument('--batch-size',type=int,default=8);a=p.parse_args()
    if a.command=='generate':generate(a.batch_size)
    else:globals()[a.command]()
