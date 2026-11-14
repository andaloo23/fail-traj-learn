"""Fetch pinned public Qwen files with checked hashes and fresh CDN redirects."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
import requests
from huggingface_hub import HfApi
from huggingface_hub.constants import HF_HUB_CACHE

MODEL='Qwen/Qwen2.5-VL-7B-Instruct'
REVISION='cc594898137f460bfe9f0759e9844b3ce807cfb5'


def main():
    info=HfApi().model_info(MODEL,revision=REVISION,files_metadata=True,token=False)
    root=Path(HF_HUB_CACHE)/'models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots'/REVISION
    root.mkdir(parents=True,exist_ok=True)
    files=[x for x in info.siblings if x.rfilename.endswith(('.safetensors','.json','.txt')) and '/' not in x.rfilename]
    def fetch(meta):
        path=root/meta.rfilename
        lfs=meta.lfs
        expected=lfs.sha256 if lfs else None
        if path.exists() and path.stat().st_size==meta.size:
            if expected:
                with path.open('rb') as f:
                    if hashlib.file_digest(f,'sha256').hexdigest()!=expected:raise ValueError('Cached weight hash mismatch: '+path.name)
            return
        partial=path.with_suffix(path.suffix+'.part')
        for attempt in range(5):
            offset=partial.stat().st_size if partial.exists() else 0
            try:
                # Explicit bounded ranges work through proxies that buffer an
                # entire multi-GB unbounded response before returning any bytes.
                while offset<meta.size:
                    end=min(meta.size-1,offset+32*1024*1024-1)
                    headers={'Range':f'bytes={offset}-{end}'} if meta.size>64*1024*1024 else {}
                    url=f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{meta.rfilename}?distill_fetch={time.time_ns()}'
                    with requests.get(url,headers=headers,stream=True,timeout=(20,60)) as r:
                        r.raise_for_status()
                        if headers and (r.status_code!=206 or not r.headers.get('Content-Range','').startswith(f'bytes {offset}-')):
                            raise ValueError('Resume range not honored')
                        written=0
                        with partial.open('ab' if offset else 'wb') as f:
                            for chunk in r.iter_content(4*1024*1024):f.write(chunk);written+=len(chunk)
                    if written!=(end-offset+1 if headers else meta.size):raise ValueError('Incomplete download range')
                    offset+=written
                if partial.stat().st_size!=meta.size:raise ValueError('Incomplete model file')
                if expected:
                    with partial.open('rb') as f:
                        if hashlib.file_digest(f,'sha256').hexdigest()!=expected:raise ValueError('Model hash mismatch')
                partial.replace(path)
                print(json.dumps(dict(file=path.name,bytes=meta.size,hash_verified=bool(expected))),flush=True)
                return
            except requests.RequestException as exc:
                print(json.dumps(dict(file=path.name,attempt=attempt+1,error=type(exc).__name__)),flush=True)
                if attempt==4:raise RuntimeError('Pinned model download failed: '+path.name) from None
                time.sleep(2**attempt)
        raise RuntimeError('Pinned model download did not finish')
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,files))
    print(json.dumps(dict(snapshot=str(root),revision=REVISION,files=len(files),complete=True)),flush=True)


if __name__=='__main__':main()
