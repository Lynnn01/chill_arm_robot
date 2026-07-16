import cv2

# 截图
def capture(img_path):
    cap = cv2.VideoCapture(0)  # 打开摄像头
    # 获取一个frame
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)  # 摄像头是和人对立的，将图像左右调换回来正常显示
    cv2.imwrite(img_path, frame)  # 保存路径
    cap.release()
    return img_path

if __name__ == "__main__":
    capture("test.png")
