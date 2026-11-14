"""Run cached local NLI and embedding baselines on a frozen judge benchmark."""
import argparse
from importlib.metadata import version
from pathlib import Path
import time

import annotation_runtime as io


def score(manifest_path, out, model_key):
    import numpy as np
    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer
    torch.set_num_threads(4)
    manifest = io.load(manifest_path)
    rows = [dict(batch=b['id'], task=b['task'], **p)
            for b in manifest['batches'] for p in b['pairs']]
    pairs = [(r['left'], r['right']) for r in rows]
    started = time.time()
    if model_key == 'nli':
        ident = 'cross-encoder/nli-deberta-v3-base'
        model = CrossEncoder(ident, device='cpu', local_files_only=True)
        labels = ['contradiction', 'entailment', 'neutral']
        # The model card specifies these class meanings; generic LABEL_n values
        # in the saved config do not establish their semantics.
        both = pairs + [(b, a) for a, b in pairs]
        for a, b in both:
            if len(model.tokenizer.encode(a, b)) > model.max_length:
                raise ValueError('Text pair would be truncated')
        probabilities = model.predict(both, batch_size=8, show_progress_bar=False,
                                      activation_fn=torch.nn.Softmax(dim=1))
        forward, reverse = probabilities[:len(rows)], probabilities[len(rows):]
        for row, a, b in zip(rows, forward, reverse):
            row.update(forward=dict(zip(labels, map(float, a))), reverse=dict(zip(labels, map(float, b))),
                       mean_entailment=float((a[1]+b[1])/2),
                       minimum_entailment=float(min(a[1], b[1])),
                       mean_contradiction=float((a[0]+b[0])/2))
    else:
        ident = 'sentence-transformers/all-MiniLM-L6-v2'
        model = SentenceTransformer(ident, device='cpu', local_files_only=True)
        texts = sorted({s for p in pairs for s in p})
        if any(len(model.tokenizer.encode(t)) > model.max_seq_length for t in texts):
            raise ValueError('Description would be truncated')
        vectors = model.encode(texts, normalize_embeddings=True, batch_size=16)
        index = {t: i for i, t in enumerate(texts)}
        for row in rows:
            row['cosine'] = float(vectors[index[row['left']]] @ vectors[index[row['right']]])
    out.parent.mkdir(parents=True, exist_ok=True)
    io.atomic_json(out, dict(model=ident, manifest_sha256=io.digest(manifest_path),
        script_sha256=io.digest(Path(__file__)), seconds=round(time.time()-started, 2),
        packages={p: version(p) for p in ('torch', 'sentence-transformers', 'transformers')},
        pairs=rows, limitations='Text relations only; probabilities and cosine are not video correctness scores. No fitted acceptance threshold.',
        paid_api_calls=0))
    print(f'{model_key}: scored {len(rows)} frozen description pairs locally; saved {out}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--model', choices=('nli', 'minilm'), required=True)
    args = parser.parse_args()
    score(args.manifest.resolve(), args.out.resolve(), args.model)
