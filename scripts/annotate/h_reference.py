"""Read frozen H human segments; explicit legacy-schema projection, never API input."""
import hashlib
import json
from pathlib import Path


def human_reference(root,eid,n):
    freeze=json.loads((root/'human_reference_freeze.json').read_text(encoding='utf-8'))
    path=root/'human_references'/(eid+'.json')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=freeze['files'][path.name]['sha256']:
        raise ValueError('Human reference hash changed')
    raw=json.loads(path.read_text(encoding='utf-8'));rows=[];cursor=0
    for s in raw['segments']:
        if s['start']!=cursor or not cursor<s['end']<=n:raise ValueError('Human coverage invalid')
        c=s['classification']
        if c not in ('progress','failure','neutral'):raise ValueError('Unsupported H class')
        rows.append({'start':s['start'],'end':s['end'],'progress':c=='progress','failure':c=='failure',
                     'legacy_classification':c,'description':s['text'],'failure_reason':s.get('note',''),
                     'failure_types':s.get('failure_type','unknown') if c=='failure' else 'none',
                     'review_required':False,'title':s['text']})
        cursor=s['end']
    if cursor!=n:raise ValueError('Human reference incomplete')
    return rows,raw


def legacy_projection(predictions):
    # Explicit evaluation-only projection; never overwrite API output or claim a four-state reference.
    return [dict(s,progress=bool(s['progress'] and not s['failure'])) for s in predictions]
