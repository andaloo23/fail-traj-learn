"""Local A-F Markdown review with full-frame cameras. Makes no API calls."""
import argparse
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from pathlib import Path
import shutil
import threading
import webbrowser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
BASELINE_RUN = ROOT / 'outputs/frame_selection_v3'
REVISED_RUN = ROOT / 'outputs/frame_selection_prompt_v2'
FULL_RUN = ROOT / 'outputs/frame_selection_full_coverage_v1'
SEMANTIC_RUN = ROOT / 'outputs/frame_selection_semantic_v2'
WINDOW_RUN = ROOT / 'outputs/frame_selection_windows_v1'
H_RUN = ROOT / 'outputs/h_pipeline_evaluation_v1'
DEFAULT_RUN = next((p for p in (H_RUN, WINDOW_RUN, SEMANTIC_RUN, FULL_RUN, REVISED_RUN, BASELINE_RUN) if p.exists()), BASELINE_RUN)
SOURCE = ROOT / 'gpt6_v3_12_episode_review_pack/episodes'
LABELS = {
    'A': 'GPT · all candidate frames',
    'B': 'Gemini · all candidate frames',
    'C': 'GPT · all frames + subset instructions',
    'D': 'GPT · uniformly selected frames',
    'E': 'Gemini · frame selection only',
    'F': 'GPT · Gemini-selected frames',
}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def parse_segments(text, n):
    """Read explicit frame intervals only; never infer labels or fill gaps."""
    segments, warnings = [], []
    kind, title, lines = None, '', []

    def finish():
        if kind is None:
            return
        block = '\n'.join(lines).strip()
        # Only the declared interval, not frame references in supporting prose.
        matches = re.findall(r'(?im)^\s*(?:[-*+]\s+)?(?:\*\*)?Interval(?:\*\*)?\s*:(?:\*\*)?\s*\[\s*(\d+)\s*,\s*(\d+)\s*(\)|\])', block)
        if not matches:
            if title:
                warnings.append(f'No explicit frame interval parsed for: {title}')
            return
        for start, end, closing in matches:
            start, end = int(start), int(end)
            interval_text = f'[{start}, {end}{closing}'
            if closing == ']':
                warnings.append(f'Model used {interval_text} instead of the requested half-open interval; plotted literally with inclusive end {end}. Verify this boundary: {title}')
                end += 1
            if not 0 <= start < end <= n:
                warnings.append(f'Out-of-range interval [{start}, {end}): {title}')
                continue
            metadata = {}
            segment_kind = kind
            if kind == 'binary':
                def field(name, lowercase=True):
                    match = re.search(r'(?im)^\s*(?:[-*+]\s+)?(?:\*\*)?' + re.escape(name) + r'(?:\*\*)?\s*:(?:\*\*)?\s*(.*?)\s*$', block)
                    value = match[1].strip() if match else ''
                    return value.lower() if lowercase else value
                progress, failure = field('Progress'), field('Failure')
                if progress not in ('yes', 'no') or failure not in ('yes', 'no'):
                    warnings.append(f'Missing or invalid explicit Progress/Failure labels: {title}')
                    continue
                segment_kind = {('no', 'no'): 'neither', ('yes', 'no'): 'progress',
                                ('no', 'yes'): 'failure', ('yes', 'yes'): 'both'}[progress, failure]
                metadata = {'progress': progress == 'yes', 'failure': failure == 'yes',
                            'progress_confidence': field('Progress confidence'),
                            'failure_confidence': field('Failure confidence'),
                            'review_required': field('Review required') != 'no'}
                for name in ('Phase', 'Description', 'Categories', 'Failure types', 'Failure reason', 'Boundary reason'):
                    value = field(name, lowercase=False)
                    if value:
                        metadata[name.lower().replace(' ', '_')] = value
                for name in ('Progress confidence', 'Failure confidence'):
                    if field(name) not in ('high', 'medium', 'low'):
                        warnings.append(f'Missing or invalid {name}: {title}')
                        metadata['review_required'] = True
                if field('Review required') not in ('yes', 'no'):
                    warnings.append(f'Missing or invalid Review required: {title}')
                if 'low' in (metadata['progress_confidence'], metadata['failure_confidence']):
                    metadata['review_required'] = True
            segments.append({'kind': segment_kind, **metadata, 'start': start, 'end': end,
                             'interval_text': interval_text,
                             'title': title or kind.capitalize(), 'markdown': block})

    sections = {'progress segments': 'progress', 'failure segments': 'failure',
                'uncertain intervals': 'uncertain', 'segments': 'binary'}
    for line in text.splitlines():
        section = re.match(r'^##\s+(.+?)\s*$', line)
        heading = re.match(r'^###\s+(.+?)\s*$', line)
        if section:
            finish()
            kind = sections.get(section[1].strip('* ').lower())
            title, lines = '', []
        elif heading:
            finish()
            title, lines = heading[1], []
        else:
            lines.append(line)
    finish()
    if re.search(r'(?im)^##\s+Segments\s*$', text):
        cursor = 0
        for segment in segments:
            if 'progress' not in segment:
                warnings.append('Mixed legacy and full-coverage annotation formats.')
            if segment['start'] != cursor:
                warnings.append(f'Incomplete partition: expected next start {cursor}, got {segment["start"]}.')
            cursor = segment['end']
        if cursor != n:
            warnings.append(f'Incomplete partition: coverage ends at {cursor}, expected {n}.')
    return segments, warnings


