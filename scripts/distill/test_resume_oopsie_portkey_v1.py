"""Offline guards for switching paid collection to the explicitly provided key."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import resume_oopsie_portkey_v1 as resume


class PortkeyContinuationTests(unittest.TestCase):
    def test_missing_portkey_key_cannot_fall_back_to_openai(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / '.env.portkey'
            path.write_text('OPENAI_API_KEY=old-key\nPORTKEY_PROVIDER=@test\n')
            with self.assertRaisesRegex(ValueError, 'Explicit PORTKEY_API_KEY'):
                resume.Portkey(path)

    def test_gateway_headers_never_send_old_openai_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / '.env.portkey'
            path.write_text('PORTKEY_API_KEY=portkey-test-key\nPORTKEY_PROVIDER=@test\n')
            client = resume.Portkey(path)
            response = Mock()
            response.read.return_value = b'{"data": []}'
            context = Mock()
            context.__enter__ = Mock(return_value=response)
            context.__exit__ = Mock(return_value=False)
            with patch.object(resume.urllib.request, 'urlopen', return_value=context) as opened:
                client.api('GET', '/v1/batches')
            request = opened.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.portkey.ai/v1/batches')
            headers = {k.lower(): v for k, v in request.header_items()}
            self.assertEqual(headers['x-portkey-api-key'], 'portkey-test-key')
            self.assertEqual(headers['x-portkey-provider'], '@test')
            self.assertNotIn('authorization', headers)
            self.assertEqual(opened.call_count, 1)

    def test_existing_journals_exclude_failed_and_unknown_submissions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'batch_jobs').mkdir()
            for stem, status in [('batch_001', 'submitted'), ('batch_002', 'submission_unresolved')]:
                (root / 'batch_jobs' / (stem + '.json')).write_text(json.dumps({'status': status}))
            manifest = {'shards': [{'path': f'batch_inputs/batch_{i:03d}.jsonl'} for i in range(1, 4)]}
            self.assertEqual(resume.pending_shards(root, manifest), manifest['shards'][2:])

    def test_reference_migration_changes_only_provider_file_ids(self):
        body = {'model': 'gpt-6.1-sol', 'reasoning': {'effort': 'low'}, 'input': [{'content': [
            {'type': 'input_text', 'text': 'Frozen prompt'},
            {'type': 'input_image', 'file_id': 'file-old', 'detail': 'high'},
            {'type': 'input_text', 'text': 'Frame 1'},
            {'type': 'input_image', 'image_url': 'data:image/webp;base64,EXACT', 'detail': 'high'}]}]}
        expected = copy.deepcopy(body)
        expected['input'][0]['content'][1]['file_id'] = 'file-new'
        upload = Mock(return_value='file-new')
        images = [{'sha256': 'first'}, {'sha256': 'second'}]
        self.assertEqual(resume.remap_images(body, {'images': images}, upload), expected)
        upload.assert_called_once_with(images[0])
        with self.assertRaisesRegex(ValueError, 'coverage changed'):
            resume.remap_images(body, {'images': []}, upload)

    def test_submission_journal_is_written_before_billable_call(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'batch_jobs').mkdir()
            (root / 'batch_inputs').mkdir()
            request = root / 'batch_inputs/batch_001.jsonl'
            request.write_text('{}\n')
            shard = dict(path='batch_inputs/batch_001.jsonl', sha256=resume.common.sha(request), custom_ids=['O1_sol_r01'])
            client = Mock(provider='@test')
            client.upload.return_value = {'id': 'file-new'}
            def reject(*args, **kwargs):
                state = resume.common.read(root / 'batch_jobs/batch_001.json')
                self.assertEqual(state['status'], 'submitting')
                raise RuntimeError('network outcome unknown')
            client.api.side_effect = reject
            with self.assertRaisesRegex(RuntimeError, 'unknown'):
                resume.submit(root, {'run_id': 'run', 'protocol': 'test'}, shard, client)
            state = resume.common.read(root / 'batch_jobs/batch_001.json')
            self.assertEqual(state['status'], 'submission_unresolved')
            with self.assertRaisesRegex(ValueError, 'no resend'):
                resume.submit(root, {'run_id': 'run', 'protocol': 'test'}, shard, client)
            self.assertEqual(client.api.call_count, 1)
            self.assertEqual(client.upload.call_count, 1)


if __name__ == '__main__':
    unittest.main()
