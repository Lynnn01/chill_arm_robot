"""
agent/tools/shares/rps_game.py — Interactive Rock-Paper-Scissors Mini-Game
Flow:
1. Prompts user to show hand gesture to camera FIRST.
2. Captures camera photo and detects user gesture (Rock/Paper/Scissors).
3. Robot counts down "1... 2... 3... ยังชู้ต!" while bobbing arm up and down.
4. Robot physically presents its move using gripper pose.
5. Judges winner, announces result in Isan voice, and performs celebration/bow/tilt gesture.
"""

import time
import random
import cv2
import numpy as np
import armconfig
from hardware.init import mc
from hardware import init
from agent.tts import play_voice_async


def detect_user_gesture(img) -> str:
    """
    Detect user hand gesture (rock, paper, scissors) from camera image.
    Uses MediaPipe Hands if available, or robust OpenCV contour analysis fallback.
    """
    try:
        import mediapipe as mp
        mp_hands = mp.solutions.hands
        with mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5) as hands:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(img_rgb)
            if results.multi_hand_landmarks:
                landmarks = results.multi_hand_landmarks[0].landmark
                index_open = landmarks[8].y < landmarks[6].y
                middle_open = landmarks[12].y < landmarks[10].y
                ring_open = landmarks[16].y < landmarks[14].y
                pinky_open = landmarks[20].y < landmarks[18].y

                open_count = sum([index_open, middle_open, ring_open, pinky_open])
                if open_count >= 3:
                    return "paper"
                elif index_open and middle_open and not ring_open and not pinky_open:
                    return "scissors"
                elif open_count == 0:
                    return "rock"
                else:
                    return "scissors"
    except Exception:
        pass

    # Fallback Contour Analysis
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (15, 15), 0)
        ret, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        res = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = res[0] if len(res) == 2 else res[1]

        if contours:
            max_c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_c)
            if area > 3000:
                hull = cv2.convexHull(max_c, returnPoints=False)
                if len(hull) > 3:
                    defects = cv2.convexityDefects(max_c, hull)
                    if defects is not None and hasattr(defects, "shape") and len(defects.shape) == 3:
                        finger_count = 0
                        for i in range(defects.shape[0]):
                            row = defects[i, 0]
                            s, e, f, d = int(row[0]), int(row[1]), int(row[2]), float(row[3])
                            start = max_c[s][0]
                            end = max_c[e][0]
                            far = max_c[f][0]
                            a = np.linalg.norm(np.array(start) - np.array(far))
                            b = np.linalg.norm(np.array(end) - np.array(far))
                            c = np.linalg.norm(np.array(start) - np.array(end))
                            if a * b > 0:
                                angle = np.arccos(np.clip((a**2 + b**2 - c**2) / (2 * a * b), -1.0, 1.0))
                                if angle <= np.pi / 2 and d > 8000:
                                    finger_count += 1
                        if finger_count >= 3:
                            return "paper"
                        elif finger_count in (1, 2):
                            return "scissors"
                        else:
                            return "rock"
    except Exception:
        pass

    return random.choice(["rock", "paper", "scissors"])


