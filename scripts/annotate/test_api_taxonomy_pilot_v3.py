import copy
import json
import unittest
import api_taxonomy_pilot_v3 as pilot
from review_taxonomy_pilot import display_annotation


class CompleteIndependentLabels(unittest.TestCase):
    def setUp(self):
        self.ep={'id':'T','n_frames':20}
        self.value={'episode_id':'T','segments':[]}
        for i,(progress,failure) in enumerate([(True,False),(True,True),(False,True),(False,False)]):
            self.value['segments'].append(dict(start_frame=i*5,end_frame=(i+1)*5,
                progress=progress,failure=failure,what_happened='Observed behavior',
                categories=['collision'] if failure else [],recovery='Reposition' if failure else None,
                severity='low' if failure else None,resetability='immediate' if failure else None))

    def test_all_four_states(self):
        pilot.validate(self.value,self.ep)

    def test_reject_gaps_overlaps_and_omitted_tail(self):
        for index,field,value in [(0,'start_frame',1),(1,'start_frame',6),(1,'start_frame',4),(3,'end_frame',19)]:
            bad=copy.deepcopy(self.value);bad['segments'][index][field]=value
            with self.assertRaises(ValueError): pilot.validate(bad,self.ep)

    def test_empty_episode_labels_rejected(self):
        self.value['segments']=[]
        with self.assertRaises(ValueError): pilot.validate(self.value,self.ep)

    def test_booleans_required(self):
        for value in ['false',0,None]:
            bad=copy.deepcopy(self.value);bad['segments'][0]['failure']=value
            with self.assertRaises(ValueError): pilot.validate(bad,self.ep)

    def test_failure_fields_consistent(self):
        bad=copy.deepcopy(self.value);bad['segments'][1]['categories']=[]
        with self.assertRaises(ValueError): pilot.validate(bad,self.ep)
        self.value['segments'][0]['severity']='low'
        with self.assertRaises(ValueError): pilot.validate(self.value,self.ep)

    def test_display_metadata_does_not_fix_missing_labels(self):
        raw=copy.deepcopy(self.value);raw['n_frames']=20
        self.assertEqual(display_annotation(json.dumps(raw),pilot,self.ep),self.value)
        raw['segments'][0]['start_frame']=1
        with self.assertRaises(ValueError): display_annotation(json.dumps(raw),pilot,self.ep)


if __name__=='__main__': unittest.main()
