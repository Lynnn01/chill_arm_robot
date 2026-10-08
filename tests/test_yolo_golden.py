"""Characterization tests for vision/yolo_detector.py (camera, YOLO model and arm are faked).

Regenerate the snapshot only for intentional behavior changes:
    UPDATE_GOLDEN=1 python -m unittest tests.test_yolo_golden
"""
import contextlib
import io
import json
import os
import re
import unittest
from unittest import mock

import numpy as np

import armconfig
from hardware import init
from vision import yolo_detector as Y

GOLDEN = os.path.join(os.path.dirname(__file__), "golden_yolo.json")


class _Arr:
    def __init__(self, a):
        self.a = np.array(a, dtype=float)

    def cpu(self):
        return self

    def numpy(self):
        return self.a


class _Box:
    def __init__(self, cls, xyxy):
        self.cls = [cls]
        self.xyxy = [_Arr(xyxy)]


class _Result:
    def __init__(self, boxes):
        self.boxes = boxes


class _Model:
    names = {0: "red_cube", 1: "blue_cube", 2: "green_cube", 3: "face"}

    def __init__(self, per_call):
        self.per_call = per_call  # list of box lists, cycled
        self.i = 0

    def __call__(self, frame, verbose=False, conf=0.3):
        boxes = self.per_call[self.i % len(self.per_call)]
        self.i += 1
        return [_Result(boxes)]


def _frame(bgr):
    f = np.zeros((480, 640, 3), dtype=np.uint8)
    f[:, :] = bgr
    return f


RED = (0, 0, 255)
BLUE = (255, 0, 0)
GREEN = (0, 200, 0)


def _scene():
    """Gray table with a red, blue and green patch exactly under the fake boxes."""
    f = _frame((128, 128, 128))
    f[100:200, 100:200] = RED
    f[100:200, 300:400] = BLUE
    f[300:400, 500:600] = GREEN
    return f


def run(name, object_name, boxes, frame=None, known=None, holding=None, model_ok=True):
    known = json.loads(json.dumps(known or {}))
    cam = mock.MagicMock()
    cam.get_frame.return_value = frame if frame is not None else _scene()
    rec = mock.MagicMock()
    model = _Model(boxes)
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch.object(Y, "mc", rec.mc))
        st.enter_context(mock.patch.object(Y, "cam_manager", cam))
        st.enter_context(mock.patch.object(Y.time, "sleep", lambda s: None))
        st.enter_context(mock.patch.object(Y, "get_yolo_model", lambda t="cube": (model if model_ok else None)))
        st.enter_context(mock.patch.object(Y.eyeonhand, "pixel_to_arm",
                                           lambda p: np.array([p[0] / 4.0 + 100.0, p[1] / 4.0 - 30.0])))
        st.enter_context(mock.patch.object(armconfig, "SCAN_ANGLES", [0, 15]))
        st.enter_context(mock.patch.object(armconfig, "SCAN_WAIT_PER_ANGLE", 0, create=True))
        st.enter_context(mock.patch.object(init, "known_objects", known))
        st.enter_context(mock.patch.object(init, "current_held_object", holding, create=True))
        st.enter_context(mock.patch.object(init, "is_holding_object", bool(holding), create=True))
        with contextlib.redirect_stdout(io.StringIO()):
            result = Y.scan_with_yolo(object_name)
    out = {
        "result": result,
        "calls": [re.sub(r" id='\d+'", "", repr(c)) for c in rec.mock_calls],
        "known": known,
        "model_calls": model.i,
    }
    return json.loads(json.dumps(out, default=repr, ensure_ascii=False))


