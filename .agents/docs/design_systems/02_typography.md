# 02 - Typography (Inter / Modern Sans-Serif)

## 1. Typeface Choice
- **Font หลัก:** แนะนำให้ใช้ Font ที่อ่านง่ายและมีความเป็น Modern Geometric เช่น **Inter**, **Geist**, หรือ **Roboto**
- ไม่ควรผสม Font หลายชนิดเกินไป (ไม่ควรเกิน 2 ชนิด: หนึ่งสำหรับ Heading และอีกหนึ่งสำหรับ Body)

## 2. Type Hierarchy (ลำดับชั้นของตัวอักษร)
- **Headings (H1, H2):** ตัวใหญ่, น้ำหนักหนา (Bold / Semibold), และระยะห่างตัวอักษรติดกัน (Tighter tracking/letter-spacing) เช่น `tracking-tight`
- **Body Text:** น้ำหนักปกติ (Regular), เน้นความอ่านง่ายในย่อหน้ายาวๆ
- **Labels / Metadata:** ขนาดเล็ก (Text-sm หรือ Text-xs), ใช้น้ำหนัก Medium และอาจเพิ่มระยะห่างตัวอักษร (Wide tracking) เพื่อความพรีเมียม และมักจะใช้ตัวพิมพ์ใหญ่ (Uppercase) เช่น `uppercase tracking-wider text-foreground/50`

## 3. Contrast by Weight and Opacity
- แทนที่จะเปลี่ยนขนาดตัวอักษรตลอดเวลา ให้สร้างความแตกต่างด้วย **น้ำหนัก (Weight)** และ **ความโปร่งใส (Opacity)**
- เช่น ข้อมูลหลักใช้ `font-medium text-foreground` ส่วนข้อมูลรองใช้ `text-sm text-foreground/60` (ไม่ต้องเปลี่ยนสีเทา แต่ใช้ Opacity ของสีหลักแทน)

## 4. Tabular Nums (ตัวเลขในระบบการเงิน)
- สำหรับแอปพลิเคชันที่มีตัวเลขเยอะ (เช่น Portfolios, Trading) **ต้องเปิดใช้ Tabular Nums** (`tabular-nums` ใน Tailwind)
- เพื่อให้ความกว้างของตัวเลขทุกตัว (0-9) เท่ากัน ทำให้เวลาแสดงตัวเลขในตาราง หรือตอนตัวเลขเปลี่ยนค่า (Animation) ข้อความจะไม่กระตุกหรือขยับไปมา
