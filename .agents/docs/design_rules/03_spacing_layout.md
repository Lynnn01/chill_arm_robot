# Design Rule 03: Spacing & Layout (ระยะห่างและการจัดวาง)
> รวมแนวคิดจาก **Awesome Design Systems** (8pt Grid, Proximity) และ **Magic UI** (Bento Grid, Hero Sections)

---

## หลักการสำคัญ

Layout ที่ดีต้อง **เป็นระเบียบและคาดเดาได้** (Awesome Design Systems) พร้อมกับ **สร้างแรงกระแทกทางสายตา** (Magic UI)

---

## กฎข้อที่ 1: 8-Point Grid System (ระบบ Grid ฐาน 8)
ระยะห่างทุกอย่าง (padding, margin, gap) ต้องเป็นพหุคูณของ **8px**:

| ชื่อ    | ขนาด | การใช้งาน                              |
|---------|------|----------------------------------------|
| xs      | 4px  | ระยะห่างเล็กมาก (ภายใน badge)          |
| sm      | 8px  | ระยะห่างระหว่าง Label และ Value         |
| md      | 16px | Padding ภายใน Card                     |
| lg      | 24px | ระยะห่างระหว่าง Section                |
| xl      | 32px | Padding รอบ Panel หลัก                 |

## กฎข้อที่ 2: Bento Grid Layout (การจัดวางแบบ Bento)
ตาม Magic UI — แทนที่จะแสดงข้อมูลเป็น List แนวตั้งเพียงอย่างเดียว ให้ใช้กล่องหลายขนาดจัดเรียงบน Grid:
- กล่องขนาด **ใหญ่กว่า = ข้อมูลสำคัญกว่า**
- เหมาะสำหรับ Dashboard ที่แสดงหลาย Metric พร้อมกัน เช่น หน้า Control ของหุ่นยนต์

## กฎข้อที่ 3: Proximity (ความใกล้ชิดบอกความสัมพันธ์)
ตาม Awesome Design Systems:
- สิ่งที่ **เกี่ยวข้องกัน** ต้องอยู่ **ใกล้กัน** (เช่น Label: "X" ต้องอยู่ติดกับ Value ของ X)
- สิ่งที่ **ไม่เกี่ยวข้องกัน** ต้องมีพื้นที่ว่างแยก **ชัดเจน** (เช่น แบ่ง Section ด้วย Divider หรือ margin ≥ 24px)

## กฎข้อที่ 4: Card-Based Grouping (การรวมข้อมูลเป็นการ์ด)
ทั้งสองระบบเห็นตรงกัน — ใช้ "Card" (กล่องมีเส้นขอบบางๆ) เพื่อรวมข้อมูลที่เกี่ยวข้อง:
- Border: `1px solid #E2E8F0` (Subtle, ไม่ดึงความสนใจ)
- Background: White (`#FFFFFF`) หรือ Off-white (`#F8FAFC`) เพื่อแยกจาก Background หลัก
- Padding ภายใน Card: **16px** (md)

## กฎข้อที่ 5: Column Layout (การแบ่งคอลัมน์)
ตาม Magic UI Hero Pattern — แบ่งหน้าจอออกเป็น 2 ฝั่งที่มีสัดส่วนชัดเจน:
- **ฝั่งซ้าย (40%)**: ข้อมูล Live เช่น กล้อง, Dashboard
- **ฝั่งขวา (60%)**: การโต้ตอบ เช่น Chat Log, Input

## การประยุกต์ใช้กับ ONE ARM
```python
# ตัวอย่างการใช้ padx/pady ใน tkinter ให้ตรงกับ 8pt grid
self.grid(sticky="nsew", padx=(24, 16), pady=24)  # xl=24, lg=16
card.grid(padx=16, pady=16)                        # md=16
```
