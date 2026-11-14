import copy
from pathlib import Path
import unittest
import tempfile
import hashlib
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import oopsie_recipe_data as data
import qwen_recipe_runner as runner
import score_recipe_suite as score
import recipe_job_plan as jobs


class RecipeTests(unittest.TestCase):
    def test_checksum_is_identical_on_python_310_and_newer(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bytes';p.write_bytes(b'abc')
            self.assertEqual(data.common.sha(p),hashlib.sha256(b'abc').hexdigest())
    def test_every_frame_is_scored_exactly_once(self):
        for n in [1,31,32,33,193,1500]:
            for core,context in [(16,8),(32,8),(32,16)]:
                counts=[0]*n
                for w in data.windows(n,core,context):
                    self.assertLessEqual(w['context_start'],w['core_start'])
                    self.assertGreaterEqual(w['context_end'],w['core_end'])
                    for f in range(w['core_start'],w['core_end']):counts[f]+=1
                self.assertEqual(counts,[1]*n)

    def test_clipping_preserves_original_frame_indices_and_source(self):
        s=[dict(start_frame=0,end_frame=25,failure=False),dict(start_frame=25,end_frame=50,failure=True),dict(start_frame=50,end_frame=100,failure=False)]
        before=copy.deepcopy(s);clipped=data.clip(s,32,64)
        self.assertEqual(clipped,[dict(start_frame=32,end_frame=50,failure=True),dict(start_frame=50,end_frame=64,failure=False)])
        self.assertEqual(s,before)
        text=data.table('fixture',clipped)+'\n## Visible failure evidence\n\nNone\n'
        self.assertEqual(data.parse_prediction(text,'fixture',32,64),clipped)

    def test_invalid_predictions_are_not_silently_nonfailure(self):
        c=score.counts([None,1,None,0],[1,1,0,0]);m=score.metrics(c)
        self.assertEqual(m['coverage'],.5);self.assertEqual(m['strict_frame_agreement'],.5)
        self.assertEqual(m['unknown_positive'],1);self.assertEqual(m['unknown_negative'],1)
        self.assertAlmostEqual(m['failure_recall'],.5)
        bad=data.table('fixture',[dict(start_frame=30,end_frame=64,failure=False)])
        with self.assertRaisesRegex(ValueError,'boundary'):data.parse_prediction(bad,'fixture',32,64)

    def test_ranged_evidence_cannot_cite_outside_visible_context(self):
        a=dict(start_frame=40,end_frame=55,categories=['grasp'],explanation='Frames 40-70 in wrist show the observation.')
        w=dict(core_start=32,core_end=64,context_start=16,context_end=64)
        self.assertEqual(data.citation_bounds(a['explanation']),[40,70])
        self.assertEqual(data.supported_details(dict(failure_annotations=[a]),w),[])
        a['explanation']='Frames 40, 45 and 54 in wrist show the observation.'
        self.assertEqual(len(data.supported_details(dict(failure_annotations=[a]),w)),1)
        a['end_frame']=80
        self.assertEqual(data.supported_details(dict(failure_annotations=[a]),w),[])

    def test_first_training_pass_covers_episodes_before_long_video_repeats(self):
        rows=[dict(id=f'{i}_{j}',episode=str(i)) for i in range(10) for j in range(i+1)]
        a=runner.sample_primary(rows,42)
        self.assertEqual(len({x['episode'] for x in a[:10]}),10)
        self.assertEqual(a,runner.sample_primary(rows,42))

    def test_no_baseline_is_reported_with_failure_metrics(self):
        m=score.metrics(score.counts([0,0,0,0],[1,1,0,0]))
        self.assertEqual(m['strict_frame_agreement'],.5)
        self.assertEqual(m['failure_f1'],0)
        self.assertEqual(m['failure_recall'],0)

    def test_stitching_does_not_merge_across_unknown_gaps(self):
        self.assertEqual(score.segments([1,1,None,1]),[
            dict(start_frame=0,end_frame=2,failure=True),dict(start_frame=3,end_frame=4,failure=True)])

    def test_unapproved_run_cannot_start_training(self):
        with tempfile.TemporaryDirectory() as d,patch.object(runner,'train') as train:
            with self.assertRaisesRegex(ValueError,'User confirmation'):
                jobs.run_arm(Path(d),'binary')
            train.assert_not_called()

    def test_approval_must_match_exact_plan(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'submission_plan.json').write_text('{}')
            (root/'submission_approval.json').write_text(json.dumps(dict(approved=True,plan_sha256='wrong-plan')))
            with self.assertRaisesRegex(ValueError,'does not match'):
                jobs.require_approval(root)

    def test_superseded_screening_plan_cannot_start(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'submission_plan_superseded.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'superseded'):
                jobs.require_approval(root)

    def test_generation_time_cap_preserves_partial_outputs(self):
        import torch
        class Batch(dict):
            def to(self,device):return self
        cfg=dict(student=dict(model='fixture',revision='fixture',max_length=32768),max_new_tokens=768)
        rows=[dict(id=f'e_{a}_{a+32}_binary',episode='e',split='development',task='binary',
                   core_start=a,core_end=a+32,messages=[dict(role='user',content=[dict(type='text',text='Fixture')]),dict(role='assistant',content='')]) for a in (0,32)]
        text=data.table('e',[dict(start_frame=0,end_frame=32,failure=False)])
        processor=SimpleNamespace(tokenizer=SimpleNamespace(decode=lambda *a,**k:text))
        model=SimpleNamespace(eval=lambda:None,generate=lambda **k:torch.tensor([[1,2,3]]))
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)/'input';folder.mkdir();(folder/'adapter.json').write_text('{}');(folder.parent/'study.json').write_text('{}')
            with patch.object(runner,'load',return_value=({'config':cfg},folder,rows)),\
                 patch.object(runner.core,'processor_for',return_value=processor),\
                 patch.object(runner.core,'load_model',return_value=model),\
                 patch.object(runner.core,'encoded_prompt',return_value=Batch(input_ids=torch.tensor([[1,2]]))),\
                 patch.object(torch,'autocast',return_value=nullcontext()),\
                 patch.object(runner.time,'monotonic',side_effect=[0,0,2,3,4]):
                result=runner.generate(folder,Path(d)/'outputs',max_hours=1/3600)
            self.assertFalse(result['complete'])
            self.assertEqual(result['generated_now'],1)
            self.assertTrue((Path(d)/'outputs'/f"{rows[0]['id']}.md").exists())
            self.assertFalse((Path(d)/'outputs'/f"{rows[1]['id']}.json").exists())


if __name__=='__main__':unittest.main()
