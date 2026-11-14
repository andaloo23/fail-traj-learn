"""Offline guards for the paid 500-episode collection."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import oopsie_bulk_v8_1 as prep
import oopsie_bulk_batch as bulk


class BulkTests(unittest.TestCase):
    def test_extension_excludes_old_labels_aliases_and_known_bad_sources(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);previous=root/'previous';previous.mkdir()
            cfg=dict(revision='release',development_labs=['dev'],test_labs=['test'],exclude_previous_runs=['previous'])
            (previous/'config.json').write_text(json.dumps(cfg))
            (previous/'selection.json').write_text(json.dumps(dict(episodes=[dict(id='O0001',release_path='old',hdf5_sha256='oldhash')],
                technical_exclusions=[dict(release_path='bad')])) )
            def row(eid,path,digest,video):
                return dict(id=eid,release_path=path,release_file_sha256=digest,video_reference_paths_json=json.dumps([video]))
            rows=[row('O0001','old','oldhash','v1'),row('O0002','hash_alias','oldhash','v2'),
                  row('O0003','video_alias','different','v1'),row('O0004','bad','bad','v2'),row('O0005','new','newhash','v2')]
            videos={'v1':dict(release_sha256='oldvideo'),'v2':dict(release_sha256='newvideo')}
            with patch.object(prep.common,'ROOT',root):
                kept,provenance,counts=prep.exclude_previous_collections({'train':rows},cfg,videos)
            self.assertEqual([r['id'] for r in kept['train']],['O0005'])
            self.assertEqual(counts['previously_collected_episode_or_video_set'],3)
            self.assertEqual(counts['previous_technical_exclusion'],1)
            self.assertEqual(provenance[0]['selection_sha256'],prep.common.sha(previous/'selection.json'))

    def test_extension_refuses_changed_held_out_labs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);previous=root/'previous';previous.mkdir()
            cfg=dict(revision='release',development_labs=['dev'],test_labs=['test'],exclude_previous_runs=['previous'])
            (previous/'config.json').write_text(json.dumps(dict(cfg,test_labs=['other'])))
            (previous/'selection.json').write_text(json.dumps(dict(episodes=[])))
            with patch.object(prep.common,'ROOT',root),self.assertRaisesRegex(ValueError,'held-out labs'):
                prep.exclude_previous_collections({'train':[]},cfg,{})

    def test_lab_balancing_is_seeded_and_preserves_rows(self):
        rows=[dict(source_repo=lab,release_path=lab+'/'+str(i)) for lab,n in [('a',8),('b',3)] for i in range(n)]
        ordered=prep.balanced_order(rows,42)
        self.assertEqual(ordered,prep.balanced_order(list(reversed(rows)),42))
        self.assertEqual({r['source_repo'] for r in ordered[:2]},{'a','b'})
        self.assertEqual(len(ordered),len(rows))

    def test_budget_reserves_cache_writes_and_long_context(self):
        cfg={'max_output_tokens':8192}
        self.assertAlmostEqual(bulk.ceiling(100000,cfg),.16596)
        self.assertAlmostEqual(bulk.ceiling(300000,cfg),.81144)
        self.assertAlmostEqual(bulk.usage_cost({'usage':{'input_tokens':100000,'output_tokens':100,
            'input_tokens_details':{'cached_tokens':20000,'cache_write_tokens':30000}}}),.089)

    def test_payload_retains_every_frame_and_only_sol(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'prompt.md').write_text('Frozen V8.1 prompt')
            images=[]
            for i in range(3):
                p=root/f'{i}.webp';Image.new('RGB',(4,4),(i,1,2)).save(p,lossless=True)
                images.append(dict(frame=i,seconds=i/10,camera='all camera panels',path=p.name,sha256=bulk.common.sha(p)))
            e=dict(id='O0001',task='Move the cup',n_frames=3,fps=10,cameras=[dict(camera='wrist',description='Native')],images=images)
            body=bulk.payload(root,{'config':{'max_output_tokens':8192}},e)
            self.assertEqual(body['model'],'gpt-6.1-sol')
            self.assertEqual(body['truncation'],'disabled')
            self.assertNotIn('service_tier',body)
            self.assertEqual(len([x for x in body['input'][0]['content'] if x['type']=='input_image']),3)
            self.assertTrue(all(x['image_url'].startswith('data:image/webp;base64,') for x in body['input'][0]['content'] if x['type']=='input_image'))

    def test_prior_submission_cannot_be_sent_again(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'batch_001.json';p.write_text('{}')
            with patch.object(bulk.batch_io,'upload') as upload:
                with self.assertRaisesRegex(ValueError,'no resend'):
                    bulk.submit_shard(root,{},dict(path='batch_001.jsonl'),p,'not-a-real-key')
                upload.assert_not_called()

    def test_ingest_preserves_native_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'manifest.json').write_text('{}');(root/'requests').mkdir()
            (root/'requests/O0001_sol.json').write_text('{}')
            m={'episodes':[dict(id='O0001',n_frames=3,cameras=[dict(camera='wrist')])]}
            answer='# Episode: O0001\n\n| Start frame | End frame | Failure |\n| --- | --- | --- |\n| 0 | 3 | No |\n\n## Failure annotations\n\nNone\n'
            raw=dict(model='gpt-6.1-sol',status='completed',output=[dict(content=[dict(type='output_text',text=answer)])],
                     usage=dict(input_tokens=100,output_tokens=20))
            record=dict(custom_id='O0001_sol_r01',response=dict(status_code=200,body=raw),error=None)
            line=json.dumps(record).encode()+b'\n';shard={'custom_ids':['O0001_sol_r01']}
            bulk.ingest(root,m,shard,line);bulk.ingest(root,m,shard,line)
            folder=root/'traces/O0001_sol_r01'
            self.assertEqual((folder/'annotation.md').read_bytes().decode(),answer)
            self.assertEqual((folder/'batch_record.jsonl').read_bytes(),line)
            self.assertEqual(json.loads((folder/'attempt.json').read_text())['status'],'validated')
            # Recover a locally interrupted ingest without a second generation.
            (folder/'attempt.json').unlink()
            bulk.ingest(root,m,shard,line)
            self.assertEqual(json.loads((folder/'attempt.json').read_text())['status'],'validated')
            with self.assertRaisesRegex(ValueError,'duplicate'):
                bulk.ingest(root,m,shard,line+line)

    def test_unknown_native_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'Unknown'):
                bulk.ingest(Path(d),{'episodes':[]},{'custom_ids':[]},b'{"custom_id":"wrong"}\n')


if __name__=='__main__':unittest.main()