def build(run_dir, source):
    import numpy as np
    from PIL import Image
    manifest = load(run_dir / 'manifest.json')
    human_run = manifest.get('version') == 'h_windows_v1'
    window_run = manifest.get('version') in ('windows_v1', 'h_windows_v1')
    if human_run:
        source = ROOT / 'outputs/preprocessing_ablation_v3/holdout_source'
    labels = {'U': 'GPT uniform', 'SP': 'Gemini point selector', 'P': 'GPT selected points',
              'SW': 'Gemini window selector', 'W': 'GPT selected windows'} if window_run else LABELS
    target = run_dir / 'web_review'
    target.mkdir(exist_ok=True)
    episodes = []
    for item in manifest['episodes']:
        eid = item['id']
        if not eid.isalnum():
            raise ValueError('Invalid episode identifier')
        ep = load(run_dir / eid / 'input.json')
        frames = target / 'frames' / eid
        frames.mkdir(parents=True, exist_ok=True)
        source_path = source / eid / 'cameras.npz'
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if digest != ep['source_sha256']['cameras.npz']:
            raise ValueError(f'{eid}: source cameras differ from experiment')
        expected = [frames / f'{i:04d}_{camera}.jpg' for i in range(ep['n_frames']) for camera in ('agent', 'wrist')]
        stamp = frames / 'source.sha256'
        if not stamp.exists() or stamp.read_text() != digest or not all(p.exists() for p in expected):
            with np.load(source_path, allow_pickle=False) as arrays:
                for camera in ('agent', 'wrist'):
                    values = arrays[camera]
                    if len(values) != ep['n_frames']:
                        raise ValueError('Frame count mismatch')
                    for i, frame in enumerate(values):
                        Image.fromarray(frame).save(frames / f'{i:04d}_{camera}.jpg', quality=95)
            stamp.write_text(digest)
        model_frames = target / 'model_frames' / eid
        model_frames.mkdir(parents=True, exist_ok=True)
        for image in (run_dir / eid / 'images').glob('*.jpg'):
            shutil.copyfile(image, model_frames / image.name)
        cells = {}
        for arm, title in labels.items():
            stem = f'{eid}_{arm}'
            attempt = run_dir / 'attempts' / f'{stem}.json'
            record = load(attempt) if attempt.exists() else {}
            answer = run_dir / 'responses' / f'{stem}.md'
            evidence = run_dir / 'requests' / f'{stem}_evidence.json'
            status = record.get('status', 'not_run')
            if status == 'preflight_completed':
                status = 'not_run'
            explanation = record.get('error', '')
            if arm in ('F', 'P', 'W') and not record:
                explanation = 'Not run: no validated Gemini selection is available.'
            if status == 'not_run' and not explanation:
                explanation = 'Generation not run; the experiment stopped on an earlier request.'
            markdown = answer.read_text(encoding='utf-8') if answer.exists() else ''
            is_selector = arm in ('E', 'SP', 'SW')
            segments, warnings = parse_segments(markdown, ep['n_frames']) if not is_selector else ([], [])
            cells[arm] = {'title': title, 'status': status, 'explanation': explanation,
                          'is_selector': is_selector,
                          'generation_sent': record.get('generation_sent', False),
                          'markdown': markdown, 'segments': segments, 'parse_warnings': warnings,
                          'annotation_scheme': 'complete_binary' if re.search(r'(?im)^##\s+Segments\s*$', markdown) else 'legacy_sparse',
                          'cost': record.get('generation_estimate_usd'),
                          'input_tokens': record.get('input_tokens'),
                          'frames': load(evidence)['frames'] if evidence.exists() else [],
                          'evaluation': f'evaluation/{stem}_differences.md' if (run_dir / 'evaluation' / f'{stem}_differences.md').exists() else None,
                          'download': f'answers/{stem}.md' if answer.exists() else None}
            if answer.exists():
                (target / 'answers').mkdir(exist_ok=True)
                shutil.copyfile(answer, target / 'answers' / answer.name)
        selection = run_dir / eid / 'selected/freeze.json'
        selections = {a: load(run_dir / eid / a / 'freeze.json') for a in ('SP', 'SW')
                      if (run_dir / eid / a / 'freeze.json').exists()}
        if human_run:
            from h_reference import human_reference
            reference, original = human_reference(run_dir, eid, ep['n_frames'])
            human_segments = []
            prose = ['# Human reference: ' + eid, '', 'Legacy exclusive labels. Annotation aid: privileged simulator contacts.', '']
            for s in reference:
                prose += ['### ' + s['title'], '- Interval: [' + str(s['start']) + ', ' + str(s['end']) + ')',
                          '- Classification: ' + s['legacy_classification'], '- Failure type: ' + s['failure_types'], '']
                human_segments.append({'start': s['start'], 'end': s['end'], 'title': s['description'],
                                       'kind': {'progress': 'progress', 'failure': 'failure', 'neutral': 'neither'}[s['legacy_classification']],
                                       'failure_types': s['failure_types'], 'legacy_classification': s['legacy_classification']})
            human_markdown = '\n'.join(prose)
            (target / 'answers').mkdir(exist_ok=True)
            (target / 'answers' / f'{eid}_H.md').write_text(human_markdown, encoding='utf-8')
            cells['H'] = {'title': 'Human reference (legacy labels)', 'status': 'human_reference',
                          'explanation': 'User-designated reference; annotated with simulator-contact assistance.',
                          'generation_sent': False, 'is_reference': True, 'is_selector': False,
                          'markdown': human_markdown, 'segments': human_segments, 'parse_warnings': [],
                          'annotation_scheme': 'legacy_reference', 'cost': None, 'input_tokens': None,
                          'frames': [], 'download': f'answers/{eid}_H.md'}
        episodes.append({'id': eid, 'task': ep['task'], 'n': ep['n_frames'], 'fps': ep['fps'],
                         'pool': ep['pool'], 'uniform': ep['uniform'],
                         'selected': load(selection)['frames'] if selection.exists() else [],
                         'overview': ep.get('overview', []), 'selections': selections, 'cells': cells})
    data = {'run': run_dir.name, 'arms': list(labels) + (['H'] if human_run else []), 'episodes': episodes, 'costs': load(run_dir / 'cost_summary.json')}
    (target / 'data.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    shutil.copyfile(Path(__file__).with_suffix('.html'), target / 'index.html')
    for name in ('costs.csv', 'RESULTS.md'):
        if (run_dir / name).exists():
            shutil.copyfile(run_dir / name, target / name)
    if (run_dir / 'evaluation').exists():
        (target / 'evaluation').mkdir(exist_ok=True)
        for report in (run_dir / 'evaluation').glob('*.md'):
            shutil.copyfile(report, target / 'evaluation' / report.name)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=DEFAULT_RUN)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    folder = build(args.run.resolve(), args.source.resolve())
    print(f'Prepared all experiment episodes: {folder}', flush=True)
    if args.prepare_only:
        return
    roots = {args.run.name: folder}
    for comparison in (BASELINE_RUN, REVISED_RUN, FULL_RUN, SEMANTIC_RUN, WINDOW_RUN, H_RUN):
        if comparison.exists() and comparison.name not in roots:
            roots[comparison.name] = build(comparison, args.source.resolve())

    class ReviewHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/review-runs.json':
                body = json.dumps([{'id': name, 'url': '/runs/' + name + '/',
                                    'label': 'H human-reference evaluation' if name == H_RUN.name else
                                             'Points vs windows' if name == WINDOW_RUN.name else
                                             'Failure reasons' if name == SEMANTIC_RUN.name else
                                             'Full coverage' if name == FULL_RUN.name else
                                             'Specific prompts' if name == REVISED_RUN.name else
                                             'Original prompts' if name == BASELINE_RUN.name else name}
                                   for name in roots]).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == '/':
                self.send_response(302)
                self.send_header('Location', '/runs/' + args.run.name + '/')
                self.end_headers()
                return
            parts = path.split('/', 3)
            if len(parts) < 4 or parts[1] != 'runs' or parts[2] not in roots:
                self.send_error(404)
                return
            self.directory = str(roots[parts[2]])
            self.path = '/' + parts[3]
            super().do_GET()

    handler = partial(ReviewHandler, directory=str(folder))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'Review A-F: {url}\nNo API calls. Stop with Ctrl+C.', flush=True)
    if not args.no_browser:
        threading.Timer(.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
