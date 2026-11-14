"""Offline semantic metric stress test. All targets are proxy controls, never correctness labels."""
import sys,json,re,math,random,itertools,collections,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/annotate'))
from annotation_metrics import text_for
from build_annotation_embeddings import build
OUT=ROOT/'outputs/similarity_exploration_v1/semantics'
OUT.mkdir(parents=True,exist_ok=True)
RNG=random.Random(417)
STOP=set('the a an is are was were to of in on and with while it its this that robot arm gripper'.split())
def tokens(t):return [w for w in re.findall(r'[a-z]+',t.lower()) if w not in STOP]
def norm(t):return re.sub(r'\s+',' ',t.lower()).strip()
def auc(pos,neg):
    if not pos or not neg:return None
    n=np.sort(neg);p=np.array(pos)
    return float(np.mean((np.searchsorted(n,p,side='left')+np.searchsorted(n,p,side='right'))/(2*len(n))))
def summary(xs):
    a=np.array(xs);return dict(n=len(a),mean=float(a.mean()),sd=float(a.std()),q05=float(np.quantile(a,.05)),median=float(np.median(a)),q95=float(np.quantile(a,.95))) if len(a) else {}
def main():
    corpus=json.loads((OUT.parent/'corpus.json').read_text(encoding='utf-8'))
    cache={}
    for p in [ROOT/'outputs/annotation_evaluation_v1/embeddings.json',ROOT/'outputs/h_pipeline_evaluation_v1/evaluation/embeddings.json',OUT/'embeddings/embeddings.json']:
        if p.exists():cache.update(json.loads(p.read_text()))
    # Use all valid records supplied by the provenance-checked corpus builder.
    groups=collections.defaultdict(list)
    for r in corpus:groups[r['episode']].append(r)
    eligible=[(ep,rs) for ep,rs in sorted(groups.items()) if len(rs)>=2]
    chosen=[]
    for ep,rs in eligible:
        rs=sorted(rs,key=lambda r:r['id'])
        chosen.extend(rs)
    entries=[];rec_entries={}
    for r in chosen:
        ids=[]
        for s in r['segments']:
            t=text_for(s)
            if t:
                ids.append(len(entries));entries.append(dict(text=t,episode=r['episode'],task=r['task'],record=r['id'],source=r['source'],start=s['start'],end=s['end'],n_frames=r['n_frames']))
        rec_entries[r['id']]=ids
    # Controlled short descriptions: original/paraphrase/factual edit triplets.
    probes=[]
    for obj,other in [('red block','blue block'),('milk carton','juice carton'),('tomato sauce jar','butter package'),('bottle','cup'),('orange juice','milk'),('small cube','large cube')]:
        specs=[(f'The robot grasps the {obj}.',f'The robot takes hold of the {obj}.',f'The robot fails to grasp the {obj}.','negation'),
          (f'The robot places the {obj} in the basket.',f'The robot puts the {obj} into the basket.',f'The robot places the {obj} beside the basket.','destination'),
          (f'The {obj} remains held by the gripper.',f'The gripper continues holding the {obj}.',f'The {obj} slips out of the gripper.','outcome'),
          (f'The robot lifts the {obj}.',f'The robot raises the {obj}.',f'The robot lifts the {other}.','object'),
          (f'The robot moves toward the {obj}.',f'The robot approaches the {obj}.',f'The robot moves away from the {obj}.','direction'),
          (f'The robot successfully grasps the {obj}.',f'The robot manages to grasp the {obj}.',f'The robot unsuccessfully grasps the {obj}.','negation')]
        for a,p,n,k in specs:probes.append(dict(base=a,positive=p,negative=n,kind=k,group=obj,scope='short_template'))
    # Preserve a real paragraph and make one controlled substitution family.
    # These test local sensitivity; source paragraphs are not truth references.
    seen=set()
    for e in entries:
        a=e['text']
        if a in seen:continue
        seen.add(a)
        p=re.sub(r'\b[Tt]he robot\b','The robotic arm',a)
        if p==a:p=re.sub(r'\b[Tt]he gripper\b','The gripping tool',a)
        if p==a:p=re.sub(r'\b[Tt]he arm\b','The robotic arm',a)
        if p==a:continue
        edits=[('basket','table','destination'),('milk','orange juice','object'),('butter','tomato sauce','object'),('orange juice','milk','object'),('tomato sauce','butter','object'),('remains','does not remain','negation')]
        for old,new,k in edits:
            n=re.sub(r'\b'+old+r'\b',new,a,flags=re.I)
            if n!=a:
                probes.append(dict(base=a,positive=p,negative=n,kind=k,group=e['episode'],scope='real_paragraph'));break
        if sum(x['scope']=='real_paragraph' for x in probes)>=80:break
    texts=sorted(set([e['text'] for e in entries]+[p[k] for p in probes for k in ['base','positive','negative']]))
    missing=[t for t in texts if t not in cache]
    print(f'Embedding {len(missing)} missing texts; {len(entries)} segments, {len(chosen)} records',flush=True)
    if missing:cache.update(build(missing,OUT/'embeddings'))
    (OUT/'embeddings/embeddings.json').write_text(json.dumps({t:cache[t] for t in texts}),encoding='utf-8')
    (OUT/'embeddings/cache_manifest.json').write_text(json.dumps({'total_vectors':len(texts),'new_vectors_this_run':len(missing),'model':'sentence-transformers/all-MiniLM-L6-v2','cache_sources':['outputs/annotation_evaluation_v1/embeddings.json','outputs/h_pipeline_evaluation_v1/evaluation/embeddings.json','outputs/similarity_exploration_v1/semantics/embeddings/embeddings.json'],'note':'embedding_manifest.json records the most recent build batch; cache_manifest.json describes the merged vector file.'},indent=2),encoding='utf-8')
    (OUT/'corpus_embeddings.json').write_text(json.dumps({e['text']:cache[e['text']] for e in entries}),encoding='utf-8')
    # Sparse TF-IDF fit only on training episodes (alternating sorted episode split).
    eps=sorted(set(e['episode'] for e in entries));train=set(eps[::2]);test=set(eps[1::2])
    traintexts=[e['text'] for e in entries if e['episode'] in train]
    features={}
    for name,fn in [('word',lambda t:tokens(t)),('char',lambda t:[norm(t)[i:i+4] for i in range(max(0,len(norm(t))-3))])]:
        df=collections.Counter(x for t in traintexts for x in set(fn(t)))
        idf={x:math.log((1+len(traintexts))/(1+n))+1 for x,n in df.items()}
        vs={}
        for t in texts:
            c=collections.Counter(fn(t));v={x:(1+math.log(n))*idf.get(x,math.log(1+len(traintexts))+1) for x,n in c.items()};z=math.sqrt(sum(y*y for y in v.values()));vs[t]={x:y/z for x,y in v.items()} if z else {}
        features[name]=vs
    def sparse(a,b,name):
        x,y=features[name][a],features[name][b];return sum(v*y.get(k,0) for k,v in x.items())
    colors=set('red blue green yellow orange black white brown'.split())
    objects=set('block cube milk juice carton sauce jar butter package bottle cup basket'.split())
    actions=[set(x.split()) for x in ['grasp grasps grasping hold holding held takes', 'lift lifts raises elevated', 'place places puts placement', 'move moves approaches transports transport', 'slips drops dropped releases']]
    def fields(t):
        ts=set(tokens(t));return [ts&colors,ts&objects,{str(i) for i,g in enumerate(actions) if ts&g}]
    def sim(a,b):
        c=float(np.dot(cache[a],cache[b]));x,y=set(tokens(a)),set(tokens(b));j=len(x&y)/len(x|y) if x|y else 1
        vals=dict(cosine=c,word_tfidf=sparse(a,b,'word'),char4_tfidf=sparse(a,b,'char'),token_jaccard=j)
        mismatch=[]
        for u,v in zip(fields(a),fields(b)):
            if u and v:mismatch.append(1-len(u&v)/len(u|v))
        penalty=sum(mismatch)/len(mismatch) if mismatch else 0
        neg=lambda t:bool(re.search(r'\b(not|no|fails?|failed|unsuccessfully|without|unable)\b',t.lower()))
        contradiction=int(neg(a)!=neg(b))
        for w in [.1,.25,.5]:
            vals[f'cosine_fieldpenalty_{w}']=c-w*penalty
            vals[f'cosine_negpenalty_{w}']=c-w*contradiction
            vals[f'cosine_bothpenalty_{w}']=c-w*(penalty+contradiction)
        for w in [.25,.5,.75]:vals[f'cosine_wordmix_{w}']=(1-w)*c+w*vals['word_tfidf']
        return vals
    pairs=[]
    def add(i,j,kind,weight=1):
        a,b=entries[i],entries[j]
        if i==j:return
        pairs.append(dict(i=i,j=j,kind=kind,episode=a['episode'],task=a['task'],split='train' if a['episode'] in train else 'test',weight=weight,scores=sim(a['text'],b['text'])))
    chosen_groups=collections.defaultdict(list)
    for r in chosen:chosen_groups[r['episode']].append(r)
    for ep,rs in chosen_groups.items():
        # Directed pairs remove arbitrary record-order dependence of midpoint shifts.
        for ra,rb in itertools.permutations(rs,2):
            for i in rec_entries[ra['id']]:
                a=entries[i]
                for j in rec_entries[rb['id']]:
                    b=entries[j];overlap=max(0,min(a['end'],b['end'])-max(a['start'],b['start']))
                    if overlap:add(i,j,'aligned',overlap)
                for shift in [.1,.25,.5]:
                    midpoint=((a['start']+a['end'])/2+ra['n_frames']*shift)%ra['n_frames']
                    js=[j for j in rec_entries[rb['id']] if entries[j]['start']<=midpoint<entries[j]['end']]
                    if js:add(i,js[0],f'shift_{shift}')
    for i,a in enumerate(entries):
        # Background examples stay within a split to prevent transductive calibration.
        for kind,pred in [('same_task',lambda b:b['task']==a['task'] and b['episode']!=a['episode']),('different_task',lambda b:b['task']!=a['task'])]:
            candidates=[j for j,b in enumerate(entries) if pred(b) and ((b['episode'] in train)==(a['episode'] in train))]
            for j in RNG.sample(candidates,min(5,len(candidates))):add(i,j,kind)
    names=list(pairs[0]['scores']);results={}
    for name in names:
        by={k:[p['scores'][name] for p in pairs if p['kind']==k and p['split']=='test'] for k in sorted(set(p['kind'] for p in pairs))}
        results[name]={'test_distributions':{k:summary(v) for k,v in by.items()},'aligned_vs_control_auc':{k:auc(by['aligned'],v) for k,v in by.items() if k!='aligned'}}
    probe_rows=[]
    for p in probes:
        pos,neg=sim(p['base'],p['positive']),sim(p['base'],p['negative']);probe_rows.append({**p,'positive_scores':pos,'negative_scores':neg})
    for name in names:
        results[name]['proxy_triplet_accuracy']=float(np.mean([p['positive_scores'][name]>p['negative_scores'][name] for p in probe_rows]))
        results[name]['proxy_by_scope']={k:{'n':sum(p['scope']==k for p in probe_rows),'triplet_accuracy':float(np.mean([p['positive_scores'][name]>p['negative_scores'][name] for p in probe_rows if p['scope']==k])),'positive_mean':float(np.mean([p['positive_scores'][name] for p in probe_rows if p['scope']==k])),'negative_mean':float(np.mean([p['negative_scores'][name] for p in probe_rows if p['scope']==k]))} for k in ['short_template','real_paragraph']}
        results[name]['proxy_by_kind']={k:float(np.mean([p['positive_scores'][name]>p['negative_scores'][name] for p in probe_rows if p['kind']==k])) for k in sorted(set(p['kind'] for p in probes))}
        results[name]['episode_macro_auc']={kind:float(np.mean([auc([p['scores'][name] for p in pairs if p['kind']=='aligned' and p['episode']==ep],[p['scores'][name] for p in pairs if p['kind']==kind and p['episode']==ep]) for ep in test if any(p['kind']==kind and p['episode']==ep for p in pairs)])) for kind in ['same_task','different_task','shift_0.5']}
    # Calibrate test cosine using training-only task-conditioned and pooled backgrounds.
    calibration={}
    for control in ['same_task','different_task','shift_0.5']:
        bg=[p['scores']['cosine'] for p in pairs if p['kind']==control and p['split']=='train']
        if not bg:continue
        taskbg={t:[p['scores']['cosine'] for p in pairs if p['kind']==control and p['split']=='train' and p['task']==t] for t in set(p['task'] for p in pairs)}
        for conditional in [False,True]:
            key=control+('_task' if conditional else '_pooled');rows=[]
            for p in pairs:
                if p['split']!='test':continue
                b=taskbg.get(p['task'],[]) if conditional else bg
                fallback=len(b)<20
                if fallback:b=bg
                v=p['scores']['cosine'];mu=float(np.mean(b));sd=float(np.std(b));pct=float(np.mean(np.array(b)<=v));z=(v-mu)/max(sd,.01)
                # Positive anchor is synthetic paraphrase mean; index not probability.
                anchor=float(np.mean([x['positive_scores']['cosine'] for x in probe_rows if x['group'] in ['red block','milk carton','tomato sauce jar']]))
                rows.append(dict(kind=p['kind'],episode=p['episode'],raw=v,percentile=pct,z=z,anchored=(v-mu)/max(anchor-mu,.01),fallback=fallback))
            calibration[key]={k:{m:summary([r[m] for r in rows if r['kind']==k]) for m in ['raw','percentile','z','anchored']} for k in sorted(set(r['kind'] for r in rows))}
            calibration[key]['fallback_fraction']=float(np.mean([r['fallback'] for r in rows]))
            calibration[key]['auc']={k:{m:auc([r[m] for r in rows if r['kind']=='aligned'],[r[m] for r in rows if r['kind']==k]) for m in ['raw','percentile','z','anchored']} for k in ['same_task','different_task','shift_0.5']}
    report=dict(corpus_records=len(corpus),selected_records=len(chosen),segments=len(entries),episodes=eps,train_episodes=sorted(train),test_episodes=sorted(test),pair_count=len(pairs),metrics=results,calibration=calibration,limitations=['Alignment is not a correctness label.','Template edits are proxy tests and lexicon penalties partly encode those edits.','No model ranking or correctness probability inferred.','All valid corpus records with repeated episodes included.','Pooled segment pairs are diagnostic; no independent-pair confidence intervals claimed.'])
    for name,data in [('results.json',report),('pairs.json',pairs),('probes.json',probe_rows),('entries.json',entries)]:
        (OUT/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({'records':len(chosen),'segments':len(entries),'pairs':len(pairs),'metrics':{k:{'triplet':v['proxy_triplet_accuracy'],'auc':v['aligned_vs_control_auc']} for k,v in results.items()}},indent=2),flush=True)
if __name__=='__main__':main()
