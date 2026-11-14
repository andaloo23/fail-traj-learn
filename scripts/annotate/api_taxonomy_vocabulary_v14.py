"""Twelve frozen vocabulary-guidance calls: Sol, Astra, Gemini; no automatic retries."""
import argparse
import json
from pathlib import Path
import shutil
import time

import api_taxonomy_complete_failures_v11 as baseline
import api_taxonomy_vocabulary_v13 as previous
import api_label_pilot as common
import os
import api_frame_selection_windows_v1 as transport

OUT = common.ROOT / 'outputs/taxonomy_vocabulary_v14'
PROMPT = common.ROOT / 'scripts/annotate/prompts/failure_taxonomy_vocabulary_v14.txt'
IDS = baseline.IDS
MODELS = {'openai': common.MODELS['openai'], 'astra': 'gpt-6-astra',
          'gemini': common.MODELS['gemini']}
RESERVES = {'openai': .50, 'astra': 2.50, 'gemini': .50}
RATES = {'openai': dict(input=2, cached=.1, cache_write=2.5, output=10),
         'astra': dict(input=10, cached=1, cache_write=12.5, output=50),
         'gemini': dict(input=1, cached=.1, cache_write=1, output=5)}
validate = baseline.validate


def hashes():
    return {str(p.relative_to(common.ROOT)): common.digest(p) for p in
            (Path(__file__), PROMPT, Path(previous.__file__), previous.PROMPT, Path(baseline.__file__), Path(common.__file__), Path(transport.__file__))}


def settings():
    return dict(models=MODELS, reserves=RESERVES, rates=RATES, retries=0,
                max_input=baseline.MAX_INPUT, max_output=baseline.MAX_OUTPUT,
                reasoning='low', image_detail='high', gemini_media_resolution='MEDIA_RESOLUTION_LOW')


def prepare():
    old = previous.verify()
    OUT.mkdir(exist_ok=False)
    shutil.copyfile(PROMPT, OUT / 'prompt.txt')
    for ep in old['episodes']:
        folder = OUT / ep['id']
        folder.mkdir()
        shutil.copyfile(previous.OUT / ep['id'] / 'input.json', folder / 'input.json')
        for frame in ep['sampled_frames']:
            for camera in ('agent', 'wrist'):
                name = f'{frame:04d}_{camera}.jpg'
                shutil.copyfile(previous.OUT / ep['id'] / name, folder / name)
    common.write_json(OUT / 'manifest.json', dict(
        version='vocabulary_v14', settings=settings(), code_hashes=hashes(),
        authorization='User explicitly requested running V14 on the same four episodes with Sol, Astra, and Gemini; expanded referent vocabulary and adjacent-segment merging guidance, unchanged schema.',
        episodes=old['episodes'], base_prompt_sha256=common.digest(previous.PROMPT),
        files={p.relative_to(OUT).as_posix(): common.digest(p) for p in OUT.rglob('*') if p.is_file()}))
    report()
    print('Prepared 12 calls; conservative total reservation $14.00', flush=True)


def verify():
    m = common.load(OUT / 'manifest.json')
    if m['settings'] != settings() or m['code_hashes'] != hashes():
        raise ValueError('Frozen code/settings changed')
    if [e['id'] for e in m['episodes']] != list(IDS):
        raise ValueError('Episode matrix changed')
    for name, digest in m['files'].items():
        if common.digest(OUT / name) != digest:
            raise ValueError('Frozen evidence changed')
    return m


def payload(provider, ep):
    wire = 'gemini' if provider == 'gemini' else 'openai'
    old_out, old_models = baseline.OUT, baseline.MODELS
    try:
        baseline.OUT, baseline.MODELS = OUT, {wire: MODELS[provider]}
        return baseline.payload(wire, ep)
    finally:
        baseline.OUT, baseline.MODELS = old_out, old_models


def report():
    records = [common.load(p) for p in sorted((OUT / 'attempts').glob('*.json'))]
    summary = dict(
        planned=12, attempted=len(records), validated=sum(r['status']=='validated' for r in records),
        generation_estimate_usd=sum(r.get('generation_estimate_usd', 0) for r in records),
        preflight_allowance_usd=sum(r.get('preflight_allowance_usd', 0) for r in records),
        unknown_reservations_usd=sum(r['reserved_usd'] for r in records if 'generation_estimate_usd' not in r),
        records=records)
    temporary = OUT / f"summary.{os.getpid()}.tmp"
    common.write_json(temporary, summary)
    temporary.replace(OUT / "summary.json")


