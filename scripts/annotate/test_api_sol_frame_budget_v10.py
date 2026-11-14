import unittest
import api_sol_frame_budget_v10 as pilot


class FrameBudgetTests(unittest.TestCase):
    def setUp(self):
        self.ep={'n_frames':280,'sampled_frames':list(range(0,280,5))+[279]}

    def test_nested_uniform_and_matched_cap(self):
        prior=set(self.ep['sampled_frames'])
        for arm,n in [('hz2',29),('hz1',15),('hz05',8),('hz025',5)]:
            fs=pilot.sampled(self.ep,arm)
            self.assertEqual(len(fs),n)
            self.assertEqual((fs[0],fs[-1]),(0,279))
            self.assertTrue(set(fs)<=prior)
            prior=set(fs)
        fs=pilot.sampled(self.ep,'uniform_cap')
        self.assertEqual(len(set(fs)),24)
        self.assertTrue(set(fs)<=set(self.ep['sampled_frames']))

    def test_request_bounds_duplicates_and_unseen(self):
        for fs in [[0],[5,5],[3],[280],list(range(5,50,5)),[True]]:
            with self.assertRaises(ValueError):
                pilot.request_frames({'request_frames':fs,'reason':'check'},self.ep,{0},0)
        self.assertEqual(pilot.request_frames({'request_frames':[15,5],'reason':'inspect contact'},self.ep,{0},1),[5,15])
        with self.assertRaises(ValueError):
            pilot.request_frames({'request_frames':[5],'reason':'check'},self.ep,{0},2)

    def test_short_episode_cap(self):
        ep={'n_frames':150,'sampled_frames':list(range(0,150,5))+[149]}
        self.assertEqual(len(pilot.sampled(ep,'adaptive')),5)
        self.assertEqual(len(pilot.sampled(ep,'uniform_cap')),21)


if __name__=='__main__': unittest.main()
