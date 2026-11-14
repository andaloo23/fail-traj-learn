import copy
import unittest
import api_taxonomy_explicit_v5 as pilot


class ExplicitContract(unittest.TestCase):
    def setUp(self):
        self.ep={'id':'T','n_frames':20,'sampled_frames':[0,5,10,15,19]}
        ev=[{'frame':5,'camera':'wrist','observation':'Container beside fingers'}]
        self.value={'episode_id':'T','identity_check':dict(requested_object='cup',
            manipulated_object='unidentified container',match_status='unresolved',
            evidence=ev,uncertainty='Label occluded'), 'segments':[dict(start_frame=0,end_frame=20,
            progress=True,failure=True,what_happened='Moves target while contacting obstacle',
            categories=['collision'],recovery='Reposition',severity='low',resetability='immediate',
            evidence=ev,review_required=True,uncertainty='Target identity unclear')]}

    def test_exact_earlier_evidence_blocks_and_taxonomy(self):
        old=(pilot.ROOT/'scripts/annotate/prompts/identity_v2/progress_failure.md').read_text(encoding='utf-8')
        tax=(pilot.ROOT/'scripts/annotate/prompts/failure_taxonomy_v2.txt').read_text(encoding='utf-8')
        prompt=pilot.PROMPT.read_text(encoding='utf-8')
        self.assertTrue(prompt.startswith(old[:old.index('## Failure categories')]))
        self.assertIn(tax[tax.index('Each segment should have the following annotations'):tax.index('Input and response format:')],prompt)

    def test_both_and_neither_supported(self):
        pilot.validate(self.value,self.ep)
        s=self.value['segments'][0]
        s.update(progress=False,failure=False,categories=[],recovery=None,severity=None,resetability=None)
        pilot.validate(self.value,self.ep)

    def test_missing_coverage_or_unsupported_evidence_rejected(self):
        for field,value in [('start_frame',1),('end_frame',19),('progress',None)]:
            bad=copy.deepcopy(self.value);bad['segments'][0][field]=value
            with self.assertRaises(ValueError): pilot.validate(bad,self.ep)
        self.value['identity_check']['evidence'][0]['frame']=7
        with self.assertRaises(ValueError): pilot.validate(self.value,self.ep)

    def test_unresolved_requires_explanation(self):
        self.value['identity_check']['uncertainty']=''
        with self.assertRaises(ValueError): pilot.validate(self.value,self.ep)


if __name__=='__main__': unittest.main()
