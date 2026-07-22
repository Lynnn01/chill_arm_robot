# 03 - Application Layer (Use Cases & Workflows)

## บทบาทของ Application Layer
Application Layer คือ "ผู้ควบคุมวงจรการทำงาน (Orchestrator)" ของ Use Cases ทั้งหมดในระบบ เลเยอร์นี้จะไม่คิดคำนวณ Business Logic ด้วยตัวเอง แต่จะรับหน้าที่จัดเตรียมข้อมูลเพื่อไปสั่งให้ Domain Layer เป็นคนจัดการ

**กฎความสัมพันธ์ (Dependencies):**
- ✅ รู้จัก Domain Layer สามารถเรียกใช้ Entity และ Value Objects ได้
- ❌ ห้ามรู้จัก Infrastructure Layer โดยตรง (เช่น ห้ามใช้ ORM ห้ามดึง SDK ภายนอกมาใช้)
- ❌ ห้ามรู้จัก Presentation Layer (ห้ามพูดถึง HTTP หรือ Web API)

เพื่อรักษาความสะอาด Application Layer จึงนำแนวคิด **Ports (Interfaces)** จาก Hexagonal Architecture และ **CQRS** มาใช้ในการจัดการ

---

## 1. CQRS (Command & Query Responsibility Segregation)
แบ่ง Use Cases ของระบบออกเป็น 2 สายอย่างชัดเจน (มักจะใช้ร่วมกับ Pattern Mediator เช่น `MediatR` ใน .NET หรือ EventBus ในภาษาอื่นๆ):

- **Commands (คำสั่งเปลี่ยนแปลงข้อมูล):**
  - เช่น `CreateOrderCommand`, `UpdateUserProfileCommand`
  - ก่อให้เกิดการเปลี่ยน State หรืออัปเดต Database
  - ไม่ควร Return ข้อมูลเยอะๆ ออกมา (มักจะตอบแค่ Success, หรือ ID ของสิ่งที่ถูกสร้างใหม่)

- **Queries (คำสั่งอ่านข้อมูล):**
  - เช่น `GetOrderDetailsQuery`, `ListUsersQuery`
  - ใช้ดึงข้อมูลอย่างเดียว ไม่มีผลกระทบ (Side-effects) ต่อระบบเด็ดขาด
  - **เคล็ดลับ:** ในฝั่ง Query เราอาจจะไม่ต้องแปลงจาก DB เป็น Domain Entity ก็ได้ สามารถใช้ตัวอ่านข้อมูลเร็วๆ ดึงออกมาเป็น DTO เลยเพื่อความรวดเร็ว

## 2. Ports (Interfaces / Contracts)
นี่คือวิธีการตัดขาดระบบจาก Database ตามหลัก Hexagonal 
- เราจะสร้าง Interface หรือ "เต้ารับ" เตรียมไว้ใน Application Layer ตัวอย่างเช่น `IOrderRepository` (ใน .NET/Java) หรือ `OrderRepositoryPort` (ใน TS)
- Interface นี้กำหนดแค่ฟังก์ชัน เช่น `Save(Order order)`, `FindById(id)`
- Application Layer จะใช้งาน Interface นี้เท่านั้น! ส่วนใครจะเป็นคนเขียนโค้ดต่อ DB จริงๆ (ปลั๊ก) จะเป็นหน้าที่ของ Infrastructure Layer 

## 3. Cross-Cutting Concerns (Pipeline Behaviors / Middlewares)
เมื่อ Use Case วิ่งเข้ามา ก่อนจะไปถึงโค้ดหลัก (Handler) Application Layer สามารถฝังตัวดักจับ (Interceptors / Pipelines) ไว้เพื่อทำงานครอบจักรวาลได้:
1. **Validation:** เช็คความถูกต้องของ Command เบื้องต้น เช่น ชื่อห้ามเว้นว่าง (ผ่าน FluentValidation หรือไลบรารีคล้ายกัน) ถ้าไม่ผ่านก็โยน Validation Error กลับไปทันที
2. **Logging:** บันทึกว่าระบบกำลังเรียกใช้ Use Case ใด ใช้เวลาไปเท่าไหร่
3. **Authorization:** ตรวจสอบว่าสิทธิ์ผู้ใช้นี้สามารถทำคำสั่งนี้ได้หรือไม่

> **สรุปการไหลของงานในเลเยอร์นี้:**
> รับ Command -> ตรวจสอบ (Validate) -> สั่ง Repository (ผ่าน Interface) ให้ดึง Entity เก่ามา -> สั่งรันคำสั่งใน Entity (Business Rule) -> สั่ง Repository เซฟ Entity กลับไป -> (เสริม: ปล่อย Domain Events ถ้ามี)
