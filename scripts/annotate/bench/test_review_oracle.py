"""CPU unit tests for review_oracle.py: timeline drawing (colours per label, hatched multi-label chunks, event markers,
decisive frame, playhead), the audit CSV writer and the gallery/index scan, on stub references.

Run: run_one_test.sh test_review_oracle   (or run_tests.sh, unittest discover under scripts/annotate/bench)
"""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_oracle as ro  # noqa: E402
from review_oracle import (CSV_COLUMNS, LABEL_COLORS, draw_timeline, gallery_html, held_by_frame, hex_to_rgb, in_hand,  # noqa: E402
                           lighter, review_row, timeline_segments, write_audit_sheet)


def stub_reference(**over):
    """drop_transport episode, 6 chunks of 10 frames (last 8): held bowl_1 20..39, drop in chunk 3, regrasp in chunk 5."""
    ref = {
        "reference_version": "r2", "dataset": "ds__t0", "episode_index": 7, "suite": "libero_object", "task_id": 0,
        "task": "pick up the bowl and place it on the plate", "success": False,
        "n_frames": 58, "fps": 20, "n_chunks": 6, "chunks": [[0, 10], [10, 20], [20, 30], [30, 40], [40, 50], [50, 58]],
        "object_slots": ["bowl_1", "plate_1", "mug_1"], "target_slot": "bowl_1", "goal_slot": "plate_1",
        "held_runs": [
            {"start": 0, "end": 17, "state": "empty", "object": None},
            {"start": 18, "end": 21, "state": "ambiguous", "object": "bowl_1"},
            {"start": 22, "end": 37, "state": "held", "object": "bowl_1"},
            {"start": 38, "end": 41, "state": "ambiguous", "object": "bowl_1"},
            {"start": 42, "end": 57, "state": "empty", "object": None},
        ],
        "events": [
            {"index": 20, "type": "grasp", "object": "bowl_1", "last_before": 19, "first_after": 20, "chunk": 1},
            {"index": 40, "type": "drop", "object": "bowl_1", "last_before": 39, "first_after": 40, "chunk": 3},
            {"index": 52, "type": "grasp", "object": "bowl_1", "last_before": 51, "first_after": 52, "chunk": 5},
            {"index": 56, "type": "release", "object": "bowl_1", "last_before": 55, "first_after": 56, "chunk": 5},
        ],
        "close_on_nothing": [], "wrong_object_contacts": [], "collisions": [], "stage_frames": {"reached": 18, "grasped": 20},
        "failure_mode": "drop_transport", "cause": "grasp", "decisive_chunk": 3, "mode_reason": "last_hold_ends_in_drop",
        "chunk_labels": [
            {"chunk": 0, "allowed": ["progress"], "primary": "progress", "rule": "advance_approach", "scorable": True},
            {"chunk": 1, "allowed": ["progress", "neutral"], "primary": "progress", "rule": "pre_other", "scorable": True},
            {"chunk": 2, "allowed": ["neutral"], "primary": "neutral", "rule": "idle", "scorable": True},
            {"chunk": 3, "allowed": ["failure_inducing"], "primary": "failure_inducing", "rule": "decisive", "scorable": True},
            {"chunk": 4, "allowed": ["aftermath", "neutral"], "primary": "aftermath", "rule": "post_other", "scorable": True},
            {"chunk": 5, "allowed": ["recovery"], "primary": "recovery", "rule": "regrasp", "scorable": True},
        ],
        "anomalies": [],
    }
    ref.update(over)
    return ref


def region_colors(im, xa, xb, ya, yb):
    px = im.load()
    return {px[x, y] for x in range(int(xa) + 1, int(xb) - 1) for y in range(int(ya) + 1, int(yb) - 1)}


