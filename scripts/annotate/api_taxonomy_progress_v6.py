"""Frozen eight-call categorical pilot. Explicit run command sends paid requests.

Reuses established credential/HTTP/usage helpers; never modifies older runners.
No retries. Unknown costs retain full reservations. No reference labels in input.
"""
import argparse
import base64
from datetime import date
import html
import json
from pathlib import Path
import shutil
import time

import api_taxonomy_pilot_v3 as baseline
import api_label_pilot as common
import api_frame_selection_windows_v1 as transport

ROOT = common.ROOT
OUT = ROOT / 'outputs/taxonomy_progress_v6'
PRIOR = ROOT / 'outputs/frame_selection_semantic_v2'
PROMPT = ROOT / 'scripts/annotate/prompts/failure_taxonomy_progress_v6.txt'
IDS = ('R001', 'R002', 'R003', 'R004')
MODELS = dict(common.MODELS)
MAX_INPUT, MAX_OUTPUT, RESERVE = 80000, 8192, .50
CATEGORIES = set(common.TAXONOMY) | {'sudden_episode_termination'}


def settings():
    return dict(models=MODELS, max_input=MAX_INPUT, max_output=MAX_OUTPUT,
                reservation_per_call=RESERVE, total_reservation=4.0,
                sample_stride=5, reasoning='low', gemini_media_resolution='MEDIA_RESOLUTION_LOW',
                retries=0, price_checked='2026-10-05', price_expiry='2026-12-31',
                pricing_sources=['https://developers.openai.com/api/docs/models/gpt-6.1-sol',
                                 'https://ai.google.dev/gemini-api/docs/pricing'],
                rates=transport.settings()['rates_per_million'])


def code_hashes():
    return {p.name: common.digest(p) for p in
            (Path(__file__), Path(common.__file__), Path(transport.__file__), Path(baseline.__file__),
             ROOT/'scripts/annotate/prompts/identity_v2/progress_failure.md',
             ROOT/'scripts/annotate/prompts/failure_taxonomy_v2.txt')}


def prepare():
    OUT.mkdir(exist_ok=False)
    shutil.copyfile(PROMPT, OUT / 'prompt.txt')
    episodes = []
    for eid in IDS:
        old = common.load(PRIOR / eid / 'input.json')
        frames = sorted(set(range(0, old['n_frames'], 5)) | {old['n_frames']-1})
        assert old['fps'] == 20 and frames == old['pool'] and len(frames) <= 80
        for name, expected in old['source_sha256'].items():
            assert common.digest(common.SOURCE / eid / name) == expected
        ep = {k: old[k] for k in ('id', 'task', 'n_frames', 'fps', 'source_sha256')}
        ep['sampled_frames'] = frames
        ep['telemetry'] = [{k: row[k] for k in
                            ('frame', 'seconds', 'eef_xyz_m', 'finger_qpos_m', 'gripper_command')}
                           for row in old['telemetry'] if row['frame'] in frames]
        assert [r['frame'] for r in ep['telemetry']] == frames
        (OUT / eid).mkdir()
        for frame in frames:
            for camera in ('agent', 'wrist'):
                name = f'{frame:04d}_{camera}.jpg'
                shutil.copyfile(PRIOR / eid / 'images' / name, OUT / eid / name)
        common.write_json(OUT / eid / 'input.json', ep)
        episodes.append(ep)
    manifest = dict(version='progress_v6', settings=settings(), code_hashes=code_hashes(),
                    authorization='User approved the observable progress definition and examples and requested rerunning VLM labeling',
                    episodes=episodes,
                    limitation='Previously inspected development episodes; no independent accuracy claims.',
                    files={p.relative_to(OUT).as_posix(): common.digest(p)
                           for p in sorted(OUT.rglob('*')) if p.is_file()})
    common.write_json(OUT / 'manifest.json', manifest)
    report()
    print('Prepared eight calls, maximum reserved estimate $4.00')


def verify():
    m = common.load(OUT / 'manifest.json')
    if m['settings'] != settings() or m['code_hashes'] != code_hashes():
        raise ValueError('Frozen settings/code changed')
    if [e['id'] for e in m['episodes']] != list(IDS):
        raise ValueError('Episode matrix changed')
    for name, expected in m['files'].items():
        p = (OUT / name).resolve()
        if not p.is_relative_to(OUT.resolve()) or common.digest(p) != expected:
            raise ValueError('Frozen input changed')
    return m


