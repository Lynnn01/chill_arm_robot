# CAT CAN'T STOCKS — Unified Design Systems Index

นี่คือดัชนีรวมกฎการออกแบบและสไตล์ไกด์ของโปรเจกต์ ซึ่งเกิดจากการหลอมรวม (Merge) ระหว่าง **Design Rules**, **Magic UI Principles** และ **Awesome Design Systems** เข้าไว้ด้วยกัน เพื่อให้เป็นแหล่งอ้างอิงเดียวที่สมบูรณ์ที่สุด (Single Source of Truth)

---

## 📚 สารบัญคู่มือการออกแบบ (Design Guidelines)

| ไฟล์ | หัวข้อหลักที่ครอบคลุม |
|------|-----------------|
| [01_color_system.md](01_color_system.md) | กฎการใช้สี Monochrome, การใช้สีสื่อความหมาย (Red/Green), High Fidelity Gradients |
| [02_typography.md](02_typography.md) | ฟอนต์หลัก (Inter), ลำดับชั้น, Contrast ด้วยน้ำหนักและ Opacity, Tabular Nums สำหรับตัวเลข |
| [03_spacing_and_layout.md](03_spacing_and_layout.md) | ระบบ Grid (4px/8px), กลยุทธ์การจัดเรียงแบบ Bento Box, การใช้พื้นที่ว่าง (Whitespace) |
| [04_components_and_states.md](04_components_and_states.md) | สถานะของ UI (Hover, Active), Skeleton Loading, Empty States, ขอบมน และ Glow |
| [05_motion_and_animations.md](05_motion_and_animations.md) | อนิเมชันที่มีความหมาย, Staggered entries (การทยอยปรากฏ), Micro-interactions |
| [06_visual_depth_and_aesthetics.md](06_visual_depth_and_aesthetics.md) | กระจกฝ้า (Glassmorphism), การสร้างมิติด้วย Drop Shadows ที่นุ่มลึก |
| [07_accessibility_and_feedback.md](07_accessibility_and_feedback.md) | Contrast ที่ผ่านมาตรฐาน, Keyboard Focus, การแจ้งเตือนผู้ใช้ (Toasts / Feedback) |
| [08_component_architecture.md](08_component_architecture.md) | ปรัชญา Copy & Paste (shadcn), การสร้าง Component ย่อยที่ทำงานจบในตัว (Self-contained) |
| [09_design_philosophy.md](09_design_philosophy.md) | ปรัชญา Anti-Generic, ความตั้งใจ, การยกย่องข้อมูล (Data as the Hero) |

---

## 🚦 กฎเหล็กที่ห้ามละเมิดเด็ดขาด (Critical Rules Checklist)
ก่อนจะ Push โค้ดหรือสร้าง UI ใหม่ ต้องผ่านเกณฑ์เหล่านี้:
- [ ] ใช้ **CSS Variables** แทนการ Fix โค้ดสี (เช่น ใช้ `bg-background` ห้ามใช้ `#ffffff`)
- [ ] ปุ่มกดหรือสิ่งโต้ตอบได้ ต้องใส่ `transition-colors` และสถานะ `hover` เสมอ
- [ ] เวลาโหลดข้อมูล ต้องมีหน้า Loading (Skeleton/Spinner) 
- [ ] เวลาตารางหรือลิสต์ว่างเปล่า ต้องมี Empty State สวยๆ โผล่มาเสมอ ไม่ใช่โชว์หน้าขาวๆ
- [ ] ตัวเลขผลกำไรขาดทุน ต้องใช้ฟอนต์แบบความกว้างเท่ากัน (Tabular Nums)
- [ ] หากต้องการเพิ่มรูปทรงใหม่ ให้ใช้ขอบมน (Rounded Corners) ตามสไตล์ภาพรวมของโปรเจกต์
