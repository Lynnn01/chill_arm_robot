# Design Rule 08: Component Architecture (โครงสร้างและการจัดระเบียบ Component)
> รวมแนวคิดจาก **Awesome Design Systems** (Scalability, Reusability) และ **Magic UI** (Copy-Paste Philosophy, Independence)

---

## หลักการสำคัญ

โค้ด UI ที่ดีต้อง **แก้ไขได้ในจุดเดียว** (Awesome Design Systems) และ **แต่ละ Component ต้องยืนหยัดด้วยตัวเอง** (Magic UI)

---

## กฎข้อที่ 1: Single Source of Truth (แหล่งข้อมูลเดียว)
ตาม Awesome Design Systems + Magic UI — ค่าคงที่ทั้งหมดต้องอยู่ที่เดียว:
- ✅ สี, Font, Spacing ทั้งหมดอยู่ใน `app/theme.py`
- ❌ ห้าม Hardcode `"#0F172A"` หรือ `("Tahoma", 12)` ตรงๆ ในไฟล์ Component ใดๆ

## กฎข้อที่ 2: One File = One Responsibility (1 ไฟล์ = 1 หน้าที่)
ตาม Magic UI Copy-Paste Philosophy:
```
app/
├── theme.py              # ระบบสีและ Font (1 หน้าที่)
└── components/
    ├── camera_view.py    # แสดงภาพกล้อง (1 หน้าที่)
    ├── dashboard_tab.py  # แสดง Status หุ่นยนต์ (1 หน้าที่)
    ├── calibration_tab.py # ตั้งค่า Offset (1 หน้าที่)
    ├── memory_tab.py     # แสดง Memory (1 หน้าที่)
    ├── left_panel.py     # รวม Component ฝั่งซ้าย (1 หน้าที่)
    └── right_panel.py    # Chat Interface (1 หน้าที่)
```

## กฎข้อที่ 3: Props/Dependency Injection (ส่งค่าแทนการ Import ตรง)
ตาม Awesome Design Systems:
- ✅ ส่ง `log_queue` เป็น parameter เข้า Component แทนการ Import Global Variable
- ✅ ส่ง Callback function เข้าไปแทนการอ้างอิง Parent โดยตรง
- การทำเช่นนี้ทำให้ Component แต่ละตัว Test แยกกันได้ง่ายขึ้น

## กฎข้อที่ 4: No Circular Dependencies (ห้ามพึ่งพาวนเวียน)
ตาม Awesome Design Systems:
- ✅ `camera_view.py` สามารถ import `theme.py` ได้
- ❌ `camera_view.py` ห้าม import `left_panel.py` (เพราะ `left_panel.py` import `camera_view.py` อยู่แล้ว)

## กฎข้อที่ 5: Graceful Degradation (ทำงานได้แม้ขาด Resource)
ตาม Awesome Design Systems + โปรเจกต์นี้โดยเฉพาะ:
- กล้องไม่มี → แสดง "Camera Offline" ไม่ใช่ Error crash
- ไม่มี Hardware → ทำงานใน Mock Mode ต่อไปได้
- ไม่มี Network → แสดงข้อความ Error ที่อ่านเข้าใจได้

## การประยุกต์ใช้กับ ONE ARM
```python
# ✅ ถูกต้อง: ใช้ค่าจาก Theme เสมอ
from app.theme import Theme
btn = tk.Button(parent, bg=Theme.PRIMARY, fg=Theme.PRIMARY_FG)

# ❌ ไม่ถูกต้อง: Hardcode สีตรงๆ
btn = tk.Button(parent, bg="#0F172A", fg="#FFFFFF")
```