def payload(provider, ep):
    text = (OUT / 'prompt.txt').read_text(encoding='utf-8') + '\n' + json.dumps(
        {'episode_id': ep['id'], **{k: ep[k] for k in ('task', 'n_frames', 'fps', 'sampled_frames')}})
    parts = [{'type': 'input_text', 'text': text}] if provider == 'openai' else [{'text': text}]
    for row in ep['telemetry']:
        caption = json.dumps(row) + '; external camera then wrist camera'
        parts.append({'type': 'input_text', 'text': caption} if provider == 'openai' else {'text': caption})
        for camera in ('agent', 'wrist'):
            p = OUT / ep['id'] / f'{row["frame"]:04d}_{camera}.jpg'
            data = base64.b64encode(p.read_bytes()).decode()
            parts.append({'type': 'input_image', 'detail': 'high', 'image_url': 'data:image/jpeg;base64,'+data}
                         if provider == 'openai' else {'inlineData': {'mimeType': 'image/jpeg', 'data': data}})
    if provider == 'openai':
        return dict(model=MODELS[provider], input=[dict(role='user', content=parts)],
                    reasoning={'effort': 'low'}, max_output_tokens=MAX_OUTPUT,
                    text={'format': {'type': 'json_object'}}, store=False,
                    service_tier='default', truncation='disabled')
    return dict(contents=[dict(role='user', parts=parts)], generationConfig=dict(
        maxOutputTokens=MAX_OUTPUT, thinkingConfig={'thinkingLevel': 'low'},
        mediaResolution='MEDIA_RESOLUTION_LOW', responseMimeType='application/json'))


def validate(value, ep):
    def require(test, message):
        if not test: raise ValueError(message)
    def evidence(items):
        require(isinstance(items,list) and bool(items), 'Evidence required')
        for e in items:
            require(isinstance(e,dict) and set(e)=={'frame','camera','observation'}, 'Evidence fields')
            require(type(e['frame']) is int and e['frame'] in ep['sampled_frames']
                    and e['camera'] in ('agent','wrist') and isinstance(e['observation'],str)
                    and bool(e['observation'].strip()), 'Supplied frame/camera evidence')
    require(isinstance(value,dict) and set(value)=={'episode_id','identity_check','segments'}, 'Envelope')
    c=value['identity_check']
    require(isinstance(c,dict) and set(c)=={'requested_object','manipulated_object','match_status','evidence','uncertainty'}, 'Identity fields')
    require(all(isinstance(c[k],str) and bool(c[k].strip()) for k in ('requested_object','manipulated_object')), 'Identity text')
    require(c['match_status'] in ('supported_match','supported_mismatch','unresolved')
            and isinstance(c['uncertainty'],str), 'Identity status')
    require(c['match_status']!='unresolved' or bool(c['uncertainty'].strip()), 'Explain unresolved identity')
    evidence(c['evidence'])
    require(isinstance(value['segments'],list), 'Segments')
    stripped=[]
    for seg in value['segments']:
        require(all(k in seg for k in ('evidence','review_required','uncertainty')), 'Segment evidence fields')
        evidence(seg['evidence'])
        require(type(seg['review_required']) is bool and isinstance(seg['uncertainty'],str), 'Review metadata')
        require(not seg['review_required'] or bool(seg['uncertainty'].strip()), 'Explain review flag')
        stripped.append({k:v for k,v in seg.items() if k not in ('evidence','review_required','uncertainty')})
    baseline.validate({'episode_id':value['episode_id'],'segments':stripped},ep)


def bouts(segments):
    result = []
    for s in segments:
        if result and result[-1][1] == s['start_frame']:
            result[-1][1] = s['end_frame']
        else:
            result.append([s['start_frame'], s['end_frame']])
    return result


