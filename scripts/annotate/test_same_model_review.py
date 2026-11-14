"""Check independent same-model outputs remain distinct in the review bundle."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import annotation_runtime as io
import annotate_trajectories as runner
import review_trajectory_annotations as review
from test_annotate_trajectories import annotation, segment


class SameModelReviewTests(unittest.TestCase):
    def test_separate_answers_metrics_and_fingerprint_for_two_sol_runs(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            for name in ('OUT', 'SOURCE', 'IDS', 'SCHEME', 'LABEL_MODE',
                         'PROMPT_DIR', 'MODELS', 'REASONING'):
                stack.enter_context(patch.object(runner, name))
            base = Path(tmp)
            source = base / 'source'
            episode = source / 'test'
            episode.mkdir(parents=True)
            cameras = np.zeros((20, 3, 3, 3), dtype=np.uint8)
            np.savez(episode / 'cameras.npz', agent=cameras, wrist=cameras)
            io.write_json(episode / 'observable.json', dict(
                id='test', task='Move the object', n_frames=20, fps=20,
                telemetry=[dict(frame=i, eef_xyz_m=[0, 0, 0],
                    finger_qpos_m=[0, 0], gripper_command='open') for i in range(20)]))
            folders = [base / name for name in ('run1', 'run2')]
            answers = []
            for index, folder in enumerate(folders):
                runner.configure(folder, source, ['test'], models=['sol'])
                runner.prepare()
                value = annotation([segment(0, 20, 'a1', 'transport', failure=bool(index))])
                value['segments'][0]['what_happened'] = f'Independent answer {index + 1}.'
                text = json.dumps(value)
                answers.append(text)
                io.write_json(folder / 'test_sol_annotation.json', value)
                (folder / 'test_sol_answer.txt').write_text(text, encoding='utf-8')
                (folder / 'attempts').mkdir()
                io.write_json(folder / 'attempts/test_sol.json',
                              dict(status='validated', generation_sent=True))
            target = review.build(folders[0], source, 'sol', 'sol', folders[1])
            review.refresh_comparison_metrics(target)
            data = io.load(target / 'data.json')
            current = data['episodes'][0]
            self.assertFalse(current['versions']['atomic_actions']['openai']['segments'][0]['failure'])
            self.assertTrue(current['versions']['atomic_actions']['gemini']['segments'][0]['failure'])
            for column, expected in zip(('openai', 'gemini'), answers):
                link = current['statuses']['atomic_actions'][column]['raw_link']
                self.assertEqual((target / link).read_text(encoding='utf-8'), expected)
            self.assertNotEqual(data['runs'][0]['columns']['openai'], data['runs'][0]['columns']['gemini'])
            report = io.load(target / 'action_group_agreement.json')
            self.assertEqual(len(report['annotation_sha256']), 2)
            self.assertEqual(report['episodes'][0]['counts']['matched_category_assignments'], 0)
            original_fingerprint = data['annotation_manifest_sha256']
            saved = io.load(folders[1] / 'manifest.json')
            saved['prepared_utc'] = 'different source manifest'
            io.write_json(folders[1] / 'manifest.json', saved)
            review.build(folders[0], source, 'sol', 'sol', folders[1])
            self.assertNotEqual(io.load(target / 'data.json')['annotation_manifest_sha256'], original_fingerprint)
            with self.assertRaisesRegex(ValueError, 'distinct source runs'):
                review.build(folders[0], source, 'sol', 'sol')


if __name__ == '__main__':
    unittest.main()
