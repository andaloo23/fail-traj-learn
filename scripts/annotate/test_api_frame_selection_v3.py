import unittest
from unittest.mock import patch
import api_frame_selection_v3 as runner
import test_api_frame_selection_v2 as previous
import test_api_frame_selection as original


class MarkdownResumeTests(previous.RevisedTests):
    def setUp(self):
        self.patch_previous = patch.object(previous, 'runner', runner)
        self.patch_previous.start()
        self.addCleanup(self.patch_previous.stop)
        super().setUp()

    def test_commonmark_bullets_preserve_selection(self):
        ep = self.episode()
        answer = self.selection(ep)
        for marker in ('-', '*', '+'):
            self.assertEqual(runner.parse_selection(answer.replace('- ', marker + ' '), ep), ep['uniform'])
        for extra in ('\n* 150', '\n* grasp failure', '\nSome explanation'):
            with self.assertRaises(ValueError):
                runner.parse_selection(answer + extra, ep)


if __name__ == '__main__':
    unittest.main()
