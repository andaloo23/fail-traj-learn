"""Run fixture-based CPU tests without paid APIs, model downloads, or GPU jobs.

Real processor/model integration tests are excluded. Each directory gets a fresh
interpreter so tests cannot share module globals across workflows.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("annotate", "distill", "tacc")


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=SCOPES)
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    if args.scope is None:
        results = [subprocess.run([sys.executable, __file__, "--scope", scope], cwd=ROOT).returncode
                   for scope in SCOPES]
        return int(any(results))
    folder = ROOT / "scripts" / args.scope
    sys.path.insert(0, str(folder))
    loader = unittest.TestLoader()
    suite = loader.discover(str(folder), pattern="test_*.py")
    safe = unittest.TestSuite()
    for case in cases(suite):
        if case.id().startswith("test_qwen_oopsie.RealProcessorTests."):
            print("Integration test excluded:", case.id())
        else:
            safe.addTest(case)
    return int(not unittest.TextTestRunner(verbosity=1).run(safe).wasSuccessful())


if __name__ == "__main__":
    raise SystemExit(main())
