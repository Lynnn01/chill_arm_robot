# CAT CAN'T STOCKS — UI Design Rules Index

กฎการออกแบบ UI ของโปรเจกต์นี้ รวมหลักการจาก **Awesome Design Systems**, **Magic UI** และ **Anthropics Frontend Design** เข้าไว้ด้วยกัน

---

## 📋 รายการกฎ

| ไฟล์ | หัวข้อ | แหล่งอ้างอิงหลัก |
|------|--------|-----------------|
| [01_color_system.md](01_color_system.md) | ระบบสี | Awesome DS + Magic UI |
| [02_typography.md](02_typography.md) | ระบบตัวอักษร | Awesome DS + Magic UI |
| [03_spacing_layout.md](03_spacing_layout.md) | ระยะห่างและการจัดวาง | Awesome DS + Magic UI (Bento) |
| [04_components_states.md](04_components_states.md) | องค์ประกอบและสถานะ | Awesome DS + Magic UI |
| [05_motion_interactions.md](05_motion_interactions.md) | การเคลื่อนไหวและการโต้ตอบ | Magic UI (Motion-First) |
| [06_visual_depth_aesthetics.md](06_visual_depth_aesthetics.md) | ความลึกและสุนทรียภาพ | Magic UI (Glassmorphism, Glow) |
| [07_accessibility_feedback.md](07_accessibility_feedback.md) | การเข้าถึงและการสื่อสาร | Awesome DS (A11y, WCAG) |
| [08_component_architecture.md](08_component_architecture.md) | โครงสร้าง Component | Awesome DS + Magic UI (Copy-Paste) |
| [09_anthropics_design_philosophy.md](09_anthropics_design_philosophy.md) | หลักการออกแบบ Anti-Generic | **Anthropics Frontend Design** ⭐ |

---

## ⚡ กฎสำคัญสูงสุด (Critical Rules)

1. **สีทุกตัวต้องมาจาก CSS Variables เท่านั้น** — ห้าม Hardcode สี (เช่น `bg-background`, `text-foreground`)
2. **1 ไฟล์ = 1 Component = 1 หน้าที่** — ห้ามรวม Logic ที่ไม่เกี่ยวข้องกัน
3. **ทุก Interactive Element ต้องมี Hover State** — `transition-colors` และ `hover:bg-foreground/5`
4. **ผู้ใช้ต้องรู้สถานะของระบบเสมอ** — Loading / Error / Empty States ต้องครบ
5. **Monochrome First** — สีเพิ่มเติมใช้ได้เฉพาะ Red/Green สำหรับ P/L เท่านั้น
6. **ออกแบบอย่างมีเจตนา** — ทุก Element ต้องมีเหตุผล ไม่ใช่ Decoration ([ดู Anthropics Philosophy](09_anthropics_design_philosophy.md))
