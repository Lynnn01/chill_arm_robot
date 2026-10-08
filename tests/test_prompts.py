import unittest
from unittest import mock

from agent import prompts as P


def _reset_state(mode="mission", count=0, steps=0):
    P._auto_mission_state.update(mode=mode, auto_command_count=count, normal_steps_left=steps)


class AnalyzeCubesTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(P._analyze_cubes_and_towers({}), ([], [], []))
        self.assertEqual(P._analyze_cubes_and_towers(None), ([], [], []))

    def test_ignores_non_cubes(self):
        objs = {"area 1": [0, 0, 0], "red cube": "in gripper", "blue cube": [1], "zzz": [0, 0, 0]}
        self.assertEqual(P._analyze_cubes_and_towers(objs), ([], [], []))

    def test_free_and_tower(self):
        objs = {"red cube": [0, 0, 110], "blue cube": [10, 0, 150], "green cube": [200, 0, 0]}
        free, towers, colors = P._analyze_cubes_and_towers(objs)
        self.assertEqual(free, [("green cube", P.COLOR_TO_THAI["green"])])
        self.assertEqual(len(towers), 1)
        self.assertEqual([t[0] for t in towers[0]], ["red cube", "blue cube"])  # z ascending
        self.assertEqual(towers[0][0][2], 110.0)
        self.assertEqual(colors, [P.COLOR_TO_THAI[c] for c in ("red", "blue", "green")])

    def test_zero_z_defaults_to_110(self):
        _, _, _ = P._analyze_cubes_and_towers({"red cube": [0, 0, 0]})
        free, towers, _ = P._analyze_cubes_and_towers({"red cube": [0, 0, 0], "blue cube": [1, 1, 200]})
        self.assertEqual(towers[0][0][2], 110.0)

    def test_distance_threshold(self):
        near = {"red cube": [0, 0, 110], "blue cube": [34, 0, 150]}
        far = {"red cube": [0, 0, 110], "blue cube": [35, 0, 150]}
        self.assertEqual(len(P._analyze_cubes_and_towers(near)[1]), 1)
        self.assertEqual(len(P._analyze_cubes_and_towers(far)[1]), 0)


class AutoPromptTest(unittest.TestCase):
    def setUp(self):
        _reset_state()
        p = mock.patch.object(P.random, "choice", side_effect=lambda s: s[0])
        p.start()
        self.addCleanup(p.stop)

    def test_holding(self):
        out = P.get_auto_prompt(holding_object="red cube", known_objects={"red cube": [0, 0, 110]})
        self.assertNotIn("{color}", out)

    def test_empty_memory_scans(self):
        self.assertIn(P.get_auto_prompt(known_objects={}), P.AUTO_PROMPTS_EMPTY_SCAN)

    def test_single_cube(self):
        out = P.get_auto_prompt(known_objects={"red cube": [0, 0, 110]})
        self.assertIn(P.COLOR_TO_THAI["red"], out)
        self.assertNotIn("{color}", out)

    def test_two_cubes_start_tower(self):
        out = P.get_auto_prompt(known_objects={"red cube": [0, 0, 110], "blue cube": [200, 0, 110]})
        self.assertNotIn("{color_a}", out)
        self.assertNotIn("{color_b}", out)

    def test_grow_tower(self):
        objs = {"red cube": [0, 0, 110], "blue cube": [10, 0, 150], "green cube": [200, 0, 110]}
        out = P.get_auto_prompt(known_objects=objs)
        self.assertNotIn("{free_color}", out)
        self.assertNotIn("{top_color}", out)

    def test_tower_complete_switches_to_normal(self):
        objs = {"red cube": [0, 0, 110], "blue cube": [10, 0, 150]}
        with mock.patch.object(P.random, "randint", return_value=7):
            out = P.get_auto_prompt(known_objects=objs)
        self.assertIn(out, P.AUTO_PROMPTS_TOWER_COMPLETE)
        self.assertEqual(P._auto_mission_state["mode"], "normal")
        self.assertEqual(P._auto_mission_state["normal_steps_left"], 7)

    def test_normal_mode_counts_down_to_mission(self):
        _reset_state(mode="normal", steps=1)
        objs = {"red cube": [0, 0, 110], "blue cube": [10, 0, 150]}
        P.get_auto_prompt(known_objects=objs)
        self.assertEqual(P._auto_mission_state["mode"], "mission")

    def test_periodic_review_resets_counter(self):
        _reset_state(count=P.MEMORY_REVIEW_INTERVAL - 1)
        out = P.get_auto_prompt(known_objects={"red cube": [0, 0, 110], "blue cube": [200, 0, 110]})
        self.assertIn(out, P.AUTO_PROMPTS_EMPTY_SCAN)
        self.assertEqual(P._auto_mission_state["auto_command_count"], 0)

    def test_anti_repetition_prefers_unseen(self):
        cands = P.AUTO_PROMPTS_EMPTY_SCAN
        self.assertGreater(len(cands), 1)
        out = P.get_auto_prompt(known_objects={}, recent_prompts=[cands[0]])
        self.assertNotEqual(out, cands[0])

    def test_anti_repetition_lru_when_all_seen(self):
        cands = list(P.AUTO_PROMPTS_EMPTY_SCAN)
        out = P.get_auto_prompt(known_objects={}, recent_prompts=cands)  # cands[0] seen longest ago
        self.assertEqual(out, cands[0])


if __name__ == "__main__":
    unittest.main()
