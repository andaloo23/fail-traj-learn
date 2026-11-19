"""Coverage, dependency and source-index checks; no paid API calls."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import corral_astra_window_pilot as runner
import rich_failure_v8_2 as schema
from test_corral_astra_v8_2 import answer, EPISODE


class CarryForwardTests(unittest.TestCase):
    def test_disjoint_parts_cover_every_frame_once_and_carry_two_frames(self):
        spans=runner.windows(2000)
        self.assertEqual(len(spans),6)
        frames=[f for w in spans for f in range(w['start'],w['end'])]
        self.assertEqual(frames,list(range(2000)))
        self.assertEqual(sum(w['start']-w['context_start'] for w in spans),10)
        self.assertIsNone(spans[0]['previous_window'])
        self.assertEqual(spans[1]['previous_window'],spans[0]['id'])

    def test_global_index_partial_timeline_has_explicit_coverage(self):
        text=answer().replace('| 0 | 2 | No |\n| 2 | 5 | Yes |','| 3 | 4 | No |\n| 4 | 5 | Yes |')
        text=text.replace('Frames: 2-5','Frames: 4-5').replace('frame 2','frame 4')
        e=copy.deepcopy(EPISODE);e['images']=[dict(frame=2),dict(frame=3),dict(frame=4)]
        parsed=schema.parse(text,e,coverage_start=3,coverage_end=5)
        self.assertEqual(parsed['segments'][0]['start_frame'],3)
        with self.assertRaises(ValueError):schema.parse(text,e)
        with self.assertRaises(ValueError):schema.parse(text,e,coverage_start=2,coverage_end=5)
        with self.assertRaises(ValueError):schema.parse(text.replace('frame 4','frame 0'),e,coverage_start=3,coverage_end=5)

    def test_next_request_waits_for_validated_previous_label(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner.pilot,'Gateway') as gateway:
            w=runner.windows(2000)[1]
            with self.assertRaisesRegex(ValueError,'Previous part must be validated'):
                runner.prepare_window(Path(tmp),{},w)
            gateway.assert_not_called()

    def test_second_pilot_keeps_its_own_chronological_dependency_chain(self):
        spans=runner.windows(1800,episode_id='C0188')
        self.assertEqual(spans[0]['id'],'C0188_W01')
        self.assertEqual(spans[1]['previous_window'],'C0188_W01')
        self.assertEqual(spans[-1]['end'],1800)
        self.assertEqual(sum(w['end']-w['start'] for w in spans),1800)
        self.assertTrue(all(w['id'].startswith('C0188_') for w in spans))

    def test_unapproved_original_episode_rejected_before_source_or_api_access(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner.pilot,'Gateway') as gateway:
            root=Path(tmp)/'new-run'
            with self.assertRaisesRegex(ValueError,'explicit pilot authorization'):
                runner.prepare(root,'C0001')
            self.assertFalse(root.exists())
            gateway.assert_not_called()

    def test_core_draft_preserves_adjacent_events_for_reconciliation(self):
        spans=runner.windows(6,size=3,context_frames=2)
        parsed={w['id']:dict(segments=[dict(start_frame=w['start'],end_frame=w['end'],failure=True)]) for w in spans}
        draft=runner.core_draft(dict(windows=spans),parsed)
        self.assertEqual([(s['start_frame'],s['end_frame']) for s in draft],[(0,3),(3,6)])
        self.assertEqual(len(draft),2)

    def test_preflight_and_payload_do_not_renumber_context_frames(self):
        e=dict(id='C0052_W02',task='Test',n_frames=2000,cameras=[dict(camera='left')])
        text=runner.text_input('Prompt',e,runner.windows(2000)[1])
        self.assertIn('Supplied interval: [350, 700)',text)
        self.assertIn('Prior-frame context: [348, 350)',text)

    def test_token_count_omits_generation_only_parameters(self):
        request=dict(model='gpt-6-astra',input=[],reasoning={},text={},truncation='disabled',max_output_tokens=8000,store=False)
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner.pilot,'Gateway') as gateway:
            gateway.return_value.post.return_value=dict(input_tokens=123)
            self.assertEqual(runner.count_tokens(Path(tmp),request)['input_tokens'],123)
            sent=gateway.return_value.post.call_args.args[1]
            self.assertNotIn('max_output_tokens',sent)
            self.assertNotIn('store',sent)


if __name__=='__main__':unittest.main()
