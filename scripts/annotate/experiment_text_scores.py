"""Freeze text-scoring controls and current descriptions; compare cached local models."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
import math
from pathlib import Path
import shutil
import time

import annotation_runtime as io
from text_score_contract import anchored_similarity

LOCAL_MODELS = {
    'sts_distil': ('cross-encoder/stsb-distilroberta-base', 'sts'),
    'sts_large': ('cross-encoder/stsb-roberta-large', 'sts'),
    'mpnet': ('sentence-transformers/paraphrase-mpnet-base-v2', 'embedding'),
    'nli': ('cross-encoder/nli-deberta-v3-base', 'nli'),
    'paws': ('domenicrosati/deberta-v3-large-finetuned-paws-paraphrase-detector', 'paraphrase'),
}


def controls():
    a = 'The robot grasps butter_1 and establishes control of butter_1.'
    cases = [
        ('identical', a, a, 'equivalent'),
        ('acquisition_paraphrase', a, 'The robot takes hold of butter_1 and gains control of butter_1.', 'equivalent'),
        ('release_paraphrase', 'Butter_1 separates from the gripper inside basket_1.', 'The gripper releases butter_1 inside basket_1.', 'equivalent'),
        ('alignment_paraphrase', 'The robot reaches toward butter_1 and aligns the gripper around butter_1.', 'The robot approaches butter_1 and positions its gripper around butter_1.', 'equivalent'),
        ('verbose_paraphrase', 'The robot transports butter_1 toward basket_1 while retaining control.', 'The robot moves butter_1 in the direction of basket_1, keeping butter_1 under its control throughout that movement.', 'equivalent'),
        ('non_temporal_reordering', 'The gripper is open. Butter_1 remains supported in basket_1.', 'Butter_1 remains supported in basket_1. The gripper is open.', 'equivalent'),
        ('case_whitespace', a, 'THE ROBOT GRASPS butter_1 AND ESTABLISHES CONTROL OF butter_1.', 'equivalent'),
        ('acquisition_negation', a, 'The robot attempts to grasp butter_1 but does not establish control of butter_1.', 'contradiction'),
        ('retention_reversal', 'The robot transports butter_1; butter_1 remains under gripper control.', 'The robot transports butter_1; butter_1 slips out of the gripper.', 'contradiction'),
        ('release_reversal', 'Butter_1 separates from the gripper.', 'Butter_1 remains retained by the gripper and does not separate.', 'contradiction'),
        ('different_product', 'The robot acquires butter_1.', 'The robot acquires orange_juice_1.', 'compatible_difference'),
        ('destination_inside_outside', 'Butter_1 is placed inside basket_1.', 'Butter_1 is placed outside basket_1.', 'contradiction'),
        ('actor_role', 'The robot pushes basket_1.', 'Basket_1 pushes the robot.', 'compatible_difference'),
        ('action_order', 'The robot opens drawer_1 before acquiring butter_1.', 'The robot acquires butter_1 before opening drawer_1.', 'contradiction'),
        ('uncertainty_erased', 'Acquisition of butter_1 is provisional because the contact region is hidden.', 'Acquisition of butter_1 is confirmed without uncertainty.', 'contradiction'),
        ('missing_collision', 'The robot transports butter_1 and contact displaces basket_1.', 'The robot transports butter_1.', 'compatible_difference'),
        ('missing_release', 'The robot transports butter_1 into basket_1 and establishes separation.', 'The robot transports butter_1 into basket_1.', 'compatible_difference'),
        ('extra_tilt_detail', 'The robot lifts butter_1.', 'The robot lifts butter_1 with a slight tilt.', 'compatible_difference'),
        ('missing_task_mismatch', 'The robot grasps orange_juice_1. Orange_juice_1 is not the requested tomato sauce.', 'The robot grasps orange_juice_1.', 'compatible_difference'),
        ('unrelated', 'Butter_1 separates from the robot gripper.', 'A person writes an email on a laptop in another room.', 'unrelated'),
        ('buried_result_negation', 'The robot reaches, closes the fingers, acquires butter_1, transports it to basket_1, and opens the gripper. Butter_1 separates.', 'The robot reaches, closes the fingers, acquires butter_1, transports it to basket_1, and opens the gripper. Butter_1 does not separate.', 'contradiction'),
        ('attempt_vs_achievement', 'The robot tries to close drawer_1, but drawer_1 does not move.', 'The robot closes drawer_1 completely.', 'contradiction'),
        ('quantifier', 'Butter_1 stays held throughout transport.', 'Butter_1 drops once during transport.', 'contradiction'),
        ('physical_vs_task_success', 'The robot acquires bottle_1, which is the wrong object for the task.', 'The robot acquires bottle_1, which is the correct object for the task.', 'contradiction'),
        ('known_alias', 'The robot acquires butter_1.', 'The robot acquires carton_1.', 'equivalent'),
        ('unresolved_alias', 'The robot acquires object_1.', 'The robot acquires object_2.', 'unresolved'),
    ]
    rows = [dict(pair_id=f'c{i+1:03d}', name=name, kind='control', left=a, right=b,
                 expected_relation=relation, context={}) for i,(name,a,b,relation) in enumerate(cases)]
    rows[-2]['context'] = {'shared_aliases': {'butter_1': 'the same butter package', 'carton_1': 'the same butter package'}}
    rows[-1]['context'] = {'identity_note': 'The two local identifiers have no established mapping; they may or may not refer to the same physical object.'}
    return rows


def prepare(viewer, out):
    if out.exists(): raise ValueError('Fresh experiment directory required')
    out.mkdir(parents=True)
    data = io.load(viewer/'data.json')
    shutil.copyfile(viewer/'data.json', out/'viewer_data.json')
    shutil.copyfile(viewer/'text_similarity.json', out/'original_text_similarity.json')
    pairs, seen = controls(), set()
    real = []
    for ep in data['episodes']:
        annotations = ep['versions'][data['default_run']]
        for a in annotations['openai']['segments']:
            for b in annotations['gemini']['segments']:
                start, end = max(a['start_frame'], b['start_frame']), min(a['end_frame'], b['end_frame'])
                key = (ep['id'], a['what_happened'], b['what_happened'])
                if start >= end or key in seen: continue
                seen.add(key)
                real.append(dict(pair_id=f'r{len(real)+1:03d}', kind='real', name=ep['id'],
                    episode=ep['id'], start_frame=start, end_frame=end,
                    left=a['what_happened'], right=b['what_happened'],
                    context={'task':ep['task'], 'identity_a': annotations['openai']['identity_check'],
                             'identity_b': annotations['gemini']['identity_check']}))
    texts = list(dict.fromkeys(r['left'] for r in real))[:7]
    for i,t in enumerate(texts):
        pairs.append(dict(pair_id=f's{i+1:03d}', kind='control', name='real_text_self',
                          left=t,right=t,expected_relation='equivalent',context={}))
    pairs += real
    io.write_json(out/'corpus.json', dict(prepared_utc=datetime.now(timezone.utc).isoformat(),
        annotation_manifest_sha256=data['annotation_manifest_sha256'], pairs=pairs,
        controls=sum(p['kind']=='control' for p in pairs), real_pairs=len(real),
        limitation='Authored semantic controls are not human-labeled video ground truth. Real pairs have no acceptance labels. Local scorers read text only; judges also receive the stated context.'))
    print('Frozen corpus:',len(pairs),'pairs;',len(real),'real pairs;',sum(p['kind']=='control' for p in pairs),'controls')


def local(out, key):
    import numpy as np
    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer
    from huggingface_hub import try_to_load_from_cache
    torch.set_num_threads(4)
    manifest=io.load(out/'corpus.json'); rows=manifest['pairs']
    ident,kind=LOCAL_MODELS[key]; started=time.time()
    texts=sorted({r[f] for r in rows for f in ('left','right')})
    pairs=[(r['left'],r['right']) for r in rows]
    self_scores={}
    if kind=='embedding':
        model=SentenceTransformer(ident,device='cpu',local_files_only=True)
        if any(len(model.tokenizer.encode(t))>model.max_seq_length for t in texts): raise ValueError('Refusing truncation')
        vectors=model.encode(texts,normalize_embeddings=True,batch_size=16,show_progress_bar=False)
        index={t:i for i,t in enumerate(texts)}
        raw=[float(vectors[index[a]]@vectors[index[b]]) for a,b in pairs]
        reverse=list(raw)
        self_scores={t:float(vectors[index[t]]@vectors[index[t]]) for t in texts}
        extras=[{} for _ in rows]
    else:
        model=CrossEncoder(ident,device='cpu',local_files_only=True)
        requests=pairs+[(b,a) for a,b in pairs]+[(t,t) for t in texts]
        limit=min(model.max_seq_length or 512,model.tokenizer.model_max_length)
        if any(len(model.tokenizer.encode(a,b))>limit for a,b in requests): raise ValueError('Refusing truncation')
        opts={'activation_fn':torch.nn.Softmax(dim=1)} if kind in ('nli','paraphrase') else {}
        pred=model.predict(requests,batch_size=8,show_progress_bar=False,**opts)
        n=len(rows)
        if kind in ('nli','paraphrase'):
            raw=[float(x[1]) for x in pred[:n]];reverse=[float(x[1]) for x in pred[n:2*n]]
            self_scores={t:float(x[1]) for t,x in zip(texts,pred[2*n:])}
            extras=[dict(contradiction_ab=float(pred[i][0]),contradiction_ba=float(pred[n+i][0])) for i in range(n)] if kind=='nli' else [{} for _ in rows]
        else:
            raw=list(map(float,pred[:n]));reverse=list(map(float,pred[n:2*n]))
            self_scores=dict(zip(texts,map(float,pred[2*n:])));extras=[{} for _ in rows]
    scored=[]
    for row,a,b,extra in zip(rows,raw,reverse,extras):
        score=(a+b)/2
        denom=math.sqrt(max(0,self_scores[row['left']]*self_scores[row['right']]))
        ratio=score/denom if denom else None
        scored.append(dict(**row,raw_score=score,ab=a,ba=b,
            anchored_score=anchored_similarity(row['left'],row['right'],score),
            self_normalized_unclipped=ratio,**extra))
    config=try_to_load_from_cache(ident,'config.json')
    io.write_json(out/f'local_{key}.json',dict(model=ident,kind=kind,
        corpus_sha256=io.digest(out/'corpus.json'), code_sha256=io.digest(Path(__file__)),
        revision=Path(config).parent.name if isinstance(config,str) else None,
        packages={p:version(p) for p in ('torch','sentence-transformers','transformers')},
        seconds=round(time.time()-started,2),self_scores=self_scores,pairs=scored,
        limitation='Raw scores are learned predictions or cosine, not calibrated robot-semantic acceptance probabilities. Identity anchoring is an explicit score contract, not learned calibration.'))
    positives=[r['raw_score'] for r in scored if r.get('expected_relation')=='equivalent' and r['left']!=r['right'] and not r['context']]
    negatives=[r['raw_score'] for r in scored if r.get('expected_relation')=='contradiction']
    selfs=[r['raw_score'] for r in scored if r['left']==r['right']]
    print(key,'self range',min(selfs),max(selfs),'nonidentical equivalence min',min(positives),
          'contradiction max',max(negatives),'self-normalized scores >1',sum(r['self_normalized_unclipped'] is not None and r['self_normalized_unclipped']>1+1e-6 for r in scored),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('prepare','local'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--viewer',type=Path)
    p.add_argument('--model',choices=LOCAL_MODELS)
    args=p.parse_args()
    prepare(args.viewer,args.out) if args.command=='prepare' else local(args.out,args.model)
