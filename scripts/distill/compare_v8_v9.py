"""Matched, Sol-only rich V8 / binary V9.1 comparison on frozen real OopsieData.

New rich responses are native Markdown. Existing V9.1 traces are read-only.
Generation is explicit, budgeted and never automatically retried.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import copy
import json
import math
import os
from pathlib import Path
import shutil

import binary_segments_v9 as binary
import oopsie_common as common
import annotation_runtime as transport
import failure_enrichment_v8_1 as enrichment

PROTOCOL = 'sol_v8_rich_v9_binary_comparison_v1'
ENRICHED_PROTOCOL = 'sol_rich_failure_v8_1_comparison_v1'
TEMPLATE = Path(__file__).with_name('prompt_comparison_review.html')
RUNNER_SHA256 = common.sha(Path(__file__))


def link_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        try:
            os.link(source, destination)
        except OSError:
            shutil.copyfile(source, destination)
    if common.sha(source) != common.sha(destination):
        raise ValueError('Review/input copy differs from its original')


def snapshot(source):
    paths = [source / p for p in ('manifest.json', 'config.json', 'prompt.md')]
    paths += list((source / 'requests').glob('*.json'))
    paths += [p for p in (source / 'traces').glob('*/*') if p.is_file()]
    paths += list((source / 'reviews').glob('*.md'))
    return {p.relative_to(source).as_posix(): common.sha(p) for p in paths}


def prepare(config_path):
    cfg = common.read(config_path)
    source = common.inside(common.ROOT, cfg['source_run'])
    original = binary.verify(source)
    if cfg['teachers'] != {'sol': original['config']['teachers']['sol']} or type(cfg['repeats']) is not int or cfg['repeats'] < 1:
        raise ValueError('This comparison requires Sol only and a positive repeat count')
    if cfg['protocol'] not in (PROTOCOL, ENRICHED_PROTOCOL):
        raise ValueError('Unknown comparison protocol')
    if original['config']['prompt_revision'] != 'v9.1':
        raise ValueError('Expected the approved V9.1 source')
    out = common.inside(common.ROOT, cfg['out'])
    if out.exists():
        raise ValueError('Prepare a fresh versioned output directory')
    out.mkdir(parents=True)
    common.write(out / 'config.json', cfg)
    shutil.copyfile(common.inside(common.ROOT, cfg['prompt']), out / 'prompt.md')
    for e in original['episodes']:
        for item in e['images'] + e.get('source_images', []) + e['videos']:
            relative = item.get('path', item.get('url'))
            link_copy(common.inside(source, relative), common.inside(out, relative))
    common.write(out / 'source_preservation.json', snapshot(source))
    manifest = dict(protocol=cfg['protocol'], repo=original['repo'], revision=original['revision'],
        config=cfg, source_manifest_sha256=common.sha(source / 'manifest.json'),
        source_annotations_used_as_model_input=False, episodes=copy.deepcopy(original['episodes']),
        files={p.relative_to(out).as_posix(): common.sha(p) for p in out.rglob('*') if p.is_file()})
    common.write(out / 'manifest.json', manifest)
    verify(out)
    review(out)
    return dict(out=str(out), episodes=len(manifest['episodes']), new_generation_calls=0)


def verify(root):
    root = Path(root)
    m = common.read(root / 'manifest.json')
    if m['protocol'] not in (PROTOCOL, ENRICHED_PROTOCOL) or m['repo'] != common.REPO_ID or m['source_annotations_used_as_model_input']:
        raise ValueError('Expected matched visual-only OopsieData comparison')
    source = common.inside(common.ROOT, m['config']['source_run'])
    original = binary.verify(source)
    if common.sha(source / 'manifest.json') != m['source_manifest_sha256'] or m['episodes'] != original['episodes']:
        raise ValueError('Comparison evidence differs from its frozen V9.1 source')
    for name, digest in m['files'].items():
        if common.sha(common.inside(root, name)) != digest:
            raise ValueError('Changed frozen comparison input: ' + name)
    preservation = common.read(root / 'source_preservation.json')
    for name, digest in preservation.items():
        if common.sha(common.inside(source, name)) != digest:
            raise ValueError('Changed preserved V9.1 artifact: ' + name)
    return m


def parse_rich(text, episode, schema=None):
    if schema == enrichment.SCHEMA:
        return enrichment.parse(text, episode)
    value = common.parse_answer(text, 'markdown')
    if value['episode_id'] != episode['id']:
        raise ValueError('Rich annotation belongs to another episode')
    native = dict(episode, images=episode.get('source_images', episode['images']),
                  sampled_frames=list(range(episode['n_frames'])))
    common.validate_annotation(value, native)
    return value


def binary_projection(segments):
    """Derived binary view only; never edits native rich boundaries or flags."""
    result = []
    for s in segments:
        if result and result[-1]['failure'] == s['failure']:
            result[-1]['end_frame'] = s['end_frame']
        else:
            result.append({k: s[k] for k in ('start_frame', 'end_frame', 'failure')})
    return result


def compare_request_inputs(rich, binary_request, rich_prompt, binary_prompt):
    """Prove that only the prompt and output allowance changed, without logging images."""
    a = rich['input'][0]['content'][0]['text']
    b = binary_request['input'][0]['content'][0]['text']
    if not a.startswith(rich_prompt) or not b.startswith(binary_prompt) or a[len(rich_prompt):] != b[len(binary_prompt):]:
        raise ValueError('Episode metadata/presentation instructions differ')
    # Restore the two allowed differences in memory, compare, then restore the input.
    allowance = rich['max_output_tokens']
    try:
        rich['input'][0]['content'][0]['text'] = b
        rich['max_output_tokens'] = binary_request['max_output_tokens']
        if rich != binary_request:
            raise ValueError('Frozen image bytes or other request settings differ')
    finally:
        rich['input'][0]['content'][0]['text'] = a
        rich['max_output_tokens'] = allowance


def audit_requests(root):
    root = Path(root); m = common.read(root / 'manifest.json')
    source = common.inside(common.ROOT, m['config']['source_run'])
    rich_prompt = (root / 'prompt.md').read_text(encoding='utf-8')
    binary_prompt = (source / 'prompt.md').read_text(encoding='utf-8')
    rows = []
    for e in m['episodes']:
        relative = 'requests/' + e['id'] + '_sol.json'
        rich = common.read(root / relative); previous = common.read(source / relative)
        compare_request_inputs(rich, previous, rich_prompt, binary_prompt)
        rows.append(dict(episode=e['id'], matched=True, images=len(e['images']),
            rich_request_sha256=common.sha(root / relative), binary_request_sha256=common.sha(source / relative)))
    receipt = dict(manifest_sha256=common.sha(root / 'manifest.json'), episodes=rows,
        allowed_changes=['annotation prompt', 'max_output_tokens'], images_and_metadata_identical=True,
        new_teachers=['sol'], labels_supplied_as_input=False)
    transport.atomic_json(root / 'matched_request_audit.json', receipt)
    return dict(matched_episodes=len(rows), images_and_metadata_identical=True)


def load_rich(root, m, e, repeat=1):
    folder = root / 'traces' / binary.trace_name(e['id'], 'sol', repeat)
    if not (folder / 'attempt.json').exists():
        return None
    state = common.read(folder / 'attempt.json')
    if state['status'] != 'validated':
        return None
    if state['manifest_sha256'] != common.sha(root / 'manifest.json'):
        raise ValueError('Rich trace belongs to another manifest')
    if (state['episode'], state['teacher'], state['repeat'], state['model']) != (e['id'], 'sol', repeat, m['config']['teachers']['sol']):
        raise ValueError('Rich trace identity/model mismatch')
    if common.sha(root / 'requests' / (e['id'] + '_sol.json')) != state['request_sha256']:
        raise ValueError('Changed frozen rich request')
    for name, key in (('annotation.md', 'annotation_sha256'), ('response.json', 'response_sha256')):
        if common.sha(folder / name) != state[key]:
            raise ValueError('Changed native rich teacher response')
    answer, complete = transport.extract_answer('openai', common.read(folder / 'response.json'))
    if not complete or (folder / 'annotation.md').read_bytes().decode('utf-8') != answer:
        raise ValueError('Native Markdown differs from completed API response')
    return parse_rich(answer, e, m['config'].get('annotation_schema')), state, answer


def preflight(root):
    root = Path(root); m = verify(root)
    keys = {'openai': transport.credentials()['openai']}
    rows = []
    for e in m['episodes']:
        body = binary.payload(root, m, e, 'sol')
        size = len(json.dumps(body).encode('utf-8'))
        if len(e['images']) > 1500 or size > 512 * 1024 * 1024:
            raise ValueError('Image/payload API limit exceeded')
        path = root / 'requests' / (e['id'] + '_sol.json')
        if path.exists():
            if common.read(path) != body:
                raise ValueError('Existing frozen request changed')
        else:
            common.write(path, body)
        count = transport.post('https://api.openai.com/v1/responses/input_tokens', 'openai',
            {k: body[k] for k in ('model', 'input', 'reasoning', 'text', 'truncation')}, keys)['input_tokens']
        if type(count) is not int or not 0 < count <= m['config']['max_input_tokens']:
            raise ValueError('Input ceiling exceeded; no truncation')
        rates = binary.request_rates(m['config'], 'sol', count)
        ceiling = (count * max(rates['input'], rates['cache_write']) + m['config']['max_output_tokens'] * rates['output']) / 1e6
        rows.append(dict(episode=e['id'], input_tokens=count, request_bytes=size,
            image_count=len(e['images']), request_sha256=common.sha(path), per_call_ceiling_usd=ceiling))
        transport.atomic_json(root / 'token_preflight.json', dict(complete=False, requests=rows))
        print(f"{e['id']}: {count} input tokens; ceiling ${ceiling:.4f}", flush=True)
    result = dict(complete=True, manifest_sha256=common.sha(root / 'manifest.json'),
                  requests=rows, run_total_ceiling_usd=sum(r['per_call_ceiling_usd'] for r in rows)*m['config']['repeats'], generation_calls=0)
    transport.atomic_json(root / 'token_preflight.json', result)
    return result


def collect_one(root, m, e, row, keys, repeat=1):
    folder = root / 'traces' / binary.trace_name(e['id'], 'sol', repeat)
    folder.mkdir(parents=True)  # Existing attempts must never be resent.
    path = root / 'requests' / (e['id'] + '_sol.json')
    body = common.read(path)
    state = dict(episode=e['id'], teacher='sol', repeat=repeat, model=body['model'], status='in_flight',
        manifest_sha256=common.sha(root / 'manifest.json'), request_sha256=row['request_sha256'],
        code_sha256=RUNNER_SHA256, parser_sha256=common.sha(Path(enrichment.__file__)), input_tokens=row['input_tokens'], reserved_usd=row['per_call_ceiling_usd'],
        started_utc=datetime.now(timezone.utc).isoformat())
    transport.atomic_json(folder / 'attempt.json', state)
    print(folder.name + ': generating '+m['config'].get('prompt_revision','V8')+' Sol', flush=True)
    try:
        raw = transport.post('https://api.openai.com/v1/responses', 'openai', body, keys)
        raw = json.loads(transport.redact(json.dumps(raw), keys))
        common.write(folder / 'response.json', raw)
        state['response_sha256'] = common.sha(folder / 'response.json')
        returned = str(raw.get('model', ''))
        if returned != body['model'] and not returned.startswith(body['model'] + '-'):
            raise ValueError('Returned model differs from requested Sol')
        u = raw['usage']; d = u.get('input_tokens_details') or {}
        inp, out = u['input_tokens'], u['output_tokens']
        cached, writes = d.get('cached_tokens', 0), d.get('cache_write_tokens', 0)
        if any(type(v) is not int or v < 0 for v in (inp, out, cached, writes)) or cached + writes > inp:
            raise ValueError('Invalid API token accounting')
        rates = binary.request_rates(m['config'], 'sol', inp)
        cost = ((inp-cached-writes)*rates['input'] + cached*rates['cached'] + writes*rates['cache_write'] + out*rates['output']) / 1e6
        state.update(usage=u, generation_estimate_usd=cost, returned_model=returned)
        answer, complete = transport.extract_answer('openai', raw)
        (folder / 'answer.txt').write_bytes(answer.encode('utf-8'))
        if not complete:
            raise ValueError('Incomplete response; no automatic retry')
        parse_rich(answer, e, m['config'].get('annotation_schema'))
        (folder / 'annotation.md').write_bytes(answer.encode('utf-8'))
        state.update(status='validated', annotation_sha256=common.sha(folder / 'annotation.md'))
    except Exception as exc:
        state.update(status='stopped', error=transport.redact(str(exc), keys)[:1500])
    finally:
        state['finished_utc'] = datetime.now(timezone.utc).isoformat()
        transport.atomic_json(folder / 'attempt.json', state)
    print(folder.name + ': ' + state['status'] + ('; ' + state['error'] if state.get('error') else ''), flush=True)
    return state['status'] == 'validated'


def collect(root, budget, workers=2):
    root = Path(root); m = verify(root)
    if not math.isfinite(budget) or budget <= 0 or workers not in (1, 2):
        raise ValueError('Positive budget and one or two workers required')
    receipt = common.read(root / 'token_preflight.json')
    if not receipt['complete'] or receipt['manifest_sha256'] != common.sha(root / 'manifest.json'):
        raise ValueError('Complete matching preflight required')
    if receipt['run_total_ceiling_usd'] > budget:
        raise ValueError('Cannot reserve all calls within the run-total budget')
    audit = common.read(root / 'matched_request_audit.json')
    if audit['manifest_sha256'] != common.sha(root / 'manifest.json') or not audit['images_and_metadata_identical']:
        raise ValueError('Matched request audit required before generation')
    by_id = {r['episode']: r for r in receipt['requests']}
    audited = {r['episode']: r['rich_request_sha256'] for r in audit['episodes']}
    pending = []
    for e in m['episodes']:
        if common.sha(root / 'requests' / (e['id'] + '_sol.json')) != by_id[e['id']]['request_sha256']:
            raise ValueError('Preflight request changed')
        if audited.get(e['id']) != by_id[e['id']]['request_sha256']:
            raise ValueError('Matched input audit does not cover this frozen request')
    for repeat in range(1,m['config']['repeats']+1):
        for e in m['episodes']:
            folder = root / 'traces' / binary.trace_name(e['id'], 'sol', repeat)
            if folder.exists():
                if load_rich(root, m, e, repeat) is None:
                    raise ValueError('Existing unfinished/stopped attempt will not be resent')
            else:
                pending.append((e,repeat))
    lock = root / 'collection.lock'
    with lock.open('x') as stream:
        stream.write(str(os.getpid()))
    try:
        keys = {'openai': transport.credentials()['openai']}
        iterator = iter(pending); stop = False
        with ThreadPoolExecutor(max_workers=workers) as pool:
            active = {}
            def submit():
                task = next(iterator, None)
                if task is not None:
                    e,repeat = task
                    active[pool.submit(collect_one, root, m, e, by_id[e['id']], keys, repeat)] = (e['id'],repeat)
            for _ in range(workers):
                submit()
            while active:
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    active.pop(future)
                    stop = not future.result() or stop
                review(root, m=m)
                if not stop:
                    for _ in done:
                        submit()
        return review(root, m=m)
    finally:
        lock.unlink()


def review_atomic(root, m=None):
    root = Path(root); m = m or verify(root)
    source = common.inside(common.ROOT, m['config']['source_run'])
    original = common.read(source / 'manifest.json')
    link_copy(source / 'prompt.md', root / 'review_annotations/v9/prompt.md')
    data = dict(protocol=PROTOCOL, prompt_revision='V8 / V9.1', manifest_sha256=common.sha(root / 'manifest.json'),
        review_ui_version=common.sha(TEMPLATE), repeats=1, planned_responses=len(m['episodes'])*(1+original['config']['repeats']), episodes=[])
    lines = ['# Sol: rich V8 and binary V9.1', '',
        '- V8: existing OopsieData Markdown adaptation of the rich atomic-action protocol.',
        '- V9.1: preserved Sol responses; no new binary calls and no Astra calls.',
        '- Identical full-rate frame/camera evidence; V8 binary timelines are derived from native rich labels.',
        '- Rich review flags are preserved; agreement includes flagged spans and is not human accuracy.', '',
        '| Episode | V8 status | Agreement with V9.1 repeat 1 | V8 review-flagged frames |',
        '| --- | --- | ---: | ---: |']
    rows = []; ready = 0; costs = 0
    for e in m['episodes']:
        traces = {'v8': [], 'v9': []}
        rich = load_rich(root, m, e)
        if rich:
            value, state, text = rich
            segments = binary_projection(value['segments'])
            relative = f"traces/{binary.trace_name(e['id'], 'sol', 1)}/annotation.md"
            traces['v8'].append(dict(repeat=1, segments=segments, rich_segments=value['segments'],
                native_markdown=text, markdown=relative, source_run=root.name))
            ready += 1; costs += state['generation_estimate_usd']
        for repeat in range(1, original['config']['repeats']+1):
            segments, _ = binary.load_trace(source, original, e, 'sol', repeat)
            relative = f"review_annotations/v9/{binary.trace_name(e['id'], 'sol', repeat)}/annotation.md"
            link_copy(source / 'traces' / binary.trace_name(e['id'], 'sol', repeat) / 'annotation.md', root / relative)
            traces['v9'].append(dict(repeat=repeat, segments=segments, markdown=relative, source_run=source.name))
        data['episodes'].append(dict(id=e['id'], task=e['task'], split=e['split'], lab=e['lab'],
            fps=e['fps'], n_frames=e['n_frames'], videos=e['videos'], teachers=traces,
            source_run=root.name + ' / ' + source.name, source_manifest_sha256=m['source_manifest_sha256']))
        if rich:
            score = binary.compare(traces['v8'][0]['segments'], traces['v9'][0]['segments'], e['n_frames'])
            flagged = sum(s['end_frame']-s['start_frame'] for s in value['segments'] if s['review_required'])
            rows.append(dict(episode=e['id'], review_flagged_frames=flagged, **score))
            lines.append(f"| {e['id']} | Ready | {100*score['frame_agreement']:.2f}% | {flagged} |")
        else:
            attempt = root / 'traces' / binary.trace_name(e['id'], 'sol', 1) / 'attempt.json'
            state = common.read(attempt) if attempt.exists() else {}
            lines.append(f"| {e['id']} | {state.get('status', 'Pending')} | - | - |")
    lines[2:2] = [f'- New V8 responses ready: {ready}/{len(m["episodes"])}. Estimated validated-call cost: ${costs:.6f}.']
    transport.atomic_json(root / 'comparison_results.json', dict(v8_ready=ready, v8_planned=len(m['episodes']),
        v9_reused=len(m['episodes'])*original['config']['repeats'], new_astra_calls=0, generation_estimate_usd=costs, rows=rows))
    html = TEMPLATE.read_text(encoding='utf-8')
    embedded = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    page = root / 'review.html'; tmp = root / 'review.html.tmp'
    tmp.write_text(html.replace('__DATA__', embedded), encoding='utf-8'); tmp.replace(page)
    transport.atomic_json(root / 'review_data.json', data)
    (root / 'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return dict(v8_ready=ready, v8_planned=len(m['episodes']), v9_reused=len(m['episodes'])*original['config']['repeats'],
                new_astra_calls=0, generation_estimate_usd=costs, review=str(page))


def review_enriched(root, m):
    source = common.inside(common.ROOT, m['config']['source_run'])
    original = common.read(source/'manifest.json')
    link_copy(source/'prompt.md', root/'review_annotations/v9/prompt.md')
    repeats=m['config']['repeats']; reference_repeats=original['config']['repeats']
    data=dict(protocol=m['protocol'], prompt_revision='V8.1 / V9.1',
        manifest_sha256=common.sha(root/'manifest.json'), review_ui_version=common.sha(TEMPLATE),
        side_labels={'v8':'V8.1 - Sol','v9':'V9.1 - Sol'}, side_repeats={'v8':repeats,'v9':reference_repeats},
        rich_prompt_description='V8.1 preserves V9.1 failure recognition and adds categories and explanations after the binary timeline.',
        repeats=repeats, planned_responses=len(m['episodes'])*(repeats+reference_repeats), episodes=[])
    rows=[]; ready=0; costs=0; stopped=[]
    for e in m['episodes']:
        traces={'v8':[],'v9':[]}; values=[]
        for repeat in range(1,repeats+1):
            folder=root/'traces'/binary.trace_name(e['id'],'sol',repeat)
            rich=load_rich(root,m,e,repeat)
            if rich:
                value,state,text=rich
                values.append(dict(value,repeat=repeat))
                traces['v8'].append(dict(repeat=repeat, segments=value['segments'],
                    failure_annotations=value['failure_annotations'], native_markdown=text,
                    markdown=f"traces/{folder.name}/annotation.md", source_run=root.name))
                ready+=1;costs+=state['generation_estimate_usd']
            elif (folder/'attempt.json').exists():
                state=common.read(folder/'attempt.json')
                if state['status']=='stopped':stopped.append(dict(trace=folder.name,error=state.get('error')))
        for repeat in range(1,reference_repeats+1):
            segments,_=binary.load_trace(source,original,e,'sol',repeat)
            relative=f"review_annotations/v9/{binary.trace_name(e['id'],'sol',repeat)}/annotation.md"
            link_copy(source/'traces'/binary.trace_name(e['id'],'sol',repeat)/'annotation.md',root/relative)
            traces['v9'].append(dict(repeat=repeat,segments=segments,markdown=relative,source_run=source.name))
        consensus=enrichment.agreement(values,e['n_frames'],repeats)
        comparisons=[dict(repeat=t['repeat'],**binary.compare(t['segments'],traces['v9'][0]['segments'],e['n_frames'])) for t in traces['v8']]
        rows.append(dict(episode=e['id'],frames=e['n_frames'],repeatability=consensus,v9_repeat_1_comparisons=comparisons))
        data['episodes'].append(dict(id=e['id'],task=e['task'],split=e['split'],lab=e['lab'],
            fps=e['fps'],n_frames=e['n_frames'],videos=e['videos'],teachers=traces,repeatability=consensus,
            source_run=root.name+' / '+source.name,source_manifest_sha256=m['source_manifest_sha256']))
    attach_action_overlay(root,m,data)
    complete=[r for r in rows if r['repeatability']['complete']]
    if stopped:
        data['status_message']='Collection stopped: API credits exhausted' if any('credit_balance_exhausted' in (s['error'] or '') for s in stopped) else 'Collection stopped; inspect the preserved request diagnostics'
    exact=sum(r['repeatability']['binary_exact_3_of_3'] for r in complete)
    full_frames=sum(r['frames'] for r in complete)
    summary=dict(v8_ready=ready,v8_planned=len(m['episodes'])*repeats,
        v9_reused=len(m['episodes'])*reference_repeats,new_astra_calls=0,generation_estimate_usd=costs,
        complete_repeat_episodes=len(complete),binary_exact_3_of_3_episodes=exact,
        unanimous_frames=sum(r['repeatability']['unanimous_frames'] for r in complete),
        evaluated_source_frames=full_frames,
        pooled_frame_unanimity=sum(r['repeatability']['unanimous_frames'] for r in complete)/full_frames if full_frames else None,
        rows=rows,stopped=stopped,collection_status='stopped' if stopped else ('completed' if ready==len(m['episodes'])*repeats else 'in_progress'))
    cross=[score for row in rows for score in row['v9_repeat_1_comparisons']]
    cross_frames=sum(s['frames'] for s in cross)
    summary['v9_repeat_1_frame_agreement']=(cross_frames-sum(s['disagreement_frames'] for s in cross))/cross_frames if cross_frames else None
    transport.atomic_json(root/'comparison_results.json',summary)
    lines=['# V8.1 Sol: three independent repeats and V9.1 comparison','',
        f'- Native enriched responses: {ready}/{len(m["episodes"])*repeats}. Estimated validated-call cost: ${costs:.6f}.',
        f'- Full-episode binary 3/3 agreement: {exact}/{len(complete)} fully repeated episodes ({len(m["episodes"])} planned).',
        '- Three-way frame unanimity counts frames where all three Yes/No labels agree. It is not average pairwise agreement.',
        '- Exact binary agreement includes all boundaries; no voting or boundary adjustment is applied.',
        '- Category-set agreement is assessed only when binary intervals match. Explanation meaning requires human review.',
        '- Repeat consistency and teacher agreement are not human-reference accuracy.',
        '- All original frames/cameras are supplied, no source labels or other predictions are supplied, and no Astra calls are made.','',
        '| Episode | Responses | Binary 3/3 exact | Frames unanimous | Category sets 3/3 |',
        '| --- | ---: | --- | ---: | --- |']
    for row in rows:
        r=row['repeatability']; exact_text='Pending' if not r['complete'] else ('Yes' if r['binary_exact_3_of_3'] else 'No')
        frames='Pending' if r['frame_unanimity'] is None else f"{100*r['frame_unanimity']:.2f}%"
        cats='Not comparable' if r['category_exact_3_of_3'] is None else ('Yes' if r['category_exact_3_of_3'] else 'No')
        lines.append(f"| {row['episode']} | {r['available_repeats']}/{repeats} | {exact_text} | {frames} | {cats} |")
    lines+=['','## Agreement with approved V9.1 Sol repeat 1','',
        'Each column compares one new V8.1 repeat to the same preselected V9.1 reference. These percentages measure teacher-label agreement.','',
        '| Episode | V8.1 repeat 1 | V8.1 repeat 2 | V8.1 repeat 3 |','| --- | ---: | ---: | ---: |']
    for row in rows:
        by_repeat={s['repeat']:s for s in row['v9_repeat_1_comparisons']}
        scores=[f"{100*by_repeat[r]['frame_agreement']:.2f}%" if r in by_repeat else 'Pending' for r in range(1,4)]
        lines.append('| '+row['episode']+' | '+' | '.join(scores)+' |')
    lines+=['','## Repeat disagreement intervals','']
    for row in complete:
        intervals=row['repeatability']['disagreement_intervals']
        spans=', '.join(f"[{s['start_frame']}, {s['end_frame']})" for s in intervals) or 'None'
        lines.append(f"- {row['episode']}: {spans}.")
    if stopped:
        lines+=['','## Stopped calls','']+[f"- {s['trace']}: {s['error']}" for s in stopped]
    template=TEMPLATE.read_text(encoding='utf-8')
    embedded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    temporary=root/'review.html.tmp';temporary.write_text(template.replace('__DATA__',embedded),encoding='utf-8');temporary.replace(root/'review.html')
    transport.atomic_json(root/'review_data.json',data)
    (root/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {k:v for k,v in summary.items() if k not in ('rows',)}


def review(root,m=None):
    root=Path(root);m=m or verify(root)
    return review_enriched(root,m) if m['config'].get('annotation_schema')==enrichment.SCHEMA else review_atomic(root,m)


def merge_action_segments(segments):
    """Derive action boxes independently of all failure/category judgments."""
    result=[]
    for index,s in enumerate(segments):
        identity=(s['action_id'],s['action'],s.get('object_id'),s.get('destination_id'))
        if result and result[-1]['identity']==identity and result[-1]['end_frame']==s['start_frame']:
            result[-1]['end_frame']=s['end_frame'];result[-1]['source_segments'].append(index+1)
        else:
            result.append(dict(start_frame=s['start_frame'],end_frame=s['end_frame'],action=s['action'],
                               identity=identity,source_segments=[index+1]))
    for s in result:s.pop('identity')
    return result


def attach_action_overlay(root,m,data):
    options=root/'review_options.json'
    if not options.exists():return
    settings=common.read(options)
    action_root=common.inside(common.ROOT,settings['action_source_run'])
    action_manifest=common.read(action_root/'manifest.json')
    if common.sha(action_root/'manifest.json')!=settings['action_manifest_sha256']:
        raise ValueError('Saved action source manifest changed')
    if action_manifest['episodes']!=m['episodes'] or action_manifest['source_manifest_sha256']!=m['source_manifest_sha256']:
        raise ValueError('Action boxes require the same original episode/frame/camera evidence')
    if action_manifest['config']['teachers']!={'sol':m['config']['teachers']['sol']}:
        raise ValueError('Action overlay must use saved Sol annotations')
    source_episodes={e['id']:e for e in action_manifest['episodes']}
    for e in data['episodes']:
        value,state,_=load_rich(action_root,action_manifest,source_episodes[e['id']],1)
        e['action_segments']=merge_action_segments(value['segments'])
        e['action_source']=dict(run=action_root.name,prompt='V8',teacher='Sol',repeat=1,
            manifest_sha256=settings['action_manifest_sha256'],annotation_sha256=state['annotation_sha256'],derived_overlay=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare'); p.add_argument('--config', type=Path, required=True)
    for name in ('verify', 'preflight', 'collect', 'review', 'audit-inputs'):
        p = commands.add_parser(name); p.add_argument('--run', type=Path, required=True)
        if name == 'collect':
            p.add_argument('--budget-usd', type=float, required=True)
            p.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.config)
    elif args.command == 'collect':
        result = collect(args.run, args.budget_usd, args.workers)
    elif args.command == 'verify':
        result = dict(verified=True, episodes=len(verify(args.run)['episodes']))
    elif args.command == 'audit-inputs':
        result = audit_requests(args.run)
    else:
        result = globals()[args.command](args.run)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
