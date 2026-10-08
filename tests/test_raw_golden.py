"""Golden-snapshot (characterization) tests for agent/tools/shares/_raw.py.

Hardware is mocked: every call on `mc`, the gripper and the vision helpers is recorded.
Refactors must keep the recorded call sequence, return values and memory state identical.
Regenerate the snapshot (only for intentional behavior changes):
    UPDATE_GOLDEN=1 python -m unittest tests.test_raw_golden
"""
import contextlib
import io
import json
import math
import os
import random
import re
import unittest
from unittest import mock

import armconfig
from agent.tools.shares import _raw
from hardware import init

GOLDEN = os.path.join(os.path.dirname(__file__), "golden_raw.json")


def _jsonable(x):
    return json.loads(json.dumps(x, default=repr, ensure_ascii=False))


def run_scenario(fn, known=None, holding=None, held_coord=None, wait_z=True, seed=1, patches=None):
    """Run fn() under a mocked world; return everything observable."""
    random.seed(seed)
    rec = mock.MagicMock()
    rec.mc.wait_for_z.return_value = wait_z
    rec.mc.get_angles.return_value = None
    known = json.loads(json.dumps(known or {}))
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch.object(_raw, "mc", rec.mc))
        st.enter_context(mock.patch.object(_raw.time, "sleep", lambda s: None))
        st.enter_context(mock.patch.object(init, "known_objects", known))
        st.enter_context(mock.patch.object(init, "current_held_object", holding, create=True))
        st.enter_context(mock.patch.object(init, "is_holding_object", bool(holding), create=True))
        st.enter_context(mock.patch.object(init, "current_held_coord", held_coord, create=True))
        st.enter_context(mock.patch.object(init, "open_gripper", rec.open_gripper))
        st.enter_context(mock.patch.object(init, "close_gripper", rec.close_gripper))
        st.enter_context(mock.patch.object(init, "BotInit", rec.BotInit))
        st.enter_context(mock.patch.object(init, "GetImage", rec.GetImage))
        for target, value in (patches or {}).items():
            st.enter_context(mock.patch(target, value))
        with contextlib.redirect_stdout(io.StringIO()):
            result = fn()
        out = {
            "result": result,
            "calls": [re.sub(r" id='\d+'", "", repr(c)) for c in rec.mock_calls],
            "known": known,
            "held": init.current_held_object,
            "is_holding": init.is_holding_object,
        }
    return _jsonable(out)


def _scan(ret):
    return mock.MagicMock(return_value=ret)


CUBES = {
    "red_cube": [200.0, 0.0, 110.0],
    "blue_cube": [200.0, 5.0, 150.0],
    "green_cube": [170.0, 90.0, 110.0],
    "blank_area": [160.0, -150.0, 0.0],
}

SCAN = "vision.yolo_detector.scan_with_yolo"
GRAB = "agent.tools.shares._raw.raw_grab_object"
MOVE = "agent.tools.shares._raw.raw_move_to"
SAFE = "agent.tools.shares._raw.raw_find_safe_spot"
UNSTACK = "agent.tools.shares._raw.raw_unstack_and_grab"


def _vision_patches(qwen_coords):
    return {
        SCAN: _scan(None),
        "PIL.Image.open": mock.MagicMock(return_value=mock.MagicMock(size=(640, 480))),
        "vision.api.QwenVLRequest": mock.MagicMock(return_value={"coordinates": qwen_coords}),
        "vision.eyeonhand.pixel_to_arm": mock.MagicMock(return_value=[220.0, 10.0]),
    }


def _unstack(name, known, holding=None, grab=None, move=None, extra=None):
    patches = {
        GRAB: mock.MagicMock(return_value=grab or {"status": "DONE TASK"}),
        MOVE: mock.MagicMock(return_value=move or {"status": "DONE TASK"}),
        SAFE: mock.MagicMock(return_value=[190.0, -60.0]),
    }
    patches.update(extra or {})

    def fn():
        r = _raw.raw_unstack_and_grab(name)
        return {"r": r, "grab": repr(patches[GRAB].mock_calls), "move": repr(patches[MOVE].mock_calls)}
    return run_scenario(fn, known=known, holding=holding, patches=patches)


