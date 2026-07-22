# 04 - Components & States

## 1. Interactive States (สถานะการโต้ตอบ)
ส่วนที่ผู้ใช้กดได้ (Buttons, Links, Cards) **ต้องมี Feedback สถานะเสมอ**:
- **Hover:** เมื่อเมาส์ชี้ ควรมีการสว่างขึ้นหรือมืดลงเล็กน้อย (ใช้ `transition-colors duration-200` คู่กับ `hover:bg-foreground/5` หรือ `hover:bg-white/10`)
- **Active / Pressed:** เวลากดคลิก ควรมีความรู้สึกว่าปุ่มยุบลง (ใช้ `active:scale-95` หรือเพิ่มความเข้มของ Background)
- **Disabled:** สีเทาจางลง อ่อนลง (`opacity-50`) และต้องใช้เคอร์เซอร์แบบ `cursor-not-allowed`

## 2. Skeleton / Loading / Empty States
- อย่าปล่อยให้ผู้ใช้มองหน้าจอว่างเปล่าตอนดึงข้อมูล
- **Loading:** ใช้ Skeleton Loader (กล่องสีเทากะพริบ) ที่มีรูปทรงตรงกับข้อมูลที่จะโหลดมา หรือใช้ Spinner เล็กๆ
- **Empty State:** ถ้าไม่มีข้อมูล (ตารางว่าง) อย่าโชว์แค่ข้อความโง่ๆ ให้มีกล่องที่ตกแต่งด้วย Icon สีจางๆ และปุ่ม Call to Action ชวนให้เริ่มสร้างข้อมูลแรก
- **Error State:** แสดงข้อความขออภัยแบบสุภาพ พร้อมปุ่ม "ลองใหม่ (Retry)" 

## 3. High Fidelity UI Elements
สร้างความรู้สึก "พรีเมียม" ด้วยองค์ประกอบเหล่านี้:
- **Subtle Borders:** เส้นขอบที่บางและจางมากๆ (เช่น `border border-white/10`)
- **Glow Effects:** ถ้าเป็นปุ่ม Primary อาจจะมีเอฟเฟกต์แสงเรืองรอง (Glow shadow) ออกมาจากใต้ปุ่ม เพื่อดึงดูดสายตา 
- **Pills / Badges:** ป้ายกำกับเล็กๆ มุมขอบมนสุดๆ (`rounded-full`) สีพื้นหลังจางๆ และสีตัวอักษรเข้มๆ เพื่อแยกแยะหมวดหมู่
