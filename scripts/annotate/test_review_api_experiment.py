import unittest
from review_api_experiment import parse_segments


class SegmentParsingTests(unittest.TestCase):
    def binary(self, pairs):
        return '## Segments\n' + '\n'.join(
            f'### Segment {i}\n- Interval: [{i*10}, {(i+1)*10})\n'
            f'- Progress: {p}\n- Failure: {f}\n- Progress confidence: high\n'
            '- Failure confidence: high\n- Review required: no'
            for i, (p, f) in enumerate(pairs))

    def test_all_four_states_cover_episode(self):
        rows, warnings = parse_segments(self.binary([('no','no'), ('yes','no'), ('no','yes'), ('yes','yes')]), 40)
        self.assertEqual([r['kind'] for r in rows], ['neither','progress','failure','both'])
        self.assertEqual(warnings, [])

    def test_gap_overlap_and_missing_label_are_flagged(self):
        source = self.binary([('no','no'), ('yes','yes')])
        for broken in (source.replace('[10, 20)', '[11, 20)'), source.replace('[10, 20)', '[9, 20)'), source.replace('Progress: yes', 'Progress: unknown')):
            self.assertTrue(parse_segments(broken, 20)[1])
        self.assertTrue(parse_segments(source, 30)[1])

    def test_low_confidence_negative_requires_review(self):
        source = self.binary([('no','no')]).replace('confidence: high', 'confidence: low')
        rows, warnings = parse_segments(source, 10)
        self.assertFalse(rows[0]['progress'])
        self.assertTrue(rows[0]['review_required'])

    def test_same_state_semantic_phases_and_reasons_preserved(self):
        source = self.binary([('no','yes'), ('no','yes')])
        source = source.replace('### Segment 1', '- Phase: Acquire carton\n- Failure types: wrong_action\n- Failure reason: Picked the wrong carton.\n### Segment 1')
        source += '\n- Phase: Transport carton\n- Failure types: wrong_action\n- Failure reason: Carried the wrong carton.\n- Boundary reason: Acquisition changed to transport.\n## Events\n### Grasp\n- Frame window: [8, 10]\n'
        rows, warnings = parse_segments(source, 20)
        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 2)
        self.assertEqual([r['kind'] for r in rows], ['failure', 'failure'])
        self.assertEqual(rows[0]['phase'], 'Acquire carton')
        self.assertEqual(rows[1]['failure_reason'], 'Carried the wrong carton.')
        self.assertEqual(rows[1]['boundary_reason'], 'Acquisition changed to transport.')

    def test_independent_overlaps_and_exclusive_end(self):
        text = '''## Progress segments
### Move
- **Interval:** [0, 20)
- Evidence: [22, 24)
## Failure segments
### Collision
- **Interval**: [10, 30)
## Uncertain intervals
### Hidden
- Interval: [30, 40)
## Limitations
Ignore [40, 50).
'''
        rows, warnings = parse_segments(text, 40)
        self.assertEqual([(r['kind'], r['start'], r['end']) for r in rows],
                         [('progress', 0, 20), ('failure', 10, 30), ('uncertain', 30, 40)])
        self.assertEqual(warnings, [])

    def test_missing_and_invalid_are_not_filled(self):
        self.assertEqual(parse_segments('## Failure segments\nNone.', 100), ([], []))
        rows, warnings = parse_segments('## Failure segments\n### Bad range\n- Interval: [90, 101)', 100)
        self.assertEqual(rows, [])
        self.assertEqual(len(warnings), 1)

    def test_closed_model_interval_is_flagged_and_preserved(self):
        rows, warnings = parse_segments('## Failure segments\n### Wrong object\n- Interval: [85, 279]', 280)
        self.assertEqual(rows[0]['end'], 280)
        self.assertEqual(rows[0]['interval_text'], '[85, 279]')
        self.assertIn('inclusive end 279', warnings[0])


if __name__ == '__main__':
    unittest.main()
