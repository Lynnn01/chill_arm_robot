# Design Rule 05: Motion & Interactions (การเคลื่อนไหวและการโต้ตอบ)
> รวมแนวคิดจาก **Awesome Design Systems** (Feedback, Responsiveness) และ **Magic UI** (Motion-First, Micro-interactions)

---

## หลักการสำคัญ

การเคลื่อนไหวต้อง **มีเหตุผลและสื่อสารสถานะ** (Awesome Design Systems) และ **ทำให้ UI รู้สึกมีชีวิตชีวา** (Magic UI)

---

## กฎข้อที่ 1: Purposeful Motion (เคลื่อนไหวอย่างมีความหมาย)
ทุกการเคลื่อนไหวต้องมีหน้าที่อย่างใดอย่างหนึ่งเท่านั้น:
- **Feedback**: บอกว่าระบบรับ Input แล้ว (เช่น ปุ่มเปลี่ยนสีตอนกด)
- **State Change**: บอกว่าสิ่งที่เห็นบนหน้าจอมีการเปลี่ยนแปลง (เช่น Log ข้อความใหม่เลื่อนเข้ามา)
- **Guidance**: ดึงสายตาไปยังส่วนที่สำคัญ

## กฎข้อที่ 2: Instant Feedback (ตอบสนองทันที)
ตาม Magic UI — ผู้ใช้ต้องได้รับ feedback ภายใน **100ms** หลังจากกระทำ:
- กดปุ่ม → สีเปลี่ยนทันที (Hover state)
- ส่งข้อความ → ปุ่ม SEND ต้อง Disabled ทันที พร้อม Text เปลี่ยน (ถ้าทำได้)
- หุ่นยนต์กำลังทำงาน → แสดงสัญลักษณ์ Loading ในพื้นที่ Log

## กฎข้อที่ 3: Stagger Animation (รายการที่เลื่อนเข้าทีละรายการ)
ตาม Magic UI Animated List — เมื่อข้อมูลใหม่เข้ามาใน Log:
- แสดงแบบ **เลื่อนจากล่างขึ้นบน** (Scroll into view) อัตโนมัติ
- ไม่แสดงข้อมูลหลายรายการพร้อมกันแบบกระตุก

## กฎข้อที่ 4: Duration & Easing (ระยะเวลาและความนุ่มนวล)
ตาม Awesome Design Systems:
- **Instant** (< 100ms): State changes เช่น Hover color
- **Fast** (150-200ms): Component transitions เช่น Tab switching
- **Medium** (300-400ms): Panel opening/closing
- ใช้ Ease-out สำหรับ Element ที่เข้ามา, Ease-in สำหรับ Element ที่ออกไป

## กฎข้อที่ 5: Loading States (สถานะกำลังโหลด)
ทั้งสองระบบเห็นตรงกัน — ห้ามให้ผู้ใช้เห็นหน้าจอนิ่งโดยไม่มีการตอบสนอง:
- **ปุ่ม SEND ขณะ AI กำลังตอบ**: ต้อง Disabled + อาจเปลี่ยน text เป็น "กำลังประมวลผล..."
- **ปุ่ม RESET ขณะหุ่นยนต์กำลังเคลื่อน**: ต้อง Disabled ทันที
- **Camera Offline**: แสดงข้อความแทน ไม่ใช่พื้นที่ว่างเปล่า

## การประยุกต์ใช้กับ ONE ARM
```python
# Pattern: Disable ทันทีเมื่อส่งคำสั่ง
def send_message(self, user_input):
    self.send_button.config(state=tk.DISABLED, bg=Theme.MUTED_FG)  # Instant feedback
    self.input_entry.config(state=tk.DISABLED)
    self.input_queue.put(user_input)

# Pattern: Auto-scroll ใน Log
self.log_text.see(tk.END)  # เลื่อนลงล่างสุดเสมอเมื่อมีข้อความใหม่
```
