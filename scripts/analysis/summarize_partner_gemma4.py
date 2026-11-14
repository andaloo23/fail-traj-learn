"""Report completed paired validation results; no inference or training."""
from collections import Counter
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'outputs/partner_gemma4_archive_20261113_v1'
KEYS = ['tp','fp','fn','tn','unknown_positive','unknown_negative']


def main():
    results = json.loads((RUN / 'results.json').read_text())
    tags = ['partner','existing_qwen_evidence_aux','existing_qwen_joint','existing_qwen_binary']
    if any(t not in results or results[t]['missing_windows'] for t in tags):
        raise ValueError('Paired comparison requires every validation window for every selected model')
    ids = sorted(r['episode'] for r in results['partner']['per_episode'])
    arrays = []
    for tag in tags:
        rows = {r['episode']:r['metrics'] for r in results[tag]['per_episode']}
        assert sorted(rows) == ids and len(ids) == 50
        arr = np.array([[rows[e][k] for k in KEYS] for e in ids],dtype=np.int64)
        assert int(arr.sum()) == 8132
        c = arr.sum(0)
        f1 = 2*c[0]/(2*c[0]+c[1]+c[2]+c[4])
        assert abs(f1-results[tag]['metrics']['failure_f1']) < 1e-12
        arrays.append(arr)
    rng = np.random.default_rng(20261113)
    sample = rng.integers(0,50,size=(5000,50))
    distributions = []; intervals = {}
    for tag, arr in zip(tags, arrays):
        c = arr[sample].sum(1)
        denominator = 2*c[:,0]+c[:,1]+c[:,2]+c[:,4]
        f1 = np.divide(2*c[:,0],denominator,out=np.full(5000,np.nan),where=denominator!=0)
        distributions.append(f1)
        intervals[tag] = np.nanpercentile(f1,[2.5,97.5]).tolist()
    difference = distributions[0]-distributions[1]
    uncertainty = dict(unit='whole validation episode',seed=20261113,rounds=5000,
        failure_f1_percentile_95=intervals,
        partner_minus_existing_qwen_evidence_aux_f1_95=np.nanpercentile(difference,[2.5,97.5]).tolist(),
        limitation='Resampling uncertainty within these 50 teacher-labeled development episodes; not human-label correctness or new-lab generalization.')
    (RUN / 'paired_uncertainty.json').write_text(json.dumps(uncertainty,indent=2))
    predictions = [json.loads(p.read_text()) for p in (RUN / 'predictions/partner').glob('*_binary.json')]
    assert len(predictions)==279
    problems=Counter(p.get('parse_error','Unspecified') for p in predictions if not p['strict_output_valid'])
    (RUN / 'output_validity_breakdown.json').write_text(json.dumps(dict(total=279,
        valid=sum(p['strict_output_valid'] for p in predictions),errors=dict(problems)),indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels = ['Partner Gemma','Qwen: explanation aux','Qwen: joint','Qwen: binary']
    colors = ['#3576B8','#399578','#A187B8','#8794A0']
    fig, axes = plt.subplots(1,3,figsize=(13,4.4),layout='constrained')
    for ax,(key,title) in zip(axes,[('failure_f1','Failure F1'),('failure_recall','Failure recall'),('coverage','Output coverage')]):
        values = [100*results[t]['metrics'][key] for t in tags]
        bars=ax.barh(labels,values,color=colors);ax.invert_yaxis();ax.set_xlim(0,110)
        ax.set_title(title);ax.set_xlabel('Percent');ax.spines[['top','right']].set_visible(False)
        for bar,value in zip(bars,values):
            ax.text(value+1,bar.get_y()+bar.get_height()/2,f'{value:.1f}%',va='center',fontsize=10)
    fig.suptitle('Same 50 real OopsieData development episodes · agreement with frozen Sol labels',fontsize=13)
    fig.savefig(RUN / 'validation_comparison.png',dpi=180)
    plt.close(fig)
    report=(RUN / 'report.md').read_text(encoding='utf-8')
    report=report.replace('[Frozen input prompt](prompt.md)',
        '[Actual student prompt example](student_prompt_example.md) · [Reference teacher prompt](prompt.md)')
    marker='\n## Additional verification\n'
    report=report.split(marker)[0]+marker
    report+='\nAll archived aggregate metrics match the supplied per-episode score files. All 50 archived teacher metadata rows also match the preserved historical LIBERO export. The historical confident subset contains only one failure-positive episode out of 19. The original comparison also includes an incomplete 44-episode SFT run alongside 50-episode runs.\n'
    report+='\nThe current real validation set contains 48 Princeton_IRoM episodes and two Princeton_PRISM episodes. Of 8,132 source frames, 2,095 are failure-positive. Always predicting non-failure gives 74.24% frame agreement and 0% failure recall/F1.\n'
    batches=Counter(p.get('batch_size',1) for p in predictions)
    report+='\nInference used the same fixed greedy decoding and 768-token cap throughout. Microbatch sizes were increased for GPU utilization; counts by microbatch size: '+', '.join(f'{size}: {count} windows' for size,count in sorted(batches.items()))+'. Batched and single inputs were checked for identical unpadded token IDs, modality markers and image tensors. Previously completed outputs were retained. No predictions were repaired or regenerated based on their score.\n'
    report+='\n| Model | Failure F1 | Episode-bootstrap 95% interval |\n| --- | ---: | ---: |\n'
    for tag,label in zip(tags,labels):
        lo,hi=intervals[tag]
        report+=f'| {label} | {100*results[tag]["metrics"]["failure_f1"]:.2f}% | {100*lo:.2f}%–{100*hi:.2f}% |\n'
    report+='\nBootstrap uses 5,000 paired resamples of whole episodes, retaining dependence between neighboring source frames. It measures uncertainty within this development set, not correctness of teacher labels.\n'
    report+='\n### Invalid-output reasons\n\n'
    report+='\n'.join(f'- {name}: {count} windows.' for name,count in problems.most_common())+'\n'
    report+='\n![Validation comparison](validation_comparison.png)\n'
    (RUN / 'report.md').write_text(report,encoding='utf-8')
    print(json.dumps(dict(complete_windows=279,valid_windows=sum(p['strict_output_valid'] for p in predictions),
        paired_f1_intervals=intervals),indent=2))


if __name__=='__main__':
    main()
