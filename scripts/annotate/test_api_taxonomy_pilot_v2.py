import copy
import json
import unittest
import api_taxonomy_pilot_v2 as pilot
from review_taxonomy_pilot import display_annotation


class OriginalTaxonomyContract(unittest.TestCase):
    def setUp(self):
        self.ep = {'id':'T','n_frames':20,'sampled_frames':[0,5,10,15,19]}
        self.value = {'episode_id':'T','segments':[dict(start_frame=3,end_frame=20,
            what_happened='The rollout ended during the attempt.',recovery='Restart the attempt.',
            categories=['sudden_episode_termination'],severity='low',resetability='immediate')]}

    def test_ninth_category_and_unsampled_estimate(self):
        pilot.validate(self.value,self.ep)

    def test_empty(self):
        self.value['segments']=[]
        pilot.validate(self.value,self.ep)

    def test_reject_out_of_range_or_invented_category(self):
        for field,value in [('end_frame',21),('start_frame',-1),('categories',['timeout']),
                            ('severity','unknown'),('resetability','unknown')]:
            candidate=copy.deepcopy(self.value)
            candidate['segments'][0][field]=value
            with self.assertRaises(ValueError): pilot.validate(candidate,self.ep)

    def test_original_wording_and_removed_constraints(self):
        text=pilot.PROMPT.read_text(encoding='utf-8')
        for phrase in ['Consider actual damage and potential damage.',
                       'Continuous “bad” actions should form the same failure segment',
                       'If a grasp just barely misses the object, count this as grasp instead.',
                       'spilled water damages a laptop', 'Sudden episode termination']:
            self.assertIn(phrase,text)
        for phrase in ['boundary window','failure bout','potential_risk','uncertain_intervals']:
            self.assertNotIn(phrase,text)

    def test_display_alias_preserves_content_and_rejects_other_errors(self):
        raw={'id':'T','segments':copy.deepcopy(self.value['segments'])}
        displayed=display_annotation(json.dumps(raw),pilot,self.ep)
        self.assertEqual(displayed,self.value)
        self.assertNotIn('episode_id',raw)
        raw['id']='WRONG'
        with self.assertRaises(ValueError): display_annotation(json.dumps(raw),pilot,self.ep)
        raw['id']='T'
        raw['segments'][0]['end_frame']=99
        with self.assertRaises(ValueError): display_annotation(json.dumps(raw),pilot,self.ep)


if __name__=='__main__': unittest.main()
