"""Inspect the requested HF dataset using local credentials; never prints secrets."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='OopsieData-Submissions/oopsiedata-v0.1')
    parser.add_argument('--out', type=Path, default=Path('outputs/oopsiedata_v0_1_access'))
    args = parser.parse_args()
    if len(args.repo.split('/')) != 2 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./' for c in args.repo):
        parser.error('Expected an owner/dataset Hugging Face repository ID')
    home = Path(os.environ.get('HF_HOME', str(Path.home()/'.cache/huggingface')))
    token_path = Path(os.environ.get('HF_TOKEN_PATH', str(home/'token')))
    token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')
    if not token and token_path.is_file():
        token = token_path.read_text(encoding='utf-8').strip()
    headers = {'User-Agent': 'fail-traj-learn-oopsiedata-inspection/1'}
    if token:
        headers['Authorization'] = 'Bearer '+token

    def get(path):
        request = urllib.request.Request('https://huggingface.co'+path, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)

    report = dict(repo=args.repo, checked_utc=datetime.now(timezone.utc).isoformat(),
                  authenticated_account=None, access_confirmed=False)
    if token:
        try:
            report['authenticated_account'] = get('/api/whoami-v2').get('name')
        except urllib.error.HTTPError as error:
            report['login_http_status'] = error.code
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        info = get('/api/datasets/'+args.repo+'?blobs=true')
        (args.out/'dataset_info.json').write_text(json.dumps(info, indent=2)+'\n', encoding='utf-8')
        report.update(access_confirmed=True, revision=info['sha'], private=info.get('private'),
                      gated=info.get('gated'), file_count=len(info.get('siblings', [])))
    except urllib.error.HTTPError as error:
        report['dataset_http_status'] = error.code
        report['next_step'] = 'Confirm the repository URL and grant dataset access to the authenticated account.'
    (args.out/'access_report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['access_confirmed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
