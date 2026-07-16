# Known Risk Points

- `GrabObject.call` in `tools.py` may still return an undefined `robot_coord` when no target is detected. Future fixes should allow empty results to return explicit errors or statuses.
- `react_agent.agent.extract_functions_and_args` assumes the number of functions and parameters are consistent, which may go out of bounds when the model output is non-standard.
- The API key in `react_agent.LLM` should not be hardcoded in the source code long-term. (Note: Currently refactored to use `.env`!).
- There is a suspected typo `self.get_lsb_release_info` in `utils.jetcobot_info.board_name()`.
