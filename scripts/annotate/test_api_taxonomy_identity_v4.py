import copy
import unittest
import api_taxonomy_identity_v4 as pilot


class IdentityEvidence(unittest.TestCase):
    def setUp(self):
        self.ep={'id':'T','n_frames':20,'sampled_frames':[0,5,10,15,19]}
        self.value={'episode_id':'T','identity_check':{'requested_object':'cup','summary':'Identity unresolved',
            'objects':[{'object_id':'obj_1','appearance':'Small container','observed_identity':'unresolved',
                'task_match':'unresolved','rationale':'Label occluded',
                'evidence':[{'frame':5,'camera':'wrist','observation':'Unmarked side visible'}]}]},
            'segments':[dict(start_frame=0,end_frame=20,progress=False,failure=False,
                what_happened='Holds container',recovery=None,categories=[],severity=None,resetability=None,
                object_ids=['obj_1'],review_required=True,uncertainty='Cannot establish task match')]}

    def test_valid_uncertainty_keeps_complete_coverage(self):
        pilot.validate(self.value,self.ep)

    def test_cannot_hide_unresolved_identity(self):
        self.value['segments'][0]['review_required']=False
        with self.assertRaises(ValueError):pilot.validate(self.value,self.ep)

    def test_reject_unseen_evidence_or_unknown_track(self):
        bad=copy.deepcopy(self.value);bad['identity_check']['objects'][0]['evidence'][0]['frame']=7
        with self.assertRaises(ValueError):pilot.validate(bad,self.ep)
        self.value['segments'][0]['object_ids']=['invented']
        with self.assertRaises(ValueError):pilot.validate(self.value,self.ep)

    def test_still_rejects_unlabeled_tail(self):
        self.value['segments'][0]['end_frame']=19
        with self.assertRaises(ValueError):pilot.validate(self.value,self.ep)


if __name__=='__main__':unittest.main()
