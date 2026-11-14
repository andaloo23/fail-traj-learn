"""Schema, evidence, authorization and transport checks; no paid calls."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import corral_astra_v8_2 as runner
import rich_failure_v8_2 as schema

EPISODE = dict(id='C0001', n_frames=5, cameras=[dict(camera='wrist')],
               images=[dict(frame=f) for f in range(5)])


def answer(positive=True):
    result = ('# Episode: C0001\n\n## Episode annotation\n\n'
        '- Language task: Pick up the cup.\n'
        '- Success label: ' + ('failure' if positive else 'success') + '\n'
        '- Outcome evidence: At frame 4 in wrist the cup remains on the table.\n\n'
        '## Timeline\n\n| Start frame | End frame | Failure |\n| --- | --- | --- |\n' +
        ('| 0 | 2 | No |\n| 2 | 5 | Yes |' if positive else '| 0 | 5 | No |') +
        '\n\n## Failure annotations\n\n')
    if not positive:
        return result + 'None\n'
    return result + ('### Failure 1\n\n- Frames: 2-5\n- Categories: grasp\n'
        '- Explanation: At frame 2 in wrist the closed gripper moves away empty.\n'
        '- Recovery: Reopen and align with the cup before retrying.\n'
        '- Severity: low\n- Severity evidence: The cup is undamaged and safely supported.\n'
        '- Resetability: immediate\n- Resetability evidence: No environmental intervention is required.\n')


class PilotTests(unittest.TestCase):
    def test_native_markdown_includes_all_requested_judgments(self):
        value = schema.parse(answer(), EPISODE)
        self.assertEqual(value['success_label'], 'failure')
        failure = value['failure_annotations'][0]
        self.assertEqual(failure['severity'], 'low')
        self.assertEqual(failure['resetability'], 'immediate')
        self.assertTrue(failure['recovery'])
        self.assertEqual(schema.parse(answer(False), EPISODE)['failure_annotations'], [])

    def test_invalid_boundaries_missing_fields_and_unsupported_values_fail(self):
        for text in [answer().replace('Frames: 2-5', 'Frames: 1-5'),
                     answer().replace('| 0 | 2 | No |', '| 0 | 1 | No |'),
                     answer().replace('- Recovery: Reopen and align with the cup before retrying.\n', ''),
                     answer().replace('Severity: low', 'Severity: high'),
                     answer().replace('Resetability: immediate', 'Resetability: easy'),
                     answer().replace('Categories: grasp', 'Categories: grasp, Unclear'),
                     answer().replace('Success label: failure', 'Success label: success')]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                schema.parse(text, EPISODE)

    def test_evidence_requires_supplied_frames_and_native_camera(self):
        for text in [answer().replace('frame 2', 'frame 20'), answer().replace('in wrist', 'in invented')]:
            with self.assertRaises(ValueError):
                schema.parse(text, EPISODE)
        sparse = copy.deepcopy(EPISODE); sparse['images'] = [dict(frame=0), dict(frame=4)]
        with self.assertRaises(ValueError):
            schema.parse(answer(), sparse)

    def test_distinct_contiguous_failure_segments_are_supported(self):
        text = answer().replace('| 2 | 5 | Yes |', '| 2 | 3 | Yes |\n| 3 | 5 | Yes |')
        block = text.split('### Failure 1')[1]
        text = text.replace('- Frames: 2-5', '- Frames: 2-3')
        text += '\n### Failure 2' + block.replace('Frames: 2-5', 'Frames: 3-5').replace('Categories: grasp', 'Categories: collision')
        self.assertEqual(len(schema.parse(text, EPISODE)['failure_annotations']), 2)

    def test_pilot_cap_checked_before_api_client(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = dict(model='gpt-6-astra', source_annotations_used_as_model_input=False,
                episodes=[dict(id=f'C{i:04d}') for i in range(1, 12)],
                selection_sha256='hash', prompt_sha256='prompt')
            runner.write_once(root / 'manifest.json', manifest)
            with patch.object(runner, 'verified_selection', return_value=dict(prompt_sha256='prompt',
                    pilot_ids=[f'C{i:04d}' for i in range(1, 11)])), patch.object(runner.common, 'sha', return_value='hash'):
                with self.assertRaisesRegex(ValueError, 'ten authorized'):
                    runner.manifest(root)

    def test_missing_gateway_configuration_cannot_fall_back(self):
        with patch.object(Path, 'read_text', return_value='OPENAI_API_KEY=direct-test-key\n'):
            with self.assertRaisesRegex(ValueError, 'Explicit Portkey'):
                runner.Gateway()

    def test_terminal_video_observation_is_preserved(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        builder = object.__new__(runner.CorralPreparation)
        builder.files = {'camera.mp4': dict(sha256='hash', bytes=1)}
        item = dict(id='C0007', timestep_count='240', video_reference_paths_json='["camera.mp4"]')
        container = MagicMock()
        container.__enter__.return_value.streams.video = [SimpleNamespace(frames=241)]
        with patch.object(builder, 'download', return_value=Path('camera.mp4')), patch('av.open', return_value=container), \
                patch.object(runner.Preparation, 'episode', return_value=dict(status='prepared', n_frames=241)) as parent:
            result = builder.episode(item)
        self.assertEqual(parent.call_args.args[0]['timestep_count'], '241')
        self.assertEqual(result['source_timestep_count'], 240)
        self.assertEqual(result['video_frame_count'], 241)
        self.assertIn('all video frames retained', result['frame_alignment_note'])


if __name__ == '__main__':
    unittest.main()
