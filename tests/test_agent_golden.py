"""Characterization tests for agent/agent.py::get_contextual_input and agent/executor.py::execute_plan.

Regenerate only for intentional behavior changes:
    UPDATE_GOLDEN=1 python -m unittest tests.test_agent_golden
"""
import contextlib
import io
import json
import os
import unittest
from unittest import mock

from agent import agent as A
from agent import executor as E
from agent import scoring
from hardware import init

GOLDEN = os.path.join(os.path.dirname(__file__), "golden_agent.json")


def context(known=None, holding=None, is_holding=None, coords=None, drop_coords=False):
    known = json.loads(json.dumps(known if known is not None else {}))
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch.object(init, "known_objects", known))
        st.enter_context(mock.patch.object(init, "current_held_object", holding, create=True))
        st.enter_context(mock.patch.object(init, "is_holding_object",
                                           bool(holding) if is_holding is None else is_holding, create=True))
        if drop_coords:
            st.enter_context(mock.patch.object(init, "last_coords", None, create=True))
            st.enter_context(mock.patch.object(init, "known_objects", object()))  # forces an error path
        else:
            st.enter_context(mock.patch.object(init, "last_coords", coords, create=True))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            res = A.get_contextual_input("hello")
    return {"res": res, "out": out.getvalue()}


class FakeThread:
    started = []

    def __init__(self, target=None, args=(), daemon=None):
        self.target, self.args = target, args

    def start(self):
        FakeThread.started.append(list(self.args))


def plan(tasks, tools, speaker_on=False, summary="sum"):
    scoring._CURRENT_SCORE = 0
    calls = []
    FakeThread.started = []

    def mk(name, ret):
        def f(**kw):
            calls.append((name, kw))
            if isinstance(ret, Exception):
                raise ret
            return ret
        return f

    tool_map = {n: mk(n, r) for n, r in tools.items()}
    with contextlib.ExitStack() as st:
        st.enter_context(mock.patch.object(E, "_get_raw_tool_map", lambda: tool_map))
        st.enter_context(mock.patch("threading.Thread", FakeThread))
        st.enter_context(mock.patch.object(A, "_play_voice", lambda *a: None, create=True))
        st.enter_context(mock.patch.object(scoring, "evaluate_task_points", lambda t, s: (5, "r:" + s)))
        st.enter_context(mock.patch.object(scoring, "add_score", lambda p, r: calls.append(("score", p, r))))
        with contextlib.redirect_stdout(io.StringIO()):
            res = E.execute_plan(tasks, summary, speaker_on=speaker_on)
    return {"res": res, "calls": calls, "voice": FakeThread.started}


OK = {"status": "DONE TASK"}


def scenarios():
    S = {}
    cubes = {
        "red_cube": [200, 0, 110], "blue_cube": [205, 3, 150],
        "green_cube": [170, 90, 0], "a_area": [160, -150, 0], "x": "in gripper", "short": [1],
    }
    S["ctx_empty"] = lambda: context(known={}, coords=None)
    S["ctx_coords"] = lambda: context(known={}, coords=[1, 2, 3])
    S["ctx_short_coords"] = lambda: context(known={}, coords=[1, 2])
    S["ctx_holding_named"] = lambda: context(known=cubes, holding="red_cube", coords=[1, 2, 3])
    S["ctx_holding_unnamed"] = lambda: context(known={}, holding=None, is_holding=True)
    S["ctx_blocked_relations"] = lambda: context(known=cubes, coords=[0, 0, 0])
    S["ctx_no_blocking_far"] = lambda: context(known={"a_cube": [0, 0, 110], "b_cube": [100, 0, 200]})
    S["ctx_error_returns_raw"] = lambda: context(drop_coords=True)

    S["plan_two_ok_move_uses_grab_coord"] = lambda: plan(
        [{"tool": "grab_object", "args": {"object_name": "red cube"}}, {"tool": "move_to", "args": {}}],
        {"grab_object": {"status": "DONE TASK", "data": [10, 20]}, "move_to": OK})
    S["plan_move_with_target_not_overridden"] = lambda: plan(
        [{"tool": "grab_object", "args": {}}, {"tool": "move_to", "args": {"target_name": "red cube"}}],
        {"grab_object": {"status": "DONE TASK", "data": [10, 20]}, "move_to": OK})
    S["plan_old_list_grab"] = lambda: plan(
        [{"tool": "grab_object()", "args": {}}, {"tool": "move_to", "args": {"target_coord": None}}],
        {"grab_object": [7, 8], "move_to": OK})
    S["plan_unknown_tool_skipped"] = lambda: plan(
        [{"tool": "nope"}, {"tool": "dance_celebrate"}], {"dance_celebrate": OK})
    S["plan_error_dict_breaks"] = lambda: plan(
        [{"tool": "a"}, {"tool": "b", "args": {"x": 1}}, {"tool": "c"}],
        {"a": OK, "b": {"status": "ERROR", "message": "boom"}, "c": OK})
    S["plan_exception_breaks"] = lambda: plan(
        [{"tool": "a"}, {"tool": "b"}], {"a": RuntimeError("bad"), "b": OK})
    S["plan_none_args_stripped"] = lambda: plan(
        [{"tool": "a", "args": {"x": None, "y": 2}}], {"a": "text result"})
    S["plan_voice_threads"] = lambda: plan(
        [{"tool": "a", "voice": "hi"}, {"tool": "b"}], {"a": OK, "b": OK}, speaker_on=True)
    S["plan_empty"] = lambda: plan([], {})
    S["plan_partial_no_score"] = lambda: plan(
        [{"tool": "a"}, {"tool": "zzz"}], {"a": OK})
    return S


class GoldenAgentTest(unittest.TestCase):
    maxDiff = None

    def test_scenarios_match_golden(self):
        got = {n: json.loads(json.dumps(fn(), default=repr, ensure_ascii=False)) for n, fn in scenarios().items()}
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


if __name__ == "__main__":
    unittest.main()
