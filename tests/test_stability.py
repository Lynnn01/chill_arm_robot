"""Regression tests for motion/memory stability fixes in _raw.py, yolo_detector.py and executor.py."""
import unittest
from unittest import mock

import armconfig
from agent import executor
from agent.tools.shares import _raw
from hardware import init
from tests.test_raw_golden import run_scenario
from vision import yolo_detector


def _coords_sent(out):
    """[x, y, z] of every send_coords call recorded by run_scenario."""
    import re
    return [[float(v) for v in m.groups()] for m in
            (re.match(r"call\.mc\.send_coords\(\[([-\d.]+), ([-\d.]+), ([-\d.]+)", c) for c in out["calls"]) if m]


class GrabApproachTest(unittest.TestCase):
    def test_tall_stack_top_is_approached_from_above(self):
        known = {"red_cube": [200.0, 0.0, 200.0]}  # 4th layer: top face at Z_SAFE_TRAVEL
        out = run_scenario(lambda: _raw.raw_grab_object("red_cube"), known=known)
        approach = _coords_sent(out)[0]
        self.assertGreaterEqual(approach[2], 200.0 + armconfig.Z_CLEARANCE)

    def test_missed_grab_reports_error_and_forgets_coord(self):
        known = {"red_cube": [200.0, 0.0, 110.0]}
        with mock.patch.object(armconfig, "GRIP_EMPTY_MAX", 5.0):
            out = run_scenario(lambda: _raw.raw_grab_object("red_cube"), known=known,
                               patches={"hardware.init.close_gripper": mock.Mock(return_value=1)})
        self.assertEqual(out["result"]["status"], "ERROR")
        self.assertNotIn("red_cube", out["known"])


class PlacementMemoryTest(unittest.TestCase):
    def test_repeated_stacking_does_not_drift(self):
        known = {"green_cube": [170.0, 90.0, 110.0], "red_cube": "in gripper"}
        out = run_scenario(lambda: _raw.raw_move_to(target_name="green_cube"), known=known, holding="red_cube")
        self.assertEqual(out["known"]["red_cube"][:2], [170.0, 90.0])
        self.assertEqual(out["known"]["green_cube"], [170.0, 90.0, 110.0])

    def test_release_clears_stale_gripper_aliases(self):
        known = {"red_cube": "in gripper", "red": "in gripper"}
        out = run_scenario(lambda: _raw.raw_move_to(target_coord=[180.0, 50.0]), known=known, holding="red_cube")
        self.assertNotIn("red", out["known"])

    def test_give_to_person_forgets_held_object(self):
        known = {"red_cube": "in gripper"}

        def opened():
            init.current_held_object = None  # real open_gripper() clears this

        out = run_scenario(_raw.raw_give_to_person, known=known, holding="red_cube",
                           patches={"hardware.init.open_gripper": opened})
        self.assertNotIn("red_cube", out["known"])


class YoloMemoryTest(unittest.TestCase):
    def test_buried_cube_survives_full_scan(self):
        known = {"red_cube": [200.0, 0.0, 110.0], "blue_cube": [200.0, 0.0, 140.0]}
        with mock.patch.object(init, "known_objects", known), \
                mock.patch.object(init, "current_held_object", None, create=True), \
                mock.patch.object(init, "is_holding_object", False, create=True):
            yolo_detector._calibrate_memory({"blue_cube": [201.0, 1.0]})
            self.assertIn("red_cube", known)

    def test_targeted_scan_on_top_of_known_cube_gets_layer_height(self):
        known = {"green_cube": [200.0, 0.0, 110.0]}
        with mock.patch.object(init, "known_objects", known):
            z = yolo_detector._estimate_z("red_cube", [202.0, 1.0])
        self.assertEqual(z, 110.0 + armconfig.STACK_HEIGHT_PER_LAYER)


