# !/usr/bin/env python
# coding: utf-8
import cv2 as cv
import numpy as np
import logging
import jetcobot_utils.logger_config as logger_config
 

class Arm_Calibration:
    def __init__(self):
        self.image = None
        self.threshold_num = 130

        logger_config.setup_logger()

    def calibration_map(self, image, threshold_num=140):
        '''
        Place block area detection function
        :param image:            input image
        :return:,  Contour area edge points, processed image
        '''
        try:
            self.image = image
            self.threshold_num = threshold_num
            # Create edge container
            dp = []
            h, w = self.image.shape[:2]
            # Get the set of contour points (coordinates)
            contours = self.Morphological_processing()
            # print("len(contours) = ",len(contours))
            # Traverse the point set
            for i, c in enumerate(contours):
                # Calculate the contour area.
                area = cv.contourArea(c)
                # Set the outline area range
                if h * w / 2 < area < h * w:
                    # Calculate the moment of a polygon
                    mm = cv.moments(c)
                    if mm['m00'] == 0:
                        continue
                    cx = mm['m10'] / mm['m00']
                    cy = mm['m01'] / mm['m00']
                    # draw outline area
                    cv.drawContours(self.image, contours, i, (255, 255, 0), 2)
                    # Get the edge points of the contour area
                    dp = np.squeeze(cv.approxPolyDP(c, 100, True))
                    # draw center
                    # print("np.int32(cx) = ",np.int32(cx))
                    # cv.circle(self.image, (np.int32(cx), np.int32(cy)), 5, (0, 0, 255), -1)
            return dp, self.image
        except Exception as e:
            self.logger.info('e = {}'.format(e))

    def Morphological_processing(self):
        '''
        Morphology and denoising, and obtain contour point set
        '''
        # Convert image to grayscale
        gray = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        # Blur image with Gaussian filter
        gray = cv.GaussianBlur(gray, (5, 5), 1)
        # Image Binarization Operation
        ref, threshold = cv.threshold(gray, self.threshold_num, 255, cv.THRESH_BINARY)
        # Get structuring elements of different shapes
        kernel = np.ones((3, 3), np.uint8)
        # Morphological opening operation
        blur = cv.morphologyEx(threshold, cv.MORPH_OPEN, kernel, iterations=4)
        # Extract mode
        mode = cv.RETR_EXTERNAL
        # method of extraction
        method = cv.CHAIN_APPROX_NONE
        # Get the set of contour points (coordinates) python2 and python3 are slightly different here
        # Hierarchical relationship Parameter 1: input binary image, parameter 2: extraction mode, parameter 3: extraction method.
        find_contours = cv.findContours(blur, mode, method)
        if len(find_contours) == 3: contours = find_contours[1]
        else: contours = find_contours[0]
        return contours

    def Perspective_transform(self, dp, image):
        '''
        perspective transformation
        :param dp: (,,,)  Box edge points (upper left, lower left, lower right, upper right)
        :param image:   The original image
        :return:   Perspective transformed image
        '''
        if len(dp)!=4: return image
        upper_left = []
        lower_left = []
        lower_right = []
        upper_right = []
        for i in range(len(dp)):
            if dp[i][0] < 320 and dp[i][1] < 240:
                upper_left = dp[i]
            if dp[i][0] < 320 and dp[i][1] > 240:
                lower_left = dp[i]
            if dp[i][0] > 320 and dp[i][1] > 240:
                lower_right = dp[i]
            if dp[i][0] > 320 and dp[i][1] < 240:
                upper_right = dp[i]
        # The four vertices in the original image, and the transformation matrix
        pts1 = np.float32([upper_left, lower_left, lower_right, upper_right])
        # The four vertices in the original image, and the transformation matrix
        pts2 = np.float32([[0, 0], [0, 480], [640, 480], [640, 0]])
        # Compute perspective transformation from four pairs of corresponding points
        M = cv.getPerspectiveTransform(pts1, pts2)
        # Apply a perspective transform to an image
        Transform_img = cv.warpPerspective(image, M, (640, 480))
        return Transform_img



