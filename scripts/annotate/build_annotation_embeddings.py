"""Local embedding cache; downloads model weights, never sends annotation text to APIs."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import numpy as np
from fastembed import TextEmbedding

ROOT=Path(__file__).resolve().parents[2]
MODEL='sentence-transformers/all-MiniLM-L6-v2'


def build(texts,folder):
    folder.mkdir(parents=True,exist_ok=True)
    model=TextEmbedding(model_name=MODEL,cache_dir=str(ROOT/'outputs/evaluation_model_cache'),threads=4)
    # Use exact tokenization to prevent silent truncation of long descriptions.
    tokenizer=model.model.tokenizer
    limit=(tokenizer.truncation or {}).get('max_length',256)
    tokenizer.no_truncation()
    chunks=[];owners=[]
    for text in sorted(set(texts)):
        current=[]
        for word in text.split():
            candidate=' '.join(current+[word])
            if len(tokenizer.encode(candidate).ids)>limit:
                if not current:raise ValueError('A single word exceeds the embedding context')
                chunks.append(' '.join(current));owners.append(text);current=[word]
            else:current.append(word)
        if current:chunks.append(' '.join(current));owners.append(text)
    tokenizer.enable_truncation(max_length=limit)
    vectors={text:[] for text in set(owners)}
    for owner,chunk,vec in zip(owners,chunks,model.embed(chunks,batch_size=32)):
        if not np.isfinite(vec).all():raise ValueError('Non-finite embedding')
        vectors[owner].append((vec,len(chunk.split())))
    result={}
    for text,parts in vectors.items():
        v=sum(vec*weight for vec,weight in parts)/sum(weight for _,weight in parts)
        v=v/np.linalg.norm(v);result[text]=v.tolist()
    model_dir=Path(model.model._model_dir)
    metadata={'model':MODEL,'fastembed_version':importlib.metadata.version('fastembed'),
              'onnxruntime_version':importlib.metadata.version('onnxruntime'),
              'model_files_sha256':{p.relative_to(model_dir).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(model_dir.rglob('*')) if p.is_file()},
              'token_limit':limit,'chunking':'exact-token-limit chunks, word-count-weighted mean then L2 normalization',
              'texts':len(result),'chunks':len(chunks),'paid_api_calls':0}
    (folder/'embeddings.json').write_text(json.dumps(result),encoding='utf-8')
    (folder/'embedding_manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('texts',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();build(json.loads(args.texts.read_text(encoding='utf-8')),args.output)
