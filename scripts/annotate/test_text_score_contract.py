import copy
import unittest
from text_score_contract import anchored_similarity, fact_agreement, dimension_agreement, DIMENSIONS
from experiment_independent_judges import validate


class ScoreContractTests(unittest.TestCase):
    def test_rejected_identity_override_is_only_an_experiment_diagnostic(self):
        self.assertEqual(anchored_similarity('held','held',.99),1)
        self.assertEqual(anchored_similarity('held','released',.7),.7)
        with self.assertRaises(ValueError): anchored_similarity('a','a',float('nan'))

    def test_fact_dice_omission_symmetry_and_contradiction(self):
        p=dict(facts_a=[dict(id='a',claim='held'),dict(id='b',claim='contact')],
               facts_b=[dict(id='x',claim='held')],alignments=[dict(a_id='a',b_id='x',relation='equivalent')])
        self.assertAlmostEqual(fact_agreement(p)['score'],2/3)
        reverse=dict(facts_a=p['facts_b'],facts_b=p['facts_a'],alignments=[dict(a_id='x',b_id='a',relation='equivalent')])
        self.assertEqual(fact_agreement(p)['score'],fact_agreement(reverse)['score'])
        p['alignments'][0]['relation']='contradiction'
        self.assertEqual(fact_agreement(p)['relation'],'contradiction')
        self.assertEqual(fact_agreement(p)['score'],0)
        p['alignments'][0]['relation']='unresolved'
        self.assertEqual(fact_agreement(p)['relation'],'unresolved')

    def test_invalid_alignment_is_rejected(self):
        p=dict(facts_a=[dict(id='a',claim='held')],facts_b=[dict(id='b',claim='held')],
               alignments=[dict(a_id='a',b_id='b',relation='equivalent')]*2)
        with self.assertRaises(ValueError): fact_agreement(p)

    def test_judge_duplicate_ids_rejected_and_endpoint_errors_not_hidden(self):
        job=dict(mode='scalar',ids=['a','b'])
        row=dict(pair_id='a',relation='equivalent',score=99,rationale='same')
        with self.assertRaises(ValueError): validate({'pairs':[row,row]},job)
        job['ids']=['a']
        self.assertEqual(validate({'pairs':[row]},job)[0]['score'],99)

    def test_dimension_score_ignores_absent_dimensions_and_keeps_conflicts(self):
        p={'dimensions':{k:dict(a=None,b=None,relation='not_applicable') for k in DIMENSIONS}}
        p['dimensions']['operation']=dict(a='grasp',b='grasp',relation='equivalent')
        self.assertEqual(dimension_agreement(p)['score'],1)
        p['dimensions']['physical_result']=dict(a='held',b='not held',relation='contradiction')
        self.assertEqual(dimension_agreement(p)['score'],.5)
        self.assertEqual(dimension_agreement(p)['relation'],'contradiction')
        p['dimensions']['physical_result']=dict(a='held',b=None,relation='compatible_difference')
        self.assertEqual(dimension_agreement(p)['score'],.5)
        self.assertEqual(dimension_agreement(p)['relation'],'compatible_difference')

    def test_dimension_null_equivalence_and_unknown_slots_rejected(self):
        p={'dimensions':{k:dict(a=None,b=None,relation='not_applicable') for k in DIMENSIONS}}
        p['dimensions']['operation']['relation']='equivalent'
        with self.assertRaises(ValueError):dimension_agreement(p)
        p['dimensions']['operation']=dict(a='grasp',b='grasp',relation='equivalent')
        p['dimensions']['extra']=dict(a=None,b=None,relation='not_applicable')
        with self.assertRaises(ValueError):dimension_agreement(p)


if __name__=='__main__':unittest.main()
