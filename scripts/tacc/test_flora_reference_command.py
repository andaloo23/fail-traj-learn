import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ReferenceCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = Path(__file__).with_name('run_flora.py')
        spec = json.loads(self.script.with_name('models.lock.json').read_text())['rewarder']
        code = self.root/'rewarder'
        code.mkdir()
        (code/'fetch_receipt.json').write_text(json.dumps(dict(spec, files={})))
        self.jobs = self.root/'jobs.jsonl'
        video = self.root/'original.mp4'
        video.write_bytes(b'command test; no decoding or inference')
        self.jobs.write_text(json.dumps(dict(id='O003', videos=[video.name]))+'\n')

    def run_command(self, mode, extra=()):
        return subprocess.run([sys.executable, str(self.script), '--root', str(self.root),
                               '--jobs', str(self.jobs), '--out', str(self.root/'unused'),
                               '--mode', mode, '--reference-defaults', '--plan', *extra],
                              capture_output=True, text=True)

    def test_reference_commands_do_not_override_inference_defaults(self):
        for mode in ('dense', 'rubric'):
            with self.subTest(mode=mode):
                result = self.run_command(mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                command = json.loads(result.stdout)['command']
                for flag in ('--max-num-seqs', '--tensor-parallel-size', '--num-samples',
                             '--max-new-tokens', '--max-model-len', '--max-num-batched-tokens'):
                    self.assertNotIn(flag, command)
                self.assertIn('--frame-scores' if mode == 'dense' else '--keep-thinking', command)

    def test_reference_profile_rejects_each_inference_override(self):
        for flag in ('--max-num-seqs', '--tensor-parallel-size', '--rubric-samples',
                     '--rubric-max-new-tokens', '--rubric-max-model-len', '--rubric-max-batched-tokens'):
            with self.subTest(flag=flag):
                result = self.run_command('rubric', [flag, '1'])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('no inference overrides', result.stderr)


if __name__ == '__main__':
    unittest.main()
