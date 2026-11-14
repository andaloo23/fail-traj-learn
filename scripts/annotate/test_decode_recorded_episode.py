"""Recorded-camera ordering and fallback checks without LeRobot or simulation."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

import numpy as np
import decode_recorded_episode as decoder


class DecoderTests(unittest.TestCase):
    def fixture(self):
        timestamps = np.array([0.0, 0.05])
        ep = SimpleNamespace(ep=0, n=2, col=lambda key: timestamps,
                             frame=lambda i: (np.full((256, 256, 3), i, np.uint8),
                                              np.full((256, 256, 3), i + 10, np.uint8)))
        row = {f"videos/{decoder.CAM_MAIN}/from_timestamp": 1.0,
               f"videos/{decoder.CAM_WRIST}/from_timestamp": 2.0}
        meta = SimpleNamespace(episodes=[row], get_video_file_path=lambda ep, key: key + ".mp4")
        ds = SimpleNamespace(meta=meta, root=Path("recordings"), tolerance_s=0.001,
                             _video_backend="fixture")
        return ds, ep

    def modules(self, function):
        return {"lerobot": SimpleNamespace(), "lerobot.datasets": SimpleNamespace(),
                "lerobot.datasets.video_utils": SimpleNamespace(decode_video_frames=function)}

    def test_camera_order_offsets_and_channel_conversion(self):
        ds, ep = self.fixture()
        calls = []
        def decode(path, timestamps, tolerance, backend, return_uint8):
            calls.append((path.name, timestamps, tolerance, backend, return_uint8))
            return np.full((2, 3, 4, 4), len(calls), np.uint8)
        with patch.dict(sys.modules, self.modules(decode)):
            main, wrist, mode = decoder.decode_episode(ds, ep)
        self.assertEqual(mode, "batched")
        self.assertEqual(main.shape, (2, 4, 4, 3))
        self.assertTrue(np.all(main == 1) and np.all(wrist == 2))
        self.assertEqual(calls[0], (decoder.CAM_MAIN + ".mp4", [1.0, 1.05], 0.001, "fixture", True))
        self.assertEqual(calls[1][1], [2.0, 2.05])
        self.assertTrue(main.flags.c_contiguous and wrist.flags.c_contiguous)

    def test_incomplete_batch_uses_original_per_frame_camera_pairs(self):
        ds, ep = self.fixture()
        with patch.dict(sys.modules, self.modules(lambda *a, **k: np.zeros((1, 4, 4, 3), np.uint8))):
            main, wrist, mode = decoder.decode_episode(ds, ep)
        self.assertEqual(mode, "per_frame")
        self.assertEqual(main.shape, (2, 256, 256, 3))
        self.assertTrue(np.all(main[0] == 0) and np.all(main[1] == 1))
        self.assertTrue(np.all(wrist[0] == 10) and np.all(wrist[1] == 11))

    def test_float_batch_preserves_original_uint8_scaling(self):
        ds, ep = self.fixture()
        with patch.dict(sys.modules, self.modules(lambda *a, **k: np.full((2, 4, 4, 3), 0.5))):
            main, wrist, mode = decoder.decode_episode(ds, ep)
        self.assertEqual(mode, "batched")
        self.assertEqual(main.dtype, np.uint8)
        self.assertTrue(np.all(main == 127) and np.all(wrist == 127))


if __name__ == "__main__":
    unittest.main()
