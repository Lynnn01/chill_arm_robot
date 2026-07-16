import requests
import base64
import re
import json
import openai
import os
from PIL import Image

qwen_vl_url = os.getenv("QWEN_VL_URL", "https://prodsvc.educg.net/serve-qwen25-vl-7b-instruct/v1")
qwen_vl_model = os.getenv("QWEN_VL_MODEL", "qwen2.5-vl:7b")
qwen_vl_api_key = os.getenv("QWEN_VL_API_KEY", "EMPTY")

vl_client = openai.OpenAI(api_key=qwen_vl_api_key, base_url=qwen_vl_url)

def QwenVLRequest(object_name, image_path):
    """
       Use OpenAI-compatible vision model to detect specified object.

       :param object_name: Object name to identify or process
       :param image_path: Local image file path
       :return: Returns {"coordinates": [{"x1": ..., "y1": ..., "x2": ..., "y2": ...}]}, coordinates are original image pixels
       """
    try:
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        prompt = (
            "You are an expert computer vision model. Carefully analyze the image and locate all instances of the object: '{object_name}'. "
            "Return ONLY a valid JSON object without any markdown formatting or explanations. "
            'The required schema is: {"coordinates":[{"x1":integer,"y1":integer,"x2":integer,"y2":integer}]}. '
            "Coordinates must be exact bounding box values in original image pixels. "
            'If the object is not found, return exactly: {"coordinates":[]}.'
        )

        response = vl_client.chat.completions.create(
            model=qwen_vl_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + image_base64
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        return {"coordinates": [], "error": str(e)}