def run(episode=None):
    m, keys = verify(), common.credentials()
    (OUT / 'attempts').mkdir(exist_ok=True)
    for ep in m['episodes']:
        if episode is not None and ep['id'] != episode:
            continue
        for provider, model in MODELS.items():
            name = ep['id'] + '_' + provider
            slot = OUT / 'attempts' / (name + '.json')
            if slot.exists():
                print(name + ': existing reservation; never resend', flush=True)
                continue
            wire = 'gemini' if provider == 'gemini' else 'openai'
            r = dict(provider=provider, model=model, episode=ep['id'], reserved_usd=RESERVES[provider],
                     status='reserved', generation_sent=False, started=time.time())
            with slot.open('x', encoding='utf-8') as f:
                json.dump(r, f)
            try:
                body = payload(provider, ep)
                base = 'https://api.openai.com/v1/responses' if wire=='openai' else 'https://generativelanguage.googleapis.com/v1beta/models/'+model
                count_body = ({k:body[k] for k in ('model','input','reasoning','text','truncation')}
                              if wire=='openai' else {'generateContentRequest': {'model':'models/'+model, **body}})
                count = transport.post(base+('/input_tokens' if wire=='openai' else ':countTokens'), wire, count_body, keys)
                common.write_json(OUT / (name+'_count.json'), count)
                n = count['input_tokens' if wire=='openai' else 'totalTokens']
                if type(n) is not int or not 0 < n <= baseline.MAX_INPUT:
                    raise ValueError('Input token ceiling')
                rates = RATES[provider]
                allowance = n*rates['input']/1e6
                worst = (n*max(rates['input'],rates['cache_write'])+baseline.MAX_OUTPUT*rates['output'])/1e6
                if allowance+worst > RESERVES[provider]:
                    raise ValueError('Reservation insufficient; generation blocked')
                r.update(counted_input_tokens=n, preflight_allowance_usd=allowance,
                         maximum_generation_usd=worst, generation_sent=True, status='in_flight')
                transport.atomic_json(slot, r)
                print(f'{name}: generating ({n} input tokens)', flush=True)
                raw = transport.post(base if wire=='openai' else base+':generateContent', wire, body, keys)
                raw = json.loads(transport.redact(json.dumps(raw), keys))
                common.write_json(OUT / (name+'_raw.json'), raw)
                usage = transport.usage_cost(wire, raw)
                usage['generation_estimate_usd'] = round(((usage['input_tokens']-usage['cached_tokens']-usage['cache_write_tokens'])*rates['input']+
                    usage['cached_tokens']*rates['cached']+usage['cache_write_tokens']*rates['cache_write']+
                    usage['output_tokens_including_thinking']*rates['output'])/1e6, 8)
                r.update(usage, returned_model=raw.get('model', raw.get('modelVersion')))
                answer, complete = transport.extract_answer(wire, raw)
                (OUT / (name+'_answer.txt')).write_text(answer, encoding='utf-8')
                if not complete:
                    raise ValueError('Incomplete response; no retry')
                value = json.loads(answer)
                validate(value, ep)
                common.write_json(OUT / (name+'_annotation.json'), value)
                r['status'] = 'validated'
            except Exception as exc:
                r.update(status='stopped', error=transport.redact(str(exc), keys)[:800])
            finally:
                r['elapsed_seconds'] = round(time.time()-r['started'], 2)
                transport.atomic_json(slot, r)
                report()
            print(name+': '+r['status'], flush=True)
            if r.get('generation_estimate_usd',0)+r.get('preflight_allowance_usd',0)>RESERVES[provider]:
                raise ValueError('Reported cost exceeded reservation')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('prepare','verify','run','report'))
    p.add_argument('--episode', choices=IDS, help='Run only this episode from the frozen matrix')
    args = p.parse_args()
    if args.command == 'run':run(args.episode)
    else:globals()[args.command]()
