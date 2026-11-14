"""Compare judge models on frozen text pairs and explicit semantic controls.

Reuse a validated prior evaluation as the input baseline. No annotation generation,
video claims, automatic retries, or silent replacement of missing judgments.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time

import annotation_runtime as io
import compare_annotation_descriptions as rubric

MAX_INPUT, MAX_OUTPUT = 10000, 8192
CONFIG = {
    'astra': dict(provider='openai', model='gpt-6-astra', reserve=.70,
                  rates=dict(input=10, cached=1, cache_write=12.5, output=50)),
    'sol': dict(provider='openai', model='gpt-6.1-sol', reserve=.15,
                rates=dict(input=2, cached=.1, cache_write=2.5, output=10)),
    'luna': dict(provider='openai', model='gpt-6-luna', reserve=.007,
                 rates=dict(input=.1, cached=.01, cache_write=.125, output=.5)),
    'gemini': dict(provider='gemini', model='gemini-3.8-flash', reserve=.07,
                   rates=dict(input=.75, cached=.075, cache_write=.75, output=3.75)),
}


def stress_controls():
    """Authored expected text relations, never assertions about a real recording."""
    cases = [
        ('identical', 'The robot grasps the carton.', 'The robot grasps the carton.', 5, 5),
        ('verbose_paraphrase', 'The robot grasps the carton and lifts it.',
         'The robot takes hold of the carton with its gripper and raises the same carton upward, picking it up and lifting it.', 5, 5),
        ('supported_alias', 'The robot grasps carton_1, the milk carton, and lifts it.',
         'The robot picks up the milk carton.', 5, 5),
        ('changed_destination', 'The robot places the carton inside the basket.',
         'The robot places the carton outside the basket.', 1, 2),
        ('action_order', 'The robot opens the drawer before picking up the carton.',
         'The robot picks up the carton before opening the drawer.', 1, 2),
        ('lost_control', 'The carton stays held during transport.',
         'The carton slips out of the gripper during transport.', 1, 2),
        ('release_reversal', 'The robot keeps holding the carton and does not release it.',
         'The robot releases the carton and no longer holds it.', 1, 2),
        ('omitted_brief_failure', 'The robot transports the carton, briefly bumps the basket, and continues moving.',
         'The robot transports the carton and continues moving.', 3, 3),
        ('scope_difference', 'The robot approaches the carton, grasps it, and transports it.',
         'The robot approaches the carton.', 3, 3),
        ('omitted_release', 'The robot transports the carton, places it in the basket, and releases it.',
         'The robot transports the carton and places it in the basket.', 3, 3),
        ('uncertainty_erased', 'The carton is occluded; whether the gripper has acquired it is unresolved.',
         'The gripper has definitely acquired the carton.', 2, 3),
        ('attempt_result', 'The robot tries to push the drawer closed, but the drawer does not move.',
         'The robot pushes the drawer fully closed.', 1, 2),
        ('physical_vs_task', 'The robot successfully grasps the wrong bottle, making no task progress.',
         'The robot successfully grasps the requested bottle, making task progress.', 1, 2),
        ('unrelated', 'The robot releases the carton into the basket.',
         'A person types a message on a laptop in another room.', 1, 1),
        ('small_detail', 'The robot lifts the carton.',
         'The robot lifts the carton with a slight tilt.', 4, 4),
        ('buried_contradiction',
         'The robot reaches toward the milk carton, closes the gripper, lifts it, carries it toward the basket, bumps the basket, and lowers the carton inside. The basket shifts after the bump.',
         'The robot reaches toward the milk carton, closes the gripper, lifts it, carries it toward the basket, bumps the basket, and lowers the carton inside. The basket remains stationary after the bump.', 1, 2),
        ('buried_identity',
         'The robot approaches the carton, adjusts its wrist, closes the gripper, and lifts the carton. It carries the juice carton toward the basket and lowers it inside.',
         'The robot approaches the carton, adjusts its wrist, closes the gripper, and lifts the carton. It carries the milk carton toward the basket and lowers it inside.', 1, 2),
        ('recovered_failure_omitted', 'The carton slips during transport; the robot re-grasps it and completes placement.',
         'The robot transports the carton and completes placement.', 3, 3),
    ]
    return [dict(pair_id=f'p{i+1:03d}', name=name, left=a, right=b,
                 expected_min=lo, expected_max=hi) for i, (name, a, b, lo, hi) in enumerate(cases)]


def content(batch, order):
    pairs = [dict(pair_id=p['pair_id'], A=p['left' if order == 'ab' else 'right'],
                  B=p['right' if order == 'ab' else 'left']) for p in batch['pairs']]
    return json.dumps(dict(task_context=batch['task'], pairs=pairs), ensure_ascii=False)


def payload(config, batch, order, prompt):
    if config['provider'] == 'openai':
        return dict(model=config['model'], input=[dict(role='developer', content=prompt),
                    dict(role='user', content=content(batch, order))],
                    reasoning=dict(effort='medium'), max_output_tokens=MAX_OUTPUT,
                    text=dict(format=dict(type='json_object')), store=False,
                    service_tier='default', truncation='disabled')
    return dict(systemInstruction=dict(parts=[dict(text=prompt)]),
                contents=[dict(role='user', parts=[dict(text=content(batch, order))])],
                generationConfig=dict(maxOutputTokens=MAX_OUTPUT,
                    thinkingConfig=dict(thinkingLevel='medium'), responseMimeType='application/json'))


def code_hashes():
    return {p.name: io.digest(p) for p in (Path(__file__), Path(io.__file__), Path(rubric.__file__))}


def prepare(baseline, out):
    if out.exists():
        raise ValueError('Fresh output directory required')
    original = io.load(baseline / 'manifest.json')
    prompt = (baseline / 'rubric.txt').read_text(encoding='utf-8')
    if original['settings']['model'] != CONFIG['astra']['model']:
        raise ValueError('Expected Astra baseline')
    if io.digest(baseline / 'rubric.txt') != original['source_hashes'][
        'scripts/annotate/prompts/description_equivalence.txt']:
        raise ValueError('Baseline rubric changed')
    out.mkdir(parents=True)
    (out / 'attempts').mkdir()
    io.write_json(out / 'baseline_manifest.json', original)
    (out / 'rubric.txt').write_text(prompt, encoding='utf-8')
    batches = original['batches'] + [dict(id='stress', task='Follow the requested robot task.',
                                        pairs=stress_controls())]
    jobs, frozen = [], {}
    for batch in original['batches']:
        for order in ('ab', 'ba'):
            stem = batch['id'] + '_' + order
            raw = io.load(baseline / (stem + '_raw.json'))
            saved = io.load(baseline / (stem + '_evaluation.json'))
            request = io.load(baseline / (stem + '_request.json'))
            answer, complete = io.extract_answer('openai', raw)
            rubric.validate(saved, batch)
            if not complete or json.loads(answer) != saved:
                raise ValueError('Baseline does not match completed raw response')
            if request != payload(CONFIG['astra'], batch, order, prompt):
                raise ValueError('Baseline request differs from matched protocol')
            if io.load(baseline / 'attempts' / (stem + '.json'))['status'] != 'validated':
                raise ValueError('Baseline call not validated')
            for suffix in ('_request.json', '_raw.json', '_evaluation.json'):
                name = 'astra_' + stem + suffix
                shutil.copyfile(baseline / (stem + suffix), out / name)
                frozen[name] = io.digest(out / name)
    for judge in CONFIG:
        for batch in batches:
            if judge == 'astra' and batch['id'] != 'stress':
                continue
            jobs.extend(dict(judge=judge, batch=batch['id'], order=order) for order in ('ab', 'ba'))
    maximum = sum(CONFIG[j['judge']]['reserve'] for j in jobs)
    if maximum > 4.50:
        raise ValueError('Maximum reservation exceeds experiment ceiling')
    io.write_json(out / 'manifest.json', dict(
        models=CONFIG, max_input=MAX_INPUT, max_output=MAX_OUTPUT, reasoning='medium',
        retries=0, workers=2, maximum_reserved_usd=round(maximum, 6),
        price_checked='2026-10-12',
        pricing_sources=['https://developers.openai.com/api/docs/models/gpt-6-astra',
                         'https://developers.openai.com/api/docs/models/gpt-6.1-sol',
                         'https://developers.openai.com/api/docs/models/gpt-6-luna',
                         'https://ai.google.dev/gemini-api/docs/pricing'],
        baseline_manifest_sha256=io.digest(baseline / 'manifest.json'),
        prompt_sha256=io.digest(out / 'rubric.txt'), frozen_baseline_files=frozen,
        code_hashes=code_hashes(), batches=batches, jobs=jobs,
        prepared_utc=datetime.now(timezone.utc).isoformat(),
        limitations='Controlled text relations are authored expectations. Real-pair agreement has no correctness reference. Cross-provider reasoning levels and API roles are not identical. Astra baseline calls are historical, not fresh repeats.',
    ))
    (out / 'manifest.sha256').write_text(io.digest(out / 'manifest.json'), encoding='utf-8')
    print(f'Prepared {len(jobs)} new calls; maximum reserved ${maximum:.3f}', flush=True)


def verify(out):
    if io.digest(out / 'manifest.json') != (out / 'manifest.sha256').read_text(encoding='utf-8'):
        raise ValueError('Frozen manifest changed')
    manifest = io.load(out / 'manifest.json')
    if manifest['models'] != CONFIG or manifest['code_hashes'] != code_hashes():
        raise ValueError('Frozen runner/configuration changed')
    if manifest['prompt_sha256'] != io.digest(out / 'rubric.txt'):
        raise ValueError('Frozen rubric changed')
    for name, digest in manifest['frozen_baseline_files'].items():
        if io.digest(out / name) != digest:
            raise ValueError('Baseline evidence changed')
    return manifest


def execute(out, job, batch, prompt, keys):
    config = CONFIG[job['judge']]
    provider = config['provider']
    stem = '_'.join(job[k] for k in ('judge', 'batch', 'order'))
    slot = out / 'attempts' / (stem + '.json')
    record = dict(**job, model=config['model'], reserved_usd=config['reserve'],
                  status='reserved', generation_sent=False, started=time.time())
    try:
        with slot.open('x', encoding='utf-8') as f:
            json.dump(record, f)
    except FileExistsError:
        print(stem + ': existing reservation; not resent', flush=True)
        return
    try:
        body = payload(config, batch, job['order'], prompt)
        io.write_json(out / (stem + '_request.json'), body)
        base = ('https://api.openai.com/v1/responses' if provider == 'openai' else
                'https://generativelanguage.googleapis.com/v1beta/models/' + config['model'])
        count_body = ({k: body[k] for k in ('model', 'input', 'reasoning', 'text', 'truncation')}
                      if provider == 'openai' else dict(generateContentRequest=dict(
                          model='models/' + config['model'], **body)))
        count = io.post(base + ('/input_tokens' if provider == 'openai' else ':countTokens'),
                        provider, count_body, keys)
        io.write_json(out / (stem + '_count.json'), count)
        tokens = count['input_tokens' if provider == 'openai' else 'totalTokens']
        if type(tokens) is not int or not 0 < tokens <= MAX_INPUT:
            raise ValueError('Input token ceiling')
        rates = config['rates']
        allowance = tokens * rates['input'] / 1e6
        worst = (tokens * max(rates['input'], rates['cache_write']) + MAX_OUTPUT * rates['output']) / 1e6
        if allowance + worst > config['reserve']:
            raise ValueError('Preflight plus generation exceeds reservation')
        record.update(preflight_allowance_usd=allowance, counted_input_tokens=tokens,
                      maximum_generation_usd=worst, generation_sent=True, status='in_flight')
        io.atomic_json(slot, record)
        raw = io.post(base if provider == 'openai' else base + ':generateContent', provider, body, keys)
        raw = json.loads(io.redact(json.dumps(raw), keys))
        io.write_json(out / (stem + '_raw.json'), raw)
        usage = io.usage_cost(provider, raw)
        usage['generation_estimate_usd'] = round((
            (usage['input_tokens']-usage['cached_tokens']-usage['cache_write_tokens']) * rates['input']
            + usage['cached_tokens']*rates['cached'] + usage['cache_write_tokens']*rates['cache_write']
            + usage['output_tokens_including_thinking']*rates['output']) / 1e6, 8)
        record.update(usage, returned_model=raw.get('model', raw.get('modelVersion')))
        answer, complete = io.extract_answer(provider, raw)
        (out / (stem + '_answer.txt')).write_text(answer, encoding='utf-8')
        if not complete:
            raise ValueError('Incomplete response; no retry')
        value = json.loads(answer)
        rubric.validate(value, batch)
        io.write_json(out / (stem + '_evaluation.json'), value)
        record['status'] = 'validated'
    except Exception as exc:
        record.update(status='stopped', error=io.redact(str(exc), keys)[:800])
    finally:
        record['elapsed_seconds'] = round(time.time() - record['started'], 2)
        io.atomic_json(slot, record)
    print(stem + ': ' + record['status'] + (' — ' + record.get('error', '') if record['status'] == 'stopped' else ''), flush=True)


def report(out):
    manifest = verify(out)
    records = [io.load(p) for p in sorted((out / 'attempts').glob('*.json'))]
    cost = dict(planned=len(manifest['jobs']), attempted=len(records),
                validated=sum(r['status'] == 'validated' for r in records),
                generation_estimate_usd=sum(r.get('generation_estimate_usd', 0) for r in records),
                preflight_allowance_usd=sum(r.get('preflight_allowance_usd', 0) for r in records),
                unknown_reservations_usd=sum(r['reserved_usd'] for r in records
                    if r['generation_sent'] and 'generation_estimate_usd' not in r))
    rows, unavailable = [], []
    summary = {}
    for judge, config in CONFIG.items():
        control_results, real, order_disagreements = [], [], 0
        for batch in manifest['batches']:
            orders = []
            for order in ('ab', 'ba'):
                stem = f"{judge}_{batch['id']}_{order}"
                path = out / (stem + '_evaluation.json')
                slot = out / 'attempts' / (stem + '.json')
                status = io.load(slot)['status'] if slot.exists() else 'reused_baseline'
                if not path.exists() or status not in ('validated', 'reused_baseline'):
                    unavailable.append(dict(judge=judge, batch=batch['id'], order=order, status=status))
                    break
                value = io.load(path)
                rubric.validate(value, batch)
                raw = io.load(out / (stem + '_raw.json'))
                answer, complete = io.extract_answer(config['provider'], raw)
                if not complete or json.loads(answer) != value:
                    raise ValueError('Saved judgment differs from completed response')
                orders.append({r['pair_id']: r for r in value['evaluations']})
            if len(orders) != 2:
                continue
            for p in batch['pairs']:
                ab, ba = [o[p['pair_id']] for o in orders]
                row = dict(judge=judge, batch=batch['id'], **p, score=(ab['score']+ba['score'])/2,
                           order_disagreement=ab['score'] != ba['score'], judgments=dict(ab=ab, ba=ba))
                if 'expected_min' in p:
                    row['passed'] = all(p['expected_min'] <= r['score'] <= p['expected_max'] for r in (ab, ba))
                    control_results.append(row)
                else:
                    real.append(row)
                order_disagreements += row['order_disagreement']
                rows.append(row)
        summary[judge] = dict(model=config['model'], controls_passed=sum(r['passed'] for r in control_results),
            controls_total=len(control_results), real_pairs=len(real),
            order_disagreements=order_disagreements, paired_items=len(control_results)+len(real),
            real_pair_mean_score=sum(r['score'] for r in real)/len(real) if real else None,
            failed_controls=[dict(name=r['name'], ab=r['judgments']['ab']['score'],
                                  ba=r['judgments']['ba']['score']) for r in control_results if not r['passed']])
    result = dict(cost=cost, summaries=summary, unavailable=unavailable, pairs=rows,
                  limitations=manifest['limitations'])
    io.atomic_json(out / 'comparison.json', result)
    print(json.dumps(dict(cost=cost, summaries=summary, unavailable=len(unavailable))), flush=True)
    return result


def run(out):
    manifest = verify(out)
    keys = io.credentials()
    batches = {b['id']: b for b in manifest['batches']}
    prompt = (out / 'rubric.txt').read_text(encoding='utf-8')
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(execute, out, j, batches[j['batch']], prompt, keys) for j in manifest['jobs']]
        for job in as_completed(jobs):
            job.result()
    result = report(out)
    if result['cost']['validated'] != result['cost']['planned']:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run', 'report'))
    parser.add_argument('--baseline', type=Path, default=io.ROOT / 'outputs/atomic_description_eval')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.baseline.resolve(), args.out.resolve())
    else:
        globals()[args.command](args.out.resolve())
