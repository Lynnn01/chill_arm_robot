import cv2

# Screenshot
def capture(img_path):
    cap = cv2.VideoCapture(0)  # Open camera
    # Get a frame
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)  # The camera is facing the person, flip the image horizontally for normal display
    cv2.imwrite(img_path, frame)  # Save path
    cap.release()
    return img_path

if __name__ == "__main__":
    capture("test.png")
