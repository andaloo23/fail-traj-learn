"""Offline budget/approval and annotation-contract checks. Never contact providers."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import api_label_pilot as pilot


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.ep = {'id': 'R001', 'n_frames': 11, 'sampled_frames': [0, 5, 10]}
        self.annotation = {'episode_id': 'R001', 'segments': [
            {'label': 'progress', 'start_frame': 0, 'end_frame_exclusive': 10,
             'failure_types': [], 'description': 'Target moves toward goal',
             'evidence_frames': [0, 5], 'uncertainty': ''},
            {'label': 'failure', 'start_frame': 5, 'end_frame_exclusive': 10,
             'failure_types': ['collision'], 'description': 'Another object topples',
             'evidence_frames': [5], 'uncertainty': ''}], 'uncertain': [], 'notes': ''}

    def test_progress_failure_overlap_is_valid(self):
        pilot.validate(self.annotation, self.ep)

    def test_unknown_is_not_a_negative_or_positive(self):
        a = copy.deepcopy(self.annotation)
        a['uncertain'] = [{'start_frame': 10, 'end_frame_exclusive': 11,
                           'labels': ['failure'], 'reason': 'Occlusion'}]
        pilot.validate(a, self.ep)
        a['uncertain'][0]['start_frame'] = 5
        with self.assertRaises(ValueError):
            pilot.validate(a, self.ep)

    def test_reject_invented_bounds_and_same_label_overlap(self):
        for mutation in ('bounds', 'overlap', 'taxonomy', 'evidence'):
            a = copy.deepcopy(self.annotation)
            if mutation == 'bounds': a['segments'][0]['start_frame'] = 1
            if mutation == 'overlap': a['segments'].append(copy.deepcopy(a['segments'][0]))
            if mutation == 'taxonomy': a['segments'][0]['failure_types'] = ['grasp']
            if mutation == 'evidence': a['segments'][1]['evidence_frames'] = [0]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                pilot.validate(a, self.ep)

    def test_four_persistent_reservations_and_no_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'attempts'
            pilot.reserve(ledger, 'openai', 'R001')
            with self.assertRaises(FileExistsError):
                pilot.reserve(ledger, 'openai', 'R001')
            for p, e in [('gemini', 'R001'), ('openai', 'R002'), ('gemini', 'R002')]:
                pilot.reserve(ledger, p, e)
            total = sum(json.loads(p.read_text())['reserved_usd'] for p in ledger.glob('*.json'))
            self.assertEqual(total, 2.0)
            with self.assertRaises(ValueError):
                pilot.reserve(ledger, 'gemini', 'R002')

    def test_no_approval_means_no_network_or_keys(self):
        with patch.object(pilot, 'verify', return_value={}), patch.object(pilot, 'digest', return_value='frozen'), \
             patch.object(pilot, 'post') as post, patch.object(pilot, 'credentials') as keys:
            with self.assertRaises(ValueError): pilot.run('')
            post.assert_not_called()
            keys.assert_not_called()

    def test_overbudget_count_blocks_generation_and_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'R001').mkdir()
            pilot.write_json(out / 'R001/input.json', self.ep)
            with patch.object(pilot, 'OUT', out), patch.object(pilot, 'verify', return_value={'episodes': [{'id': 'R001'}]}), \
                 patch.object(pilot, 'digest', return_value='frozen'), patch.object(pilot, 'credentials', return_value={'openai': 'fake'}), \
                 patch.object(pilot, 'build_payload', return_value={k: [] for k in ('model', 'input', 'reasoning', 'text', 'truncation')}), \
                 patch.object(pilot, 'post', return_value={'input_tokens': pilot.MAX_INPUT + 1}) as post:
                with self.assertRaises(RuntimeError): pilot.run('frozen')
                self.assertEqual(post.call_count, 1)
                self.assertTrue(post.call_args.args[0].endswith('/input_tokens'))
                with self.assertRaises(FileExistsError): pilot.run('frozen')
                self.assertEqual(post.call_count, 1)
                self.assertEqual(pilot.load(out / 'attempts/openai_R001.json')['status'], 'stopped')

    def test_count_network_failure_retains_reservation_and_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'R001').mkdir()
            pilot.write_json(out / 'R001/input.json', self.ep)
            with patch.object(pilot, 'OUT', out), patch.object(pilot, 'verify', return_value={'episodes': [{'id': 'R001'}]}), \
                 patch.object(pilot, 'digest', return_value='frozen'), patch.object(pilot, 'credentials', return_value={'openai': 'fake'}), \
                 patch.object(pilot, 'build_payload', return_value={k: [] for k in ('model', 'input', 'reasoning', 'text', 'truncation')}), \
                 patch.object(pilot, 'post', side_effect=TimeoutError) as post:
                with self.assertRaises(RuntimeError): pilot.run('frozen')
                self.assertEqual(post.call_count, 1)
                record = pilot.load(out / 'attempts/openai_R001.json')
                self.assertEqual(record['reserved_usd'], 0.5)
                self.assertEqual(record['status'], 'stopped')


if __name__ == '__main__':
    unittest.main()
