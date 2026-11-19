"""Authorization, chronology, cache scope and Batch cost guards; no API calls."""
import copy
from concurrent.futures import Future
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import corral_astra_carryforward_batch as runner
from oopsie_bulk_v8_1 import write_once


class BatchCarryForwardTests(unittest.TestCase):
    def test_preparation_failure_records_cause_and_keeps_queue_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_once(root/'recipe.json',{'C0025':[]})
            failed=Future();failed.set_exception(RuntimeError('staging unavailable'))
            desc=dict(id='C0025_W01_A0',key='C0025_W01')
            sleeps=[]
            def stop_after_two_cycles(_):
                sleeps.append(True)
                if len(sleeps)==2:write_once(root/'STOP_REQUESTED.json',{})
            with patch.object(runner,'verify',return_value={}), \
                 patch.object(runner,'collect',return_value=(set(),0,[])) as collect, \
                 patch.object(runner,'descriptor',return_value=desc), \
                 patch.object(runner,'ThreadPoolExecutor') as pool, \
                 patch.object(runner,'accounting',return_value=(0,0)), \
                 patch.object(runner,'publish'), \
                 patch.object(runner.time,'sleep',side_effect=stop_after_two_cycles):
                pool.return_value.__enter__.return_value.submit.return_value=failed
                runner.run(root,interval=0)
            error=runner.common.read(root/'preparation_errors/C0025_W01_A0.json')
            self.assertEqual(error['error'],'staging unavailable')
            self.assertFalse(error['generation_submitted'])
            self.assertEqual(collect.call_count,2)
            self.assertEqual(runner.common.read(root/'queue_status.json')['preparing'],0)
            self.assertFalse((root/'worker_error.json').exists())
            self.assertFalse((root/'worker.lock').exists())

    def test_cache_preserves_visible_text_and_excludes_unique_images(self):
        body=dict(input=[dict(content=[dict(type='input_text',text='SHARED\nUnique task and prior label'),
             dict(type='input_image',image_url='data:image/webp;base64,AA',detail='high')])])
        original=copy.deepcopy(body);value=runner.apply_shared_cache(body,'SHARED')
        content=value['input'][0]['content']
        self.assertEqual(''.join(x['text'] for x in content if x['type']=='input_text'),original['input'][0]['content'][0]['text'])
        self.assertEqual(content[2],original['input'][0]['content'][1])
        self.assertEqual([x.get('text') for x in content if 'prompt_cache_breakpoint' in x],['SHARED'])
        self.assertEqual(value['prompt_cache_options']['mode'],'explicit')

    def test_chronological_stage_does_not_advance_before_canonical_validation(self):
        spans=runner.window.windows(700,episode_id='C0025')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);first=runner.descriptor(root,'C0025',spans,set())
            self.assertEqual(first['key'],'C0025_W01')
            self.assertIsNone(runner.descriptor(root,'C0025',spans,{'C0025_W01_A0'}))
            write_once(runner.canonical(root,'C0025_W01')/'status.json',dict(status='validated'))
            second=runner.descriptor(root,'C0025',spans,set())
            self.assertEqual(second['key'],'C0025_W02')
            self.assertEqual(second['bounds']['context_start'],348)

    def test_terminal_validation_repair_is_bounded_and_unknown_calls_not_resent(self):
        spans=runner.window.windows(350,episode_id='C0025')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for attempt in range(runner.MAX_REPAIRS+1):
                desc=runner.descriptor(root,'C0025',spans,set())
                self.assertEqual(desc['attempt'],attempt)
                write_once(root/'traces'/f'C0025_W01_A{attempt}'/'error.json',dict(retryable=True,error='schema'))
            self.assertIsNone(runner.descriptor(root,'C0025',spans,set()))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertIsNone(runner.descriptor(root,'C0025',spans,{'C0025_W01_A0'}))

    def test_out_of_scope_batch_refused_before_gateway(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner,'verify',return_value=dict(authorized_episode_ids=['C0025'])),patch.object(runner.batch,'Gateway') as gateway:
            with self.assertRaisesRegex(ValueError,'Unauthorized'):
                runner.submit(Path(tmp),[dict(episode='C9999')])
            gateway.assert_not_called()

    def test_corrupted_predecessor_refused_before_batch_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_once(root/'request.json',dict(model=runner.MODEL))
            write_once(runner.canonical(root,'C0025_W01')/'response.json',dict(id='changed'))
            row=dict(episode='C0025',request_path='request.json',request_sha256=runner.common.sha(root/'request.json'),
                     dependencies=[dict(key='C0025_W01',response_sha256='frozen-original')])
            with patch.object(runner,'verify',return_value=dict(authorized_episode_ids=['C0025'])),patch.object(runner.batch,'Gateway') as gateway:
                with self.assertRaisesRegex(ValueError,'Changed predecessor'):runner.submit(root,[row])
                gateway.assert_not_called()

    def test_budget_refuses_paid_call_before_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_once(root/'request.json',dict(model=runner.MODEL))
            row=dict(episode='C0025',request_path='request.json',request_sha256=runner.common.sha(root/'request.json'),dependencies=[],ceiling_usd=2)
            with patch.object(runner,'verify',return_value=dict(authorized_episode_ids=['C0025'],budget_usd=1)),patch.object(runner.batch,'Gateway') as gateway:
                with self.assertRaisesRegex(ValueError,'budget guard'):runner.submit(root,[row])
                gateway.assert_not_called()

    def test_unknown_submission_journal_is_never_resent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_once(root/'batch_jobs/test.json',dict(status='submission_unresolved',rows=[dict(id='C0025_W01_A0')]))
            with patch.object(runner.batch,'Gateway') as gateway:
                assigned,queued,unresolved=runner.collect(root)
                self.assertEqual(assigned,{'C0025_W01_A0'});self.assertEqual(queued,0);self.assertEqual(unresolved,['test.json'])
                gateway.return_value.api.assert_not_called()

    def test_successful_submission_uses_batch_purpose_and_batch_endpoint_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_once(root/'request.json',dict(model=runner.MODEL))
            row=dict(id='C0025_W01_A0',episode='C0025',request_path='request.json',request_sha256=runner.common.sha(root/'request.json'),
                     dependencies=[],ceiling_usd=.4,input_tokens=20000)
            plan=dict(authorized_episode_ids=['C0025'],budget_usd=10,protocol='test')
            with patch.object(runner,'verify',return_value=plan),patch.object(runner.batch,'Gateway') as gateway,patch.object(runner.batch,'upload_immutable_file') as upload:
                upload.return_value=dict(id='file-test');gateway.return_value.api.return_value=dict(id='batch-test',status='validating')
                runner.submit(root,[row])
                self.assertEqual(upload.call_args.kwargs['purpose'],'batch')
                self.assertEqual(gateway.return_value.api.call_args.args[:2],('POST','/v1/batches'))
                journal=runner.common.read(next((root/'batch_jobs').glob('*.json')))
                self.assertTrue(journal['generation_post_started']);self.assertEqual(journal['batch']['id'],'batch-test')
                with self.assertRaisesRegex(ValueError,'must not be resent'):
                    runner.finish_submission(root,next((root/'batch_jobs').glob('*.json')),journal)


if __name__=='__main__':unittest.main()
