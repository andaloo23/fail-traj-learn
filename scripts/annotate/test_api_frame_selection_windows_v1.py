import unittest
import api_frame_selection_windows_v1 as r

class SelectionTests(unittest.TestCase):
    def ep(self, n):
        budget = 12 if n == 150 else 24
        uniform = r.evenly(list(range(n)), budget)
        overview = r.evenly(uniform, 4 if n == 150 else 6)
        return dict(n_frames=n,budget=budget,uniform=uniform,overview=overview,
                    pool=sorted(set(range(0,n,5))|{n-1}), point_count=budget-len(overview),
                    window_count=2 if n==150 else 3,pairs_per_window=4 if n==150 else 6,
                    allowed_window_starts=list(range(0,n-10,5)))
    def window_text(self, n):
        return '# Window selection\n## Selected windows\n' + '\n'.join('- [%d, %d]'%(f,f+10) for f in ([0,50] if n==150 else [0,50,100]))
    def test_windows_preserve_budget_and_overview(self):
        for n in (150,280):
            ep=self.ep(n);frames,details=r.parse_selection(self.window_text(n),ep,'SW')
            self.assertEqual(len(frames),ep['budget'])
            self.assertEqual(len(set(frames)),len(frames))
            self.assertTrue(set(ep['overview'])<=set(frames))
            for (a,b),dense in zip(details['windows'],details['window_frames']):
                self.assertEqual(len(dense),ep['pairs_per_window'])
                self.assertTrue(all(a<=f<=b for f in dense))
                self.assertFalse(set(dense)&set(ep['overview']))
    def test_reject_overlap_and_out_of_bounds(self):
        for text in (self.window_text(280).replace('[50, 60]','[5, 15]'), self.window_text(280).replace('[100, 110]','[275, 285]')):
            with self.assertRaises(ValueError):r.parse_selection(text,self.ep(280),'SW')
    def test_points_budget_and_invalid_membership(self):
        ep=self.ep(280);points=sorted(set(ep['pool'])-set(ep['overview']))[:ep['point_count']]
        text='# Frame selection\n## Selected frames\n'+'\n'.join('- '+str(f) for f in points)
        frames,_=r.parse_selection(text,ep,'SP');self.assertEqual(len(frames),24)
        with self.assertRaises(ValueError):r.parse_selection(text.replace('- 5\n','- 1\n'),ep,'SP')
    def test_budget(self):
        self.assertEqual(len(r.jobs()),20)
        self.assertAlmostEqual(sum(j['reserved_usd'] for j in r.jobs()),3.36)

if __name__=='__main__':unittest.main()
