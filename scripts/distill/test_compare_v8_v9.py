"""Offline checks of matched rich/binary comparison and paid-call safeguards."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import compare_v8_v9 as comparison
import oopsie_common as common
import oopsie_markdown as markdown
from test_oopsie_pipeline import fixture, answer


class ComparisonTests(unittest.TestCase):
    def test_action_boxes_merge_across_failure_transitions_without_copying_failure_labels(self):
        segments=[dict(start_frame=0,end_frame=3,action_id='a1',action='grasp',object_id='cup',destination_id=None,failure=False),
                  dict(start_frame=3,end_frame=5,action_id='a1',action='grasp',object_id='cup',destination_id=None,failure=True),
                  dict(start_frame=5,end_frame=8,action_id='a2',action='transport',object_id='cup',destination_id=None,failure=False)]
        before=copy.deepcopy(segments)
        boxes=comparison.merge_action_segments(segments)
        self.assertEqual([(s['start_frame'],s['end_frame'],s['action']) for s in boxes],[(0,5,'grasp'),(5,8,'transport')])
        self.assertTrue(all('failure' not in s for s in boxes))
        self.assertEqual(segments,before)

    def test_publisher_tolerates_new_attempt_directory_before_atomic_state_arrives(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'traces/O001_sol_r01').mkdir(parents=True)
            self.assertIsNone(comparison.load_rich(root, {}, dict(id='O001')))

    def test_ready_review_publishes_rich_and_preserved_binary_annotations(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); source = base / 'binary'; root = base / 'rich'
            source.mkdir(); root.mkdir()
            common.write(source / 'manifest.json', dict(config=dict(repeats=3)))
            common.write(root / 'manifest.json', {})
            (source / 'prompt.md').write_text('Frozen binary prompt')
            e = dict(id='O001', task='Move object', split='train', lab='fixture', fps=20, n_frames=20, videos=[])
            m = dict(config=dict(source_run='binary'), source_manifest_sha256=common.sha(source / 'manifest.json'), episodes=[e])
            value = answer(flagged=True); text = markdown.render(value)
            segments = comparison.binary_projection(value['segments'])
            for repeat in range(1, 4):
                path = source / f'traces/O001_sol_r{repeat:02d}/annotation.md'
                path.parent.mkdir(parents=True); path.write_text('Preserved binary ' + str(repeat))
            with patch.object(common, 'ROOT', base), patch.object(comparison, 'load_rich', return_value=(value, dict(generation_estimate_usd=.1), text)), patch.object(comparison.binary, 'load_trace', return_value=(segments, {})):
                result = comparison.review(root, m=m)
            self.assertEqual(result['v8_ready'], 1)
            data = common.read(root / 'review_data.json')
            self.assertEqual(data['episodes'][0]['teachers']['v8'][0]['native_markdown'], text)
            self.assertEqual(len(data['episodes'][0]['teachers']['v9']), 3)
            self.assertEqual(common.read(root / 'comparison_results.json')['rows'][0]['frames'], 20)
            self.assertEqual((source / 'traces/O001_sol_r01/annotation.md').read_text(), 'Preserved binary 1')

    def test_request_audit_allows_only_prompt_and_output_budget_changes(self):
        a = dict(input=[dict(content=[dict(type='input_text', text='RICH\nEpisode: O001'),
                                     dict(type='input_image', image_url='data:exact-frozen-image')])], max_output_tokens=100)
        b = copy.deepcopy(a); b['input'][0]['content'][0]['text'] = 'BINARY\nEpisode: O001'; b['max_output_tokens'] = 10
        before = copy.deepcopy(a)
        comparison.compare_request_inputs(a, b, 'RICH', 'BINARY')
        self.assertEqual(a, before)
        b['input'][0]['content'][1]['image_url'] += 'changed'
        with self.assertRaisesRegex(ValueError, 'image bytes'):
            comparison.compare_request_inputs(a, b, 'RICH', 'BINARY')
        self.assertEqual(a, before)

    def test_projection_merges_labels_without_modifying_rich_flags_or_actions(self):
        segments = [dict(start_frame=0, end_frame=5, failure=False, action='reach', review_required=True),
                    dict(start_frame=5, end_frame=10, failure=False, action='grasp', review_required=False),
                    dict(start_frame=10, end_frame=20, failure=True, action='grasp', review_required=True)]
        before = copy.deepcopy(segments)
        self.assertEqual(comparison.binary_projection(segments), [
            dict(start_frame=0, end_frame=10, failure=False), dict(start_frame=10, end_frame=20, failure=True)])
        self.assertEqual(segments, before)

    def test_rich_validation_uses_native_panel_cameras_and_preserves_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'fixture'
            m = fixture(root); e = copy.deepcopy(m['episodes'][0])
            e['source_images'] = e['images']
            e['images'] = [dict(frame=i, camera='all camera panels') for i in range(20)]
            value = answer(flagged=True); text = markdown.render(value)
            self.assertEqual(comparison.parse_rich(text, e), value)
            with self.assertRaisesRegex(ValueError, 'another episode'):
                comparison.parse_rich(text.replace('# Episode: O001', '# Episode: O002'), e)
            with self.assertRaisesRegex(ValueError, 'unsupplied'):
                comparison.parse_rich(text.replace('camera left_wrist', 'camera nonexistent'), e)

    def test_stopped_attempt_is_preserved_and_never_resent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'manifest.json').write_text('{}')
            request = root / 'requests/O001_sol.json'; request.parent.mkdir(); request.write_text('{}')
            folder = root / 'traces/O001_sol_r01'; folder.mkdir(parents=True)
            (folder / 'attempt.json').write_text(json.dumps(dict(status='stopped', error='Unknown outcome')))
            receipt = dict(complete=True, manifest_sha256=common.sha(root / 'manifest.json'),
                           run_total_ceiling_usd=1, requests=[dict(episode='O001', request_sha256=common.sha(request))])
            common.write(root / 'token_preflight.json', receipt)
            common.write(root / 'matched_request_audit.json', dict(manifest_sha256=common.sha(root / 'manifest.json'),
                images_and_metadata_identical=True, episodes=[dict(episode='O001', rich_request_sha256=common.sha(request))]))
            m = dict(episodes=[dict(id='O001')],config=dict(repeats=1))
            before = (folder / 'attempt.json').read_bytes()
            with patch.object(comparison, 'verify', return_value=m), patch.object(comparison.transport, 'post') as post:
                with self.assertRaisesRegex(ValueError, 'budget'):
                    comparison.collect(root, .1)
                with self.assertRaisesRegex(ValueError, 'not be resent'):
                    comparison.collect(root, 2)
                post.assert_not_called()
            self.assertEqual((folder / 'attempt.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
