"""Enriched native Markdown, three-way scoring and independent paid-call reuse."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import compare_v8_v9 as runner
import failure_enrichment_v8_1 as rich
import oopsie_common as common


def answer(positive=True, explanation='At frame 1 in cam, the gripper moves away empty while the target remains.'):
    table='| 0 | 1 | No |\n| 1 | 3 | Yes |' if positive else '| 0 | 3 | No |'
    details='### Failure 1\n\n- Frames: 1-3\n- Categories: grasp\n- Explanation: '+explanation if positive else 'None'
    return '# Episode: O001\n\n| Start frame | End frame | Failure |\n| --- | --- | --- |\n'+table+'\n\n## Failure annotations\n\n'+details


EPISODE=dict(id='O001',n_frames=3,cameras=[dict(camera='cam')])


class EnrichmentTests(unittest.TestCase):
    def test_preflight_reserves_all_three_repeats_but_counts_each_request_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);common.write(root/'manifest.json',{})
            cfg=dict(repeats=3,max_input_tokens=1000,max_output_tokens=10,
                rates_per_million={'sol':dict(input=2,cached=.1,cache_write=2.5,output=10)})
            m=dict(config=cfg,episodes=[dict(EPISODE,images=[])])
            body=dict(model='gpt-6.1-sol',input=[],reasoning=dict(effort='low'),text={},truncation='disabled')
            with patch.object(runner,'verify',return_value=m),patch.object(runner.binary,'payload',return_value=body),patch.object(runner.transport,'credentials',return_value={'openai':'fixture'}),patch.object(runner.transport,'post',return_value=dict(input_tokens=100)) as post:
                receipt=runner.preflight(root)
            post.assert_called_once()
            self.assertAlmostEqual(receipt['run_total_ceiling_usd'],3*receipt['requests'][0]['per_call_ceiling_usd'])

    def test_repeat_aware_publisher_preserves_native_enrichment_and_marks_unanimity(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);source=base/'binary';root=base/'new';source.mkdir();root.mkdir()
            common.write(source/'manifest.json',dict(config=dict(repeats=3)))
            common.write(root/'manifest.json',{})
            (source/'prompt.md').write_text('Frozen binary prompt')
            e=dict(EPISODE,task='Pick object',split='train',lab='fixture',fps=20,videos=[])
            cfg=dict(source_run='binary',repeats=3,annotation_schema=rich.SCHEMA)
            m=dict(protocol=runner.ENRICHED_PROTOCOL,config=cfg,episodes=[e],source_manifest_sha256=common.sha(source/'manifest.json'))
            value=rich.parse(answer(),e)
            for repeat in range(1,4):
                p=source/f'traces/O001_sol_r{repeat:02d}/annotation.md';p.parent.mkdir(parents=True);p.write_text('Preserved '+str(repeat))
            with patch.object(common,'ROOT',base),patch.object(runner,'load_rich',return_value=(value,dict(generation_estimate_usd=.1),answer())),patch.object(runner.binary,'load_trace',return_value=(value['segments'],{})):
                result=runner.review(root,m)
            self.assertEqual(result['v8_ready'],3);self.assertEqual(result['binary_exact_3_of_3_episodes'],1)
            data=common.read(root/'review_data.json')
            self.assertEqual(data['planned_responses'],6)
            self.assertEqual([t['repeat'] for t in data['episodes'][0]['teachers']['v8']],[1,2,3])
            self.assertEqual(data['episodes'][0]['teachers']['v8'][0]['failure_annotations'],value['failure_annotations'])
            self.assertEqual(data['side_repeats'],dict(v8=3,v9=3))

    def test_positive_and_all_negative_native_markdown(self):
        value=rich.parse(answer(),EPISODE)
        self.assertEqual(value['failure_annotations'][0]['categories'],['grasp'])
        self.assertEqual(rich.parse(answer(False),EPISODE)['failure_annotations'],[])

    def test_mismatched_intervals_missing_or_extra_annotations_rejected(self):
        for text in (answer().replace('- Frames: 1-3','- Frames: 0-3'),
                     answer().replace('### Failure 1','### Failure 2'),
                     answer().replace('### Failure 1','### Failure 1\n\n### Failure 2'),
                     answer(False).replace('None','### Failure 1'),
                     answer().replace('grasp\n- Explanation','invented\n- Explanation')):
            with self.subTest(text=text),self.assertRaises(ValueError):rich.parse(text,EPISODE)

    def test_frame_camera_checks_and_unclear_category(self):
        for explanation in ('An unsupported explanation.', 'At frame 9 in cam, it misses.', 'At frame 1 in unknown, it misses.'):
            with self.assertRaises(ValueError):rich.parse(answer(explanation=explanation),EPISODE)
        unclear=rich.parse(answer().replace('Categories: grasp','Categories: Unclear'),EPISODE)
        self.assertTrue(unclear['failure_annotations'][0]['category_unclear'])
        with self.assertRaises(ValueError):rich.parse(answer().replace('Categories: grasp','Categories: Unclear, grasp'),EPISODE)

    def test_three_way_unanimity_is_not_average_pairwise_agreement(self):
        yes=rich.parse(answer(),EPISODE);no=rich.parse(answer(False),EPISODE)
        result=rich.agreement([yes,yes,no],3)
        self.assertFalse(result['binary_exact_3_of_3'])
        self.assertEqual(result['unanimous_frames'],1)
        self.assertAlmostEqual(result['frame_unanimity'],1/3)
        self.assertEqual(result['disagreement_intervals'],[dict(start_frame=1,end_frame=3)])
        self.assertIsNone(result['category_exact_3_of_3'])
        self.assertIsNone(rich.agreement([yes,yes],3)['binary_exact_3_of_3'])

    def test_explanation_wording_and_category_order_do_not_change_binary_agreement(self):
        a=rich.parse(answer(),EPISODE);b=copy.deepcopy(a);b['failure_annotations'][0]['explanation']='Different supported wording.'
        result=rich.agreement([a,b,a],3)
        self.assertTrue(result['binary_exact_3_of_3']);self.assertTrue(result['category_exact_3_of_3'])
        b['failure_annotations'][0]['categories']=['other']
        result=rich.agreement([a,b,a],3)
        self.assertTrue(result['binary_exact_3_of_3']);self.assertFalse(result['category_exact_3_of_3'])

    def test_three_independent_identical_requests_reused_without_resubmission(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            cfg=dict(repeats=3,annotation_schema=rich.SCHEMA,teachers={'sol':'gpt-6.1-sol'},
                     rates_per_million={'sol':dict(input=2,cached=.1,cache_write=2.5,output=10)})
            m=dict(config=cfg,episodes=[EPISODE]);common.write(root/'manifest.json',m)
            path=root/'requests/O001_sol.json';common.write(path,dict(model='gpt-6.1-sol',input=[]))
            digest=common.sha(path)
            common.write(root/'token_preflight.json',dict(complete=True,manifest_sha256=common.sha(root/'manifest.json'),
                run_total_ceiling_usd=.01,requests=[dict(episode='O001',request_sha256=digest,input_tokens=10,per_call_ceiling_usd=.003)]))
            common.write(root/'matched_request_audit.json',dict(manifest_sha256=common.sha(root/'manifest.json'),
                images_and_metadata_identical=True,episodes=[dict(episode='O001',rich_request_sha256=digest)]))
            calls=[]
            def post(url,provider,body,keys):
                calls.append(copy.deepcopy(body))
                return dict(status='completed',model=body['model'],usage=dict(input_tokens=10,output_tokens=20),
                            output=[dict(content=[dict(type='output_text',text=answer())])])
            with patch.object(runner,'verify',return_value=m),patch.object(runner,'review',return_value={}),patch.object(runner.transport,'credentials',return_value={'openai':'fixture'}),patch.object(runner.transport,'post',side_effect=post):
                runner.collect(root,1);runner.collect(root,1)
            self.assertEqual(len(calls),3);self.assertTrue(all(c==calls[0] for c in calls))
            self.assertEqual(len(list((root/'traces').glob('*/annotation.md'))),3)
            for repeat in range(1,4):self.assertIsNotNone(runner.load_rich(root,m,EPISODE,repeat))


if __name__=='__main__':unittest.main()
