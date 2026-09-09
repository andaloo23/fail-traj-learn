"""Reveal oracle diagnostics only after both independent annotations are frozen."""
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from common import Episode,open_dataset
from oracle_reference import build_reference

OUT=HERE.parents[2]/'outputs/oopsie_transfer_v1'

def main():
    freeze=json.loads((OUT/'freeze.json').read_text())
    for c in ('a','b'):
        assert hashlib.sha256((OUT/f'condition_{c}.json').read_bytes()).hexdigest()==freeze['sha256'][c]
    folder=OUT/'oracle_after_freeze';folder.mkdir(exist_ok=True)
    reports=[]
    for entry in json.loads((OUT/'private_manifest.json').read_text()):
        ds=open_dataset(entry['dataset']);ep=Episode(ds,entry['dataset'],entry['episode_index'])
        assert ep.chunks==[(a,min(a+10,ep.n)) for a in range(0,ep.n,10)],'Unexpected recorder chunk boundaries'
        ref=build_reference(ep)
        (folder/f'{entry["id"]}_reference.json').write_text(json.dumps(ref,indent=2)+'\n')
        report={k:ref[k] for k in ('task','success','target_slot','events','attempts','close_on_nothing','wrong_object_contacts','final','anomalies')}
        report['id']=entry['id'];reports.append(report)
    (folder/'diagnostics.json').write_text(json.dumps(reports,indent=2)+'\n')
    freeze['oracle_review_started']=True
    (OUT/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    print('Oracle facts written after hash freeze; original recorder chunk boundaries verified.')

if __name__=='__main__':main()
