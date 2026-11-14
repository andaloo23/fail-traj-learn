"""Local full-frame GPT/Gemini taxonomy review. No API calls."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import shutil
import webbrowser
from pathlib import Path
import api_taxonomy_pilot_v1 as pilot
import api_taxonomy_pilot_v2 as revised
import api_taxonomy_pilot_v3 as complete
import api_taxonomy_identity_v4 as identity
import api_taxonomy_explicit_v5 as explicit
import api_taxonomy_progress_v6 as progress
import api_taxonomy_approach_v7 as approach
import api_taxonomy_luna_v8 as luna
import api_taxonomy_astra_v9 as astra
import api_taxonomy_complete_failures_v11 as complete_failures
import api_taxonomy_stages_v12 as stages
import api_taxonomy_vocabulary_v13 as vocabulary
import api_taxonomy_vocabulary_v14 as vocabulary14
import api_taxonomy_states_v15 as states15


def display_annotation(answer, module, ep):
    """Display-only envelope normalization; never change interval content."""
    value=json.loads(answer)
    if module in (explicit,progress,approach,luna,astra,complete_failures,stages,vocabulary,vocabulary14,states15):
        # The request captions call the agent view "external camera".
        # Preserve the raw answer/strict failure; map that camera alias for display.
        changed=False
        for item in [value['identity_check'],*value['segments']]:
            for evidence in item['evidence']:
                if evidence['camera']=='external':
                    evidence['camera']='agent'
                    changed=True
        for segment in value['segments']:
            if segment['resetability']=='immediately_reattempt':
                segment['resetability']='immediate'
                changed=True
        if not changed:
            raise ValueError('Not the recognized external-camera alias')
        displayed=value
    elif module is complete:
        required={'episode_id','segments'}
        extra={'task','n_frames','fps','sampled_frames'}
        if not required <= set(value) or not set(value) <= required|extra:
            raise ValueError('Not recognized echoed input metadata')
        if any(value[k]!=ep[k] for k in extra & set(value)):
            raise ValueError('Echoed metadata differs from source')
        displayed={k:value[k] for k in required}
    else:
        if set(value) != {'id','segments'} or value['id'] != ep['id']:
            raise ValueError('Not the recognized episode-id spelling mismatch')
        displayed={'episode_id':value['id'],'segments':value['segments']}
    module.validate(displayed,ep)
    return displayed


def build():
    import numpy as np
    from PIL import Image
    m = pilot.verify()
    runs = [('v1', 'V1 — adapted taxonomy', pilot)]
    if (revised.OUT / 'manifest.json').exists():
        revised.verify()
        runs.append(('v2', 'V2 — your original taxonomy', revised))
    if (complete.OUT / 'manifest.json').exists():
        complete.verify()
        runs.append(('v3', 'V3 — complete progress + failure', complete))
    if (explicit.OUT / 'manifest.json').exists():
        explicit.verify()
        runs.append(('v5', 'V5 — restored explicit evidence instructions', explicit))
    if (progress.OUT / 'manifest.json').exists():
        progress.verify()
        runs.append(('v6', 'V6 - observable progress definition', progress))
    if (approach.OUT / 'manifest.json').exists():
        approach.verify()
        runs.append(('v7', 'V7 - useful approach and failure boundaries', approach))
    if (luna.OUT / 'manifest.json').exists():
        luna.verify()
        runs.append(('v8', 'V8 - current Sol / Luna (same V7 prompt)', luna))
    if (astra.OUT / 'manifest.json').exists():
        astra.verify()
        runs.append(('v9', 'V9 - current Sol / Astra (same V7 prompt)', astra))
    if (complete_failures.OUT / 'manifest.json').exists():
        complete_failures.verify()
        runs.append(('v11', 'V11 - Sol V7 / Sol complete failure tracking', complete_failures))
    if (stages.OUT / 'manifest.json').exists():
        stages.verify()
        runs.append(('v12', 'V12 - Sol / Gemini (manipulation stages)', stages))
    if (vocabulary.OUT / 'manifest.json').exists():
        vocabulary.verify()
        runs.append(('v13', 'V13 - Sol / Gemini (vocabulary guidance)', vocabulary))
    if (vocabulary14.OUT / 'manifest.json').exists():
        vocabulary14.verify()
        runs.append(('v14', 'V14 - Sol / Gemini (expanded vocabulary and stage merging)', vocabulary14))
    if (states15.OUT / 'manifest.json').exists():
        states15.verify()
        runs.append(('v15', 'V15 - Sol / Gemini (state-based segments)', states15))
    target = pilot.OUT / 'web_review'
    target.mkdir(exist_ok=True)
    for ident, label, module in runs:
        shutil.copyfile(module.OUT / 'prompt.txt', target / (ident+'_prompt.txt'))
    identity_run=(identity.OUT/'manifest.json').exists()
    if identity_run:
        identity.verify()
        shutil.copyfile(identity.OUT/'prompt.txt',target/'v4_prompt.txt')
    episodes = []
    for ep in m['episodes']:
        eid = ep['id']
        source = pilot.common.SOURCE / eid / 'cameras.npz'
        digest = pilot.common.digest(source)
        if digest != ep['source_sha256']['cameras.npz']:
            raise ValueError('Source camera hash mismatch')
        folder = target / 'frames' / eid
        folder.mkdir(parents=True, exist_ok=True)
        stamp = folder / 'source.sha256'
        expected = [folder / f'{i:04d}_{c}.jpg' for i in range(ep['n_frames']) for c in ('agent','wrist')]
        if not stamp.exists() or stamp.read_text()!=digest or not all(p.exists() for p in expected):
            with np.load(source,allow_pickle=False) as arrays:
                for c in ('agent','wrist'):
                    if len(arrays[c]) != ep['n_frames']: raise ValueError('Frame count')
                    for i,frame in enumerate(arrays[c]):
                        Image.fromarray(frame).save(folder/f'{i:04d}_{c}.jpg',quality=95)
            stamp.write_text(digest)
        sampled=target/'sampled'/eid
        sampled.mkdir(parents=True,exist_ok=True)
        for f in ep['sampled_frames']:
            for c in ('agent','wrist'):
                name=f'{f:04d}_{c}.jpg'
                shutil.copyfile(pilot.OUT/eid/name,sampled/name)
        versions={}
        statuses={}
        for ident, label, module in runs:
            other=module.common.load(module.OUT/eid/'input.json')
            if other != ep:
                raise ValueError('Viewer requires identical episode inputs across prompt versions')
            for f in ep['sampled_frames']:
                for c in ('agent','wrist'):
                    name=f'{f:04d}_{c}.jpg'
                    if module.common.digest(module.OUT/eid/name)!=pilot.common.digest(pilot.OUT/eid/name):
                        raise ValueError('Sampled image bytes differ across versions')
            annotations={}
            run_status={}
            for provider in module.MODELS:
                p=module.OUT/f'{eid}_{provider}_annotation.json'
                annotations[provider]=module.common.load(p) if p.exists() else None
                if annotations[provider] is not None: module.validate(annotations[provider],ep)
                slot=module.OUT/'attempts'/f'{eid}_{provider}.json'
                record=module.common.load(slot) if slot.exists() else {}
                answer=module.OUT/f'{eid}_{provider}_answer.txt'
                raw_link=None
                if answer.exists():
                    raw_link=f'{ident}_{eid}_{provider}_answer.txt'
                    shutil.copyfile(answer,target/raw_link)
                display_note=''
                if annotations[provider] is None and ident in ('v2','v3','v5','v6','v7','v8','v9','v11','v12','v13','v14','v15') and answer.exists():
                    try:
                        annotations[provider]=display_annotation(answer.read_text(encoding='utf-8'),module,ep)
                        display_note=('Original response used id instead of episode_id. Display-only field mapping; labels and timing are unchanged. Original strict validation remains failed.' if ident=='v2' else
                            'Original response echoed extra input metadata. Display ignores those extra envelope fields; every segment and label is unchanged and full coverage validates. Original strict schema validation remains failed.')
                        if ident in ('v5','v6','v7','v8','v9','v11','v12','v13','v14','v15'):
                            display_note='Display-only schema aliases: external camera → agent; immediately_reattempt → immediate where present. All frame references, categorical meanings, and timing are unchanged. Original strict validation remains failed; see the raw response.'
                    except (ValueError,TypeError,KeyError):
                        pass
                run_status[provider]={'status':record.get('status','pending'),
                    'error':record.get('error',''),'raw_link':raw_link,'display_note':display_note}
            versions[ident]=annotations
            statuses[ident]=run_status
        for comparison in ('v8','v9','v11'):
            if comparison in versions:
                # Column IDs are historical; visible titles identify the actual models.
                versions[comparison]={'openai':versions['v7']['openai'],'gemini':versions[comparison]['openai']}
                statuses[comparison]={'openai':statuses['v7']['openai'],'gemini':statuses[comparison]['openai']}
        for version in ('v12','v13','v14','v15'):
            if version not in versions:continue
            current=versions[version]; current_status=statuses[version]
            versions[version+'_astra']={'openai':current['openai'],'gemini':current['astra']}
            statuses[version+'_astra']={'openai':current_status['openai'],'gemini':current_status['astra']}
            versions[version+'_astra_gemini']={'openai':current['astra'],'gemini':current['gemini']}
            statuses[version+'_astra_gemini']={'openai':current_status['astra'],'gemini':current_status['gemini']}
            versions[version]={'openai':current['openai'],'gemini':current['gemini']}
            statuses[version]={'openai':current_status['openai'],'gemini':current_status['gemini']}
        if 'v12' in versions and 'v13' in versions:
            for model, run, provider in [('sol','', 'openai'),('astra','_astra','gemini'),('gemini','', 'gemini')]:
                ident='v13_before_after_'+model
                versions[ident]={'openai':versions['v12'+run][provider],'gemini':versions['v13'+run][provider]}
                statuses[ident]={'openai':statuses['v12'+run][provider],'gemini':statuses['v13'+run][provider]}
        if 'v13' in versions and 'v14' in versions:
            for model, run, provider in [('sol','', 'openai'),('astra','_astra','gemini'),('gemini','', 'gemini')]:
                ident='v14_before_after_'+model
                versions[ident]={'openai':versions['v13'+run][provider],'gemini':versions['v14'+run][provider]}
                statuses[ident]={'openai':statuses['v13'+run][provider],'gemini':statuses['v14'+run][provider]}
        if 'v14' in versions and 'v15' in versions:
            for model, run, provider in [('sol','', 'openai'),('astra','_astra','gemini'),('gemini','', 'gemini')]:
                ident='v15_before_after_'+model
                versions[ident]={'openai':versions['v14'+run][provider],'gemini':versions['v15'+run][provider]}
                statuses[ident]={'openai':statuses['v14'+run][provider],'gemini':statuses['v15'+run][provider]}
        if 'v11' in versions and 'v9' in versions:
            versions['v11_astra']={'openai':versions['v11']['gemini'],
                                   'gemini':versions['v9']['gemini']}
            statuses['v11_astra']={'openai':statuses['v11']['gemini'],
                                  'gemini':statuses['v9']['gemini']}
        if identity_run:
            updated=None
            record={}
            raw_link=None
            if eid in identity.IDS:
                if identity.common.load(identity.OUT/eid/'input.json')!=ep:
                    raise ValueError('Identity diagnostic inputs differ')
                for f in ep['sampled_frames']:
                    for c in ('agent','wrist'):
                        name=f'{f:04d}_{c}.jpg'
                        if identity.common.digest(identity.OUT/eid/name)!=pilot.common.digest(pilot.OUT/eid/name):
                            raise ValueError('Identity diagnostic image bytes differ')
                path=identity.OUT/f'{eid}_openai_annotation.json'
                if path.exists():
                    updated=identity.common.load(path)
                    identity.validate(updated,ep)
                slot=identity.OUT/'attempts'/f'{eid}_openai.json'
                record=identity.common.load(slot) if slot.exists() else {}
                answer=identity.OUT/f'{eid}_openai_answer.txt'
                if answer.exists():
                    raw_link=f'v4_{eid}_openai_answer.txt'
                    shutil.copyfile(answer,target/raw_link)
            # These are display columns, explicitly titled GPT before/after in V4.
            versions['v4']={'openai':versions['v3']['openai'],'gemini':updated}
            statuses['v4']={'openai':statuses['v3']['openai'],'gemini':{
                'status':record.get('status','not planned: diagnostic covers R001 and R003'),
                'error':record.get('error',''),'raw_link':raw_link,'display_note':''}}
        episodes.append({k:ep[k] for k in ('id','task','n_frames','fps','sampled_frames')} |
                        {'annotations':versions[runs[-1][0]], 'versions':versions, 'statuses':statuses})
    choices=[{'id':i,'label':label} for i,label,module in runs]
    for choice in choices:
        if choice['id']=='v11':
            choice.update(columns={'openai':'Sol V7 (previous prompt)',
                                   'gemini':'Sol V11 (complete failure tracking)'},
                          heading='Sol V7 vs Sol V11 - complete failure tracking')
    if all(any(i==version for i,_,_ in runs) for version in ('v11','v9')):
        choices.append(dict(id='v11_astra',label='Sol V11 / Astra V9 (previous prompt)',
                            columns={'openai':'Sol V11 (complete failure tracking)',
                                     'gemini':'Astra V9 (V7 prompt)'},
                            heading='Sol V11 vs Astra V9 - different prompts',
                            prompt_file='v11_prompt.txt',prompt_label='Sol V11 prompt',
                            right_prompt_file='v9_prompt.txt',right_prompt_label='Astra V9 prompt'))
    if any(i=='v12' for i,_,_ in runs):
        for choice in choices:
            if choice['id']=='v12':
                choice.update(columns={'openai':'Sol V12','gemini':'Gemini V12'},
                              heading='Sol vs Gemini - V12 manipulation stages',prompt_file='v12_prompt.txt')
        choices.extend([
            dict(id='v12_astra',label='V12 - Sol / Astra (manipulation stages)',
                 columns={'openai':'Sol V12','gemini':'Astra V12'},
                 heading='Sol vs Astra - V12 manipulation stages',prompt_file='v12_prompt.txt'),
            dict(id='v12_astra_gemini',label='V12 - Astra / Gemini (manipulation stages)',
                 columns={'openai':'Astra V12','gemini':'Gemini V12'},
                 heading='Astra vs Gemini - V12 manipulation stages',prompt_file='v12_prompt.txt')])
    if any(i=='v13' for i,_,_ in runs):
        for choice in choices:
            if choice['id']=='v13':
                choice.update(columns={'openai':'Sol V13','gemini':'Gemini V13'},
                              heading='Sol vs Gemini - V13 vocabulary guidance',prompt_file='v13_prompt.txt')
        choices.extend([
            dict(id='v13_astra',label='V13 - Sol / Astra (vocabulary guidance)',
                 columns={'openai':'Sol V13','gemini':'Astra V13'},
                 heading='Sol vs Astra - V13 vocabulary guidance',prompt_file='v13_prompt.txt'),
            dict(id='v13_astra_gemini',label='V13 - Astra / Gemini (vocabulary guidance)',
                 columns={'openai':'Astra V13','gemini':'Gemini V13'},
                 heading='Astra vs Gemini - V13 vocabulary guidance',prompt_file='v13_prompt.txt')])
        for model in ('sol','astra','gemini'):
            name=model.title()
            choices.append(dict(id='v13_before_after_'+model,label='Vocabulary before / after - '+name,
                                columns={'openai':name+' V12 (before)','gemini':name+' V13 (vocabulary)'},
                                heading=name+' - vocabulary before / after',
                                prompt_file='v12_prompt.txt',prompt_label='Before: V12 prompt',
                                right_prompt_file='v13_prompt.txt',right_prompt_label='After: V13 prompt'))
    if any(i=='v14' for i,_,_ in runs):
        for choice in choices:
            if choice['id']=='v14':
                choice.update(columns={'openai':'Sol V14','gemini':'Gemini V14'},heading='Sol vs Gemini - V14',prompt_file='v14_prompt.txt')
        choices.extend([
            dict(id='v14_astra',label='V14 - Sol / Astra',columns={'openai':'Sol V14','gemini':'Astra V14'},heading='Sol vs Astra - V14',prompt_file='v14_prompt.txt'),
            dict(id='v14_astra_gemini',label='V14 - Astra / Gemini',columns={'openai':'Astra V14','gemini':'Gemini V14'},heading='Astra vs Gemini - V14',prompt_file='v14_prompt.txt')])
        for model in ('sol','astra','gemini'):
            name=model.title()
            choices.append(dict(id='v14_before_after_'+model,label='V13 / V14 - '+name,
                columns={'openai':name+' V13','gemini':name+' V14'},heading=name+' - V13 vs V14',
                prompt_file='v13_prompt.txt',prompt_label='Before: V13 prompt',right_prompt_file='v14_prompt.txt',right_prompt_label='After: V14 prompt'))
    if any(i=='v15' for i,_,_ in runs):
        for choice in choices:
            if choice['id']=='v15':
                choice.update(columns={'openai':'Sol V15','gemini':'Gemini V15'},heading='Sol vs Gemini - V15',prompt_file='v15_prompt.txt')
        choices.extend([
            dict(id='v15_astra',label='V15 - Sol / Astra (state-based)',columns={'openai':'Sol V15','gemini':'Astra V15'},heading='Sol vs Astra - V15',prompt_file='v15_prompt.txt'),
            dict(id='v15_astra_gemini',label='V15 - Astra / Gemini (state-based)',columns={'openai':'Astra V15','gemini':'Gemini V15'},heading='Astra vs Gemini - V15',prompt_file='v15_prompt.txt')])
        for model in ('sol','astra','gemini'):
            name=model.title()
            choices.append(dict(id='v15_before_after_'+model,label='V14 / V15 - '+name,
                columns={'openai':name+' V14','gemini':name+' V15'},heading=name+' - V14 vs V15',
                prompt_file='v14_prompt.txt',prompt_label='Before: V14 prompt',right_prompt_file='v15_prompt.txt',right_prompt_label='After: V15 prompt'))
    if identity_run:
        choices.append({'id':'v4','label':'V4 — GPT identity check: before / after'})
    from review_sol_frame_budget_v10 import extend
    frame_default=extend(target,episodes,choices)
    from review_atomic_actions import extend as extend_atomic
    atomic_default=extend_atomic(target,episodes,choices)
    pilot.common.write_json(target/'data.json',dict(models=pilot.MODELS,episodes=episodes,
        runs=sorted(choices,key=lambda choice: choice['id']),
        default_run=atomic_default or ('v15_astra' if any(c['id']=='v15_astra' for c in choices) else 'v14_astra' if any(c['id']=='v14_astra' for c in choices) else 'v13_astra' if any(c['id']=='v13_astra' for c in choices) else 'v12_astra' if any(c['id']=='v12_astra' for c in choices) else 'v11_astra' if any(c['id']=='v11_astra' for c in choices) else 'v11' if any(i=='v11' for i,_,_ in runs) else frame_default or (runs[-1][0] if runs[-1][0] in ('v5','v6','v7','v8','v9') else ('v4' if identity_run else runs[-1][0])))))
    shutil.copyfile(Path(__file__).with_suffix('.html'),target/'index.html')
    return target


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=int,default=8767)
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--no-browser',action='store_true')
    args=p.parse_args()
    folder=build()
    if not args.prepare_only:
        server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(SimpleHTTPRequestHandler,directory=str(folder)))
        url=f'http://127.0.0.1:{args.port}/'
        print(url,flush=True)
        if not args.no_browser: webbrowser.open(url)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()
