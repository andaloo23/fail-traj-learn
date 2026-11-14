import copy
import json
from pathlib import Path
import unittest

from flora_camera_mapping import map_cameras


class CameraMappingTests(unittest.TestCase):
    def setUp(self):
        self.mapping = json.loads(Path(__file__).with_name('oopsie_camera_mapping.json').read_text())['episodes']['O003']
        self.cameras = [dict(camera=name, path=name+'.mp4', sha256=name)
                        for name in ('aria', 'left_wrist', 'right_wrist')]

    def apply(self, mapping=None, cameras=None):
        return map_cameras('O003', cameras or self.cameras, mapping or self.mapping,
                           Path('/source'), Path('/jobs'))

    def test_dense_uses_spatial_order_while_rubric_descriptions_follow_separate_videos(self):
        dense, rubric, descriptions = self.apply()
        self.assertEqual([Path(p).stem for p in dense], ['left_wrist', 'aria', 'right_wrist'])
        self.assertEqual([Path(p).stem for p in rubric], ['aria', 'left_wrist', 'right_wrist'])
        self.assertIn('scene camera', descriptions[0])

    def test_reordered_slots_are_rejected(self):
        mapping = copy.deepcopy(self.mapping)
        mapping['dense'][0], mapping['dense'][1] = mapping['dense'][1], mapping['dense'][0]
        with self.assertRaisesRegex(ValueError, 'slot order'):
            self.apply(mapping=mapping)

    def test_unaccounted_source_camera_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'every source camera'):
            self.apply(cameras=self.cameras+[dict(camera='extra', path='extra.mp4', sha256='extra')])

    def test_unreviewed_geometry_is_rejected(self):
        mapping = copy.deepcopy(self.mapping)
        mapping['visually_reviewed'] = False
        with self.assertRaisesRegex(ValueError, 'visual review'):
            self.apply(mapping=mapping)

    def test_duplicate_inputs_are_rejected(self):
        cameras = copy.deepcopy(self.cameras)
        cameras[1]['sha256'] = cameras[0]['sha256']
        with self.assertRaisesRegex(ValueError, 'duplicate video'):
            self.apply(cameras=cameras)


if __name__ == '__main__':
    unittest.main()
