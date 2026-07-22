import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.robot_arm.domain.coordinates import TargetCoordinate, AngleSet
from modules.vision.domain.calibration import PixelCoordinate, BoundingBox
from modules.tts.domain.speech import SpeechMessage
from modules.agent_planner.domain.task_plan import ActionStep, TaskPlan

class TestUnifiedArchitectureDomain(unittest.TestCase):

    def test_target_coordinate_clamping(self):
        coord = TargetCoordinate(500.0, -400.0, 350.0)
        self.assertEqual(coord.x, 280.0)
        self.assertEqual(coord.y, -280.0)
        self.assertEqual(coord.z, 280.0)

    def test_target_coordinate_base_radius_safety(self):
        coord = TargetCoordinate(10.0, 10.0, 50.0)
        self.assertGreaterEqual(coord.x**2 + coord.y**2, 80**2 - 0.1)

    def test_angle_set_validation(self):
        angles = AngleSet([0, 10, -20, 30, 40, -45])
        self.assertEqual(len(angles.angles), 6)

    def test_speech_message_validation(self):
        speech = SpeechMessage("สวัสดีครับ")
        self.assertEqual(speech.text, "สวัสดีครับ")

    def test_task_plan_structure(self):
        step1 = ActionStep("grab_object", {"object_name": "red block"})
        plan = TaskPlan("หยิบกล่องสีแดง", [step1])
        self.assertEqual(plan.plan_summary, "หยิบกล่องสีแดง")
        self.assertEqual(len(plan.tasks), 1)

if __name__ == "__main__":
    unittest.main()
