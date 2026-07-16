# AGENTS.MD

本文件用于帮助后续协作者快速、安全地接手这个项目。项目是一个 Python 机械臂 Agent，结合大模型、视觉检测、摄像头和 JetCobot/MyCobot 硬件完成抓取、展示、摆放等任务。

## 项目概览

- 主入口：`agent.py`
  - 默认启动交互循环。
  - 当前使用键盘输入。
  - 初始化 `RequestLLM`、`ReactAgent`，并注册工具。
- 命令行入口：`agent2.py`
  - 支持直接传入一句用户指令，也支持 `--interactive` / `--voice`。
  - 使用另一组 LLM endpoint/model 配置。
- 工具实现：`tools.py`
  - 注册给 ReAct Agent 的硬件工具：`grab_object`、`move_to`、`show_object`。
  - 导入时会实例化机械臂并执行初始化相关逻辑，处理时要谨慎。
- Agent 框架：`react_agent/`
  - `agent.py`：解析模型输出中的 `✿FUNCTION✿` / `✿ARGS✿`，执行工具调用；也会执行模型生成的 Python 代码并读取全局变量 `Result`。
  - `LLM.py`：OpenAI-compatible client 封装。
  - `tools.py`：工具注册表和 `BaseTool`。
  - `camera.py`：简单摄像头截图工具。
- 硬件与视觉辅助：
  - `init.py`：机械臂初始化、夹爪控制、摄像头拍照。
  - `eyeonhand.py`：根据 `config.json` 中的标定点做像素坐标到机械臂坐标的仿射映射。
  - `api.py`：调用外部视觉服务。
  - `utils/`：JetCobot 配置、ROI 裁剪、视觉工具函数。

## 常用命令

在 Jetson/机械臂环境中运行：

```powershell
python agent.py
```

命令行单次指令运行：

```powershell
python agent2.py "抓取红色方块并展示给我"
```

安装依赖：

```powershell
pip install -r requirements.txt
```

运行测试：

```powershell
python -m pytest
```

注意：普通 Windows 开发机通常没有 `/dev/ttyUSB0`、Jetson GPIO、摄像头或机械臂环境。不要把无法连接硬件误判成业务逻辑失败。

## 配置文件

`config.json` 是运行时核心配置：

- `points_pixel` / `points_arm`：抓取区域手眼标定点。
- `points_pixel_place` / `points_arm_place`：放置区域手眼标定点。
- `x` / `y` / `z`：抓取坐标偏移量，用于整体校正偏差。
- `threshold`：视觉二值化阈值，部分流程中可能使用。

修改标定点或偏移量会直接影响真实机械臂动作。除非用户明确要求调参，否则不要随意改 `config.json`。

## 重要副作用与安全边界

- `tools.py` 和 `init.py` 在导入时会创建 `MyCobot('/dev/ttyUSB0', 1000000)`，并可能触发机械臂初始化。后续写测试、脚本或静态检查时，避免无意中导入这些模块。
- `grab_object` 会拍照、调用外部视觉 API、计算坐标并驱动机械臂抓取。
- `move_to` 和 `show_object` 会直接发送机械臂坐标/角度命令。
- `ReactAgent.run_code_and_format_result` 会执行模型生成的 Python 代码。它当前用于生成摆放坐标，改动时必须考虑代码执行风险和结果格式兼容性。
- 项目里存在外部服务地址和硬编码凭据。不要在提交、文档或日志里新增、复制或暴露密钥；如需调整，优先改成环境变量或本地配置。

## 开发约定

- 尽量保持现有简单结构，不引入大型框架。
- 新增工具时：
  - 在 `tools.py` 中继承 `BaseTool`。
  - 使用 `@register_tool('tool_name')` 注册。
  - 提供清晰的 `description` 和 `parameters`，因为这些内容会进入系统提示词。
  - 工具参数应保持 JSON 可序列化。
- 修改 Agent 解析逻辑时，注意保持这些特殊标记兼容：
  - `✿FUNCTION✿`
  - `✿ARGS✿`
  - `✿RESULT✿`
  - `✿RETURN✿`
- 不要无关重排硬件动作序列、坐标范围、等待时间或夹爪开合逻辑。
- 源码中有少量历史编码乱码。除非任务目标是修复编码/文案，否则不要顺手大面积改注释，避免制造噪声。
- `dist/`、`__pycache__/`、录音文件和生成图片属于生成产物，通常不要手动编辑或提交。

## 测试与验证建议

- 可在无硬件环境中优先测试纯函数和低副作用模块，例如：
  - `eyeonhand.pixel_to_arm`
  - `utils.roi_cropper.ROICropper`
  - `utils.vutils` 中的几何辅助函数
  - `react_agent.agent` 的字符串解析逻辑，但要避免导入 `tools.py`
- 涉及硬件的改动需要在真实 JetCobot/Jetson 环境验证：
  - 机械臂串口是否存在。
  - 摄像头是否能正常保存 `captured_image.jpg`。
  - 夹爪开合方向是否正确。
  - 坐标是否落在安全工作区内。
- 涉及外部 API 的改动需要考虑网络失败、非 200 响应、空检测结果和响应字段变化。

## 已知风险点

- `tools.py` 的 `GrabObject.call` 在没有检测到目标时仍可能返回未定义的 `robot_coord`，后续修复时应让空结果返回明确错误或状态。
- `react_agent.agent.extract_functions_and_args` 假设函数数量和参数数量一致，模型输出不规范时可能越界。
- `react_agent.LLM` 中的 API key 不应长期硬编码在源码里。
- `utils.jetcobot_info.board_name()` 中有疑似 `self.get_lsb_release_info` 笔误。

## 给后续 Agent 的协作提示

接手任务时先判断是否会触碰硬件。如果只是改解析、配置、文档或纯工具函数，可以在普通开发机上处理；如果会执行机械臂动作，先向用户确认当前是否连接真实设备、是否允许动作、工作区是否安全。实现时保持改动小而明确，最后说明哪些命令已验证、哪些因为缺少硬件或网络未验证。
