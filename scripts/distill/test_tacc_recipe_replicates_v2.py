"""Independent replicas, authorization and real CPU interoperability checks."""
import importlib.metadata
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import tacc_recipe_replicates_v2 as replicas
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tacc'))
import submit_tacc_replicates_v2 as submit


class ReplicaTests(unittest.TestCase):
    def test_three_node_packs_cover_all_nine_experiments_once(self):
        flat=[r for pack in replicas.PACKS for r in pack]
        self.assertEqual(set(flat),set(['base']+replicas.TRAIN))
        self.assertEqual(len(flat),len(set(flat)))
        self.assertTrue(all(len(pack)==3 for pack in replicas.PACKS))
        self.assertLessEqual(len(replicas.PACKS)*32*3+.75+.143+.286,300)

    def test_real_cpu_array_image_and_hdf5_interoperability(self):
        # Exercise the setup smoke check with the installed NumPy, without
        # modifying any environment or touching the busy local GPU.
        with patch.object(replicas,'approved',return_value=({'numpy_pin':importlib.metadata.version('numpy')},Path('.'))),patch('torch.cuda.is_available',return_value=False):
            result=replicas.verify_environment()
        self.assertTrue(result['cpu_import_and_array_checks_passed'])
        self.assertFalse(result['cuda_available'])

    def test_wrong_numpy_is_rejected_before_setup_is_ready(self):
        with patch.object(replicas,'approved',return_value=({'numpy_pin':'unsupported-version'},Path('.'))):
            with self.assertRaisesRegex(ValueError,'Wrong NumPy'):replicas.verify_environment()

    def test_new_runs_require_explicit_duplicate_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);plan={'duplicate_local_experiments_authorized':False}
            replicas.save(root/'plan.json',plan,True)
            replicas.save(root/'approval.json',{'approved':True,'plan_sha256':replicas.frozen.digest(root/'plan.json')},True)
            with patch.object(replicas,'ROOT',root),patch.object(replicas.frozen,'approval',return_value=({},root)):
                with self.assertRaisesRegex(ValueError,'not authorized'):replicas.approved()

    def test_readiness_gate_cannot_reuse_old_attempt_marker(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'plan.json').write_text('{}')
            replicas.save(root/'setup_ready.json',{'plan_sha256':'different-plan'},True)
            with patch.object(replicas,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'another plan'):replicas.require_ready('setup_ready.json')

    def test_dependency_submission_sets_the_repo_workdir(self):
        args=submit.submission_args('train','12345')
        self.assertIn('--dependency=afterok:12345',args)
        self.assertIn('--chdir='+submit.REMOTE,args)
        self.assertIn('--kill-on-invalid-dep=yes',args)
        self.assertTrue(args[-1].endswith('oopsie_replicates_v2_train.sbatch'))


if __name__=='__main__':unittest.main()