class ExecutorArgsTest(unittest.TestCase):
    def test_unknown_args_are_dropped(self):
        def tool(object_name, target_coord=None):
            return None
        args = executor._filter_args("grab_object", tool, {"object_name": "red_cube", "color": "red", "_auto_unstack": False})
        self.assertEqual(args, {"object_name": "red_cube"})

    def _names(self, tasks, holding=False):
        with mock.patch.object(init, "is_holding_object", holding, create=True),                 mock.patch.object(init, "current_held_object", "red_cube" if holding else None, create=True):
            return [t["tool"] for t in executor._sanitize_plan([{"tool": n} for n in tasks])]

    def test_stray_release_after_release_is_dropped(self):
        self.assertEqual(self._names(["grab_object", "move_to", "smart_place"]), ["grab_object", "move_to"])

    def test_release_without_grab_is_dropped_unless_already_holding(self):
        self.assertEqual(self._names(["move_to"]), [])
        self.assertEqual(self._names(["move_to"], holding=True), ["move_to"])

    def test_three_cube_tower_plan_untouched(self):
        plan = ["grab_object", "move_to"] * 3
        self.assertEqual(self._names(plan), plan)

    def test_show_object_keeps_holding(self):
        self.assertEqual(self._names(["grab_object", "show_object", "move_to"]),
                         ["grab_object", "show_object", "move_to"])

    def test_aliases_resolve(self):
        m = executor._get_raw_tool_map()
        for alias in ("play_rps", "dance", "execute_code", "unstack", "grab", "place"):
            self.assertTrue(callable(m[alias]), alias)


class RetryAndVerifyTest(unittest.TestCase):
    def test_missed_grab_rescans_and_retries_once(self):
        known = {"red_cube": [200.0, 0.0, 110.0]}
        grips = iter([1, 30])  # first close on air, second on the cube
        scan = mock.Mock(return_value=[205.0, 3.0])
        with mock.patch.object(armconfig, "GRIP_EMPTY_MAX", 5.0):
            out = run_scenario(lambda: _raw.raw_grab_object("red_cube"), known=known,
                               patches={"hardware.init.close_gripper": lambda: next(grips),
                                        "vision.yolo_detector.scan_with_yolo": scan})
        self.assertEqual(out["result"]["status"], "DONE TASK")
        scan.assert_called_once()  # forgot the stale coordinate -> fresh scan
        self.assertEqual(out["result"]["data"][0], 205.0)

    def test_retry_gives_up_after_configured_attempts(self):
        known = {"red_cube": [200.0, 0.0, 110.0]}
        scan = mock.Mock(return_value=[205.0, 3.0])
        with mock.patch.object(armconfig, "GRIP_EMPTY_MAX", 5.0), mock.patch.object(armconfig, "GRAB_RETRIES", 1):
            out = run_scenario(lambda: _raw.raw_grab_object("red_cube"), known=known,
                               patches={"hardware.init.close_gripper": lambda: 1,
                                        "vision.yolo_detector.scan_with_yolo": scan})
        self.assertEqual(out["result"]["status"], "ERROR")
        self.assertTrue(out["result"]["message"].startswith("Missed grab"))

    def _verify(self, readings):
        rec = mock.MagicMock()
        rec.safe_get_coords.side_effect = readings
        with mock.patch.object(_raw, "mc", rec), mock.patch.object(_raw.time, "sleep", lambda s: None):
            res = _raw._verify_xy([200.0, 0.0, 110.0], armconfig.WRIST_DOWN, "grab", "red_cube")
        return res, rec

    def test_short_x_is_corrected_once(self):
        res, rec = self._verify([[190.0, 0.0, 110.0, 0, 0, 0], [199.0, 0.0, 110.0, 0, 0, 0]])
        self.assertTrue(res["corrected"])
        rec.send_coords.assert_called_once()
        self.assertAlmostEqual(res["err"][0], -1.0)

    def test_in_tolerance_is_left_alone(self):
        res, rec = self._verify([[198.0, 1.0, 110.0, 0, 0, 0]])
        self.assertFalse(res["corrected"])
        rec.send_coords.assert_not_called()

    def test_absurd_reading_is_not_chased(self):
        res, rec = self._verify([[0.0, 0.0, 200.0, 0, 0, 0]])  # stale / mock position
        self.assertFalse(res["corrected"])
        rec.send_coords.assert_not_called()

    def test_no_reading_is_safe(self):
        res, _ = self._verify([None, None, None])
        self.assertIsNone(res["actual"])


if __name__ == "__main__":
    unittest.main()
