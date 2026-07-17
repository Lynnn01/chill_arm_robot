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

# Configure OpenAI client with explicit timeouts to prevent infinite hanging
vl_client = openai.OpenAI(api_key=qwen_vl_api_key, base_url=qwen_vl_url, timeout=15.0)

def _extract_json_from_text(text):
    text = text.strip()
    code_block = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if code_block:
        text = code_block.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start_candidates = [pos for pos in (text.find("{"), text.find("[")) if pos != -1]
    if not start_candidates:
        raise ValueError("No JSON object or array found in model output")

    start = min(start_candidates)
    end = max(text.rfind("}"), text.rfind("]"))
    if end <= start:
        raise ValueError("Incomplete JSON found in model output")

    return json.loads(text[start:end + 1])

def _normalize_box_value(value):
    value = float(value)
    value = max(0, min(1000, value))
    if value.is_integer():
        return int(value)
    return value

def _pixel_to_normalized(value, axis_length):
    return _normalize_box_value(float(value) / axis_length * 1000)

def _box_values_to_normalized(x1, y1, x2, y2, image_size=None):
    if image_size is None:
        return {
            "x1": _normalize_box_value(x1),
            "y1": _normalize_box_value(y1),
            "x2": _normalize_box_value(x2),
            "y2": _normalize_box_value(y2),
        }

    width, height = image_size
    values_look_like_pixels = (
        0 <= float(x1) <= width and
        0 <= float(x2) <= width and
        0 <= float(y1) <= height and
        0 <= float(y2) <= height
    )
    if not values_look_like_pixels:
        return {
            "x1": _normalize_box_value(x1),
            "y1": _normalize_box_value(y1),
            "x2": _normalize_box_value(x2),
            "y2": _normalize_box_value(y2),
        }

    return {
        "x1": _pixel_to_normalized(x1, width),
        "y1": _pixel_to_normalized(y1, height),
        "x2": _pixel_to_normalized(x2, width),
        "y2": _pixel_to_normalized(y2, height),
    }

def _box_from_dict(item, image_size=None):
    if all(key in item for key in ("x1", "y1", "x2", "y2")):
        return _box_values_to_normalized(
            item["x1"], item["y1"], item["x2"], item["y2"], image_size
        )

    bbox = item.get("bbox_2d")
    if isinstance(bbox, list) and len(bbox) >= 4:
        return _box_values_to_normalized(bbox[0], bbox[1], bbox[2], bbox[3], image_size)

    return None

def _normalize_vl_result(result, image_size=None):
    if isinstance(result, dict):
        raw_coordinates = result.get("coordinates", [])
    elif isinstance(result, list):
        raw_coordinates = result
    else:
        raise ValueError("Model output JSON must be an object or array")

    if not isinstance(raw_coordinates, list):
        raise ValueError("coordinates must be a list")

    coordinates = []
    for item in raw_coordinates:
        if not isinstance(item, dict):
            continue
        box = _box_from_dict(item, image_size)
        if box is not None:
            coordinates.append(box)

    return {"coordinates": coordinates}

def _normalize_vl_text_result(text, image_size=None):
    number = r"[-+]?\d+(?:\.\d+)?"
    keyed_box_pattern = re.compile(
        r'\\?"x1\\?"\s*:\s*(' + number + r").*?"
        r'\\?"y1\\?"\s*:\s*(' + number + r").*?"
        r'\\?"x2\\?"\s*:\s*(' + number + r").*?"
        r'\\?"y2\\?"\s*:\s*(' + number + r")",
        re.DOTALL,
    )
    keyed_match = keyed_box_pattern.search(text)
    if keyed_match:
        return {
            "coordinates": [
                _box_values_to_normalized(
                    keyed_match.group(1),
                    keyed_match.group(2),
                    keyed_match.group(3),
                    keyed_match.group(4),
                    image_size,
                )
            ]
        }

    array_match = re.search(
        r'\\?"coordinates\\?"\s*:\s*\[\s*(' + number + r")\s*,\s*("
        + number + r")\s*,\s*(" + number + r")\s*,\s*(" + number + r")",
        text,
    )
    if array_match:
        return {
            "coordinates": [
                _box_values_to_normalized(
                    array_match.group(1),
                    array_match.group(2),
                    array_match.group(3),
                    array_match.group(4),
                    image_size,
                )
            ]
        }

    raise ValueError("No valid bounding box found in model output")

def QwenVLRequest(object_name, image_path):
    """
       Use OpenAI-compatible vision model to detect specified object.

       :param object_name: Object name to identify or process
       :param image_path: Local image file path
       :return: Returns {"coordinates": [{"x1": ..., "y1": ..., "x2": ..., "y2": ...}]}, coordinates are 0-1000 normalized coordinates
       """
    try:
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        image_size = Image.open(image_path).size

        prompt = (
            "Return ONLY a valid JSON object, no markdown and no explanation. "
            f"Detect {object_name} in the image. "
            'The required schema is {"coordinates":[{"x1":integer,"y1":integer,"x2":integer,"y2":integer}]}. '
            "Coordinates must be bounding box values in original image pixels. "
            'If the object is not found, return {"coordinates":[]}.'
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
        try:
            result = _extract_json_from_text(content)
            return _normalize_vl_result(result, image_size)
        except Exception:
            return _normalize_vl_text_result(content, image_size)

    except Exception as e:
        return {"coordinates": [], "error": str(e)}

def QwenVLDescribe(question, image_path):
    """
    Use OpenAI-compatible vision model to answer a general question about an image.
    
    :param question: The question to ask about the image
    :param image_path: Local image file path
    :return: Returns text description from the model
    """
    try:
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        response = vl_client.chat.completions.create(
            model=qwen_vl_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + image_base64
                            },
                        },
                    ],
                }
            ],
            temperature=0.4,
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"
