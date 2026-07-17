import json
import numpy as np
from scipy.optimize import least_squares

# Disable scientific notation and set print precision
np.set_printoptions(suppress=True, precision=1)

# Load data from config.json
with open("config.json", "r") as file:
    data = json.load(file)

# Extract coordinate points
points_pixel = np.array(data["points_pixel"], dtype="float32")
points_arm = np.array(data["points_arm"], dtype="float32")
points_pixel_place = np.array(data["points_pixel_place"], dtype="float32")
points_arm_place = np.array(data["points_arm_place"], dtype="float32")

# Define residuals function
def residuals(params, src, dst):
    a, b, c, d, e, f = params
    transform_matrix = np.array([[a, b, c], [d, e, f], [0, 0, 1]])
    src_h = np.hstack([src, np.ones((src.shape[0], 1))])
    transformed = src_h @ transform_matrix.T
    return (transformed[:, :2] - dst).ravel()

# Initial guess for affine transformation parameters
initial_guess = [1, 0, 0, 0, 1, 0]

# Use least squares optimization to find affine transformation matrix
result = least_squares(residuals, initial_guess, args=(points_pixel, points_arm))
optimized_params = result.x
affine_matrix = np.array([[optimized_params[0], optimized_params[1], optimized_params[2]],
                          [optimized_params[3], optimized_params[4], optimized_params[5]]])

# Use least squares optimization to find affine transformation matrix for place area
result_place = least_squares(residuals, initial_guess, args=(points_pixel_place, points_arm_place))
optimized_params_place = result_place.x
affine_matrix_place = np.array([[optimized_params_place[0], optimized_params_place[1], optimized_params_place[2]],
                                [optimized_params_place[3], optimized_params_place[4], optimized_params_place[5]]])

# Define mapping function
def pixel_to_arm(pixel_point):
    pixel_point = np.array([*pixel_point, 1])  # Add a 1 for matrix calculation
    transformed_point = affine_matrix @ pixel_point
    return np.round(transformed_point[:2], 1)  # Round to one decimal place

# Define mapping function for place area
def pixel_to_arm_place(pixel_point):
    pixel_point = np.array([*pixel_point, 1])  # Add a 1 for matrix calculation
    transformed_point = affine_matrix_place @ pixel_point
    return np.round(transformed_point[:2], 1)  # Round to one decimal place

# Use x and y from config.json as test points
#test_pixel_point = [0,480]
#mapped_arm_point = pixel_to_arm(test_pixel_point)
#print("Pixel coordinates: ", test_pixel_point)
#print("Mapped to Arm coordinates (rounded to one decimal place): ", mapped_arm_point)
