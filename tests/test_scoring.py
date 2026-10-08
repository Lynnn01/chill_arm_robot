import contextlib
import io
import unittest

from agent import scoring


class ScoringTest(unittest.TestCase):
    def setUp(self):
        scoring._CURRENT_SCORE = 0
        scoring._SCORE_LISTENERS.clear()

    def test_empty_tasks(self):
        self.assertEqual(scoring.evaluate_task_points([]), (0, "No tasks"))

    def test_single_action_is_one_point(self):
        self.assertEqual(scoring.evaluate_task_points([{"tool": "dance_celebrate"}], "เต้น")[0], 1)

    def test_mission_signals(self):
        self.assertEqual(scoring.evaluate_task_points([{"tool": "sort_by_color()"}])[0], 10)
        self.assertEqual(scoring.evaluate_task_points([{"tool": "unstack_and_grab"}])[0], 10)
        self.assertEqual(scoring.evaluate_task_points([{"tool": "x"}], "สร้างหอคอย")[0], 10)
        stack = [{"tool": "move_to", "args": {"target_name": "red cube"}}]
        self.assertEqual(scoring.evaluate_task_points(stack)[0], 10)
        self.assertEqual(scoring.evaluate_task_points([{"tool": "move_to", "args": {"smart_place": True}}])[0], 10)

    def test_add_score_notifies_and_ignores_non_positive(self):
        seen = []
        scoring.register_score_listener(seen.append)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(scoring.add_score(10, "m"), 10)
            self.assertEqual(scoring.add_score(0, "none"), 10)
            self.assertEqual(scoring.add_score(1, "t"), 11)
        self.assertEqual(seen, [10, 11])
        self.assertEqual(scoring.get_score(), 11)

    def test_failing_listener_does_not_break_others(self):
        seen = []
        scoring.register_score_listener(lambda s: 1 / 0)
        scoring.register_score_listener(seen.append)
        with contextlib.redirect_stdout(io.StringIO()):
            scoring.add_score(1, "t")
        self.assertEqual(seen, [1])


if __name__ == "__main__":
    unittest.main()
