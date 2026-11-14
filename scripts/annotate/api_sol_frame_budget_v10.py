"""Sol-only frame-budget stress test; explicit run sends at most 32 requests.

Existing V7 labels are never model inputs. Adaptive JSON frame requests are
executed by a bounded controller, with all calls/evidence/costs retained.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import shutil
import time

import api_taxonomy_approach_v7 as baseline
import api_label_pilot as common
import api_frame_selection_windows_v1 as transport

OUT=common.ROOT/'outputs/sol_frame_budget_v10'
ARMS={'hz2':'2 Hz','hz1':'1 Hz','hz05':'0.5 Hz','hz025':'0.25 Hz',
      'uniform_cap':'Uniform at adaptive maximum budget','adaptive':'Adaptive from 0.5 Hz'}
STRIDES={'hz2':10,'hz1':20,'hz05':40,'hz025':80}
MODEL='gpt-6.1-sol'
MAX_OUTPUT=8192
RESERVE=.50
ADAPTIVE='''
## Optional evidence requests
Before returning the final annotation, you may request additional camera pairs
at specific source frames to resolve identity, missed short events, or boundaries.
Inspect the whole episode, not just suspected failures. Select before/after views
when useful; do not assume an interval is uneventful because its sparse endpoints
look similar. Do not invent details between supplied observations.
Return EITHER the final annotation object specified above OR exactly:
{"request_frames": [integer source indices], "reason": "brief evidence need"}.
Each request must contain 1 to 8 distinct, previously unseen indices from
available_frames. The controller supplies both cameras and telemetry at those
indices. There are at most two request rounds; after the second, return the final
annotation. You may finalize earlier when evidence is sufficient. Do not request
frames just to use the budget. The final annotation must cover every source frame,
and evidence citations may use any frames supplied in this conversation.
'''


def sampled(ep,arm):
    if arm=='adaptive': arm='hz05'
    if arm in STRIDES:
        return sorted(set(range(0,ep['n_frames'],STRIDES[arm]))|{ep['n_frames']-1})
    if arm!='uniform_cap': raise ValueError('Unknown arm')
    pool=ep['sampled_frames']; k=min(len(pool),len(sampled(ep,'hz05'))+16)
    return [pool[(i*(len(pool)-1)*2+(k-1))//(2*(k-1))] for i in range(k)]


def code_hashes():
    return {Path(m).name:common.digest(Path(m)) for m in
            (__file__,baseline.__file__,common.__file__,transport.__file__)}


def prepare():
    m=baseline.verify()
    OUT.mkdir(exist_ok=False)
    text=(baseline.OUT/'prompt.txt').read_text(encoding='utf-8')
    old='external/wrist pairs sampled every five source frames plus the final frame, with'
    assert text.count(old)==1
    text=text.replace(old,'external/wrist pairs at the explicitly listed sampled source frames, with')
    (OUT/'prompt.txt').write_text(text,encoding='utf-8')
    (OUT/'adaptive_prompt.txt').write_text(text+ADAPTIVE,encoding='utf-8')
    for ep in m['episodes']:
        shutil.copytree(baseline.OUT/ep['id'],OUT/ep['id'])
    common.write_json(OUT/'manifest.json',dict(episodes=m['episodes'],arms=ARMS,
        model=MODEL,reasoning='low',image_detail='high',max_output=MAX_OUTPUT,
        adaptive_rounds=2,additional_pairs_per_round=8,maximum_calls=32,
        reservation_per_call=RESERVE,total_reservation=16,code_hashes=code_hashes(),
        files={p.relative_to(OUT).as_posix():common.digest(p) for p in OUT.rglob('*') if p.is_file()},
        baseline_hashes={p.relative_to(baseline.OUT).as_posix():common.digest(p)
                         for p in baseline.OUT.rglob('*') if p.is_file()},
        authorization='User requested pushing Sol frame reduction and model-requested additional frames',
        limitation='Four previously reviewed development episodes; baseline agreement is not accuracy'))
    (OUT/'attempts').mkdir()
    print('Prepared 24 episode/arm jobs; at most 32 calls, $16 reservation ceiling')


def verify():
    m=common.load(OUT/'manifest.json')
    if m['code_hashes']!=code_hashes(): raise ValueError('Frozen code changed')
    for rel,digest in m['files'].items():
        if common.digest(OUT/rel)!=digest: raise ValueError('Frozen evidence changed')
    for rel,digest in m['baseline_hashes'].items():
        if common.digest(baseline.OUT/rel)!=digest: raise ValueError('V7 baseline changed')
    return m


def images(ep,frames):
    rows={r['frame']:r for r in ep['telemetry']}; parts=[]
    for f in frames:
        parts.append(dict(type='input_text',text=json.dumps(rows[f])+'; external camera then wrist camera'))
        for camera in ('agent','wrist'):
            data=base64.b64encode((OUT/ep['id']/f'{f:04d}_{camera}.jpg').read_bytes()).decode()
            parts.append(dict(type='input_image',detail='high',image_url='data:image/jpeg;base64,'+data))
    return parts


def request_frames(value,ep,seen,round_index):
    if set(value)!={'request_frames','reason'}: raise ValueError('Frame request fields')
    fs=value['request_frames']
    if round_index>=2: raise ValueError('Frame request rounds exhausted')
    if not isinstance(fs,list) or not 1<=len(fs)<=8: raise ValueError('Frame request budget')
    if any(type(f) is not int or f not in ep['sampled_frames'] or f in seen for f in fs):
        raise ValueError('Request must name unseen available frames')
    if len(set(fs))!=len(fs): raise ValueError('Duplicate request frames')
    if not isinstance(value['reason'],str) or not value['reason'].strip(): raise ValueError('Request reason')
    return sorted(fs)


def call(name,history,keys):
    slot=OUT/'attempts'/f'{name}.json'
    if slot.exists():
        r=common.load(slot)
        if r['status']=='returned': return json.loads((OUT/f'{name}_answer.txt').read_text(encoding='utf-8'))
        raise ValueError('Existing reservation; never resend '+name)
    r=dict(status='reserved',reserved_usd=RESERVE,generation_sent=False,started=time.time())
    with slot.open('x',encoding='utf-8') as f: json.dump(r,f)
    body=dict(model=MODEL,input=history,reasoning={'effort':'low'},max_output_tokens=MAX_OUTPUT,
              text={'format':{'type':'json_object'}},store=False,service_tier='default',truncation='disabled')
    # Store only a hash of the full payload, not duplicated image base64.
    r['payload_sha256']=transport.sha_bytes(json.dumps(body,sort_keys=True).encode())
    try:
        count=transport.post('https://api.openai.com/v1/responses/input_tokens','openai',
                             {k:body[k] for k in ('model','input','reasoning','text','truncation')},keys)
        common.write_json(OUT/f'{name}_count.json',count)
        n=count['input_tokens']
        if type(n) is not int or not 0<n<=80000: raise ValueError('Input token ceiling')
        r.update(input_count=n,preflight_allowance_usd=n*2/1e6)
        if n*4.5/1e6+MAX_OUTPUT*10/1e6>RESERVE: raise ValueError('Reservation insufficient')
        r.update(status='in_flight',generation_sent=True);transport.atomic_json(slot,r)
        print(name+': generating',flush=True)
        raw=transport.post('https://api.openai.com/v1/responses','openai',body,keys)
        raw=json.loads(transport.redact(json.dumps(raw),keys))
        common.write_json(OUT/f'{name}_raw.json',raw)
        r.update(transport.usage_cost('openai',raw))
        r['returned_model']=raw.get('model')
        answer,complete=transport.extract_answer('openai',raw)
        (OUT/f'{name}_answer.txt').write_text(answer,encoding='utf-8')
        if not complete: raise ValueError('Incomplete output; no retry')
        value=json.loads(answer)
        r['status']='returned'
        return value
    except Exception as e:
        r.update(status='stopped',error=transport.redact(str(e),keys)[:800])
        raise
    finally:
        r['elapsed_seconds']=round(time.time()-r['started'],2)
        transport.atomic_json(slot,r)


def job(ep,arm,keys):
    name=ep['id']+'_'+arm;result_path=OUT/f'{name}_result.json'
    if result_path.exists(): return common.load(result_path)
    frames=sampled(ep,arm);seen=set(frames)
    prompt=(OUT/('adaptive_prompt.txt' if arm=='adaptive' else 'prompt.txt')).read_text(encoding='utf-8')
    meta={'episode_id':ep['id'],**{k:ep[k] for k in ('task','n_frames','fps')},'sampled_frames':frames}
    if arm=='adaptive':meta.update(available_frames=ep['sampled_frames'],request_rounds_remaining=2)
    history=[dict(role='user',content=[dict(type='input_text',text=prompt+'\n'+json.dumps(meta))]+images(ep,frames))]
    result=dict(episode=ep['id'],arm=arm,initial_frames=frames,seen_frames=frames,requests=[],calls=[],status='pending')
    try:
        for round_index in range(3 if arm=='adaptive' else 1):
            call_id=f'{name}_{round_index}';result['calls'].append(call_id)
            value=call(call_id,history,keys)
            if isinstance(value,dict) and 'request_frames' in value:
                if arm!='adaptive':raise ValueError('Static arm requested frames')
                extra=request_frames(value,ep,seen,round_index)
                result['requests'].append(dict(round=round_index+1,frames=extra,reason=value['reason']))
                seen.update(extra);result['seen_frames']=sorted(seen)
                # Explicit application-level request/reply conversation; not hidden tool calls.
                history.append(dict(role='assistant',content=json.dumps(value)))
                follow=dict(supplied_frames=extra,all_seen_frames=sorted(seen),request_rounds_remaining=1-round_index)
                history.append(dict(role='user',content=[dict(type='input_text',text=json.dumps(follow)+
                    ('\nNo request rounds remain. Return the final annotation now.' if round_index==1 else ''))]+images(ep,extra)))
                common.write_json(OUT/f'{name}_trace.json',result)
                continue
            baseline.validate(value,{**ep,'sampled_frames':sorted(seen)})
            common.write_json(OUT/f'{name}_annotation.json',value)
            result.update(status='validated',final_call=call_id)
            break
        else: raise ValueError('No final annotation')
    except Exception as e:
        result.update(status='stopped',error=transport.redact(str(e),keys)[:800])
    common.write_json(result_path,result)
    print(name+': '+result['status'],flush=True)
    return result


def report():
    results=[common.load(p) for p in sorted(OUT.glob('*_result.json'))]
    records=[common.load(p) for p in sorted((OUT/'attempts').glob('*.json'))]
    for r in results:
        calls=[common.load(OUT/'attempts'/f'{c}.json') for c in r['calls'] if (OUT/'attempts'/f'{c}.json').exists()]
        r['generation_estimate_usd']=sum(c.get('generation_estimate_usd',0) for c in calls)
        r['preflight_allowance_usd']=sum(c.get('preflight_allowance_usd',0) for c in calls)
        r['cached_tokens']=sum(c.get('cached_tokens',0) for c in calls)
        r['unknown_reservations_usd']=sum(RESERVE for c in calls if c.get('generation_sent') and 'generation_estimate_usd' not in c)
    summary=dict(planned_jobs=24,finished_jobs=len(results),validated=sum(r['status']=='validated' for r in results),
        calls=len(records),generation_estimate_usd=sum(c.get('generation_estimate_usd',0) for c in records),
        preflight_allowance_usd=sum(c.get('preflight_allowance_usd',0) for c in records),
        unknown_reservations_usd=sum(RESERVE for c in records if c.get('generation_sent') and 'generation_estimate_usd' not in c),results=results)
    common.write_json(OUT/'summary.json',summary)
    return summary


def run():
    m=verify()
    if date.today()>date(2026,12,31):raise ValueError('Recheck pricing')
    keys=common.credentials()
    # Independent episode/arm jobs overlap; each adaptive conversation is sequential.
    tasks=[(ep,arm) for arm in ARMS for ep in m['episodes']]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(job,ep,arm,keys) for ep,arm in tasks]
        for f in futures:f.result()
    report()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','verify','run','report'))
    args=p.parse_args();globals()[args.command]()
