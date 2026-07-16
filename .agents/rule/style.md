# Development Conventions

- Try to keep the existing simple structure without introducing large frameworks.
- When adding a new tool:
  - Inherit from `BaseTool` in `tools.py`.
  - Register it using `@register_tool('tool_name')`.
  - Provide a clear `description` and `parameters`, as this content will go into the system prompt.
  - Tool parameters should remain JSON serializable.
- When modifying Agent parsing logic, ensure compatibility with these special markers:
  - `✿FUNCTION✿`
  - `✿ARGS✿`
  - `✿RESULT✿`
  - `✿RETURN✿`
- Do not unnecessarily reorder hardware action sequences, coordinate ranges, wait times, or gripper opening/closing logic.
- There are a few historical encoding gibberish in the source code. Unless the task goal is to fix encoding/copywriting, do not casually change comments on a large scale to avoid creating noise.
- `dist/`, `__pycache__/`, audio recordings, and generated images belong to generation artifacts, and generally should not be manually edited or committed.
