# 06 - Visual Depth & Aesthetics (Glassmorphism & Glow)

## 1. Glassmorphism & Translucency
สร้าง "ความลึก (Depth)" ในหน้าจอด้วยเทคนิคกระจกฝ้า (Glassmorphism)
- แทนที่จะใช้สีพื้นหลังทึบตัน (Solid Background) บน Modal หรือ Top Navigation ให้ใช้พื้นหลังแบบโปร่งแสง (เช่น `bg-background/80`)
- คู่กับการเบลอภาพพื้นหลัง `backdrop-blur-md` 
- ช่วยให้ผู้ใช้รู้สึกถึงลำดับชั้น (Layering) ว่า Modal นี้กำลังลอยทับเนื้อหาด้านหลังอยู่จริงๆ 

## 2. Elevating with Shadows and Glows
- **Drop Shadows แบบนุ่มลึก:** เงาไม่ควรดำปี๋และแข็งกระด้าง (Avoid heavy black box shadows) ควรใช้เงาที่กว้าง นุ่ม และจางมากๆ (เช่น `shadow-2xl` ผสมกับ `shadow-foreground/5`)
- **Glow Effects:** ใน Dark mode การใช้เงาจะไม่ค่อยเห็นผล เปลี่ยนมาใช้แสงเรืองรอง (Glow) แทน เช่น การกระจายแสงสี Accent เบาๆ ออกมาจากใต้ปุ่มหรือกล่องการ์ดที่สำคัญ

## 3. Subtlety is Key (ความแยบยลคือสิ่งสำคัญ)
- เอฟเฟกต์แสงเงาและกระจก ต้องใช้ **อย่างประหยัดและพอดี**
- ถ้าทุกจุดในแอปพลิเคชันสะท้อนแสงและเบลอไปหมด มันจะกลายเป็นแอปที่รกและแย่งสายตา
- สงวนเทคนิคที่เตะตามากๆ ไว้สำหรับปุ่มหลัก (Primary Button), แจ้งเตือนสำคัญ (Toasts) หรือกล่องราคา (Pricing Plans) เท่านั้น
