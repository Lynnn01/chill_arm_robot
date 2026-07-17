import init
import api
from agents import function_tool

@function_tool
def describe_scene(question: str) -> str:
    """
    Takes a photo using the robot's camera and asks the vision model to describe the scene or answer a specific question about it.
    
    Args:
        question: The specific question to ask about the scene. E.g., "What objects are on the table?", "Do you see a person?", "What color is the block?"
    """
    print(f"Taking a photo to answer: '{question}'...")
    
    # 1. Take a picture
    init.GetImage()
    image_path = "captured_image.jpg"
    
    # 2. Call the Vision API
    print("Analyzing image...")
    result_text = api.QwenVLDescribe(question, image_path)
    
    return f"Vision Model Description:\n{result_text}"
