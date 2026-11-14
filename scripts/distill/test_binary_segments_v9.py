"""Binary V9 partitions, frozen all-frame inputs, repeatability and paid-call guards."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import binary_segments_v9 as v9
import oopsie_common as common


def text(eid="O005", n=3):
    return f"# Episode: {eid}\n\n| Start frame | End frame | Failure |\n| --- | --- | --- |\n| 0 | 1 | No |\n| 1 | {n} | Yes |\n"


def fixture(root):
    root.mkdir()
    cfg=common.read(common.ROOT/"configs/oopsie_binary_v9.json")
    cfg["episodes"]=["O005"]
    common.write(root/"config.json",cfg)
    (root/"prompt.md").write_text("Return only the binary segment table.",encoding="utf-8")
    images=[]
    for frame in range(3):
        path=f"images/{frame}.jpg"
        (root/path).parent.mkdir(exist_ok=True)
        (root/path).write_bytes(b"isolated offline fixture")
        images.append(dict(frame=frame,seconds=frame/5,camera="native_wrist",path=path))
    episode=dict(id="O005",release_path="labs/test/episode.h5",lab="test",split="train",task="Place object",fps=5,n_frames=3,
                 cameras=[dict(camera="native_wrist",description="Wrist camera")],images=images,videos=[])
    manifest=dict(protocol=v9.PROTOCOL,repo=common.REPO_ID,revision="pinned",source_annotations_used_as_model_input=False,
                  config=cfg,episodes=[episode],files={p.relative_to(root).as_posix():common.sha(p) for p in root.rglob("*") if p.is_file()})
    common.write(root/"manifest.json",manifest)
    return manifest


class BinaryTests(unittest.TestCase):
    def test_camera_strips_retain_each_frame_view_and_pixels(self):
        from PIL import Image, ImageChops
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            episode = dict(id='O011', n_frames=2, cameras=[dict(camera='left'),dict(camera='wrist')], images=[])
            for frame in range(2):
                for index, camera in enumerate(('left','wrist')):
                    relative = f'{frame}_{camera}.png'
                    Image.new('RGB',(3+index,4-index),(frame*80,index*90,30)).save(root/relative)
                    episode['images'].append(dict(frame=frame,seconds=frame/5,camera=camera,path=relative))
            v9.pack_camera_views(root,episode)
            self.assertEqual([x['frame'] for x in episode['images']], [0,1])
            self.assertEqual(len(episode['source_images']),4)
            for packed in episode['images']:
                with Image.open(root/packed['path']) as strip:
                    self.assertEqual(strip.size,(7,4))
                    for panel in packed['panels']:
                        with Image.open(root/panel['source_path']) as original:
                            crop=strip.crop((panel['x'],0,panel['x']+panel['width'],panel['height']))
                            self.assertIsNone(ImageChops.difference(crop,original).getbbox())

    def test_long_context_prices_apply_to_whole_request_without_changing_frozen_rates(self):
        cfg=dict(rates_per_million=dict(sol=dict(input=2,cached=.1,cache_write=2.5,output=10)),
                 long_context_pricing=dict(threshold_input_tokens=272000,input_multiplier=2,output_multiplier=1.5))
        self.assertEqual(v9.request_rates(cfg,'sol',272000)['input'],2)
        self.assertEqual(v9.request_rates(cfg,'sol',272001),dict(input=4,cached=.2,cache_write=5,output=15))
        self.assertEqual(cfg['rates_per_million']['sol']['input'],2)

    def test_binary_only_partition_preserves_exact_labels(self):
        expected=[dict(start_frame=0,end_frame=1,failure=False),dict(start_frame=1,end_frame=3,failure=True)]
        self.assertEqual(v9.parse(text(),dict(id="O005",n_frames=3)),expected)
        self.assertEqual(v9.parse(text().replace("\n","\r\n"),dict(id="O005",n_frames=3)),expected)

    def test_nonfailure_episode_is_valid_without_forced_positives(self):
        answer=text().replace("| 0 | 1 | No |\n| 1 | 3 | Yes |","| 0 | 3 | No |")
        self.assertEqual(v9.parse(answer,dict(id="O005",n_frames=3)),[dict(start_frame=0,end_frame=3,failure=False)])

    def test_invalid_partition_and_additional_fields_are_rejected(self):
        original=text()
        candidates=[original+"Explanation: something failed.\n",original.replace("| 1 | 3 | Yes |","| 2 | 3 | Yes |"),
            original.replace("| 1 | 3 | Yes |","| 0 | 3 | Yes |"),original.replace("| 1 | 3 | Yes |","| 1 | 2 | Yes |"),
            original.replace("| 1 | 3 | Yes |","| 1 | 4 | Yes |"),original.replace("| 1 | 3 | Yes |","| 1 | 3 | No |"),
            original.replace("| Failure |","| Failure | Category |"),original.replace("O005","O006"),
            original.replace("| Yes |","| Maybe |"),"```markdown\n"+original+"```"]
        for invalid in candidates:
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                v9.parse(invalid,dict(id="O005",n_frames=3))

    def test_agreement_does_not_score_all_negative_as_perfect_failure_iou(self):
        negative=[dict(start_frame=0,end_frame=3,failure=False)]
        r=v9.compare(negative,negative,3)
        self.assertEqual(r["frame_agreement"],1)
        self.assertIsNone(r["failure_iou"])
        positive=v9.parse(text(),dict(id="O005",n_frames=3))
        r=v9.compare(positive,negative,3)
        self.assertAlmostEqual(r["frame_agreement"],1/3)
        self.assertEqual(r["failure_iou"],0)


class CollectionTests(unittest.TestCase):
    def test_complete_preflight_freezes_requests_and_collection_reuses_token_counts(self):
        calls=[]
        def post(url,provider,body,keys):
            calls.append(url)
            if url.endswith('input_tokens'):
                return dict(input_tokens=100)
            return dict(status='completed',model=body['model'],usage=dict(input_tokens=100,output_tokens=30),
                        output=[dict(content=[dict(type='output_text',text=text())])])
        with patch.object(v9.transport,'post',side_effect=post),patch.object(v9.transport,'credentials',return_value={'openai':'fixture'}):
            receipt=v9.preflight(self.root)
            self.assertTrue(receipt['complete'])
            self.assertEqual(receipt['generation_calls'],0)
            self.assertEqual(len(calls),2)
            result=v9.collect(self.root,10)
        self.assertEqual(sum(url.endswith('input_tokens') for url in calls),2)
        self.assertEqual(result['validated'],6)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"run";self.manifest=fixture(self.root)

    def test_every_camera_frame_is_required(self):
        v9.verify(self.root)
        changed=copy.deepcopy(self.manifest);changed["episodes"][0]["images"].pop(1)
        (self.root/"manifest.json").write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError,"full-rate"):
            v9.verify(self.root)

    def test_payload_is_visual_only_and_retains_all_frames(self):
        body=v9.payload(self.root,self.manifest,self.manifest["episodes"][0],"sol")
        content=body["input"][0]["content"]
        self.assertEqual(sum(c["type"]=="input_image" for c in content),3)
        self.assertTrue(all(f"Frame {f} |" in str(content) for f in range(3)))
        self.assertNotIn("gripper_command",str(body))
        self.assertNotIn("episode_annotations",str(body))

    def test_repeats_are_independent_identical_requests_and_never_resent(self):
        calls=[]
        def post(url,provider,body,keys):
            if url.endswith("input_tokens"):return dict(input_tokens=100)
            calls.append(body)
            return dict(status="completed",model=body["model"],usage=dict(input_tokens=100,output_tokens=30),
                        output=[dict(content=[dict(type="output_text",text=text())])])
        with patch.object(v9.transport,"post",side_effect=post),patch.object(v9.transport,"credentials",return_value={"openai":"fixture"}):
            r=v9.collect(self.root,10)
            self.assertEqual(r["validated"],6)
            self.assertFalse(r["invalid"])
            again=v9.collect(self.root,10)
        self.assertEqual(len(calls),6)
        self.assertEqual(again["validated"],6)
        self.assertEqual(calls[0],calls[2]);self.assertEqual(calls[1],calls[3])
        for p in (self.root/"traces").glob("*/annotation.md"):
            self.assertEqual(p.read_bytes().decode(),text())
        v9.report(self.root)
        self.assertIn("Repeatability",(self.root/"report.md").read_text())

    def test_budget_and_unknown_submission_stop_without_retries(self):
        def post(url,*args):
            if url.endswith("input_tokens"):return dict(input_tokens=100)
            raise RuntimeError("Unknown network outcome")
        with patch.object(v9.transport,"post",side_effect=post),patch.object(v9.transport,"credentials",return_value={"openai":"fixture"}):
            with self.assertRaisesRegex(ValueError,"budget"):
                v9.collect(self.root,0.00001)
            r=v9.collect(self.root,10)
            self.assertEqual(len(r["invalid"]),1)
            with self.assertRaisesRegex(ValueError,"not be resent"):
                v9.collect(self.root,10)
        self.assertFalse((self.root/"collection.lock").exists())

    def test_frozen_input_tampering_is_rejected(self):
        (self.root/"images/0.jpg").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"Changed frozen input"):
            v9.verify(self.root)

    def test_combined_review_preserves_native_answers_and_source_manifests(self):
        extra=self.root.parent/"extra"
        m=fixture(extra)
        m["episodes"][0].update(id="O007",release_path="labs/other/O007.h5",lab="other",split="development")
        m["config"]["episodes"]=["O007"]
        (extra/"config.json").write_text(json.dumps(m["config"]))
        m["files"]["config.json"]=common.sha(extra/"config.json")
        (extra/"manifest.json").write_text(json.dumps(m))
        def post(url,provider,body,keys):
            if url.endswith("input_tokens"):return dict(input_tokens=100)
            eid="O007" if "- Episode: O007" in body["input"][0]["content"][0]["text"] else "O005"
            return dict(status="completed",model=body["model"],usage=dict(input_tokens=100,output_tokens=30),
                        output=[dict(content=[dict(type="output_text",text=text(eid))])])
        with patch.object(v9.transport,"post",side_effect=post),patch.object(v9.transport,"credentials",return_value={"openai":"fixture"}):
            v9.collect(self.root,10);v9.collect(extra,10)
        before={p:common.sha(p) for p in [self.root/"manifest.json",extra/"manifest.json",*self.root.glob("traces/*/annotation.md"),*extra.glob("traces/*/annotation.md")]}
        result=v9.review(extra,[self.root])
        self.assertEqual(result["episodes"],2)
        self.assertEqual(result["validated"],12)
        copy=extra/"review_annotations/run/traces/O005_sol_r01/annotation.md"
        self.assertEqual(copy.read_bytes(),(self.root/"traces/O005_sol_r01/annotation.md").read_bytes())
        self.assertTrue(all(common.sha(p)==digest for p,digest in before.items()))
        self.assertIn("source_manifest_sha256",(extra/"review.html").read_text(encoding='utf-8'))
        self.assertIn("review_report.md",(extra/"review.html").read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError,"Duplicate episode"):
            v9.review(extra,[extra])
        (self.root/"prompt.md").write_text("Different protocol")
        changed=common.read(self.root/"manifest.json");changed["files"]["prompt.md"]=common.sha(self.root/"prompt.md")
        (self.root/"manifest.json").write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError,"same prompt"):
            v9.review(extra,[self.root])


if __name__=="__main__":
    unittest.main()
