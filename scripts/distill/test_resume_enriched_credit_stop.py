"""Credit-resume safety: preserve explicit rejections, never resend unknown outputs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oopsie_common as common
import resume_enriched_credit_stop as resume


class ResumeTests(unittest.TestCase):
    def fixture(self,base,error='openai HTTP 429 [credit_balance_exhausted]: no credits',status='stopped'):
        root=base/'run';root.mkdir()
        for name in ['manifest.json','prompt.md','config.json','token_preflight.json','matched_request_audit.json']:
            (root/name).write_text('Preserved '+name)
        folder=root/'traces/O001_sol_r01';folder.mkdir(parents=True)
        (folder/'attempt.json').write_text(json.dumps(dict(status=status,error=error)))
        m=dict(protocol=resume.runner.ENRICHED_PROTOCOL,config=dict(teachers={'sol':'gpt-6.1-sol'},repeats=3),episodes=[dict(id='O001')])
        return root,folder,m

    def test_explicit_rejection_is_archived_with_exact_bytes_and_frozen_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root,folder,m=self.fixture(base)
            before=(folder/'attempt.json').read_bytes();prompt=(root/'prompt.md').read_bytes()
            with patch.object(common,'ROOT',base),patch.object(resume.runner,'verify',return_value=m):
                result=resume.prepare_resume(root)
            self.assertEqual(result['api_calls'],0);self.assertEqual(result['remaining_responses'],3)
            self.assertFalse(folder.exists())
            archived=list((root/'stopped_attempts').glob('*/attempt.json'))
            self.assertEqual(len(archived),1);self.assertEqual(archived[0].read_bytes(),before)
            self.assertEqual((root/'prompt.md').read_bytes(),prompt)

    def test_response_bearing_or_unknown_attempt_cannot_be_archived(self):
        for mode in ['response','unknown','in_flight']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                base=Path(temp)
                root,folder,m=self.fixture(base,status='in_flight' if mode=='in_flight' else 'stopped',error='Unknown network outcome' if mode=='unknown' else 'openai HTTP 429 [credit_balance_exhausted]: no credits')
                if mode=='response':(folder/'response.json').write_text('Preserved charged response')
                before=(folder/'attempt.json').read_bytes()
                with patch.object(common,'ROOT',base),patch.object(resume.runner,'verify',return_value=m),self.assertRaises(ValueError):
                    resume.prepare_resume(root)
                self.assertTrue(folder.exists());self.assertEqual((folder/'attempt.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
