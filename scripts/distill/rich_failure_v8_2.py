"""Native Markdown schema for the fresh Astra severity/resetability pilot."""
import re

from failure_enrichment_v8_1 import CATEGORIES

SCHEMA = 'rich_failure_v8_2'
OUTCOMES = {'success', 'failure', 'success but suboptimal', 'success but side effects'}
SEVERITIES = {'low', 'medium', 'catastrophic'}
RESETABILITIES = {'immediate', 'minor_reset', 'hard_reset', 'unresettable'}


def fields(block, names):
    lines = [line for line in block.strip().splitlines() if line.strip()]
    if len(lines) != len(names):
        raise ValueError('Unexpected fields; expected ' + ', '.join(names))
    result = {}
    for line, name in zip(lines, names):
        prefix = '- ' + name + ': '
        if not line.startswith(prefix) or not line[len(prefix):].strip():
            raise ValueError('Missing or out-of-order field: ' + name)
        result[name] = line[len(prefix):].strip()
    return result


def evidence(text, episode):
    references = re.findall(r'\bframes?\s+(\d+)', text, re.I)
    if not references or any(int(f) not in {x['frame'] for x in episode['images']} for f in references):
        raise ValueError('Evidence must cite supplied source frames')
    if not any(re.search(r'(?<!\w)' + re.escape(c['camera']) + r'(?!\w)', text)
               for c in episode['cameras']):
        raise ValueError('Evidence must cite a native camera name')


def parse(text, episode, *, coverage_start=0, coverage_end=None):
    # Windowed protocols retain global frame indices. Defaults preserve the
    # historical full-episode contract and all frozen native outputs.
    coverage_end = episode['n_frames'] if coverage_end is None else coverage_end
    if not 0 <= coverage_start < coverage_end <= episode['n_frames']:
        raise ValueError('Invalid requested timeline coverage')
    if '```' in text or not text.startswith('# Episode: ' + episode['id'] + '\n'):
        raise ValueError('Expected native Markdown with the matching episode heading')
    parts = re.split(r'^## (Episode annotation|Timeline|Failure annotations)\s*$', text, flags=re.M)
    if len(parts) != 7 or parts[1::2] != ['Episode annotation', 'Timeline', 'Failure annotations']:
        raise ValueError('Expected Episode annotation, Timeline and Failure annotations in order')
    if parts[0].strip() != '# Episode: ' + episode['id']:
        raise ValueError('Unexpected text before episode annotation')
    outcome = fields(parts[2], ['Language task', 'Success label', 'Outcome evidence'])
    if outcome['Success label'] not in OUTCOMES:
        raise ValueError('Invalid episode outcome')
    evidence(outcome['Outcome evidence'], episode)
    rows = [s.strip() for s in parts[4].splitlines() if s.strip()]
    if len(rows) < 3 or rows[0] != '| Start frame | End frame | Failure |' or not re.fullmatch(
            r'\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|\s*:?-+:?\s*\|', rows[1]):
        raise ValueError('Expected the three-column timeline')
    segments = []; cursor = coverage_start
    for row in rows[2:]:
        match = re.fullmatch(r'\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(Yes|No)\s*\|', row)
        if not match:
            raise ValueError('Invalid timeline row')
        start, end, failure = int(match[1]), int(match[2]), match[3] == 'Yes'
        if start != cursor or not start < end <= coverage_end:
            raise ValueError('Timeline gaps, overlaps or invalid boundaries')
        if segments and not failure and not segments[-1]['failure']:
            raise ValueError('Merge adjacent No rows')
        segments.append(dict(start_frame=start, end_frame=end, failure=failure)); cursor = end
    if cursor != coverage_end:
        raise ValueError('Timeline must cover the requested interval')
    positives = [s for s in segments if s['failure']]
    annotations = []; details = parts[6]
    if not positives:
        if details.strip() != 'None':
            raise ValueError('No failures require None annotations')
    else:
        headings = list(re.finditer(r'^### Failure (\d+)\s*$', details, re.M))
        if len(headings) != len(positives) or details[:headings[0].start()].strip():
            raise ValueError('Expected one numbered annotation per Yes row')
        for i, (heading, segment) in enumerate(zip(headings, positives)):
            if int(heading[1]) != i + 1:
                raise ValueError('Failure numbering must be chronological')
            stop = headings[i + 1].start() if i + 1 < len(headings) else len(details)
            f = fields(details[heading.end():stop], ['Frames', 'Categories', 'Explanation', 'Recovery',
                'Severity', 'Severity evidence', 'Resetability', 'Resetability evidence'])
            bounds = re.fullmatch(r'(\d+)\s*[-–]\s*(\d+)', f['Frames'])
            if not bounds or tuple(map(int, bounds.groups())) != (segment['start_frame'], segment['end_frame']):
                raise ValueError('Annotation boundaries must match the Yes row')
            categories = [c.strip() for c in f['Categories'].split(',')]
            if categories != ['Unclear'] and (len(set(categories)) != len(categories) or not set(categories) <= CATEGORIES):
                raise ValueError('Unsupported taxonomy or mixed Unclear')
            if f['Severity'] not in SEVERITIES or f['Resetability'] not in RESETABILITIES:
                raise ValueError('Unsupported severity or resetability')
            evidence(f['Explanation'], episode)
            annotations.append(dict(start_frame=segment['start_frame'], end_frame=segment['end_frame'],
                categories=categories, explanation=f['Explanation'], recovery=f['Recovery'],
                severity=f['Severity'], severity_evidence=f['Severity evidence'],
                resetability=f['Resetability'], resetability_evidence=f['Resetability evidence']))
    if outcome['Success label'] == 'success' and positives:
        raise ValueError('An unqualified success cannot contain failure segments')
    if outcome['Success label'].startswith('success but ') and not positives:
        raise ValueError('Qualified success must describe its observed failure/side effect')
    return dict(episode_id=episode['id'], language_task=outcome['Language task'],
        success_label=outcome['Success label'], outcome_evidence=outcome['Outcome evidence'],
        segments=segments, failure_annotations=annotations)
