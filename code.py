code = """
import math

# Define center point and radius (here centered at origin)
center = (0, 215)
radius = 100

# Calculate the position of 6 points, the angle between each point is 360/6=60 degrees
angles = [math.radians(60 * i) for i in range(6)]
points = [(int(center[0] + radius * math.cos(angle)), int(center[1] + radius * math.sin(angle))) for angle in angles]

Result = points  # Return coordinate result variable named Result
"""

# Use exec to execute code
exec(code)

# Check the Result variable in global scope
execution_result = globals().get('Result', None)

# Return the obtained result
print(execution_result)