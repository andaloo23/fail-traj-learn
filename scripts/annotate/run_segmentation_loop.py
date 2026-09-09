"""Reproduce the selected event-first iteration loop on one episode, resumably.

It scans twice with shifted sampling, refines model-proposed events, labels every chunk twice with
different context/seeds, and combines the evidence. It does not read human or simulator reference labels.
"""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dataset")
    p.add_argument("episode", type=int)
    p.add_argument("--tag", required=True)
    args = p.parse_args()
    directory = Path(__file__).resolve().parent
    common = ["--dataset", args.dataset, "--episode", str(args.episode)]
    def run(script, *options):
        command = [sys.executable, str(directory / script), *common, *options]
        print("RUN", " ".join(command), flush=True)
        subprocess.run(command, check=True)

    scan_a, scan_b, dense = (args.tag + suffix for suffix in ("_scan_a", "_scan_b", "_dense"))
    phase_a, phase_b = args.tag + "_phase_a", args.tag + "_phase_b"
    run("segmentation_lab.py", "--tag", scan_a, "--configs", "state_both", "--frame-stride", "5", "--scale", "2")
    run("segmentation_lab.py", "--tag", scan_b, "--configs", "state_both", "--frame-stride", "5", "--offset", "2", "--scale", "2")
    run("segmentation_lab.py", "--tag", dense, "--configs", "state_both", "--refine-from", scan_a,
        "--scale", "2", "--repeats", "3", "--temperature", "0.3")
    run("local_segmenter.py", "--tag", phase_a, "--motion", "--states-tag", scan_a)
    run("local_segmenter.py", "--tag", phase_b, "--motion", "--states-tag", scan_b, "--context", "5", "--seed", "9100")
    run("combine_local_evidence.py", "--states-tags", scan_a, scan_b, "--refinement-tags", dense,
        "--local-tag", phase_a, "--context-tag", phase_b, "--out-tag", args.tag + "_review")


if __name__ == "__main__":
    main()
