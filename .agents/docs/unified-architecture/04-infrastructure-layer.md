# 04 - Infrastructure Layer (The Concrete Implementations)

## บทบาทของ Infrastructure Layer
Infrastructure Layer คือเลเยอร์ที่เป็น "รูปธรรม (Concrete)" ที่สุดในระบบ เป็นที่เดียวที่อนุญาตให้มีโค้ดต่อกับฐานข้อมูล, เรียกใช้ HTTP Client เพื่อยิง API ชาวบ้าน, หรือต่อกับ File System

**กฎความสัมพันธ์ (Dependencies):**
- เลเยอร์นี้จะเป็นฝ่ายวิ่งเข้าไปหา (Depend on) Application Layer เพื่อขอนำ "Interfaces / Ports" ที่กำหนดไว้ มาเขียนโค้ดการทำงานจริงๆ (Implementation)
- เลเยอร์นี้ห้ามเอา Logic การคำนวณทางธุรกิจมาเขียนเด็ดขาด (เพราะนั่นเป็นหน้าที่ของ Domain)

---

## 1. Adapters (ปลั๊กเชื่อมต่อ)
ตามหลัก Hexagonal, Adapter คือคลาสที่รับหน้าที่แปลงโลกภายนอกให้เข้ากับโลกภายใน
- สมมติว่า Application Layer มี Port ชื่อ `IEmailSender`
- ใน Infrastructure Layer เราจะสร้าง Adapter ชื่อ `SendGridEmailService` หรือ `MailchimpEmailService` ที่สืบทอด (Implement) จาก `IEmailSender` 
- การใช้ Dependency Injection (DI) คอยสลับปลั๊กพวกนี้ตอนโปรแกรมรัน จะทำให้ระบบยืดหยุ่นสูงสุด สมมติวันนึงต้องเปลี่ยนผู้ให้บริการอีเมล ก็แค่เปลี่ยน Adapter ปลั๊กตัวใหม่ โดยที่ Application ไม่รู้ตัวเลย

## 2. Repositories และ Data Models
ในระบบ Enterprise แบบ DDD เราจะแยก "อ็อบเจกต์ของธุรกิจ" กับ "อ็อบเจกต์ของฐานข้อมูล" ออกจากกันอย่างชัดเจน:
- **Persistence Models / Data Models:** โครงสร้างตารางใน Database (เช่น TypeORM Entity, EF Core Model, Prisma Schema) ซึ่งจะมีหน้าตาแบบตารางเป๊ะๆ
- **Repository Pattern:** คือ Adapter ตัวเชื่อมต่อฐานข้อมูล โดย Repository จะรับค่าเป็น Domain Entity ล้วนๆ -> จากนั้นแปลงเป็น Data Model -> ใช้ ORM เซฟลง Database
- **ขาอ่านกลับ:** ดึง Data Model จาก ORM -> แปลงร่างกลับเป็น Domain Entity -> ส่งกลับไปให้ Application Layer

*หมายเหตุ: ในโปรเจกต์ .NET ที่ใช้ EF Core บ่อยครั้งที่ชุมชนจะอนุโลมให้ใช้ Domain Entity เป็นตัว Map เข้า Database ไปเลยเพื่อลดความซ้ำซ้อน (Pragmatic approach) แต่ถ้าจะยึดหลัก Hexagonal แท้ๆ ต้องแยกกัน 100%*

## 3. External API Clients & Other Services
นอกจากฐานข้อมูลแล้ว การเรียกใช้ Web Services ของบุคคลที่สาม (เช่น Payment Gateway, Google Maps API) หรือการเชื่อมต่อกับ Message Broker (Kafka, RabbitMQ) ก็จะถูกรวบรวมไว้ที่เลเยอร์นี้ทั้งหมด

## 4. กลไกการเผยแพร่ Domain Events (Event Dispatching)
บ่อยครั้งที่เราเลือกที่จะปล่อย (Dispatch) Domain Events ในเลเยอร์ Infrastructure 
- เช่น ใน EF Core เราดักการทำงานก่อน `SaveChanges` เพื่อกวาดเอา Domain Events ทั้งหมดที่มีอยู่ใน Entity ออกมา 
- จากนั้นใช้ Mediator ส่ง Event เหล่านี้ไปยัง Application Layer ให้ดำเนินการต่อ (เช่น ส่งอีเมลหลังเซฟออร์เดอร์ลงฐานข้อมูลสำเร็จ)
