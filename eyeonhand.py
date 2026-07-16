import json
import numpy as np
from scipy.optimize import least_squares

# 禁用科学计数法并设置打印精度
np.set_printoptions(suppress=True, precision=1)

# 从 config.json 文件加载数据
with open("config.json", "r") as file:
    data = json.load(file)

# 提取坐标点
points_pixel = np.array(data["points_pixel"], dtype="float32")
points_arm = np.array(data["points_arm"], dtype="float32")
points_pixel_place = np.array(data["points_pixel_place"], dtype="float32")
points_arm_place = np.array(data["points_arm_place"], dtype="float32")

# 定义残差函数
def residuals(params, src, dst):
    a, b, c, d, e, f = params
    transform_matrix = np.array([[a, b, c], [d, e, f], [0, 0, 1]])
    src_h = np.hstack([src, np.ones((src.shape[0], 1))])
    transformed = src_h @ transform_matrix.T
    return (transformed[:, :2] - dst).ravel()

# 初始猜测的仿射变换参数
initial_guess = [1, 0, 0, 0, 1, 0]

# 使用最小二乘法优化仿射变换矩阵
result = least_squares(residuals, initial_guess, args=(points_pixel, points_arm))
optimized_params = result.x
affine_matrix = np.array([[optimized_params[0], optimized_params[1], optimized_params[2]],
                          [optimized_params[3], optimized_params[4], optimized_params[5]]])

# 使用最小二乘法优化place区域的仿射变换矩阵
result_place = least_squares(residuals, initial_guess, args=(points_pixel_place, points_arm_place))
optimized_params_place = result_place.x
affine_matrix_place = np.array([[optimized_params_place[0], optimized_params_place[1], optimized_params_place[2]],
                                [optimized_params_place[3], optimized_params_place[4], optimized_params_place[5]]])

# 定义映射函数
def pixel_to_arm(pixel_point):
    pixel_point = np.array([*pixel_point, 1])  # 添加一个1用于矩阵计算
    transformed_point = affine_matrix @ pixel_point
    return np.round(transformed_point[:2], 1)  # 保留一位小数

# 定义place区域的映射函数
def pixel_to_arm_place(pixel_point):
    pixel_point = np.array([*pixel_point, 1])  # 添加一个1用于矩阵计算
    transformed_point = affine_matrix_place @ pixel_point
    return np.round(transformed_point[:2], 1)  # 保留一位小数

# 使用 config.json 中的 x 和 y 作为测试点
#test_pixel_point = [0,480]
#mapped_arm_point = pixel_to_arm(test_pixel_point)
#print("Pixel坐标：", test_pixel_point)
#print("映射到Arm坐标（保留一位小数）：", mapped_arm_point)
