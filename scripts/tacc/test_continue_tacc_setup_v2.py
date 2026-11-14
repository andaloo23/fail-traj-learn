"""A resumed integrity check must never skip an unverified image prefix."""
import json
import unittest
import continue_tacc_setup_v2 as continuation


class ContinuationTests(unittest.TestCase):
    def test_only_complete_contiguous_verified_chunks_are_reused(self):
        lines=[dict(audited=11500,total=11535)]+[dict(verified_images=i,total=174028) for i in range(10000,120001,10000)]
        text='ordinary log output\n'+'\n'.join(json.dumps(x) for x in lines)+'\n{partial'
        self.assertEqual(continuation.verified_prefix(text,174028),120000)

    def test_missing_chunk_cannot_be_silently_skipped(self):
        text='\n'.join(json.dumps(dict(verified_images=i,total=174028)) for i in (10000,30000))
        with self.assertRaisesRegex(ValueError,'contiguous'):continuation.verified_prefix(text,174028)

    def test_another_inventory_or_empty_log_cannot_authorize_reuse(self):
        with self.assertRaises(ValueError):continuation.verified_prefix(json.dumps(dict(verified_images=10000,total=200000)),174028)
        with self.assertRaisesRegex(ValueError,'no verified'):continuation.verified_prefix('no completed chunks',174028)


if __name__=='__main__':unittest.main()
