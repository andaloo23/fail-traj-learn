import unittest
from unittest.mock import patch
import api_frame_selection_v2 as runner
import test_api_frame_selection as original


class RevisedTests(original.ExperimentTests):
    def setUp(self):
        self.module_patch = patch.object(original, 'runner', runner)
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)
        super().setUp()

    def test_reservation_cannot_repeat_and_cap(self):
        for job in runner.jobs():
            runner.reserve(job)
        with self.assertRaises(ValueError):
            runner.reserve(runner.jobs()[0])
        self.assertAlmostEqual(sum(j['reserved_usd'] for j in runner.jobs()) + .27, 4.45)

    def test_count_preserves_resolution_and_is_reused(self):
        self.episode()
        job = runner.jobs()[1]
        raw = {'usageMetadata': {'promptTokenCount': 100, 'candidatesTokenCount': 10},
               'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '# Annotation'}]}}]}
        with patch.object(runner, 'post', side_effect=[{'totalTokens': 100}, raw]) as post:
            runner.preflight(job, {'gemini': 'fake-key'})
            runner.execute(job, {'gemini': 'fake-key'})
        self.assertEqual(post.call_count, 2)
        counted = post.call_args_list[0].args[2]['generateContentRequest']
        generated = post.call_args_list[1].args[2]
        self.assertEqual(counted['contents'], generated['contents'])
        self.assertEqual(counted['generationConfig'], generated['generationConfig'])
        self.assertEqual(counted['generationConfig']['mediaResolution'], 'MEDIA_RESOLUTION_LOW')
        with patch.object(runner, 'post') as post:
            with self.assertRaises(ValueError):
                runner.execute(job, {'gemini': 'fake-key'})
            post.assert_not_called()

    def test_modified_preflight_input_blocks_generation(self):
        self.episode()
        job = runner.jobs()[0]
        with patch.object(runner, 'post', return_value={'input_tokens': 100}):
            runner.preflight(job, {'openai': 'fake-key'})
        (self.out / 'prompts/progress_failure.md').write_text('changed')
        with patch.object(runner, 'post') as post:
            with self.assertRaises(RuntimeError):
                runner.execute(job, {'openai': 'fake-key'})
            post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
