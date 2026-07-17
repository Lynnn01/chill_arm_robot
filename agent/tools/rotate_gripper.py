import time
from hardware.init import mc
from agents import function_tool

@function_tool
def rotate_gripper(angle_range: int = 45, speed: int = 40) -> str:
    """
    Rotates the gripper back and forth by a specified angle range, then returns to its original position.
    Can be used when the user asks the robot to show off, wave the gripper, or rotate the gripper.
    
    Args:
        angle_range: The angle in degrees to rotate left and right. Default is 45.
        speed: Rotation speed (1-100). Default is 40.
    """
    print(f"Rotating gripper back and forth by {angle_range} degrees at speed {speed}...")
    
    # Try to get current angles
    current_angles = mc.get_angles()
    
    if not current_angles or len(current_angles) != 6:
        print("Warning: Could not read current angles. Using default base position (-45) for Joint 6.")
        j6_base = -45
    else:
        j6_base = current_angles[5]

    # Rotate left
    mc.send_angle(6, j6_base + angle_range, speed)
    time.sleep(1.5)
    
    # Rotate right
    mc.send_angle(6, j6_base - angle_range, speed)
    time.sleep(2.0)
    
    # Return to original position
    mc.send_angle(6, j6_base, speed)
    time.sleep(1.5)
    
    return "Gripper successfully rotated back and forth and returned to its original position."
