"""Frozen, bounded third-party text-judge experiments; no automatic retries."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import time

import annotation_runtime as io
from text_score_contract import fact_agreement, dimension_agreement

MODELS = {'flash': ('gemini-3.8-flash', .75, .075, 3.75, .12),
          'argon': ('gemini-4-argon', 2., .1, 10., .26)}
RELATIONS = {'equivalent', 'compatible_difference', 'contradiction', 'unrelated', 'unresolved'}


def prepare(out, modes=('scalar','facts'), batch_size=8, selected_models=None, orders=('ab','ba'), pair_ids=None):
    folder = out/'judges'
    if folder.exists(): raise ValueError('Fresh judge directory required')
    folder.mkdir()
    rows = io.load(out/'corpus.json')['pairs']
    if pair_ids:
        if not set(pair_ids)<= {r['pair_id'] for r in rows}:raise ValueError('Unknown pair IDs')
        rows=[r for r in rows if r['pair_id'] in pair_ids]
    if batch_size<1:raise ValueError('Positive batch size required')
    jobs = []
    for mode in modes:
        shutil.copyfile(Path(__file__).parent/'prompts/text_evaluation'/f'{mode}.txt',folder/f'{mode}.txt')
        batches = [rows[i:i+batch_size] for i in range(0,len(rows),batch_size)]
        for model in (selected_models or MODELS):
            for order in orders:
                for index,batch in enumerate(batches):
                    payload = []
                    for row in batch:
                        context = dict(row['context'])
                        if order=='ba' and 'identity_a' in context:
                            context['identity_a'],context['identity_b']=context['identity_b'],context['identity_a']
                        payload.append(dict(pair_id=row['pair_id'],
                            description_a=row['left' if order=='ab' else 'right'],
                            description_b=row['right' if order=='ab' else 'left'],context=context))
                    name=f'{model}_{mode}_{order}_{index:02d}'
                    body={'systemInstruction':{'parts':[{'text':(folder/f'{mode}.txt').read_text(encoding='utf-8')}]},
                          'contents':[{'role':'user','parts':[{'text':json.dumps({'pairs':payload})}]}],
                          'generationConfig':{'temperature':0,'maxOutputTokens':16384,
                              'thinkingConfig':{'thinkingLevel':'medium'},'responseMimeType':'application/json'}}
                    io.write_json(folder/f'{name}_request.json',body)
                    jobs.append(dict(name=name,model=model,mode=mode,order=order,ids=[r['pair_id'] for r in batch]))
    files={p.name:io.digest(p) for p in folder.iterdir()}
    shutil.copyfile(__file__,folder/'runner_frozen.py')
    files['runner_frozen.py']=io.digest(folder/'runner_frozen.py')
    shutil.copyfile(Path(__file__).parent/'text_score_contract.py',folder/'text_score_contract_frozen.py')
    files['text_score_contract_frozen.py']=io.digest(folder/'text_score_contract_frozen.py')
    io.write_json(folder/'manifest.json',dict(corpus_sha256=io.digest(out/'corpus.json'),files=files,jobs=jobs,
        models=MODELS,max_reservation_usd=sum(MODELS[j['model']][4] for j in jobs),
        rates_source='https://ai.google.dev/gemini-api/docs/pricing',
        limitation='Temperature zero does not guarantee deterministic generation. AB/BA differences measure order plus sampling sensitivity. Authored controls are not video ground truth.'))
    print('Prepared',len(jobs),'calls; reservation ceiling',sum(MODELS[j['model']][4] for j in jobs))


def validate(answer,job):
    if set(answer)!= {'pairs'} or not isinstance(answer['pairs'],list): raise ValueError('Invalid root')
    items=answer['pairs']
    if len(items)!=len(job['ids']) or {x['pair_id'] for x in items}!=set(job['ids']): raise ValueError('Missing/duplicate/unexpected IDs')
    for item in items:
        if job['mode']=='scalar':
            if set(item)!= {'pair_id','relation','score','rationale'}: raise ValueError('Invalid scalar fields')
            if item['relation'] not in RELATIONS or type(item['score']) is not int or not 0<=item['score']<=100: raise ValueError('Invalid score/relation')
        elif job['mode']=='facts':
            if set(item)!= {'pair_id','facts_a','facts_b','alignments','rationale'}: raise ValueError('Invalid fact fields')
            for key in ('facts_a','facts_b'):
                if any(set(f)!= {'id','claim'} or not isinstance(f['id'],str) or not isinstance(f['claim'],str) for f in item[key]): raise ValueError('Invalid fact')
            if any(set(a)!= {'a_id','b_id','relation'} for a in item['alignments']): raise ValueError('Invalid alignment')
            item['computed']=fact_agreement(item)
        else:
            if set(item)!= {'pair_id','dimensions','overall_relation','rationale'} or item['overall_relation'] not in RELATIONS:
                raise ValueError('Invalid dimension result')
            item['computed']=dimension_agreement(item)
            # Preserve the judge's global relation independently, including unrelated.
            item['computed']['judge_overall_relation']=item['overall_relation']
        if not isinstance(item['rationale'],str): raise ValueError('Invalid rationale')
    return items


def run(out):
    folder=out/'judges'; manifest=io.load(folder/'manifest.json')
    if io.digest(out/'corpus.json')!=manifest['corpus_sha256']: raise ValueError('Corpus changed')
    if io.digest(__file__)!=manifest['files']['runner_frozen.py']: raise ValueError('Runner changed after preparation')
    contract_hash=manifest['files'].get('text_score_contract_frozen.py')
    if contract_hash and io.digest(Path(__file__).parent/'text_score_contract.py')!=contract_hash:
        raise ValueError('Score contract changed after preparation')
    for name,digest in manifest['files'].items():
        if io.digest(folder/name)!=digest: raise ValueError('Frozen inputs changed')
    keys=io.credentials()
    if 'gemini' not in keys: raise ValueError('Missing Google credential')
    def execute(job):
        name=job['name']; attempt=folder/f'{name}_attempt.json'
        if attempt.exists(): return
        model,inp_rate,cache_rate,out_rate,reserve=MODELS[job['model']]
        record=dict(job=job,reserved_usd=reserve,status='reserved',started_unix=time.time())
        # Exclusive reservation: interrupted or failed requests are never resent.
        with attempt.open('x',encoding='utf-8') as f: json.dump(record,f)
        try:
            body=io.load(folder/f'{name}_request.json')
            count=io.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:countTokens','gemini',
                {'generateContentRequest':dict(model=f'models/{model}',**body)},keys)
            io.write_json(folder/f'{name}_count.json',count)
            if count['totalTokens']>20000: raise ValueError('Input ceiling exceeded')
            raw=io.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent','gemini',body,keys)
            io.write_json(folder/f'{name}_raw.json',raw)
            u=raw.get('usageMetadata',{}); inp=u.get('promptTokenCount',0); cached=u.get('cachedContentTokenCount',0)
            output=u.get('candidatesTokenCount',0)+u.get('thoughtsTokenCount',0)
            record['generation_estimate_usd']=((inp-cached)*inp_rate+cached*cache_rate+output*out_rate)/1e6
            record['usage']=u
            answer,complete=io.extract_answer('gemini',raw)
            (folder/f'{name}_answer.txt').write_text(answer,encoding='utf-8')
            if not complete: raise ValueError('Incomplete generation')
            items=validate(json.loads(answer),job)
            io.write_json(folder/f'{name}_result.json',dict(job=job,pairs=items))
            record['status']='valid'
        except Exception as e:
            record['status']='error';record['error']=io.redact(str(e),keys)
            if isinstance(e,io.APIHTTPError): record['error_details']=e.details
        record['seconds']=time.time()-record['started_unix']
        io.write_json(attempt,record)
        print(name,record['status'],record.get('error',''),round(record.get('generation_estimate_usd',0),4),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(execute,manifest['jobs']))
    attempts=[io.load(folder/f"{j['name']}_attempt.json") for j in manifest['jobs']]
    io.write_json(folder/'summary.json',dict(valid=sum(a['status']=='valid' for a in attempts),total=len(attempts),
        generation_estimate_usd=sum(a.get('generation_estimate_usd',0) for a in attempts),attempts=attempts))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','run'));p.add_argument('--out',type=Path,required=True)
    p.add_argument('--modes',nargs='+',choices=('scalar','facts','slots'),default=['scalar','facts'])
    p.add_argument('--batch-size',type=int,default=8)
    p.add_argument('--models',nargs='+',choices=MODELS)
    p.add_argument('--orders',nargs='+',choices=('ab','ba'),default=['ab','ba'])
    p.add_argument('--pair-ids',nargs='+')
    a=p.parse_args();prepare(a.out,a.modes,a.batch_size,a.models,a.orders,a.pair_ids) if a.command=='prepare' else run(a.out)
