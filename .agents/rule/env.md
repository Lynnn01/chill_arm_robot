# Configuration File

`config.json` is the core runtime configuration:

- `points_pixel` / `points_arm`: Hand-eye calibration points for the grasping area.
- `points_pixel_place` / `points_arm_place`: Hand-eye calibration points for the placement area.
- `x` / `y` / `z`: Grasping coordinate offsets, used to correct overall deviation.
- `threshold`: Visual binarization threshold, which may be used in some processes.

Modifying the calibration points or offsets will directly affect the real robotic arm movements. Do not arbitrarily change `config.json` unless the user explicitly requests parameter tuning.

## Environment Variables (.env)
This project uses `python-dotenv` for loading sensitive keys and configuration.
- `MYCOBOT_PORT` / `MYCOBOT_BAUD`: Hardware port settings.
- `OPENAI_API_KEY`: API key for OpenAI-compatible LLMs.
- `LLM_BASE_URL` / `LLM_MODEL_NAME`: Target LLM settings.
- `QWEN_VL_URL` / `QWEN_VL_MODEL` / `QWEN_VL_API_KEY`: Target Qwen-VL endpoint settings.
