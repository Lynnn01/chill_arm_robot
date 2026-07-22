# CAT CAN'T STOCKS — Documentation Index

ยินดีต้อนรับสู่ศูนย์กลางเอกสารคู่มือการพัฒนาโปรเจกต์ **CAT CAN'T STOCKS** เอกสารที่นี่ถูกแบ่งออกเป็น 2 หมวดหมู่หลัก ได้แก่ **คู่มือสถาปัตยกรรม (Architecture)** และ **คู่มือการออกแบบ (Design System)**

---

## 🏗️ 1. สถาปัตยกรรมซอฟต์แวร์ (Unified Architecture)
โฟลเดอร์: `unified-architecture/`
รวบรวมหลักการออกแบบโครงสร้างโปรแกรมที่ผสมผสานระหว่าง Clean Architecture และ Domain-Driven Design (DDD) เพื่อให้โค้ดทนทานต่อการเปลี่ยนแปลงและดูแลรักษาง่าย

| ไฟล์ | รายละเอียด |
|------|-----------|
| [01-architecture-overview.md](./unified-architecture/01-architecture-overview.md) | ภาพรวมสถาปัตยกรรม กฎ The Dependency Rule และการจัดโครงสร้างแบบ Vertical Slicing |
| [02-domain-layer.md](./unified-architecture/02-domain-layer.md) | แกนกลางธุรกิจ (Entities, Aggregates, Value Objects) ที่ไม่พึ่งพา Framework ใดๆ |
| [03-application-layer.md](./unified-architecture/03-application-layer.md) | ชั้นควบคุม Workflow การทำ CQRS (Command/Query) และการกำหนด Ports (Interfaces) |
| [04-infrastructure-layer.md](./unified-architecture/04-infrastructure-layer.md) | ชั้นเชื่อมต่อระบบภายนอก (Adapters, Database Repositories, External APIs) |
| [05-presentation-interface-layer.md](./unified-architecture/05-presentation-interface-layer.md) | ด่านหน้ารับ HTTP Request (Controllers, DTOs) และการจัดการ Error จากส่วนกลาง |
| [06-best-practices.md](./unified-architecture/06-best-practices.md) | แนวทางปฏิบัติที่ดี ห้ามทำ Anemic Domain และการเทสต์ระบบแบบเน้นพฤติกรรม |

---

## 🎨 2. ระบบการออกแบบ (Design Systems)
โฟลเดอร์: `design_systems/`
รวบรวมกฎเกณฑ์การออกแบบ UI ที่ล้ำสมัย (Modern & Minimal) ผสมผสานหลักการแบบ Anti-Generic และความพรีเมียมจาก Magic UI

| ไฟล์ | รายละเอียด |
|------|-----------|
| [01_color_system.md](./design_systems/01_color_system.md) | ระบบสี Monochrome การใช้สีเพื่อสื่อความหมาย (เขียว/แดง) และ Gradients |
| [02_typography.md](./design_systems/02_typography.md) | การใช้ฟอนต์ Inter, ลำดับชั้นความสำคัญตัวอักษร และการใช้ Tabular Nums สำหรับตัวเลข |
| [03_spacing_and_layout.md](./design_systems/03_spacing_and_layout.md) | ระบบ Grid (4px/8px), การจัดวางแบบ Bento Box และการใช้พื้นที่ว่าง (Whitespace) |
| [04_components_and_states.md](./design_systems/04_components_and_states.md) | สถานะโต้ตอบ (Hover, Active), หน้า Loading (Skeleton) และหน้าว่าง (Empty States) |
| [05_motion_and_animations.md](./design_systems/05_motion_and_animations.md) | การขยับอย่างมีความหมาย, การให้ของโผล่ทีละชิ้น (Stagger), และ Micro-interactions |
| [06_visual_depth_and_aesthetics.md](./design_systems/06_visual_depth_and_aesthetics.md) | การสร้างมิติภาพด้วยกระจกฝ้า (Glassmorphism) และเทคนิคแสงเงา (Drop Shadows/Glow) |
| [07_accessibility_and_feedback.md](./design_systems/07_accessibility_and_feedback.md) | ความคมชัด (Contrast), การรองรับคีย์บอร์ด, และการตอบกลับผู้ใช้ (Toasts) |
| [08_component_architecture.md](./design_systems/08_component_architecture.md) | โครงสร้าง Component ตามปรัชญา Copy-Paste และการสร้าง Component ที่ยืดหยุ่น |
| [09_design_philosophy.md](./design_systems/09_design_philosophy.md) | ปรัชญา Anti-Generic ที่เน้นให้ "ข้อมูลคือพระเอก" และการออกแบบระดับมืออาชีพ |
| [INDEX.md](./design_systems/INDEX.md) | ดัชนีเจาะลึกเฉพาะหมวด Design Systems และเช็คลิสต์กฎเหล็ก UI ก่อนเขียนโค้ด |
