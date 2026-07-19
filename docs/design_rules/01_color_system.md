# Design Rule 01: Color System (ระบบสี)
> รวมแนวคิดจาก **Awesome Design Systems** (IBM Carbon, Shopify Polaris, Google Material) และ **Magic UI**

---

## หลักการสำคัญ

ระบบสีที่ดีต้องทั้ง **มีระเบียบ** (Awesome Design Systems) และ **สร้างความประทับใจด้วยสายตา** (Magic UI) ไปพร้อมกัน

---

## กฎข้อที่ 1: Palette Structure (โครงสร้างชุดสี)
กำหนดสีไว้ใน **Single Source of Truth** (เช่น `app/theme.py`) เท่านั้น ห้าม hardcode hex color ในไฟล์ component

```
Primary    → สีหลักสำหรับ CTA และ Interactive elements
Secondary  → สีรองสำหรับ Supporting elements  
Neutral    → White/Gray/Black สำหรับ Background, Text, Border
Semantic   → Success (เขียว), Warning (เหลือง), Danger (แดง), Info (ฟ้า)
```

## กฎข้อที่ 2: White-First Approach (เน้นสีขาวเป็นหลัก)
ตาม Magic UI — พื้นหลังที่ขาวสะอาด (Pure White `#FFFFFF`) ทำให้ส่วนประกอบอื่นๆ โดดเด่นขึ้นโดยไม่ต้องแข่งกัน:
- **80%** White/Off-white สำหรับ Background, Surface
- **10%** Black/Dark Slate สำหรับ Text, Primary Actions
- **10%** Accent/Semantic สำหรับ States, Borders, Interactive

## กฎข้อที่ 3: Semantic Colors (สีที่มีความหมาย)
ตาม Awesome Design Systems — ทุก Semantic Color ต้องถูกใช้อย่างสม่ำเสมอทั่วทั้งระบบ:
- ❌ อย่าใช้สีแดงสำหรับอะไรก็ตามที่ไม่ใช่ Danger/Error
- ❌ อย่าใช้สีเขียวสำหรับอะไรก็ตามที่ไม่ใช่ Success

## กฎข้อที่ 4: Gradient as Accent (Gradient เป็นแค่ส่วนเสริม)
ตาม Magic UI — Gradient สามารถใช้เพื่อเพิ่มความพรีเมียมได้ แต่ต้องใช้อย่างระมัดระวัง:
- ✅ ใช้ Gradient ที่ปุ่ม Primary หรือ Header ที่ต้องการดึงดูดสายตา
- ❌ อย่าใช้ Gradient กับพื้นหลังหลักหรือข้อความ body

## กฎข้อที่ 5: Contrast Ratio (ความเปรียบต่าง)
ตาม WCAG ที่ Awesome Design Systems อ้างอิง:
- ข้อความ Body: Contrast Ratio ≥ 4.5:1
- ข้อความขนาดใหญ่ (Heading): ≥ 3:1

## การประยุกต์ใช้กับ ONE ARM
```python
# app/theme.py
BG = "#FFFFFF"        # 80% White
FG = "#0F172A"        # Near-black for text
PRIMARY = "#0F172A"   # Black for buttons
DANGER = "#EF4444"    # Red for RESET action
BORDER = "#E2E8F0"    # Subtle gray border
```
