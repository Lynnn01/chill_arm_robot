# Testing and Verification Suggestions

- Pure functions and low-side-effect modules can be tested first in a hardware-free environment, for example:
  - `eyeonhand.pixel_to_arm`
  - `utils.roi_cropper.ROICropper`
  - Geometric auxiliary functions in `utils.vutils`
  - String parsing logic in `react_agent.agent`, but avoid importing `tools.py`
- Changes involving hardware need to be verified in a real JetCobot/Jetson environment:
  - Whether the robotic arm serial port exists.
  - Whether the camera can save `captured_image.jpg` normally.
  - Whether the gripper opens and closes in the correct direction.
  - Whether coordinates fall within the safe workspace.
- Changes involving external APIs need to consider network failures, non-200 responses, empty detection results, and response field changes.
