"""Strict native V8.1 Markdown parsing and explicit three-repeat agreement."""
from itertools import combinations
import re

import binary_segments_v9 as binary

SCHEMA = 'binary_failure_enrichment_v8_1'
CATEGORIES = {'reaching', 'grasp', 'manipulation', 'sequencing_semantic', 'collision',
              'task_not_attempted', 'sudden_episode_termination', 'visible_hardware_issue', 'other'}


def parse(text, episode):
    if not isinstance(text, str) or '```' in text or text.count('## Failure annotations') != 1:
        raise ValueError('Expected binary Markdown followed by one Failure annotations section')
    table, details = text.split('## Failure annotations', 1)
    segments = binary.parse(table, episode)
    positive = [s for s in segments if s['failure']]
    if not positive:
        if details.strip() != 'None':
            raise ValueError('An all-No timeline requires None under Failure annotations')
        return dict(episode_id=episode['id'], segments=segments, failure_annotations=[])
    sections = list(re.finditer(r'^### Failure (\d+)[ \t]*\r?$', details, re.MULTILINE))
    if len(sections) != len(positive) or details[:sections[0].start()].strip():
        raise ValueError('Exactly one numbered annotation is required for each Yes row')
    annotations = []
    cameras = {c['camera'] for c in episode['cameras']}
    for i, (heading, segment) in enumerate(zip(sections, positive)):
        if int(heading[1]) != i+1:
            raise ValueError('Failure annotations must be numbered in chronological order')
        stop = sections[i+1].start() if i+1 < len(sections) else len(details)
        block = details[heading.end():stop].strip()
        match = re.fullmatch(r'- Frames: (\d+)\s*(?:-|–|to)\s*(\d+)\s*\r?\n'
            r'- Categories: ([^\r\n]+)\r?\n- Explanation: (.+)', block, re.DOTALL)
        if not match or re.search(r'^\s*(?:#{1,6} |-[ ]+[A-Z][^:\n]*:)', match[4], re.MULTILINE):
            raise ValueError('Expected only Frames, Categories and Explanation for each failure')
        start, end = int(match[1]), int(match[2])
        if (start, end) != (segment['start_frame'], segment['end_frame']):
            raise ValueError('Failure annotation boundaries differ from the primary Yes interval')
        categories = [c.strip() for c in match[3].split(',')]
        if categories != ['Unclear'] and (not categories or len(set(categories)) != len(categories) or not set(categories) <= CATEGORIES):
            raise ValueError('Unsupported/duplicate category or mixed Unclear marker')
        explanation = match[4].strip()
        if not explanation:
            raise ValueError('A failure explanation is required')
        # Presence/range checks only: visual support still requires human review.
        references = re.findall(r'\bframes?\s+(\d+)', explanation, re.IGNORECASE)
        if not references or any(not 0 <= int(f) < episode['n_frames'] for f in references):
            raise ValueError('Explanation must cite valid supplied source frame indices')
        if not any(re.search(r'(?<![\w])'+re.escape(c)+r'(?![\w])', explanation) for c in cameras):
            raise ValueError('Explanation must cite a supplied native camera name')
        annotations.append(dict(start_frame=start, end_frame=end, categories=categories,
                                category_unclear=categories == ['Unclear'], explanation=explanation))
    return dict(episode_id=episode['id'], segments=segments, failure_annotations=annotations)


def agreement(values, n_frames, expected=3):
    result = dict(available_repeats=len(values), expected_repeats=expected, complete=len(values)==expected,
                  binary_exact_3_of_3=None, boundary_exact_3_of_3=None, unanimous_frames=None,
                  frame_unanimity=None, disagreement_intervals=[], category_exact_3_of_3=None,
                  explanation_semantic_agreement_assessed=False, pairwise=[])
    for (i, a), (j, b) in combinations(enumerate(values, 1), 2):
        result['pairwise'].append(dict(repeats=[a.get('repeat',i), b.get('repeat',j)], **binary.compare(a['segments'], b['segments'], n_frames)))
    if not result['complete']:
        return result
    labels = []
    for value in values:
        row = [None] * n_frames
        for s in value['segments']:
            row[s['start_frame']:s['end_frame']] = [s['failure']] * (s['end_frame']-s['start_frame'])
        if None in row:
            raise ValueError('Cannot score an incomplete timeline')
        labels.append(row)
    conflicts = [len({row[f] for row in labels}) != 1 for f in range(n_frames)]
    start = None
    for frame, conflict in enumerate(conflicts + [False]):
        if conflict and start is None:
            start = frame
        elif not conflict and start is not None:
            result['disagreement_intervals'].append(dict(start_frame=start, end_frame=frame)); start = None
    unanimous = n_frames - sum(conflicts)
    exact = unanimous == n_frames
    result.update(binary_exact_3_of_3=exact, unanimous_frames=unanimous, frame_unanimity=unanimous/n_frames,
                  boundary_exact_3_of_3=all(v['segments'] == values[0]['segments'] for v in values[1:]))
    if exact and values[0]['failure_annotations']:
        categories = [[(s['start_frame'], s['end_frame'], sorted(s['categories'])) for s in v['failure_annotations']] for v in values]
        result['category_exact_3_of_3'] = all(c == categories[0] for c in categories[1:])
    return result
