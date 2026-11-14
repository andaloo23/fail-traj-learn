import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import api_frame_selection as runner


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.patch = patch.object(runner, 'OUT', self.out)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def episode(self):
        pool, k, uniform, anchors = runner.pool_and_budget(150)
        ep = dict(id='R001', task='Move the object', n_frames=150, fps=20,
                  pool=pool, k=k, uniform=uniform, anchors=anchors, telemetry=[])
        folder = self.out / 'R001'
        (folder / 'images').mkdir(parents=True)
        runner.common.write_json(folder / 'input.json', ep)
        for frame in pool:
            for camera in ('agent', 'wrist'):
                (folder / 'images' / f'{frame:04d}_{camera}.jpg').write_bytes(f'{frame}-{camera}'.encode())
        (self.out / 'prompts').mkdir()
        for name in runner.PROMPTS:
            (self.out / 'prompts' / name).write_text(name)
        return ep

    def selection(self, ep, frames=None):
        return '# Frame selection\n\n## Selected frames\n' + '\n'.join(f'- {f}' for f in (frames or ep['uniform']))

    def test_sampling(self):
        for n, expected in [(280, (57, 15, [0, 80, 180, 279])), (150, (31, 8, [0, 45, 85, 149]))]:
            pool, k, uniform, anchors = runner.pool_and_budget(n)
            self.assertEqual((len(pool), k, anchors), expected)
            self.assertEqual(len(set(uniform)), k)

    def test_strict_selector(self):
        ep = self.episode()
        answer = self.selection(ep)
        self.assertEqual(runner.parse_selection(answer, ep), ep['uniform'])
        for bad in [answer + '\nFailure happened', answer + '\n- 149', answer.replace('- 45', '- 46'), answer.replace('- 0\n', '')]:
            with self.assertRaises(ValueError):
                runner.parse_selection(bad, ep)

    def test_matched_payload_and_provenance(self):
        ep = self.episode()
        answer = self.selection(ep)
        (self.out / 'responses').mkdir()
        (self.out / 'responses/R001_E.md').write_text(answer, encoding='utf-8')
        runner.freeze_selection(ep, answer)
        jobs = {j['arm']: j for j in runner.jobs() if j['episode'] == 'R001'}
        direct, text_d, _ = runner.build_payload(jobs['D'])
        selected, text_f, _ = runner.build_payload(jobs['F'])
        self.assertEqual(direct, selected)
        self.assertEqual(text_d, text_f)
        self.assertNotIn('# Frame selection', text_f)
        (self.out / 'R001/selected/0000_agent.jpg').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            runner.build_payload(jobs['F'])

    def test_cost_includes_thinking_once(self):
        result = runner.usage_cost('openai', {'usage': {'input_tokens': 1000, 'output_tokens': 200,
            'input_tokens_details': {'cached_tokens': 100}, 'output_tokens_details': {'reasoning_tokens': 150}}})
        self.assertAlmostEqual(result['generation_estimate_usd'], .00381)
        result = runner.usage_cost('gemini', {'usageMetadata': {'promptTokenCount': 1000,
            'candidatesTokenCount': 50, 'thoughtsTokenCount': 150, 'cachedContentTokenCount': 100}})
        self.assertAlmostEqual(result['generation_estimate_usd'], .00191)

    def test_reservation_cannot_repeat_and_cap(self):
        first = runner.jobs()[0]
        runner.reserve(first)
        with self.assertRaises(FileExistsError):
            runner.reserve(first)
        for job in runner.jobs()[1:]:
            runner.reserve(job)
        with self.assertRaises(ValueError):
            runner.reserve(first)
        self.assertAlmostEqual(sum(json.loads(p.read_text())['reserved_usd'] for p in (self.out / 'attempts').glob('*.json')), 4.48)

    def test_preflight_blocks_generation(self):
        self.episode()
        with patch.object(runner, 'post', return_value={'input_tokens': 40001}) as post:
            with self.assertRaises(RuntimeError):
                runner.execute(runner.jobs()[0], {'openai': 'fake-key'})
        self.assertEqual(post.call_count, 1)
        record = runner.common.load(self.out / 'attempts/R001_A.json')
        self.assertFalse(record['generation_sent'])
        self.assertEqual(record['status'], 'stopped')

    def test_truncation_still_records_cost(self):
        self.episode()
        raw = {'status': 'incomplete', 'usage': {'input_tokens': 100, 'output_tokens': 4096},
               'output': [{'content': [{'type': 'output_text', 'text': '# Partial annotation'}]}]}
        with patch.object(runner, 'post', side_effect=[{'input_tokens': 100}, raw]) as post:
            with self.assertRaises(RuntimeError):
                runner.execute(runner.jobs()[0], {'openai': 'fake-key'})
        self.assertEqual(post.call_count, 2)
        record = runner.common.load(self.out / 'attempts/R001_A.json')
        self.assertEqual(record['status'], 'stopped')
        self.assertAlmostEqual(record['generation_estimate_usd'], .04116)
        self.assertTrue((self.out / 'responses/R001_A.md').exists())


if __name__ == '__main__':
    unittest.main()
