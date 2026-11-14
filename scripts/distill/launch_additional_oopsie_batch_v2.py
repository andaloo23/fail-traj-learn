"""Run the approved additional 500-video Sol collection on the local PC.

Preparation and token preflights overlap; the existing Batch runner enforces the
full-run budget before submission. No GPU workloads or training are launched.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

import oopsie_common as common
import annotation_runtime as transport
from oopsie_bulk_v8_1 import plan


CONFIG = common.ROOT/'configs/oopsie_rich_failure_v8_1_additional_500_batch_v2.json'


def main():
    root, cfg, selection, _ = plan(CONFIG)
    lock = root/'local_controller.lock'
    with lock.open('x', encoding='utf-8') as f:
        json.dump(dict(pid=os.getpid(), started_utc=datetime.now(timezone.utc).isoformat()), f)
    children = {}; logs = []
    env = dict(os.environ, PYTHONUNBUFFERED='1', PYTHONIOENCODING='utf-8')
    def start(name, script, *args):
        out=(root/(name+'.stdout.log')).open('a',encoding='utf-8')
        err=(root/(name+'.stderr.log')).open('a',encoding='utf-8');logs.extend([out,err])
        p=subprocess.Popen([sys.executable,str(common.ROOT/script),*map(str,args)],cwd=common.ROOT,
            env=env,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        children[name]=p
        return p
    def receipt(stage, **extra):
        transport.atomic_json(root/'local_controller_status.json',dict(stage=stage,controller_pid=os.getpid(),
            updated_utc=datetime.now(timezone.utc).isoformat(),
            processes={name:dict(pid=p.pid,returncode=p.poll()) for name,p in children.items()},**extra))
    try:
        if cfg['budget_usd']!=75 or cfg['teachers']!={'sol':'gpt-6.1-sol'}:
            raise ValueError('Approved collection scope changed')
        if not selection.get('previous_collections'):
            raise ValueError('Previous 500-video collection must be excluded')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',8801))
        start('server','scripts/distill/serve_oopsie_review.py','--directory',root,'--port',8801)
        prepare=start('prepare','scripts/distill/oopsie_bulk_v8_1.py','prepare','--config',CONFIG,'--workers',4)
        pipeline=start('pipeline','scripts/distill/oopsie_bulk_batch.py','run','--run',root,'--workers',2)
        monitor=start('status','scripts/distill/watch_oopsie_bulk_status.py','--run',root,
            '--url','http://127.0.0.1:8801/review.html')
        receipt('Local preparation and token preflight running')
        while True:
            if prepare.poll() not in (None,0):
                raise RuntimeError('Evidence preparation failed; inspect prepare.stderr.log')
            if pipeline.poll() not in (None,0):
                raise RuntimeError('Collection pipeline stopped; inspect preserved pipeline diagnostics')
            if monitor.poll() not in (None,0):
                raise RuntimeError('Status monitor stopped; inspect status.stderr.log')
            if prepare.poll()==0 and pipeline.poll()==0:
                receipt('Batch collection complete; final browser check pending')
                if monitor.poll() is not None:
                    receipt('Batch collection complete',browser_status=common.read(root/'browser_status.json')
                        if (root/'browser_status.json').exists() else None)
                    return
            else:
                receipt('Local preparation, token preflight or Sol Batch collection running')
            time.sleep(15)
    except Exception as exc:
        # Stop the pending stage rather than restarting or buying duplicate calls.
        for name in ('prepare','pipeline'):
            p=children.get(name)
            if p is not None and p.poll() is None:p.terminate()
        transport.atomic_json(root/'local_controller_failure.json',dict(message=str(exc),
            updated_utc=datetime.now(timezone.utc).isoformat()))
        if not (root/'pipeline_failure.json').exists():
            transport.atomic_json(root/'pipeline_failure.json',dict(message=str(exc),utc=datetime.now(timezone.utc).isoformat()))
        receipt('Stopped; inspect preserved diagnostics')
        raise
    finally:
        lock.unlink(missing_ok=True)
        for stream in logs:stream.close()


if __name__=='__main__':main()
