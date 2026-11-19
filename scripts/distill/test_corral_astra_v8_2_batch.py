"""No paid calls: full-run authorization, cache boundaries, limits and journals."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from fractions import Fraction
from unittest.mock import patch

import av
import h5py
from PIL import Image

import corral_astra_v8_2_batch as batch


class BatchTests(unittest.TestCase):
    def test_native_timestamps_and_every_frame_survive_variable_clock(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'source_files').mkdir()
            video=root/'clock.mp4'
            with av.open(str(video),'w') as out:
                stream=out.add_stream('libx264',rate=20);stream.width=32;stream.height=32;stream.pix_fmt='yuv420p'
                stream.time_base=Fraction(1,20)
                for i,pts in enumerate([0,1,3]):
                    frame=av.VideoFrame.from_image(Image.new('RGB',(32,32),(i*40,0,0)))
                    frame.pts=pts;frame.time_base=Fraction(1,20)
                    for packet in stream.encode(frame):out.mux(packet)
                for packet in stream.encode():out.mux(packet)
            hdf5=root/'episode.h5'
            with h5py.File(hdf5,'w') as f:
                f.attrs['language_instruction']='Move the object.'
                f.create_dataset('observations/video_paths/wrist',data='clock.mp4')
            files={}
            for rel,path in [('labs/test/episode.h5',hdf5),('labs/test/clock.mp4',video)]:
                meta=dict(sha256=batch.common.sha(path),bytes=path.stat().st_size);files[rel]=meta
                batch.link_file(path,batch.pilot.source_path(root,rel,meta))
            builder=object.__new__(batch.FullPreparation);builder.root=root;builder.files=files
            item=dict(id='C0042',lab='test',release_path='labs/test/episode.h5',timestep_count='4',
                video_reference_paths_json=json.dumps(['labs/test/clock.mp4']))
            result=builder.episode(item)
            self.assertEqual(result['n_frames'],3)
            self.assertEqual(result['source_timestep_count'],4)
            self.assertEqual([x['frame'] for x in result['images']],[0,1,2])
            for actual,expected in zip(result['frame_times'],[0,.05,.15]):self.assertAlmostEqual(actual,expected)
            self.assertTrue(all((root/x['path']).exists() for x in result['images']))

    def test_explicit_cache_ends_before_changing_episode_and_images(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'prompt.md').write_text('Shared exact prompt',encoding='utf-8')
            original=dict(input=[dict(role='user',content=[dict(type='input_text',text='Shared exact prompt\nEpisode 42'),
                dict(type='input_text',text='Frame 0'),dict(type='input_image',image_url='exact-pixels')])])
            with patch.object(batch.pilot,'payload',return_value=copy.deepcopy(original)):
                value=batch.payload(root,dict(id='C0042'))
            content=value['input'][0]['content']
            self.assertEqual(content[0]['text'],'Shared exact prompt')
            self.assertEqual(content[0]['prompt_cache_breakpoint'],dict(mode='explicit'))
            self.assertEqual(content[1]['text'],'\nEpisode 42')
            self.assertEqual(content[2:],original['input'][0]['content'][1:])
            self.assertEqual(value['prompt_cache_options'],dict(mode='explicit',ttl='30m'))

    def test_conservative_ceiling_includes_batch_long_context_and_writes(self):
        self.assertAlmostEqual(batch.batch_ceiling(100000),.80512)
        self.assertAlmostEqual(batch.batch_ceiling(300000),3.46024)
        self.assertGreater(batch.batch_ceiling(272001),batch.batch_ceiling(272000))

    def test_oversized_episode_is_held_without_network_or_frame_removal(self):
        episode=dict(id='C0042',images=[dict(frame=i) for i in range(1501)])
        with tempfile.TemporaryDirectory() as d, patch.object(batch,'verify_plan'), patch.object(batch,'Gateway') as gateway:
            with self.assertRaisesRegex(ValueError,'Image limit'):
                batch.preflight_one(Path(d),episode)
            gateway.assert_not_called()
        self.assertEqual(len(episode['images']),1501)

    def test_cached_preflight_rejects_changed_request(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'preflight').mkdir();(root/'requests').mkdir()
            (root/'preflight/C0042.json').write_text(json.dumps(dict(episode='C0042',request_sha256='frozen')))
            (root/'requests/C0042_astra.json').write_text('Changed request')
            with patch.object(batch,'verify_plan'),self.assertRaisesRegex(ValueError,'Frozen request changed'):
                batch.preflight_one(root,dict(id='C0042'))

    def test_existing_journal_prevents_any_resubmission(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'batch_jobs').mkdir();(root/'batch_jobs/batch_a.json').write_text('{}')
            with patch.object(batch,'verify_plan'),patch.object(batch,'Gateway') as gateway:
                with self.assertRaisesRegex(ValueError,'Existing submission journal'):
                    batch.submit_shard(root,dict(path='batch_inputs/batch_a.jsonl'),gateway)
                gateway.upload.assert_not_called()

    def test_user_review_hold_blocks_submission_before_upload_or_api(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'contact_sheet_submission_hold.json').write_text(json.dumps(dict(submission_allowed=False,episode_ids=['C0094'])))
            with patch.object(batch,'verify_plan') as verify,patch.object(batch,'Gateway') as gateway:
                with self.assertRaisesRegex(ValueError,'User review required'):
                    batch.submit_shard(root,dict(episodes=['C0094']),gateway)
                verify.assert_not_called()
                gateway.upload.assert_not_called()
                gateway.api.assert_not_called()

    def test_file_ids_preserve_every_exact_image_and_reuse_upload_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'images').mkdir()
            images=[];content=[dict(type='input_text',text='Shared prompt')]
            for index in range(4):
                path=root/'images'/f'{index}.webp';Image.new('RGB',(8,8),(index,0,0)).save(path,lossless=True)
                images.append(dict(frame=index,path=path.relative_to(root).as_posix(),sha256=batch.common.sha(path)))
                content.append(dict(type='input_image',image_url='data:image/webp;base64,'+'A'*2000,detail='high'))
            episode=dict(id='C0042',images=images);body=dict(input=[dict(role='user',content=content)])
            class FakeGateway:
                calls=0
                def upload(self,path,request_id,purpose):
                    self.assert_purpose=purpose
                    FakeGateway.calls+=1
                    return dict(id='file-'+path.stem,bytes=path.stat().st_size)
            with patch.object(batch,'Gateway',FakeGateway):
                packed=batch.file_id_payload(root,episode,copy.deepcopy(body),max_bytes=3000)
                before=FakeGateway.calls
                again=batch.file_id_payload(root,episode,copy.deepcopy(body),max_bytes=3000)
            self.assertEqual(FakeGateway.calls,before)
            self.assertEqual(packed,again)
            self.assertEqual(sum(x['type']=='input_image' for x in packed['input'][0]['content']),4)
            self.assertTrue(all((root/x['path']).exists() and batch.common.sha(root/x['path'])==x['sha256'] for x in images))

    def test_png_fallback_preserves_rgb_when_provider_rejects_valid_webp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'images').mkdir();path=root/'images/frame.webp'
            Image.new('RGB',(8,8),(12,34,56)).save(path,lossless=True)
            episode=dict(id='C0042',images=[dict(frame=0,path='images/frame.webp',sha256=batch.common.sha(path))])
            body=dict(input=[dict(role='user',content=[dict(type='input_image',image_url='A'*5000,detail='high')])])
            class FakeGateway:
                def upload(self,path,request_id,purpose):
                    if path.suffix=='.webp':raise RuntimeError('Invalid file format application/octet-stream')
                    return dict(id='file-png',bytes=path.stat().st_size)
            with patch.object(batch,'Gateway',FakeGateway),patch.object(batch.time,'sleep'):
                value=batch.file_id_payload(root,episode,body,max_bytes=3000)
            self.assertEqual(value['input'][0]['content'][0]['file_id'],'file-png')
            with Image.open(path) as original,Image.open(root/'transport_images/C0042/frame.png') as copy_image:
                self.assertEqual(original.convert('RGB').tobytes(),copy_image.convert('RGB').tobytes())

    def test_wrong_native_teacher_is_preserved_and_stops_collection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            state=dict(shard=dict(episodes=['C0042']),batch=dict(id='batch-test'))
            raw=dict(model='another-model',output=[])
            envelope=dict(custom_id='C0042_astra_r01',error=None,response=dict(status_code=200,body=raw))
            with patch.object(batch.transport,'extract_answer',return_value=('native answer',True)):
                with self.assertRaisesRegex(ValueError,'Unexpected native teacher'):
                    batch.ingest(root,state,json.dumps(envelope).encode())
            folder=root/'traces/C0042_astra'
            self.assertEqual(json.loads((folder/'response.json').read_text())['model'],'another-model')
            self.assertFalse((folder/'status.json').exists())
            self.assertTrue((folder/'error.json').exists())


if __name__=='__main__':unittest.main()
