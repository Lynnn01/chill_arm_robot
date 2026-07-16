code = """
import math

# 定义中心点和半径（这里以原点为中心）
center = (0, 215)
radius = 100

# 计算6个点的位置，每个点相隔的角度为360/6=60度
angles = [math.radians(60 * i) for i in range(6)]
points = [(int(center[0] + radius * math.cos(angle)), int(center[1] + radius * math.sin(angle))) for angle in angles]

Result = points  # 返回坐标结果变量名为Result
"""

# 使用 exec 执行代码
exec(code)

# 检查全局作用域中的 Result 变量
execution_result = globals().get('Result', None)

# 返回获取到的结果
print(execution_result)