import copy
import unittest
import api_taxonomy_pilot_v1 as pilot
import summarize_taxonomy_pilot_v1 as summary


class TaxonomyValidation(unittest.TestCase):
    def setUp(self):
        self.ep = dict(id='T', n_frames=20, sampled_frames=[0,5,10,15,19])
        self.seg = dict(start_frame=0,end_frame=10,start_window=[0,5],end_window=[5,10],
                        categories=['grasp'],what_happened='Missed object',recovery='Reposition',
                        evidence_frames=[5],severity='low',potential_risk='none',
                        resetability='immediate',uncertainty='')
        self.value = dict(episode_id='T',segments=[self.seg],uncertain_intervals=[],
                          termination=dict(status='unknown',frame=None,evidence='Clip ends'),notes='Sparse frames')

    def test_valid_and_clean(self):
        pilot.validate(self.value,self.ep)
        self.value['segments']=[]
        pilot.validate(self.value,self.ep)

    def test_unknown_is_not_negative(self):
        self.value['uncertain_intervals']=[dict(start_frame=10,end_frame=20,reason='Occlusion')]
        pilot.validate(self.value,self.ep)
        self.value['uncertain_intervals'][0]['start_frame']=5
        with self.assertRaises(ValueError): pilot.validate(self.value,self.ep)

    def test_category_change_is_same_bout(self):
        other=copy.deepcopy(self.seg)
        other.update(start_frame=10,end_frame=20,start_window=[10,10],end_window=[20,20],
                     categories=['grasp','collision'],evidence_frames=[15])
        self.value['segments'].append(other)
        pilot.validate(self.value,self.ep)
        self.assertEqual(pilot.bouts(self.value['segments']),[[0,20]])
        other['categories']=['grasp']
        with self.assertRaises(ValueError): pilot.validate(self.value,self.ep)

    def test_reject_invalid_category_evidence_and_window(self):
        for field,value in [('categories',['sudden_termination']),('evidence_frames',[15]),
                            ('start_window',[5,10]),('severity','severe')]:
            bad=copy.deepcopy(self.value)
            bad['segments'][0][field]=value
            with self.assertRaises(ValueError): pilot.validate(bad,self.ep)

    def test_termination_requires_endpoint_and_evidence(self):
        self.value['termination']=dict(status='observed',frame=20,evidence='Interrupted movement')
        pilot.validate(self.value,self.ep)
        self.value['termination']['frame']=19
        with self.assertRaises(ValueError): pilot.validate(self.value,self.ep)

    def test_agreement_identity_and_no_positive_na(self):
        result=summary.compare(self.value,self.value,20,20)
        self.assertEqual(result['duration_agreement']['any_failure']['f1'],1)
        self.assertEqual(result['bout_overlap']['0.5']['f1'],1)
        self.value['segments']=[]
        result=summary.compare(self.value,self.value,20,20)
        self.assertIsNone(result['duration_agreement']['any_failure']['f1'])
        self.assertIsNone(result['bout_overlap']['0.5']['f1'])

    def test_unknown_mask_does_not_create_boundaries(self):
        other=copy.deepcopy(self.value)
        other['segments']=[]
        other['uncertain_intervals']=[dict(start_frame=0,end_frame=10,reason='Occlusion')]
        result=summary.compare(self.value,other,20,20)
        self.assertEqual(result['eligible_fraction'],.5)
        self.assertIsNone(result['bout_overlap'])
        self.assertIsNone(result['duration_agreement']['any_failure']['f1'])

    def test_events_cannot_reuse_match(self):
        result=summary.overlap([[0,5],[5,10]],[[0,10]],.5)
        self.assertEqual(result['tp'],1)
        self.assertEqual(result['fp'],1)


if __name__=='__main__': unittest.main()
