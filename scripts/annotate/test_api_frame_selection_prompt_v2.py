import unittest
from unittest.mock import patch
import api_frame_selection_prompt_v2 as runner
import test_api_frame_selection_v2 as previous


class PromptRerunTests(previous.RevisedTests):
    def setUp(self):
        self.patch_previous = patch.object(previous, 'runner', runner)
        self.patch_previous.start()
        self.addCleanup(self.patch_previous.stop)
        super().setUp()

    def test_reservation_cannot_repeat_and_cap(self):
        first = runner.jobs()[0]
        runner.reserve(first)
        with self.assertRaises(FileExistsError):
            runner.reserve(first)
        for job in runner.jobs()[1:]:
            runner.reserve(job)
        with self.assertRaises(ValueError):
            runner.reserve(first)
        self.assertAlmostEqual(sum(j['reserved_usd'] for j in runner.jobs()), 4.16)

    def test_redaction_preserves_task_words(self):
        secret = 'example-real-key'
        text = 'task-inconsistent task-level task-directed risk-taking ' + secret
        self.assertEqual(runner.redact(text, {'openai': secret}),
                         'task-inconsistent task-level task-directed risk-taking [REDACTED]')

    def test_selector_bullets(self):
        ep = self.episode()
        self.assertEqual(runner.parse_selection(self.selection(ep).replace('- ', '* '), ep), ep['uniform'])

    def test_a_b_same_text_and_images(self):
        self.episode()
        a, at, ae = runner.build_payload(runner.jobs()[0])
        b, bt, be = runner.build_payload(runner.jobs()[1])
        self.assertEqual(at, bt)
        self.assertEqual(ae['frames'], be['frames'])
        self.assertEqual(ae['image_sha256'], be['image_sha256'])


if __name__ == '__main__':
    unittest.main()
