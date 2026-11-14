"""Offline checks for the input-reduction experiment; no real credentials/network."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import api_input_ablation as a


class AblationTests(unittest.TestCase):
    def test_matrix_has_independent_gemini_and_no_openai_video(self):
        jobs = a.jobs()
        self.assertEqual(len(jobs), 28)
        self.assertEqual(sum(j['provider'] == 'openai' for j in jobs), 12)
        self.assertEqual(sum(j['provider'] == 'gemini' for j in jobs), 16)
        self.assertFalse(any(j['arm'] == 'video' and j['provider'] != 'gemini' for j in jobs))
        self.assertAlmostEqual(sum(j['reserved_usd'] for j in jobs), 4.56)

    def test_nested_sampling_keeps_endpoints(self):
        for n in (150, 280):
            baseline = set(a.frame_indices(n, 5))
            sparse = set(a.frame_indices(n, 20))
            self.assertTrue(sparse <= baseline)
            self.assertTrue({0, n - 1} <= sparse)

    def test_ledger_cannot_repeat_or_exceed_plan(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, 'OUT', Path(tmp)):
            for job in a.jobs(): a.reserve(job)
            with self.assertRaises(ValueError): a.reserve(a.jobs()[0])
            records = [json.loads(p.read_text()) for p in (Path(tmp) / 'attempts').glob('*.json')]
            for provider in a.CAP:
                self.assertAlmostEqual(sum(r['reserved_usd'] for r in records if r['provider'] == provider), a.CAP[provider])

    def test_missing_approval_never_reads_keys_or_sends(self):
        with patch.object(a, 'verify', return_value={}), patch.object(a.common, 'digest', return_value='approved'), \
             patch.object(a.common, 'post') as post, patch.object(a.common, 'credentials') as creds:
            with self.assertRaises(ValueError): a.run('')
            post.assert_not_called()
            creds.assert_not_called()

    def test_overlimit_preflight_stops_before_generation(self):
        job = a.jobs()[0]
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, 'OUT', Path(tmp)), \
             patch.object(a, 'verify', return_value={'jobs': [job]}), patch.object(a.common, 'digest', return_value='approved'), \
             patch.object(a.common, 'credentials', return_value={'openai': 'fake'}), \
             patch.object(a, 'payload', return_value={k: [] for k in ('model', 'input', 'reasoning', 'text', 'truncation')}), \
             patch.object(a.common, 'post', return_value={'input_tokens': a.MAX_INPUT + 1}) as post:
            with self.assertRaises(RuntimeError): a.run('approved')
            self.assertEqual(post.call_count, 1)
            self.assertTrue(post.call_args.args[0].endswith('/input_tokens'))
            with self.assertRaises(FileExistsError): a.run('approved')
            self.assertEqual(post.call_count, 1)

    def test_markdown_is_prose_not_json(self):
        text = "# Episode R001\n\n## Progress segments\n\nMoves the target toward the basket."
        a.validate_markdown(text)
        for bad in ['', '  ', '{"segments": []}', '```markdown\n# Episode R001\n```']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                a.validate_markdown(bad)

    def test_context_is_markdown_and_telemetry_matches_across_conditions(self):
        ep = {'id': 'R001', 'task': 'Move object', 'n_frames': 40, 'fps': 20,
              'telemetry': [{'frame': 0, 'seconds': 0, 'eef_xyz_m': [0.1, 0.2, 0.3],
                             'finger_qpos_m': [0.01, -0.01], 'gripper_command': 'open'}]}
        contexts = [a.episode_context(ep, spec) for spec in a.ARMS.values()]
        self.assertTrue(all('# Episode R001' in c for c in contexts))
        self.assertEqual(len({c.split('## Ordinary robot telemetry')[1] for c in contexts}), 1)

    def test_payload_does_not_request_json_output(self):
        ep = {'id': 'R001', 'task': 'Move object', 'n_frames': 2, 'fps': 20, 'telemetry': []}
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, 'OUT', Path(tmp)):
            root = Path(tmp)
            (root / 'prompt.md').write_text('# Instructions')
            d = root / 'R001/baseline'
            d.mkdir(parents=True)
            a.common.write_json(root / 'R001/input.json', ep)
            (d / 'context.md').write_text(a.episode_context(ep, a.ARMS['baseline']))
            for frame in (0, 1):
                for camera in ('agent', 'wrist'):
                    (d / f'{frame:04d}_{camera}.jpg').write_bytes(b'fake-image-for-offline-payload-test')
            for provider in a.common.MODELS:
                body = a.payload({'episode': 'R001', 'arm': 'baseline', 'provider': provider})
                if provider == 'openai':
                    self.assertNotIn('text', body)
                else:
                    self.assertNotIn('responseMimeType', body['generationConfig'])
                self.assertNotIn('json_object', json.dumps(body))


if __name__ == '__main__': unittest.main()
