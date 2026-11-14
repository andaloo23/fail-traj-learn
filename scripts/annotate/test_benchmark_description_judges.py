"""Check matched judge inputs, control isolation, and no-repeat submission."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import benchmark_description_judges as bench


class JudgeBenchmarkTests(unittest.TestCase):
    def test_providers_receive_same_rubric_and_pair_text_without_control_answers(self):
        batch = dict(task='Task', pairs=bench.stress_controls())
        bodies = {k: bench.payload(c, batch, 'ab', 'Rubric') for k, c in bench.CONFIG.items()}
        self.assertEqual(bodies['sol']['input'], bodies['astra']['input'])
        self.assertEqual(bodies['sol']['input'], bodies['luna']['input'])
        self.assertEqual(bodies['sol']['input'][0]['content'],
                         bodies['gemini']['systemInstruction']['parts'][0]['text'])
        self.assertEqual(bodies['sol']['input'][1]['content'],
                         bodies['gemini']['contents'][0]['parts'][0]['text'])
        values = json.loads(bodies['sol']['input'][1]['content'])
        self.assertTrue(all(set(p) == {'pair_id', 'A', 'B'} for p in values['pairs']))

    def test_swapped_order_changes_only_description_positions(self):
        batch = dict(task='Task', pairs=bench.stress_controls())
        a, b = [json.loads(bench.content(batch, order)) for order in ('ab', 'ba')]
        for x, y in zip(a['pairs'], b['pairs']):
            self.assertEqual(x['pair_id'], y['pair_id'])
            self.assertEqual((x['A'], x['B']), (y['B'], y['A']))

    def test_reserved_call_is_never_resent(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'attempts').mkdir()
            (out / 'attempts/sol_stress_ab.json').write_text('{}', encoding='utf-8')
            with patch.object(bench.io, 'post') as post:
                bench.execute(out, dict(judge='sol', batch='stress', order='ab'), {}, '', {})
                post.assert_not_called()

    def test_failed_count_blocks_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'attempts').mkdir()
            job = dict(judge='sol', batch='stress', order='ab')
            batch = dict(task='Task', pairs=bench.stress_controls())
            with patch.object(bench.io, 'post', return_value={'input_tokens': bench.MAX_INPUT+1}) as post:
                bench.execute(out, job, batch, 'Rubric', {'openai': 'test-key'})
                self.assertEqual(post.call_count, 1)
            record = bench.io.load(out / 'attempts/sol_stress_ab.json')
            self.assertFalse(record['generation_sent'])
            self.assertEqual(record['status'], 'stopped')


if __name__ == '__main__':
    unittest.main()