class update_hsv:
    def __init__(self):
        self.image = None
        self.binary = None

    def Image_Processing(self, hsv_range):
        '''
        Morphological transformation to remove small interference factors
        :param img:       Enter the initial image
        :return: ()  Detected contour point set (coordinates)
        '''
        (lowerb, upperb) = hsv_range
        # Copy the original image to avoid interference during processing
        color_mask = self.image.copy()
        # Convert image to HSV
        hsv_img = cv.cvtColor(self.image, cv.COLOR_BGR2HSV)
        # filter out elements between two arrays
        color = cv.inRange(hsv_img, lowerb, upperb)
        # Set the non-mask detection part to be all black
        color_mask[color == 0] = [0, 0, 0]
        # Convert image to grayscale
        gray_img = cv.cvtColor(color_mask, cv.COLOR_RGB2GRAY)
        # Get structuring elements of different shapes
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
        # morphological closure
        dst_img = cv.morphologyEx(gray_img, cv.MORPH_CLOSE, kernel)
        # Image Binarization Operation
        ret, binary = cv.threshold(dst_img, 10, 255, cv.THRESH_BINARY)
        # Get the set of contour points (coordinates)
        find_contours = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        if len(find_contours) == 3: contours = find_contours[1]
        else: contours = find_contours[0]
        return contours, binary

    def draw_contours(self, hsv_name, contours):
        '''
        draw outline
        '''
        for i, cnt in enumerate(contours):
            # Calculate the moment of a polygon
            mm = cv.moments(cnt)
            if mm['m00'] == 0:
                continue
            cx = mm['m10'] / mm['m00']
            cy = mm['m01'] / mm['m00']
            # Calculate the area of ​​the contour
            area = cv.contourArea(cnt)
            # Area greater than 800
            if area > 800:
                # Get the center of the polygon
                (x, y) = (np.int32(cx), np.int32(cy))
                # drawing center
                cv.circle(self.image, (x, y), 5, (0, 0, 255), -1)
                # Calculate the smallest rectangular area
                rect = cv.minAreaRect(cnt)
                # get box vertices
                box = cv.boxPoints(rect)
                # Convert to long type
                box = np.int64(box)
                # draw the smallest rectangle
                cv.drawContours(self.image, [box], 0, (255, 0, 0), 2)
                cv.putText(self.image, hsv_name, (int(x - 15), int(y - 15)),
                           cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
    
    def draw_contours_and_get_color(self, hsv_name, contours):
        '''
        draw outline
        '''
        color = ""
        for i, cnt in enumerate(contours):
            # Calculate the moment of a polygon
            mm = cv.moments(cnt)
            if mm['m00'] == 0:
                continue
            cx = mm['m10'] / mm['m00']
            cy = mm['m01'] / mm['m00']
            # Calculate the area of ​​the contour
            area = cv.contourArea(cnt)
            # Area greater than 800
            if area > 800:
                # Get the center of the polygon
                (x, y) = (np.int32(cx), np.int32(cy))
                # drawing center
                cv.circle(self.image, (x, y), 5, (0, 0, 255), -1)
                # Calculate the smallest rectangular area
                rect = cv.minAreaRect(cnt)
                # get box vertices
                box = cv.boxPoints(rect)
                # Convert to long type
                box = np.int64(box)
                # draw the smallest rectangle
                cv.drawContours(self.image, [box], 0, (255, 0, 0), 2)
                cv.putText(self.image, hsv_name, (int(x - 15), int(y - 15)),
                           cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                color = hsv_name
        return color

    def get_contours(self, img, color_name, hsv_msg, color_hsv):
        binary = None
        self.image = cv.resize(img, (640, 480), )
        for key, value in color_hsv.items():
            # Detect contour point set
            if color_name == key:
                color_contours, binary = self.Image_Processing(hsv_msg)
            else:
                color_contours, _ = self.Image_Processing(color_hsv[key])
            # Draw the detection image and control the following
            self.draw_contours(key, color_contours)
        return self.image, binary
    

    def get_color(self, img, color_hsv):
        binary = None
        color = ""
        self.image = cv.resize(img, (640, 480), )
        for key, value in color_hsv.items():
            color_contours, _ = self.Image_Processing(color_hsv[key])
            color = self.draw_contours_and_get_color(key, color_contours)
            if len(color) > 0:
                break
        return self.image, color


def write_HSV(wf_path, dict):
    with open(wf_path, "w") as wf:
        for key, value in dict.items():
            wf_str = '"' + key + '": [' + str(value[0][0]) + ', ' + str(
                value[0][1]) + ', ' + str(value[0][2]) + ', ' + str(
                value[1][0]) + ', ' + str(value[1][1]) + ', ' + str(
                value[1][2]) + '], ' + '\n'
            wf.write(wf_str)
        wf.flush()


def read_HSV(rf_path, dict):
    rf = open(rf_path, "r+")
    for line in rf.readlines():
        list = []
        name = None
        aa = line.find('"')
        bb = line.rfind('"')
        cc = line.find('[')
        dd = line.rfind(']')
        if aa >= 0 and bb >= 0: name = line[aa + 1:bb]
        if cc >= 0 and dd >= 0:
            rf_str = line[cc + 1:dd].split(',')
            for index, i in enumerate(rf_str): list.append(int(i))
            if name != None: dict[name] = ((list[0], list[1], list[2]), (list[3], list[4], list[5]))
    rf.flush()


def write_XYT(wf_path, joint1456, thresh):
    with open(wf_path, "w") as wf:
        str1 = 'joint1' + '=' + str(joint1456[0])
        str2 = 'joint4' + '=' + str(joint1456[1])
        str3 = 'joint5' + '=' + str(joint1456[2])
        str4 = 'joint6' + '=' + str(joint1456[3])
        str5 = 'thresh' + '=' + str(thresh)
        wf_str = str1 + '\n' + str2 + '\n' + str3 + '\n' + str4 + '\n' + str5
        wf.write(wf_str)
        wf.flush()


def read_XYT(rf_path):
    dict = {}
    rf = open(rf_path, "r+")
    for line in rf.readlines():
        index = line.find('=')
        dict[line[:index]] = line[index + 1:]
    joint1456 = [int(dict['joint1']), int(dict['joint4']),int(dict['joint5']),int(dict['joint6'])]
    thresh = int(dict['thresh'])
    rf.flush()
    return joint1456, thresh


def write_PIDT(wf_path, PID, time_config):
    with open(wf_path, "w") as wf:
        str1 = 'P' + '=' + str(PID[0])
        str2 = 'I' + '=' + str(PID[1])
        str3 = 'D' + '=' + str(PID[2])
        str4 = 'T1' + '=' + str(time_config[1])
        str5 = 'T2' + '=' + str(time_config[1])
        str6 = 'T3' + '=' + str(time_config[2])
        wf_str = str1 + '\n' + str2 + '\n' + str3 + '\n' + str4 + '\n' + str5 + '\n' + str6
        wf.write(wf_str)
        wf.flush()


def read_PIDT(rf_path):
    dict = {}
    rf = open(rf_path, "r+")
    for line in rf.readlines():
        index = line.find('=')
        dict[line[:index]] = line[index + 1:]
    PID = [int(dict['P']), int(dict['I']), int(dict['D'])]
    time_config = [int(dict['T1']), int(dict['T2']), int(dict['T3'])]
    rf.flush()
    return PID, time_config