def scenarios():
    S = {}
    S["safe_spot_empty"] = lambda: run_scenario(lambda: _raw.raw_find_safe_spot(), known={"red_cube": [1, 1, 1]})
    S["safe_spot_crowded"] = lambda: run_scenario(
        lambda: _raw.raw_find_safe_spot(margin_mm=500.0), known=CUBES, held_coord=[150, 20])
    S["safe_spot_scan_first"] = lambda: run_scenario(
        lambda: _raw.raw_find_safe_spot(scan_first=True), known={}, patches={SCAN: _scan({})})
    S["safe_spot_scan_error"] = lambda: run_scenario(
        lambda: _raw.raw_find_safe_spot(), known={}, patches={SCAN: mock.MagicMock(side_effect=RuntimeError("cam"))})

    S["move_to_not_holding"] = lambda: run_scenario(lambda: _raw.raw_move_to(target_coord=[200, 50]))
    S["move_to_ground"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_coord=[200, 50]), known={}, holding="red_cube")
    S["move_to_stack_by_name"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_name="blue cube"), known=CUBES, holding="red_cube")
    S["move_to_stack_by_coord"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_coord=[200, 10]), known=CUBES, holding="yellow_cube")
    S["move_to_held_coord_fallback"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_coord=[170, 10], target_name="green cube"),
        known=CUBES, holding="red_cube", held_coord=[170, 10])
    S["move_to_invalid_zero"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_coord=[0, 0]), known={}, holding="red_cube")
    S["move_to_area_unknown"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_coord=[1, 1], target_name="red area"), known={}, holding="red_cube")
    S["move_to_unknown_name_scan"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_name="purple cube"), known={}, holding="red_cube",
        patches={SCAN: _scan([190.0, -40.0])})
    S["move_to_explicit_height"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_coord=[250, 300], target_height=500), known={}, holding="red_cube")
    S["move_to_smart_place_stack"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_name="smart"), known=CUBES, holding="yellow_cube")
    S["move_to_smart_place_random"] = lambda: run_scenario(
        lambda: _raw.raw_move_to(target_name="random spot"), known=CUBES, holding="yellow_cube")
    S["smart_place_not_holding"] = lambda: run_scenario(lambda: _raw.raw_smart_place())

    S["grab_target_coord"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("red cube", target_coord=[200, 0, 110]), known=CUBES)
    S["grab_memory_first"] = lambda: run_scenario(lambda: _raw.raw_grab_object("green cube"), known=CUBES)
    S["grab_buried_redirect"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("red cube"), known=CUBES,
        patches={UNSTACK: mock.MagicMock(return_value={"status": "UNSTACK"})})
    S["grab_cube_not_found"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("yellow cube"), known={}, patches={SCAN: _scan(None)})
    S["grab_yolo_found"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("yellow cube"), known={}, patches={SCAN: _scan([180.0, 60.0])})
    S["grab_radius_clamp"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("red cube", target_coord=[40.0, 20.0]), known={})
    S["grab_over_bounds_clamp"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("red cube", target_coord=[999.0, -999.0]), known={})
    S["grab_z_unreachable"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("red cube", target_coord=[200, 0, 110]), known=CUBES, wait_z=False)
    S["grab_holding_first"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("green cube", target_coord=[170, 90, 110]), known=CUBES,
        holding="red_cube", held_coord=[200, 0])
    S["grab_generic_name_alias"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("cube", target_coord=[200, 0, 110]), known=CUBES)
    S["grab_alias_cleanup_other_color_kept"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("blue cube", target_coord=[200, 3, 150]), known=CUBES)
    S["grab_vision_fallback_found"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("pen"), known={},
        patches=_vision_patches([{"x1": 400, "y1": 400, "x2": 600, "y2": 600}]))
    S["grab_vision_fallback_missing"] = lambda: run_scenario(
        lambda: _raw.raw_grab_object("pen"), known={}, patches=_vision_patches([]))

    S["unstack_blocking"] = lambda: _unstack("red cube", CUBES)
    S["unstack_no_blocking"] = lambda: _unstack("green cube", CUBES)
    S["unstack_generic_buried"] = lambda: _unstack("buried", CUBES)
    S["unstack_grab_blocker_fails"] = lambda: _unstack("red cube", CUBES, grab={"status": "ERROR", "message": "x"})
    S["unstack_place_blocker_fails"] = lambda: _unstack("red cube", CUBES, move={"status": "ERROR", "message": "y"})
    S["unstack_holding_first"] = lambda: _unstack("green cube", CUBES, holding="yellow_cube")
    S["unstack_holding_place_fails"] = lambda: _unstack(
        "green cube", CUBES, holding="yellow_cube", move={"status": "ERROR", "message": "z"})
    S["unstack_not_found_delegates"] = lambda: _unstack("pink cube", {}, extra={SCAN: _scan(None)})
    S["unstack_yolo_found"] = lambda: _unstack(
        "pink cube", {"red_cube": [180, 20, 150]}, extra={SCAN: _scan([180.0, 20.0, 110.0])})
    S["unstack_generic_scan_fallback"] = lambda: _unstack(
        "buried", {"red_cube": [180, 20, 110]}, extra={SCAN: mock.MagicMock(return_value=None)})
    return S