def scenarios():
    red = _Box(0, [100, 100, 200, 200])
    blue = _Box(1, [300, 100, 400, 200])
    green = _Box(2, [500, 300, 600, 400])
    face = _Box(3, [200, 200, 260, 280])
    S = {}
    S["full_scan_new_cubes"] = lambda: run("a", "cube", [[red, blue]])
    S["full_scan_calibrate_moved_stale_held"] = lambda: run(
        "b", "all", [[red], [green]],
        known={"red_cube": [1000.0, 1000.0, 110.0], "blue_cube": [5.0, 5.0, 110.0],
               "green_cube": [9.0, 9.0, 110.0], "held_cube": "in gripper"}, holding="blue_cube")
    S["full_scan_unchanged_position_kept"] = lambda: run(
        "c", "", [[red]], known={"red_cube": [198.0, 59.8, 110.0]})
    S["full_scan_thai_generic"] = lambda: run("d", "กล่อง", [[green]])
    S["targeted_found_first_angle"] = lambda: run("e", "red cube", [[red, blue]])
    S["targeted_color_mismatch_skipped"] = lambda: run("f", "green cube", [[red, blue]])
    S["targeted_not_found"] = lambda: run("g", "yellow cube", [[blue]])
    S["targeted_thai_name"] = lambda: run("h", "กล่องสีน้ำเงิน", [[red, blue]])
    S["face_target"] = lambda: run("i", "face", [[face]])
    S["no_model"] = lambda: run("j", "cube", [[]], model_ok=False)
    S["frame_none_never_detects"] = run_none_frame
    S["hsv_overrides_model_name"] = lambda: run("l", "cube", [[_Box(1, [100, 100, 200, 200])]], frame=_frame(RED))
    S["hsv_tiny_crop_keeps_name"] = lambda: run("m", "cube", [[_Box(1, [10, 10, 12, 12])]], frame=_frame(RED))
    S["empty_results"] = lambda: run("n", "cube", [[]])
    return S


def run_none_frame():
    cam_frame = None
    known = {}
    cam = mock.MagicMock()
    cam.get_frame.return_value = cam_frame
    rec = mock.MagicMock()
    model = _Model([[_Box(0, [100, 100, 200, 200])]])
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch.object(Y, "mc", rec.mc))
        st.enter_context(mock.patch.object(Y, "cam_manager", cam))
        st.enter_context(mock.patch.object(Y.time, "sleep", lambda s: None))
        st.enter_context(mock.patch.object(Y, "get_yolo_model", lambda t="cube": model))
        st.enter_context(mock.patch.object(armconfig, "SCAN_ANGLES", [0]))
        st.enter_context(mock.patch.object(init, "known_objects", known))
        with contextlib.redirect_stdout(io.StringIO()):
            result = Y.scan_with_yolo("red cube")
    return {"result": result, "model_calls": model.i, "calls": [re.sub(r" id='\d+'", "", repr(c)) for c in rec.mock_calls]}


class GoldenYoloTest(unittest.TestCase):
    maxDiff = None

    def test_scenarios_match_golden(self):
        got = {n: fn() for n, fn in scenarios().items()}
        if os.environ.get("UPDATE_GOLDEN"):
            with open(GOLDEN, "w", encoding="utf-8") as f:
                json.dump(got, f, ensure_ascii=False, indent=1, sort_keys=True)
            self.skipTest("golden updated")
        with open(GOLDEN, encoding="utf-8") as f:
            want = json.load(f)
        self.assertEqual(sorted(got), sorted(want))
        for n in want:
            with self.subTest(n):
                self.assertEqual(got[n], want[n])


class ClassifyColorTest(unittest.TestCase):
    def crop(self, bgr, h=40, w=40):
        return _frame(bgr)[:h, :w].copy()

    def test_solid_colors(self):
        self.assertEqual(Y.classify_cube_color_hsv(self.crop(RED)), "red_cube")
        self.assertEqual(Y.classify_cube_color_hsv(self.crop(BLUE)), "blue_cube")
        self.assertEqual(Y.classify_cube_color_hsv(self.crop(GREEN)), "green_cube")
        self.assertEqual(Y.classify_cube_color_hsv(self.crop((0, 230, 230))), "yellow_cube")

    def test_none_empty_tiny_gray(self):
        self.assertIsNone(Y.classify_cube_color_hsv(None))
        self.assertIsNone(Y.classify_cube_color_hsv(np.zeros((0, 0, 3), dtype=np.uint8)))
        self.assertIsNone(Y.classify_cube_color_hsv(np.zeros((4, 4, 3), dtype=np.uint8)))
        self.assertIsNone(Y.classify_cube_color_hsv(self.crop((128, 128, 128))))


if __name__ == "__main__":
    unittest.main()