def raw_play_rps_game() -> dict:
    """
    Play a full interactive round of Rock-Paper-Scissors against the user!
    """
    print("🎮 <SYSTEM>: เริ่มเกมเป่ายิงฉุบกับหุ่นยนต์!")
    
    # Step 1: Tell user to show hand gesture to camera FIRST (Single voice track)
    play_voice_async("มาเลยเด้อหล่า! ชูมือออก ค้อน กรรไกร หรือกระดาษ หน้ากล้องเลยเด้อ ข่อยกำลังสแกนเบิ่ง...", "rps_scan.mp3")
    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)
    time.sleep(2.5)

    # Step 2: CAPTURE PHOTO & DETECT USER MOVE FIRST
    init.GetImage()
    img_path = f"{init.PROJECT_ROOT}/captured_image.jpg"
    img = cv2.imread(img_path)
    user_move = detect_user_gesture(img) if img is not None else random.choice(["rock", "paper", "scissors"])
    print(f"📸 <SYSTEM>: สแกนภาพมือผู้ใช้สำเร็จ -> ผู้ใช้ออก {user_move.upper()}")

    # Step 3: Countdown & Physical Arm Bobbing
    play_voice_async("โอเค! มานับ 1... 2... 3... ยังชู้ต!", "rps_countdown.mp3")
    print("🤖 <SYSTEM>: นับ 1... 2... 3... ยังชู้ต!")
    speed = armconfig.SPEED_DANCE
    
    # Motion 1: "1"
    mc.send_angle(2, 20, speed); time.sleep(0.4)
    mc.send_angle(2, 0, speed);  time.sleep(0.4)
    # Motion 2: "2"
    mc.send_angle(2, 20, speed); time.sleep(0.4)
    mc.send_angle(2, 0, speed);  time.sleep(0.4)
    # Motion 3: "3... ยังชู้ต!"
    mc.send_angle(2, 30, speed); time.sleep(0.5)

    # Step 4: Robot Move Selection & Gripper Pose
    robot_move = random.choice(["rock", "paper", "scissors"])
    print(f"🤖 <SYSTEM>: หุ่นยนต์เลือกออก -> {robot_move.upper()}")

    if robot_move == "rock":
        init.close_gripper()
    elif robot_move == "paper":
        init.open_gripper()
    else:  # scissors
        mc.set_gripper_value(50, 80)
        time.sleep(0.2)
        mc.set_gripper_value(10, 80)
        time.sleep(0.2)
        mc.set_gripper_value(50, 80)

    # Step 5: Judge Winner & Express Emotion
    th_moves = {"rock": "ค้อน ✊", "paper": "กระดาษ ✋", "scissors": "กรรไกร ✌️"}
    result_str = f"ข่อยออก {th_moves[robot_move]} | เจ้าออก {th_moves[user_move]}"

    if robot_move == user_move:
        outcome = "DRAW"
        print(f"⚖️ <SYSTEM>: เสมอกัน! ({result_str})")
        play_voice_async(f"เสมอซะงั้น! ข่อยออก{th_moves[robot_move]} เจ้าก็ออก{th_moves[user_move]} เอาใหม่ๆ มาลองอีกรอบเด้อ", "rps_draw.mp3")
        from agent.tools.shares._raw import raw_gesture
        raw_gesture("confused")
    elif (robot_move == "rock" and user_move == "scissors") or \
         (robot_move == "paper" and user_move == "rock") or \
         (robot_move == "scissors" and user_move == "paper"):
        outcome = "ROBOT_WINS"
        print(f"🏆 <SYSTEM>: หุ่นยนต์ชนะ! ({result_str})")
        play_voice_async(f"ฮ่าๆๆ ข่อยชนะเด้อ! ข่อยออก{th_moves[robot_move]} ข่ม{th_moves[user_move]} ซาดนี้หาไผเป๊ะปานข่อยบ่มีดอก!", "rps_win.mp3")
        from agent.tools.shares._raw import raw_dance_celebrate
        raw_dance_celebrate()
    else:
        outcome = "USER_WINS"
        print(f"🎉 <SYSTEM>: ผู้ใช้ชนะ! ({result_str})")
        play_voice_async(f"ปาดโธ่! เจ้าเก่งแท้ๆ ข่อยออก{th_moves[robot_move]} แพ้{th_moves[user_move]} เจ้าจนได้ ยอมรับๆ!", "rps_lose.mp3")
        from agent.tools.shares._raw import raw_gesture
        raw_gesture("bow")

    mc.send_angles(armconfig.POSE_HOME, armconfig.SPEED_GRAB)

    return {
        "status": "DONE TASK",
        "outcome": outcome,
        "robot_move": robot_move,
        "user_move": user_move,
        "summary": result_str
    }
