"""Execute the approved full-data first wave without automatic retries."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO/'outputs/oopsie_distillation_full_v1'


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def approval():
    plan=read(ROOT/'submission_plan.json');a=read(ROOT/'submission_approval.json')
    if a.get('approved') is not True or a.get('plan_sha256')!=digest(ROOT/'submission_plan.json'):
        raise ValueError('No matching user approval for full-data submission')
    if plan['tacc_su_ceiling']>plan['authorized_tacc_su_cap']:raise ValueError('Budget exceeded')
    for rel,expected in plan['code_sha256'].items():
        if digest(REPO/rel)!=expected:raise ValueError('Execution code changed: '+rel)
    if digest(ROOT/'study.json')!=plan['study_sha256']:raise ValueError('Frozen study changed')
    folder=ROOT/plan['selected_adapter']
    for name,key in [('records.jsonl','records_sha256'),('adapter.json','adapter_sha256')]:
        if digest(folder/name)!=plan[key]:raise ValueError('Frozen evidence changed')
    return plan,folder


def verify_data():
    import oopsie_common as common
    import qwen_recipe_runner as runner
    from oopsie_bulk_v8_1 import write_once
    plan,folder=approval();s,source,rows=runner.load(folder)
    if len({r['episode'] for r in rows if r['task']=='binary' and r['split']=='train'})!=400:
        raise ValueError('All 400 training episodes must be present')
    inventory=read(ROOT/'image_inventory.json');started=time.monotonic()
    for i,item in enumerate(inventory['files']):
        path=common.inside(REPO,item['path'])
        if path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:
            raise ValueError('Evidence integrity failed: '+item['path'])
        if (i+1)%10000==0:print(json.dumps(dict(verified_images=i+1,total=len(inventory['files']))),flush=True)
    for e in s['episodes']:
        if e['split']=='test':continue
        native=source/'traces'/f"{e['episode']}_sol_r01"/'annotation.md'
        if digest(native)!=e['annotation_sha256']:raise ValueError('Teacher reference changed')
    write_once(ROOT/'tacc_data_ready.json',dict(verified_images=len(inventory['files']),bytes=inventory['bytes'],
        plan_sha256=digest(ROOT/'submission_plan.json'),seconds=time.monotonic()-started,test_images_staged=False))


def timing():
    import torch
    import oopsie_common as common
    import qwen_recipe_runner as runner
    import qwen_oopsie_sft as core
    from oopsie_bulk_v8_1 import write_once
    plan,folder=approval()
    if not (ROOT/'tacc_data_ready.json').exists():raise ValueError('Data has not been verified')
    audit=read(folder/'token_audit.json')
    if audit['overlength']:raise ValueError('Overlength training records')
    s,source,rows=runner.load(folder);cfg=runner.cfg_for(s);processor=core.processor_for(cfg)
    model=core.load_model(cfg,trainable=True);model.train()
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=cfg['learning_rate'])
    binary=[r for r in rows if r['split']=='train' and r['task']=='binary']
    ranked=sorted(((runner.estimated_tokens(processor,source,r),r) for r in binary),key=lambda x:x[0])
    samples=[ranked[len(ranked)//2][1],ranked[-1][1]]
    results=[]
    for row in samples:
        optimizer.zero_grad(set_to_none=True);torch.cuda.reset_peak_memory_stats();started=time.monotonic()
        batch=core.encode_train(processor,source,row,cfg['max_length']);batch={k:v.to('cuda') for k,v in batch.items()}
        with torch.autocast('cuda',dtype=torch.bfloat16):loss,count=core.sft_loss(model,batch)
        (loss/count).backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1,error_if_nonfinite=True)
        optimizer.step();torch.cuda.synchronize()
        results.append(dict(window=row['id'],seconds=time.monotonic()-started,
            peak_gpu_gib=torch.cuda.max_memory_allocated()/1024**3,loss=float(loss.detach())/count))
        del batch,loss
        print(json.dumps(results[-1]),flush=True)
    # Timing updates are discarded, never reused as a recipe checkpoint.
    write_once(ROOT/'tacc_timing_ready.json',dict(gpu=torch.cuda.get_device_name(),results=results,
        plan_sha256=digest(ROOT/'submission_plan.json'),temporary_updates_discarded=True))


def run(recipe):
    import oopsie_common as common
    import annotation_runtime as transport
    import qwen_recipe_runner as runner
    import score_recipe_suite as scoring
    from oopsie_bulk_v8_1 import write_once
    plan,folder=approval()
    if recipe not in ['base']+plan['training_recipes']:raise ValueError('Recipe outside approved scope')
    for marker in ('tacc_setup_ready.json','tacc_data_ready.json','tacc_timing_ready.json'):
        if not (ROOT/marker).exists():raise ValueError('Missing readiness gate: '+marker)
    states=ROOT/'arm_states';states.mkdir(exist_ok=True);path=states/(recipe+'.json')
    if path.exists():raise ValueError('Existing run: refusing an automatic duplicate/restart')
    state=dict(recipe=recipe,status='running',started_utc=datetime.now(timezone.utc).isoformat(),
        plan_sha256=digest(ROOT/'submission_plan.json'))
    write_once(path,state)
    try:
        adapter=None
        if recipe!='base':
            result=runner.train(folder,recipe,ROOT/'runs'/recipe,updates=plan['optimizer_updates'],max_hours=plan['train_max_hours'])
            state['training']=result;adapter=Path(result['adapter'])
            transport.atomic_json(path,state)
        # Separate model lifetimes: release the trained GPU model before loading
        # the frozen base plus the saved adapter for evaluation.
        import gc,torch
        gc.collect();torch.cuda.empty_cache()
        generated=runner.generate(folder,ROOT/'predictions'/recipe,adapter=adapter,split='development',
            max_hours=1.75 if recipe=='base' else plan['development_max_hours'])
        scored=scoring.score(folder,ROOT/'predictions'/recipe)
        write_once(ROOT/'arm_scores'/(recipe+'.json'),scored)
        scores={p.stem:common.read(p) for p in (ROOT/'arm_scores').glob('*.json')}
        scoring.write_report(ROOT,scores)
        state.update(status='completed' if generated['complete'] and (recipe=='base' or state['training']['completed_schedule']) else 'time_capped',generation=generated)
    except Exception as exc:
        state.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
    finally:
        state['finished_utc']=datetime.now(timezone.utc).isoformat();transport.atomic_json(path,state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['check-approval','verify-data','timing','run']);p.add_argument('--recipe');a=p.parse_args()
    if a.command=='check-approval':approval();print('Approved full-data plan verified.')
    elif a.command=='verify-data':verify_data()
    elif a.command=='timing':timing()
    else:run(a.recipe)