class TimelineTests(unittest.TestCase):
    X0, X1, Y, H = 10, 610, 40, 20  # 600 px for 58 frames

    def render(self, ref, playhead=None):
        im = Image.new("RGB", (620, 90), ro.BG)
        segs = draw_timeline(im, ref, self.X0, self.X1, self.Y, self.H, playhead=playhead, fonts=None)
        return im, segs

    def test_segments_geometry_and_flags(self):
        segs = timeline_segments(stub_reference(), self.X0, self.X1)
        self.assertEqual([s["chunk"] for s in segs], list(range(6)))
        self.assertAlmostEqual(segs[0]["xa"], self.X0)
        self.assertAlmostEqual(segs[-1]["xb"], self.X1)
        self.assertAlmostEqual(segs[1]["xa"], self.X0 + 10 / 58 * 600)
        self.assertEqual([s["multi"] for s in segs], [False, True, False, False, True, False])
        self.assertEqual([s["color"] for s in segs], [LABEL_COLORS[s["primary"]] for s in segs])

    def test_single_label_chunks_are_uniform_in_their_label_colour(self):
        ref = stub_reference()
        im, segs = self.render(ref)
        for c, label in [(0, "progress"), (2, "neutral"), (3, "failure_inducing"), (5, "recovery")]:
            s = segs[c]
            # inset by 4 px: the decisive chunk carries a 3 px white outline, other chunks a 1 px separator
            colors = region_colors(im, s["xa"] + 4, s["xb"] - 4, self.Y + 4, self.Y + self.H - 4)
            self.assertEqual(colors, {hex_to_rgb(LABEL_COLORS[label])}, f"chunk {c} ({label}) not uniform: {colors}")

    def test_multi_label_chunks_are_hatched_and_lighter(self):
        ref = stub_reference()
        im, segs = self.render(ref)
        for c in (1, 4):
            s = segs[c]
            colors = region_colors(im, s["xa"] + 2, s["xb"] - 2, self.Y + 2, self.Y + self.H - 2)
            full, light = hex_to_rgb(s["color"]), lighter(s["color"])
            self.assertIn(light, colors, f"chunk {c}: lighter tone missing")
            self.assertIn(full, colors, f"chunk {c}: hatch lines in the label colour missing")
            self.assertGreaterEqual(len(colors), 2)
        # the lighter tone is between the label colour and the background
        p, bg = hex_to_rgb(LABEL_COLORS["aftermath"]), hex_to_rgb(ro.BG)
        for k in range(3):
            self.assertTrue(min(p[k], bg[k]) <= lighter(LABEL_COLORS["aftermath"])[k] <= max(p[k], bg[k]))

    def test_event_markers_decisive_frame_and_playhead(self):
        ref = stub_reference()
        im, segs = self.render(ref, playhead=25)
        px = im.load()
        # drop at frame 40: a red down-triangle above the bar whose tip touches y - 3 (probe near the base)
        x_drop = int(round(ro.frame_x(ref, 40, self.X0, self.X1)))
        self.assertEqual(px[x_drop, self.Y - 12], hex_to_rgb(ro.EVENT_STYLE["drop"][1]))
        # grasp at frame 20: white up-triangle, base at y - 3 (probe inside the triangle)
        x_grasp = int(round(ro.frame_x(ref, 20, self.X0, self.X1)))
        self.assertEqual(px[x_grasp, self.Y - 6], hex_to_rgb(ro.EVENT_STYLE["grasp"][1]))
        self.assertEqual(px[x_grasp, self.Y - 9], hex_to_rgb(ro.EVENT_STYLE["grasp"][1]))
        # release at frame 56: blue down-triangle
        x_rel = int(round(ro.frame_x(ref, 56, self.X0, self.X1)))
        self.assertEqual(px[x_rel, self.Y - 12], hex_to_rgb(ro.EVENT_STYLE["release"][1]))
        # decisive chunk 3: white outline around the chunk and a white bar below it
        s = segs[3]
        self.assertEqual(px[int(s["xa"]) + 5, self.Y - 1], (255, 255, 255))
        self.assertEqual(px[int((s["xa"] + s["xb"]) / 2), self.Y + self.H + 6], (255, 255, 255))
        # no white outline around a non-decisive chunk
        self.assertNotEqual(px[int(segs[0]["xa"]) + 5, self.Y - 1], (255, 255, 255))
        # playhead: white 3 px line at frame 25.5 crossing the bar
        x_ph = int(round(ro.frame_x(ref, 25.5, self.X0, self.X1)))
        self.assertEqual(px[x_ph, self.Y + self.H // 2], (255, 255, 255))

    def test_no_decisive_chunk_draws_no_frame(self):
        ref = stub_reference(decisive_chunk=None)
        im, segs = self.render(ref)
        px = im.load()
        self.assertNotEqual(px[int(segs[3]["xa"]) + 5, self.Y - 1], (255, 255, 255))
        self.assertNotEqual(px[int((segs[3]["xa"] + segs[3]["xb"]) / 2), self.Y + self.H + 6], (255, 255, 255))


class ReferenceHelperTests(unittest.TestCase):
    def test_held_by_frame_and_in_hand(self):
        ref = stub_reference()
        states, objects = held_by_frame(ref)
        self.assertEqual(len(states), 58)
        self.assertEqual((states[0], objects[0]), ("empty", None))
        self.assertEqual((states[30], objects[30]), ("held", "bowl_1"))
        self.assertEqual(states[40], "ambiguous")
        self.assertEqual(in_hand(ref, 30, states, objects), "bowl_1 (target)")
        self.assertTrue(in_hand(ref, 40, states, objects).startswith("bowl_1? (target, ambiguous)"))
        self.assertEqual(in_hand(ref, 5, states, objects), "none")
        self.assertEqual(in_hand(ref, 45, states, objects), "none  (last held: bowl_1, target)")
        ref["target_slot"] = "mug_1"
        self.assertEqual(in_hand(ref, 30, states, objects), "bowl_1 (WRONG object)")

    def test_chunk_of(self):
        ref = stub_reference()
        self.assertEqual([ro.chunk_of(ref, f) for f in (0, 9, 10, 39, 40, 57)], [0, 0, 1, 3, 4, 5])


class AuditSheetTests(unittest.TestCase):
    def test_csv_columns_prefill_and_empty_human_columns(self):
        rows = [review_row(stub_reference(), "heldout", seconds=3.2, decode="batched", fps=20, poster_frame=30),
                review_row(stub_reference(episode_index=8, decisive_chunk=None, failure_mode="hold_no_release", cause="manipulation"), "dev"),
                review_row(stub_reference(episode_index=9, success=True, failure_mode="success", cause="unclear", decisive_chunk=None), "success_clean")]
        with tempfile.TemporaryDirectory() as td:
            path = write_audit_sheet(rows, Path(td) / "sub" / "audit_sheet.csv")
            raw = path.read_bytes()
            self.assertNotIn(b"\r\n", raw)
            with open(path, newline="", encoding="utf-8") as f:
                rd = csv.DictReader(f)
                self.assertEqual(rd.fieldnames, CSV_COLUMNS)
                got = list(rd)
        self.assertEqual(len(got), 3)
        self.assertEqual(got[0]["dataset"], "ds__t0")
        self.assertEqual(got[0]["episode_index"], "7")
        self.assertEqual(got[0]["failure_mode"], "drop_transport")
        self.assertEqual(got[0]["oracle_decisive_chunk"], "3")
        self.assertEqual(got[0]["oracle_cause"], "grasp")
        self.assertEqual(got[1]["oracle_decisive_chunk"], "")
        self.assertEqual(got[1]["oracle_cause"], "manipulation")
        self.assertEqual(got[2]["failure_mode"], "success")
        for r in got:
            for col in ("human_decisive_chunk", "human_cause", "human_mechanism", "human_recoverable_until", "chunk_labels_ok", "notes"):
                self.assertEqual(r[col], "", f"{col} should be empty")

    def test_review_row_fields(self):
        row = review_row(stub_reference(), "heldout", seconds=1.26, decode="batched", fps=20, poster_frame=30)
        self.assertEqual(row["dir"], "ds__t0/ep0007")
        self.assertEqual(row["n_events"], 4)
        self.assertEqual(row["render_seconds"], 1.3)
        self.assertEqual(row["fps"], 20)


class IndexTests(unittest.TestCase):
    def test_gallery_and_scan(self):
        ref = stub_reference()
        with tempfile.TemporaryDirectory() as td:
            old = ro.OUT_ROOT
            ro.OUT_ROOT = Path(td)
            try:
                d = Path(td) / "ds__t0" / "ep0007"
                d.mkdir(parents=True)
                (d / "video.mp4").write_bytes(b"")
                (d / "reference.json").write_text(json.dumps(ref))
                (d / "review.json").write_text(json.dumps(review_row(ref, "heldout", fps=20)))
                rows, refs = ro.scan_rows()
                self.assertEqual(len(rows), 1)
                page = gallery_html(rows, refs)
                self.assertIn('data-src="ds__t0/ep0007/video.mp4"', page)
                self.assertIn('<option value="drop_transport">drop_transport (1)</option>', page)
                self.assertIn("ds__t0/ep0007/index.html", page)
                self.assertIn("decisive", page)
                self.assertEqual(page.count("<tr class=\"D\">"), 1)  # decisive row of the chunk table
                ro.build_index()
                self.assertTrue((Path(td) / "index.html").exists())
                self.assertTrue((Path(td) / "audit_sheet.csv").exists())
                self.assertIn("3 minutes", (Path(td) / "audit_protocol.md").read_text())
            finally:
                ro.OUT_ROOT = old


if __name__ == "__main__":
    unittest.main()
