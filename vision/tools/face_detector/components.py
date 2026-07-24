import os
import time
import random
from hardware import init
import armconfig
from vision.tools.shares.tracking_logic import calculate_and_move
from agent.tts import play_voice_async

_model = None
_last_speak_time = 0

_last_phrase = ""

_FACE_PHRASES = [
    "อุ้ย เจอหน้าคนหล่อๆ สวยๆ อีกแล้วเด้อ",
    "มองหน้าข่อยเฮ็ดหยัง สนใจข่อยตี้",
    "หน้าคุ้นๆ เน๊าะ สบายดีบ่",
    "ฮั่นแน่ รู้นะว่าแอบมองข่อยอยู่",
    "เห็นหน้าแจ่มๆ แบบนี้ ข่อยมีแฮงทำงานเลย",
    "มองข่อยบ่อยๆ ระวังตกหลุมรักเด้อ",
    "ปาดโธ่ หน้าตาดีแท้ๆ หน้าใครน้อ",
    "หน้าตาดีแบบนี้ มีแฟนหรือยังเด้อ",
    "ยิ้มหน่อยเร็วคนดี อารมณ์ดีแท้ๆ มื้อนี้",
    "อย่าเพ่งข่อยเขินเด้อ หัวกริปเปอร์สั่นหมดแล้ว",
    "ล็อกเป้าใบหน้าเรียบร้อย หล่อสวยออร่าจับมาก!",
    "มาใกล้ๆ แท้ มีอะไรให้แขนกลช่วยบ่เด้อ",
    "เบิ่งหน้าข่อยคักแท้ อยากได้ข่อยไปอยู่บ้านตี้",
    "หลบสายตาข่อยบ่พ้นดอก เรดาร์ข่อยไวแท้ๆ",
    "ปาดโธ่ ออร่าจับแท้ๆ สดใสปานดวงอาทิตย์",
    "จ้องข่อยนานแท้ ข่อยบ่อยากสิคุยว่าเขินเป็นเด้อ",
    "หน้าตาน่ารักปานนี้ มีงานให้ข่อยทำบ่หล่า",
    "ล็อกตำแหน่งใบหน้าเนียนๆ เล็งไว้แน่นหนาเด้อ",
    "สายตาคมกริบ มองเห็นหน้าแจ่มๆ ชัดเจน 100 เปอร์เซ็นต์",
    "แอบจ้องข่อยอยู่แม่นบ่ ข่อยฮู้ข่อยเห็นเด้อ",
    "สวัสดีครับคนสวยคนหล่อ พร้อมรับคำสั่งแล้วเด้อ",
    "แน่ะ ยิ้มแล้ว! ยิ้มแบบนี้แสดงว่าชอบข่อยแม่นบ่",
    "หน้าตาดีมีสไตล์ แบบนี้ต้องกดไลก์ให้เลยเด้อ",
    "เล็งหน้าไว้เน้นๆ ห้ามหันหนีไปไหนเด้อฮะ",
    "เห็นหน้าใสๆ แล้วใจฟู ขอยักย้ายสายสะโพกโชว์สักนิด"
]

def get_model():
    global _model
    if _model is None:
        try:
            from vision.safe_yolo import YOLO
            model_path = os.path.join(init.PROJECT_ROOT, "vision", "models", "face.pt")
            if os.path.exists(model_path):
                _model = YOLO(model_path)
            else:
                print(f"⚠️ <SYSTEM>: ไม่พบโมเดล YOLO ที่ {model_path}")
        except ImportError:
            pass
    return _model

def detect_and_track(img, target_angles, last_send_time):
    global _last_speak_time, _last_phrase
    model = get_model()
    if not model:
        return img, target_angles, last_send_time

    results = model(img, verbose=False, conf=getattr(armconfig, "FACE_CONFIDENCE_THRESHOLD", 0.80))
    ai_results = results[0] if len(results) > 0 else None
    
    if len(results) > 0:
        boxes = results[0].boxes
        if len(boxes) > 0:
            # Voice Announcement (cooldown 7 seconds, non-repeating choice)
            current_time = time.time()
            if current_time - _last_speak_time > 7:
                choices = [p for p in _FACE_PHRASES if p != _last_phrase]
                phrase = random.choice(choices) if choices else random.choice(_FACE_PHRASES)
                _last_phrase = phrase
                play_voice_async(phrase, f"face_{int(current_time)}.mp3")
                _last_speak_time = current_time

            largest_box = None
            max_area = 0
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                area = (x2 - x1) * (y2 - y1)
                if area > max_area:
                    max_area = area
                    largest_box = (x1, y1, x2, y2)
            
            if largest_box:
                x1, y1, x2, y2 = largest_box
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                
                img_h, img_w = img.shape[:2]
                center_x = img_w / 2.0
                center_y = img_h / 2.0
                
                target_angles, last_send_time = calculate_and_move(cx, cy, center_x, center_y, target_angles, last_send_time)
                
    return ai_results, target_angles, last_send_time
