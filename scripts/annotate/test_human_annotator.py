import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

try:
    from human_annotator import discover_sources, handler_for, privileged_contact_payload
except ModuleNotFoundError:  # Supports `python -m unittest scripts.annotate...` from the repo root.
    from scripts.annotate.human_annotator import discover_sources, handler_for, privileged_contact_payload


class HumanAnnotatorTests(unittest.TestCase):
    def make_episode(self, root: Path, name: str, annotated: bool = False) -> Path:
        episode = root / name
        episode.mkdir()
        frames = np.zeros((2, 4, 4, 3), dtype=np.uint8)
        np.savez(episode / "cameras.npz", agent=frames, wrist=frames)
        (episode / "observable.json").write_text(json.dumps({"id": name, "task": f"task {name}"}))
        if annotated:
            (episode / "human_annotation.json").write_text(json.dumps({"id": name, "segments": []}))
        return episode

    def test_discovers_natural_order_and_first_unfinished(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            h1 = self.make_episode(root, "H1", annotated=True)
            self.make_episode(root, "H10")
            self.make_episode(root, "H2")
            sources, start = discover_sources(root)
            self.assertEqual([p.name for p in sources], ["H1", "H2", "H10"])
            self.assertEqual(start, 1)
            siblings, requested = discover_sources(h1)
            self.assertEqual([p.name for p in siblings], ["H1", "H2", "H10"])
            self.assertEqual(requested, 0)

    def test_privileged_contacts_are_named_and_ignore_padded_slots(self):
        contact = np.array([[1, 0, 0], [0, 1, 1]])
        grasped = np.array([[0, 0, 0], [0, 1, 1]])
        supported = np.array([[1, 0, 0], [0, 0, 1]])
        payload = privileged_contact_payload(["target", "distractor"], "target", contact, grasped, supported)
        self.assertEqual(payload["frames"][0], {
            "contact": ["target"], "grasped": [], "supported": ["target"],
        })
        self.assertEqual(payload["frames"][1], {
            "contact": ["distractor"], "grasped": ["distractor"], "supported": [],
        })

    def test_http_navigation_frames_and_episode_scoped_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.make_episode(root, "H001")
            second = self.make_episode(root, "H002")
            sources = [first, second]
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(sources, 0))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                page = urlopen(base + "/", timeout=5).read().decode()
                self.assertIn("H001", page)
                self.assertIn("Save &amp; next episode", page)
                self.assertIn("Replay annotations from start", page)
                self.assertIn('id="reviewPanel"', page)
                self.assertIn('id="privilegedPanel"', page)
                self.assertIn('"base_url": "/episode/0"', page)
                self.assertEqual(urlopen(base + "/episode/0/frames/agent_000000.jpg", timeout=5).status, 200)

                value = {"id": "H001", "segments": [], "updated_at": "now"}
                request = Request(base + "/episode/0/save", data=json.dumps(value).encode(),
                                  headers={"Content-Type": "application/json"}, method="POST")
                self.assertEqual(urlopen(request, timeout=5).read(), b"saved")
                saved = json.loads((first / "human_annotation.json").read_text())
                self.assertEqual(saved["source"], str(first))
                self.assertFalse((second / "human_annotation.json").exists())

                next_page = urlopen(base + "/episode/1/", timeout=5).read().decode()
                self.assertIn('"base_url": "/episode/1"', next_page)
                self.assertIn("H002", next_page)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