def run():
    m = verify()
    if date.today() > date(2026,12,31):
        raise ValueError('Recheck expired pricing')
    keys = common.credentials()
    (OUT / 'attempts').mkdir(exist_ok=True)
    for ep in m['episodes']:
        for provider in MODELS:
            name = ep['id']+'_'+provider
            slot = OUT / 'attempts' / (name+'.json')
            if slot.exists():
                print(name+': existing reservation; never resend', flush=True)
                continue
            record = dict(provider=provider, episode=ep['id'], reserved_usd=RESERVE,
                          status='reserved', generation_sent=False, started=time.time())
            with slot.open('x', encoding='utf-8') as f:
                json.dump(record,f)
            try:
                body = payload(provider,ep)
                base = ('https://api.openai.com/v1/responses' if provider=='openai' else
                        'https://generativelanguage.googleapis.com/v1beta/models/'+MODELS[provider])
                count_body = ({k:body[k] for k in ('model','input','reasoning','text','truncation')}
                              if provider=='openai' else
                              {'generateContentRequest': {'model':'models/'+MODELS[provider],**body}})
                count = transport.post(base+('/input_tokens' if provider=='openai' else ':countTokens'),
                                       provider,count_body,keys)
                common.write_json(OUT / (name+'_count.json'),count)
                n = count['input_tokens' if provider=='openai' else 'totalTokens']
                if type(n) is not int or not 0 < n <= MAX_INPUT:
                    raise ValueError('Input token ceiling')
                allowance = n*(2 if provider=='openai' else 1)/1e6
                worst = (n*(2.5 if provider=='openai' else 1)+MAX_OUTPUT*(10 if provider=='openai' else 5))/1e6
                if allowance+worst > RESERVE:
                    raise ValueError('Reservation insufficient; generation blocked')
                record.update(counted_input_tokens=n, preflight_allowance_usd=allowance,
                              maximum_generation_usd=worst, generation_sent=True, status='in_flight')
                transport.atomic_json(slot,record)
                print(f'{name}: generating ({n} input tokens)',flush=True)
                raw = transport.post(base if provider=='openai' else base+':generateContent',provider,body,keys)
                raw = json.loads(transport.redact(json.dumps(raw),keys))
                common.write_json(OUT / (name+'_raw.json'),raw)
                record.update(transport.usage_cost(provider,raw))
                record['returned_model'] = raw.get('model',raw.get('modelVersion'))
                answer, complete = transport.extract_answer(provider,raw)
                (OUT / (name+'_answer.txt')).write_text(answer,encoding='utf-8')
                if not complete:
                    raise ValueError('Incomplete output; no retry')
                value = json.loads(answer)
                validate(value,ep)
                common.write_json(OUT / (name+'_annotation.json'),value)
                record['status']='validated'
            except Exception as e:
                record.update(status='stopped',error=transport.redact(str(e),keys)[:800])
            finally:
                record['elapsed_seconds']=round(time.time()-record['started'],2)
                transport.atomic_json(slot,record)
                report()
            print(name+': '+record['status'],flush=True)
            if record.get('generation_estimate_usd',0)+record.get('preflight_allowance_usd',0)>RESERVE:
                raise ValueError('Reported cost exceeded reservation; halt')


def report():
    m = common.load(OUT / 'manifest.json')
    records = [common.load(p) for p in sorted((OUT/'attempts').glob('*.json'))]
    summary = dict(planned=8, attempted=len(records), validated=sum(r['status']=='validated' for r in records),
                   generation_estimate_usd=sum(r.get('generation_estimate_usd',0) for r in records),
                   preflight_allowance_usd=sum(r.get('preflight_allowance_usd',0) for r in records),
                   unknown_reservations_usd=sum(RESERVE for r in records if 'generation_estimate_usd' not in r),
                   records=records)
    common.write_json(OUT/'summary.json',summary)
    parts=['<!doctype html><meta charset="utf-8"><title>Taxonomy pilot</title>',
           '<style>body{font:16px system-ui;margin:30px}pre{white-space:pre-wrap}td{vertical-align:top;width:50%;padding:12px}img{width:256px}summary{cursor:pointer}</style>',
           '<h1>V6: observable progress definition and examples</h1>',
           '<p>Agreement is not accuracy. No human or simulator references supplied. 4 Hz images can miss brief events.</p>',
           '<p><a href="prompt.txt">Frozen taxonomy/prompt</a> | <a href="manifest.json">Manifest</a> | <a href="summary.json">Costs/status</a></p>',
           '<pre>'+html.escape(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))+'</pre>']
    for ep in m['episodes']:
        parts.append('<h2>'+html.escape(ep['id']+': '+ep['task'])+'</h2><table><tr>')
        for provider in MODELS:
            p=OUT/(ep['id']+'_'+provider+'_annotation.json')
            parts.append('<td><h3>'+html.escape(MODELS[provider])+'</h3>')
            if p.exists():
                a=common.load(p)
                parts.append('<pre>'+html.escape(json.dumps(a,indent=2))+'</pre>')
            else:
                parts.append('<p>Unavailable/pending; see status ledger.</p>')
            parts.append('</td>')
        parts.append('</tr></table><details><summary>Show exact sampled camera evidence</summary>')
        for f in ep['sampled_frames']:
            parts.append(f'<div>Frame {f} ({f/ep["fps"]:.2f}s)<br>')
            for camera in ('agent','wrist'):
                parts.append(f'<img loading="lazy" src="{ep["id"]}/{f:04d}_{camera}.jpg">')
            parts.append('</div>')
        parts.append('</details>')
    (OUT/'review.html').write_text('\n'.join(parts),encoding='utf-8')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('prepare','run','report','verify'))
    args=p.parse_args()
    {'prepare':prepare,'run':run,'report':report,'verify':verify}[args.command]()
