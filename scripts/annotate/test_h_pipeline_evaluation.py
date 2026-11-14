import json
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import api_h_pipeline_evaluation_v1 as run
from h_reference import legacy_projection

class HProtocolTests(unittest.TestCase):
    def test_projection_is_explicit_and_does_not_mutate_predictions(self):
        original=[{'start':0,'end':10,'progress':True,'failure':True}]
        projected=legacy_projection(original)
        self.assertFalse(projected[0]['progress'])
        self.assertTrue(projected[0]['failure'])
        self.assertTrue(original[0]['progress'])
    def test_parallel_reservations_keep_cap_and_complete_records(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(run,'OUT',Path(directory)):
            jobs=run.jobs()
            self.assertEqual(len(jobs),60)
            with ThreadPoolExecutor(max_workers=4) as executor:list(executor.map(run.reserve,jobs))
            records=[json.loads(p.read_text()) for p in (Path(directory)/'attempts').glob('*.json')]
            self.assertEqual(len(records),60)
            self.assertAlmostEqual(sum(r['reserved_usd'] for r in records),10.08)
            with self.assertRaises(ValueError):run.reserve(jobs[0])
    def test_annotation_context_does_not_use_extra_reference_fields(self):
        ep={'id':'H001','task':'test task','n_frames':20,'fps':20,'telemetry':[],
            'human_annotation':'SECRET HUMAN LABEL','events':'SECRET EVENTS','source':'PRIVATE'}
        text=run.context(ep,[0,19])
        self.assertNotIn('SECRET',text);self.assertNotIn('PRIVATE',text)
    def test_single_frame_windows_keep_budget(self):
        ep={'window_count':3,'pairs_per_window':6,'overview':[0,61,109,170,218,279],
            'allowed_window_starts':list(range(0,270,5)),'budget':24}
        frames,details=run.parse_selection('# Window selection\n## Selected windows\n- [0, 10]\n- [100, 110]\n- [200, 210]',ep,'SW')
        self.assertEqual(len(frames),24);self.assertEqual(len(set(frames)),24)

if __name__=='__main__':unittest.main()
