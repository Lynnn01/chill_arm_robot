# 02 - Domain Layer (Core Business Rules)

## บทบาทของ Domain Layer
Domain Layer คือหัวใจที่อยู่ตรงกลางสุดของระบบตามหลัก Clean Architecture 
กฎสูงสุดคือ **ห้ามอ้างอิงถึงเลเยอร์ใดๆ ทั้งสิ้น (Zero Dependencies)** ไม่ว่าจะเป็น Database ORM, Web Framework, หรือแม้แต่ Libraries ภายนอกที่ไม่จำเป็น โค้ดในชั้นนี้ควรใช้เพียง Standard Library ของตัวภาษาโปรแกรมนั้นๆ เท่านั้น

เพื่อการจัดระเบียบ Business Logic ให้ลึกซึ้งและไม่กระจัดกระจาย เราจะนำแนวคิดของ **Domain-Driven Design (DDD)** มาประยุกต์ใช้เป็นชุดเครื่องมือหลัก (Building Blocks) ดังนี้:

---

## ส่วนประกอบสำคัญ (DDD Building Blocks)

### 1. Entities
Entity คืออ็อบเจกต์ที่มี "ตัวตน (Identity)" ถึงแม้สถานะ (State/Data) ของมันจะเปลี่ยนไป เราก็ยังรู้ว่ามันคือตัวเดิมผ่าน ID
- **ตัวอย่าง:** `User` หรือ `Order` (คนเดิม แม้จะเปลี่ยนชื่อ)
- **พฤติกรรม (Behavior):** ใน Unified Architecture ห้ามสร้าง Entity แบบ Anemic (มีแค่ Getter/Setter ข้อมูลโง่ๆ) Entity ที่ดีต้องมี "พฤติกรรม" ฝังอยู่ เช่น ฟังก์ชัน `Order.cancel()` หรือ `User.changePassword()` เพื่อควบคุมไม่ให้ใครมาแก้ข้อมูลมั่วๆ

### 2. Aggregates & Aggregate Roots
เมื่อ Entity หรืออ็อบเจกต์บางตัวมีความสัมพันธ์กันอย่างแนบแน่น เราจะจัดกลุ่มมันไว้ด้วยกัน เรียกว่า "Aggregate"
- และในกลุ่มนั้น จะต้องมีตัวแทนเพียงหนึ่งเดียว เรียกว่า **"Aggregate Root"**
- **กฎเหล็ก:** โลกภายนอก (หรือ Database Repository) จะสั่งการ, แก้ไข, ดึงข้อมูล หรือลบ จะทำผ่าน Aggregate Root เท่านั้น ห้ามลัดคิวเข้าไปแก้ของข้างในโดยตรง
- **ตัวอย่าง:** `Order` เป็น Aggregate Root ส่วน `OrderItem` เป็นส่วนประกอบ ถ้าจะเพิ่มสินค้าลงออร์เดอร์ ต้องสั่งผ่าน `Order.addOrderItem(...)` ทำให้ `Order` คอยตรวจสอบราคารวมหรือโปรโมชั่นได้ครบถ้วน (ควบคุม Domain Invariants)

### 3. Value Objects
Value Object คืออ็อบเจกต์ที่ "ไม่มีตัวตน" เราดูความต่างของมันด้วย "ค่า (Value)" เท่านั้น (ถ้าค่าเท่ากัน ถือว่าเป็นตัวเดียวกันเป๊ะ)
- **ตัวอย่าง:** `Money (Currency, Amount)`, `Address (Street, City, ZipCode)`, `Email`
- **กฎเหล็ก (Immutable):** สร้างแล้วห้ามแก้ค่า หากจะแก้ให้ new instance ตัวใหม่ขึ้นมาแทน
- **ข้อดี:** ช่วย Validation ในตัวมันเอง (เช่น ถ้า `Email` ถูกสร้างขึ้นมาได้ แปลว่ามันผ่าน Format ถูกต้องแน่นอน) ช่วยลดการใช้ชนิดข้อมูลแบบ Primitive (String, Int) ที่เสี่ยงต่อความผิดพลาด

### 4. Domain Events
เมื่อมีบางสิ่งที่ "สำคัญมากๆ ในทางธุรกิจ" เกิดขึ้น (State เปลี่ยน) Aggregate สามารถผลิต "Event" ออกมาได้
- **ตัวอย่าง:** `UserRegisteredEvent`, `OrderShippedEvent`
- การใช้ Event ช่วยลดการผูกมัด (Decoupling) ตัวอย่างเช่น เมื่อ User สมัครเสร็จ เราไม่ต้องเขียนโค้ดส่งอีเมลต่อท้ายทันทีใน Aggregate แค่ปล่อย Event ออกมา แล้วปล่อยให้ Application Layer นำไปโยนให้ระบบแจ้งเตือน (Notification Module) ทำงานต่อเอง

### 5. Domain Exceptions / Errors
ถ้ามีการทำผิดกฎกติกาทางธุรกิจ (Business Rule Violation) ให้โยน Error ออกมาทันทีในชั้นนี้
- ให้สร้าง Custom Error ของธุรกิจเอง เช่น `InsufficientFundsException` หรือ `OrderAlreadyCancelledException`
- ห้ามไปโยน HTTP Status 400 Bad Request ในนี้เด็ดขาด (เพราะ Domain ไม่ควรรู้จักโลกของ Web)
