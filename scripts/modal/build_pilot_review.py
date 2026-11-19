"""Build a local, anonymized video review for development predictions."""
import argparse
from base64 import b64encode
from fractions import Fraction
import json
from pathlib import Path
import random
import subprocess

from qwen_astra_pilot import failure_intervals, read


def build_preview(plan_file, predictions, output):
    plan = read(plan_file)
    windows = [window for window in plan["windows"] if window["split"] == "development"]
    output.mkdir(parents=True, exist_ok=True)
    clips = output / "clips"
    clips.mkdir(exist_ok=True)
    rng = random.Random(plan["seed"])
    items = []
    for window in windows:
        case = window["id"]
        start, count, fps = window["start"], window["count"], window["fps"]
        target = window["targets"]["SCE"]
        members = [("Astra", target)]
        for arm, name in (("base", "Base Qwen"), ("adapter", "Fine-tuned Qwen")):
            path = predictions / f"{case}_{arm}.md"
            members.append((name, path.read_text(encoding="utf-8") if path.is_file() else ""))
        rng.shuffle(members)
        answers = []
        for name, text in members:
            try:
                intervals = failure_intervals(text, start, start + count)
            except ValueError:
                intervals = None
            answers.append(dict(identity=name, markdown=text, intervals=intervals))
        clip = clips / f"{case}.mp4"
        native_rate = Fraction(str(fps)).limit_denominator(10000)
        if not clip.is_file():
            media = plan_file.parent / "images" / window["episode"] / "%06d.webp"
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-framerate", str(native_rate),
                            "-start_number", str(start), "-i", str(media), "-frames:v", str(count),
                            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-an", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(clip)], check=True)
        probe = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                         "-show_entries", "stream=nb_frames,avg_frame_rate",
                                         "-of", "json", str(clip)])
        stream = json.loads(probe)["streams"][0]
        if int(stream["nb_frames"]) != count or Fraction(stream["avg_frame_rate"]) != native_rate:
            raise ValueError(f"Clip timing differs from the model input: {case}")
        items.append(dict(id=case, task=window["task"], start=start, count=count, fps=fps,
                          cameras=[panel["camera"] for panel in window["images"][0]["panels"]],
                          video=b64encode(clip.read_bytes()).decode("ascii"), answers=answers))

    embedded = json.dumps(items, ensure_ascii=False).replace("<", "\\u003c")
    template = Path(__file__).with_name("pilot_review.html").read_text(encoding="utf-8")
    (output / "index.html").write_text(template.replace("__PILOT_DATA__", embedded), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_preview(args.plan, args.predictions, args.output)
