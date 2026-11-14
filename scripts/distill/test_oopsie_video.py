"""Video review byte ranges and isolated Markdown note persistence."""
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import copy

from serve_oopsie_review import OopsieReviewHandler
from review_oopsie_video import compatible_episodes


class ReviewSourceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = dict(repo="OopsieData-Submissions/oopsiedata-v0.1", revision="pinned", episodes=[dict(
            id="O001", release_path="labs/lab/episode.h5", task="Pick cup", split="train", n_frames=50,
            fps=20, sampled_frames=[0, 49], cameras=[dict(camera="wrist", description="Wrist view")],
            original_cameras=[dict(camera="wrist", sha256="original-video-hash")])])

    def test_prompt_format_can_differ_for_the_same_original_recording(self):
        other = copy.deepcopy(self.manifest)
        other["config"] = dict(annotation_format="markdown")
        compatible_episodes(self.manifest, other)

    def test_changed_source_split_or_sample_grid_is_rejected(self):
        for key, value in (("split", "test"), ("release_path", "different.h5"), ("sampled_frames", [0, 10, 49])):
            other = copy.deepcopy(self.manifest)
            other["episodes"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                compatible_episodes(self.manifest, other)

    def test_changed_native_video_or_dataset_release_is_rejected(self):
        other = copy.deepcopy(self.manifest)
        other["episodes"][0]["original_cameras"][0]["sha256"] = "changed"
        with self.assertRaises(ValueError):
            compatible_episodes(self.manifest, other)
        other = copy.deepcopy(self.manifest)
        other["revision"] = "different"
        with self.assertRaises(ValueError):
            compatible_episodes(self.manifest, other)


class QuietHandler(OopsieReviewHandler):
    def log_message(self, *args):
        pass


class VideoServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = bytes(range(256)) * 4
        (self.root / "video.mp4").write_bytes(self.video)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(self.root)))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def test_video_range_supports_seeking(self):
        request = urllib.request.Request(self.url + "/video.mp4", headers={"Range": "bytes=10-29"})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.headers["Content-Range"], "bytes 10-29/1024")
            self.assertEqual(response.read(), self.video[10:30])

    def test_markdown_notes_are_append_only_and_exact_utf8(self):
        text = "# Automated fixture, not human review\n\nA café object 🤖 is visible.\n"
        paths = []
        for _ in range(2):
            request = urllib.request.Request(self.url + "/review-notes", data=text.encode(),
                      headers={"Content-Type": "text/markdown;charset=utf-8", "Origin": self.url}, method="POST")
            with urllib.request.urlopen(request) as response:
                self.assertEqual(response.status, 201)
                relative = response.read().decode()
                paths.append(relative)
                self.assertEqual((self.root / relative).read_bytes().decode(), text)
        self.assertNotEqual(*paths)

    def test_cross_origin_and_non_markdown_notes_are_rejected(self):
        for headers in ({"Content-Type": "text/markdown", "Origin": "https://example.com"},
                        {"Content-Type": "application/json"}):
            request = urllib.request.Request(self.url + "/review-notes", data=b"fixture", headers=headers, method="POST")
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(request)
        self.assertFalse((self.root / "reviews").exists())


if __name__ == "__main__":
    unittest.main()
