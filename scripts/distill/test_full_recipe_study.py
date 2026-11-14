"""Full-data invariants against the actual frozen derived export."""
import json
import unittest
from collections import Counter,defaultdict

import oopsie_common as common
import oopsie_full_study as full
import qwen_recipe_runner as runner
import oopsie_recipe_data as data


class FullStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=full.ROOT;cls.folder=cls.root/'evidence_c32_x8_v3'
        cls.study,cls.source,cls.rows=runner.load(cls.folder)

    def test_every_training_and_development_timestamp_scored_once(self):
        episodes={e['episode']:e for e in self.study['episodes']}
        by_episode=defaultdict(list)
        for r in self.rows:
            self.assertNotEqual(r['split'],'test')
            if r['task']=='binary':by_episode[r['episode']].append(r)
        self.assertEqual(Counter(episodes[e]['split'] for e in by_episode),{'train':400,'development':50})
        for eid,rows in by_episode.items():
            cursor=0
            for r in sorted(rows,key=lambda x:x['core_start']):
                self.assertEqual(r['core_start'],cursor);cursor=r['core_end']
                data.parse_prediction(r['messages'][-1]['content'],eid,r['core_start'],r['core_end'])
            self.assertEqual(cursor,episodes[eid]['n_frames'])

    def test_invalid_auxiliary_fields_never_become_false_none_targets(self):
        invalid={e['episode'] for e in self.study['episodes'] if e['split']=='train' and not e['auxiliary_valid']}
        self.assertEqual(len(invalid),6)
        self.assertEqual(len({r['episode'] for r in self.rows if r['task']=='binary' and r['episode'] in invalid}),6)
        binary={r['id']:r for r in self.rows if r['task']=='binary'}
        for r in self.rows:
            if r['episode'] not in invalid:continue
            self.assertIn(r['task'],('binary','joint'))
            if r['task']=='joint':
                self.assertIn('auxiliary_omitted_reason',r)
                self.assertEqual(r['messages'],binary[r['id'].removesuffix('_joint')+'_binary']['messages'])

    def test_complete_primary_budget_and_grounded_auxiliary(self):
        primary=[r for r in self.rows if r['task']=='binary' and r['split']=='train']
        cfg=self.study['config'];ga=cfg['student']['gradient_accumulation']
        self.assertEqual(len(primary)*cfg['student']['epochs'],cfg['optimizer_updates']*ga)
        order=runner.sample_primary(primary,cfg['student']['seed'])
        self.assertEqual({r['episode'] for r in order},{e['episode'] for e in self.study['episodes'] if e['split']=='train'})
        self.assertEqual(len({r['id'] for r in order}),5376)
        for r in self.rows:
            if r['task'].endswith('_aux'):
                self.assertGreater(r['eligible_aux_annotations'],0)
                self.assertEqual(r['split'],'train')


if __name__=='__main__':unittest.main()
