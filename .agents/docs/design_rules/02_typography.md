# Design Rule 02: Typography (ระบบตัวอักษร)
> รวมแนวคิดจาก **Awesome Design Systems** (IBM Carbon, Shopify Polaris) และ **Magic UI**

---

## หลักการสำคัญ

Typography ที่ดีต้อง **อ่านง่ายและมีลำดับชั้น** (Awesome Design Systems) พร้อมกับ **สร้างความโดดเด่นด้วยขนาดและน้ำหนัก** (Magic UI)

---

## กฎข้อที่ 1: Type Scale (ลำดับขนาดตัวอักษร)
กำหนดขนาดที่ใช้เป็น Scale คงที่ ห้ามใช้ขนาดนอกจากนี้:

| ระดับ       | ขนาด  | น้ำหนัก | การใช้งาน                      |
|-------------|-------|---------|-------------------------------|
| Title       | 24px  | Bold    | ชื่อแอป, หัวข้อหน้าหลัก      |
| Heading 1   | 16px  | Bold    | หัวข้อ Section                |
| Heading 2   | 14px  | Bold    | หัวข้อ Card, Tab              |
| Body        | 12px  | Normal  | เนื้อหาทั่วไป                 |
| Body Bold   | 12px  | Bold    | Label, Strong emphasis         |
| Log         | 16px  | Normal  | ข้อความใน Chat / Log          |
| Small       | 10px  | Normal  | คำอธิบายเพิ่มเติม, Timestamp  |

## กฎข้อที่ 2: Font Family (แบบอักษร)
- ใช้ **Sans-serif** เท่านั้นสำหรับ UI (เช่น Tahoma, Inter, Segoe UI) — อ่านง่ายบนหน้าจอ
- ไม่ใช้ Font เกิน **1 ตระกูล** ในโปรเจกต์เดียวกัน เพื่อความสม่ำเสมอ

## กฎข้อที่ 3: Visual Hierarchy ด้วย Weight และ Color
ตาม Magic UI — แทนที่จะใช้ขนาดต่างกันมากๆ ให้ใช้ **น้ำหนัก (Weight)** และ **สี (Color)** เพื่อสร้างลำดับชั้น:
- หัวข้อ → Bold + สีดำเข้ม (`#0F172A`)
- เนื้อหา → Normal + สีดำเข้ม (`#0F172A`)
- ข้อความรอง → Normal + สีเทา (`#64748B`)

## กฎข้อที่ 4: Line Height (ความห่างระหว่างบรรทัด)
ตาม Awesome Design Systems:
- Body Text: Line Height = 1.5 เท่าของขนาดตัวอักษร
- Heading: Line Height = 1.2 - 1.3 เท่า

## กฎข้อที่ 5: Animated Text (ตัวอักษรที่มีชีวิต)
ตาม Magic UI — สำหรับหัวข้อหลักที่ต้องการเน้น สามารถเพิ่มเอฟเฟกต์ได้เล็กน้อย เช่น:
- Shimmer/Shine บน Heading ที่สำคัญ
- Gradient Text สำหรับชื่อแอปหรือ Title หลัก (เช่น "ONE ARM" ในสีดำ-เทาไล่ระดับ)

## การประยุกต์ใช้กับ ONE ARM
```python
# app/theme.py
FONT_TITLE     = ("Tahoma", 24, "bold")  # "ONE ARM" title
FONT_H1        = ("Tahoma", 16, "bold")  # Panel headings
FONT_H2        = ("Tahoma", 14, "bold")  # Tab headings
FONT_BODY      = ("Tahoma", 12)          # General text
FONT_BODY_BOLD = ("Tahoma", 12, "bold")  # Labels
FONT_LOG       = ("Tahoma", 16)          # Chat messages
FONT_SMALL     = ("Tahoma", 10)          # System messages
```
