# Design Rule 04: Components & States (องค์ประกอบและสถานะ)
> รวมแนวคิดจาก **Awesome Design Systems** (Consistency, States) และ **Magic UI** (Affordance, Premium Details)

---

## หลักการสำคัญ

ทุก Component ต้อง **สม่ำเสมอทั่วทั้งระบบ** (Awesome Design Systems) และ **สื่อสารชัดเจนว่าใช้งานได้** (Magic UI + Affordance)

---

## กฎข้อที่ 1: Component States (สถานะของทุก Component)
ทุก Interactive Element ต้องออกแบบให้ครบ **5 สถานะ**:

| State     | การแสดงผล                                            |
|-----------|------------------------------------------------------|
| Default   | สีและขนาดปกติ                                       |
| Hover     | สีเปลี่ยนเล็กน้อย (เข้มขึ้น ~10-15%) + cursor=hand2 |
| Active    | กด แล้วกดค้างอยู่ (สีเข้มกว่า Hover)                |
| Disabled  | สีจางลง (Muted Gray) + cursor=default, ไม่ตอบสนอง   |
| Focus     | เส้นขอบเด่นชัดขึ้น (Focus Ring) สำหรับ Input fields |

## กฎข้อที่ 2: Button Hierarchy (ลำดับความสำคัญของปุ่ม)
ตาม Awesome Design Systems — แต่ละหน้าควรมีปุ่ม **หนึ่งประเภทเป็นหลัก**:
- **Primary** (สำคัญที่สุด): พื้นสีดำ, ตัวอักษรขาว — ใช้สำหรับ Action หลัก เช่น SEND
- **Danger** (อันตราย): พื้นสีแดง, ตัวอักษรขาว — ใช้สำหรับ Destructive Action เช่น RESET
- **Outline/Ghost**: พื้นใส, มีเส้นขอบ — ใช้สำหรับ Secondary Actions

## กฎข้อที่ 3: Affordance (ความชัดเจนในการใช้งาน)
ตาม Magic UI + Awesome Design Systems — ทำให้ผู้ใช้รู้ทันทีว่าอะไรกดได้:
- ✅ ปุ่มทุกปุ่มต้องมี `cursor="hand2"` เมื่อ hover
- ✅ Input ต้องมีเส้นขอบชัดเจน (Border) เพื่อบอกว่า "พิมพ์ได้ที่นี่"
- ✅ Icon ควรมี Label กำกับเสมอ

## กฎข้อที่ 4: Consistent Radius (มุมโค้งมนที่สม่ำเสมอ)
ตาม Magic UI — ใช้ความโค้งมนที่คงที่ทั่วทั้งระบบ (ใน tkinter ใช้ `relief=SOLID` แทน `relief=FLAT` เพื่อให้เห็นขอบ):
- Cards: เส้นขอบบาง 1px, ไม่มี shadow หนัก
- Buttons: เส้นขอบตัด (No border-radius ใน tkinter แต่ใช้ flat/solid ให้สม่ำเสมอ)

## กฎข้อที่ 5: Micro-detail on Interactive Elements
ตาม Magic UI — เพิ่ม Depth ให้ปุ่ม Primary ด้วย:
- สีพื้นหลังที่มี Subtle gradient (เช่น จาก `#1E293B` ไป `#0F172A`)
- Hover state ที่เปลี่ยนสีอย่าง Smooth (แม้ใน tkinter จะเป็นการเปลี่ยนสีตรงๆ ก็ยังดีกว่าไม่มีเลย)

## การประยุกต์ใช้กับ ONE ARM
```python
# Button Pattern มาตรฐาน
btn = tk.Button(parent, text="SEND",
    bg=Theme.PRIMARY,        # #0F172A
    fg=Theme.PRIMARY_FG,     # #FFFFFF
    relief=tk.FLAT,
    cursor="hand2")
btn.bind("<Enter>", lambda e: e.widget.config(bg=Theme.PRIMARY_HOVER))
btn.bind("<Leave>", lambda e: e.widget.config(bg=Theme.PRIMARY))
```
