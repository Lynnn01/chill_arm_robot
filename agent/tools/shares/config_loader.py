import json
from hardware import init

def load_offsets() -> dict:
    """โหลด x/y/z offset จาก config.json"""
    try:
        with open(init.CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return {
            "x": cfg.get("x", 0),
            "y": cfg.get("y", 0),
            "z": cfg.get("z", 0),
        }
    except Exception as e:
        print(f"⚠️ <SYSTEM>: Failed to load offsets: {e}")
        return {"x": 0, "y": 0, "z": 0}