class GoldenRawTest(unittest.TestCase):
    maxDiff = None

    def test_scenarios_match_golden(self):
        got = {name: fn() for name, fn in scenarios().items()}
        if os.environ.get("UPDATE_GOLDEN"):
            with open(GOLDEN, "w", encoding="utf-8") as f:
                json.dump(got, f, ensure_ascii=False, indent=1, sort_keys=True)
            self.skipTest("golden updated")
        with open(GOLDEN, encoding="utf-8") as f:
            want = json.load(f)
        self.assertEqual(sorted(got), sorted(want))
        for name in want:
            with self.subTest(name):
                self.assertEqual(got[name], want[name])


class PureHelpersTest(unittest.TestCase):
    def test_get_english_name(self):
        self.assertEqual(_raw.get_english_name("กล่องสีแดง"), "red_cube")
        self.assertEqual(_raw.get_english_name("Blue Cube"), "blue_cube")
        self.assertEqual(_raw.get_english_name(""), "")
        self.assertEqual(_raw.get_english_name("พื้นที่สีเขียว"), "green_area")

    def test_find_in_memory_color_strict(self):
        known = {"red_cube": [1, 2, 3], "blue_cube": [4, 5, 6], "x_area": [0, 0, 0], "g": "in gripper"}
        with mock.patch.object(init, "known_objects", known):
            self.assertEqual(_raw._find_in_memory("red_cube"), ("red_cube", [1, 2, 3]))
            self.assertEqual(_raw._find_in_memory("blue block"), ("blue_cube", [4, 5, 6]))
            self.assertEqual(_raw._find_in_memory("green cube"), (None, None))
            self.assertEqual(_raw._find_in_memory(""), (None, None))

    def test_safe_spot_respects_margin(self):
        random.seed(3)
        known = {"red_cube": [175.0, 0.0, 110.0]}
        with mock.patch.object(init, "known_objects", known), contextlib.redirect_stdout(io.StringIO()):
            spot = _raw.raw_find_safe_spot(margin_mm=55.0)
        self.assertGreaterEqual(math.hypot(spot[0] - 175.0, spot[1]), 55.0)
        self.assertGreaterEqual(math.hypot(*spot), armconfig.GRAB_MIN_RADIUS)


if __name__ == "__main__":
    unittest.main()
