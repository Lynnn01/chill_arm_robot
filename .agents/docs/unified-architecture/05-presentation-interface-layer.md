# 05 - Presentation / Interface Layer (The Gateway)

## บทบาทของ Presentation Layer
Presentation Layer (หรือบางสำนักเรียกว่า Web API / Interface Adapters / UI) คือ "ประตูหน้าบ้าน" ที่คอยรับแขก (Requests) จากระบบอื่นๆ หรือจากผู้ใช้โดยตรง
- ทำหน้าที่แค่ **รับข้อมูลเข้ามา และ ส่งข้อมูลกลับออกไป**
- หน้าที่ของมันบางเบามาก (Thin Layer) และต้องไม่มี Business Logic ใดๆ แอบซ่อนอยู่เด็ดขาด!
- ตามกฎ Dependency Rule, เลเยอร์นี้จะวิ่งเข้าไปเรียกใช้ Application Layer เพื่อฝากงานต่อไป

---

## 1. Controllers / Resolvers / Endpoints
ในโลกของ REST API หรือ GraphQL เรามักจะมี Controller หรือ Resolver ที่รับหน้าที่เป็นด่านหน้า:
1. รับ HTTP Request (เช่น ข้อมูลใน JSON Payload, Route Parameters)
2. โยน Payload เหล่านั้นแปลงร่างไปเป็น **Command** หรือ **Query** (DTOs)
3. ส่ง Command/Query นั้นเข้าคิวให้ `Mediator` หรือ `Application Service` นำไปจัดการ
4. ได้รับผลลัพธ์จากวงใน กลับมาแปลงร่างเป็น HTTP Response (เช่น `200 OK`, `201 Created`) แล้วส่งกลับหาผู้เรียก

> ถ้าอยากเปลี่ยนจาก REST API ไปทำ GraphQL หรือทำ Background Job / CLI เลเยอร์ข้างในคุณก็แทบไม่ต้องแก้อะไรเลย เพราะคุณแค่เปลี่ยนหรือสร้างประตูบานใหม่ที่เลเยอร์ Presentation นี้เท่านั้น

## 2. DTOs (Data Transfer Objects)
กฎเหล็กในการป้องกันระบบคือ **ห้ามคืนค่า (Return) Domain Entity ออกไปสู่โลกภายนอกตรงๆ เด็ดขาด!**
- Entity มีไว้สำหรับทำ Business Rule บางครั้งมันมีข้อมูลสำคัญ (เช่น Hashed Password) หรือมีฟิลด์เทคนิคที่เราไม่อยากให้ API Client เห็น
- เราต้องแปลง (Map) Entity เหล่านั้นออกมาเป็น **Response DTO** เสมอ เพื่อเลือกส่งออกเฉพาะข้อมูลที่จำเป็นและปลอดภัย (บางครั้งเราใช้ AutoMapper เป็นตัวช่วย)
- เช่นเดียวกัน ขาเข้าเราก็จะรับข้อมูลด้วย **Request DTO** แล้วโยนเข้ากระบวนการ Validation เบื้องต้นก่อนจะส่งเข้าสู่วงใน

## 3. Global Exception Handling (ดักจับ Error ส่วนกลาง)
เราสามารถติดตั้งตัวดักจับ (Middleware หรือ Exception Filters) ไว้ที่เลเยอร์หน้าบ้านนี้
- เพื่อทำหน้าที่ "แปลภาษา (Translate)" ระหว่าง Domain Errors กับ HTTP Status
- เช่น ถ้าระบบวงในโยน `UserNotFoundException` ออกมา... Controller ไม่จำเป็นต้องเขียน `try-catch` ทุกจุด
- ตัว Middleware จะเป็นคนดักจับ Exception ตัวนี้ แล้วจับแปลงร่างเป็น HTTP Status `404 Not Found` กลับไปหา Client ได้โดยอัตโนมัติ ช่วยลดโค้ดขยะใน Controller ได้อย่างมหาศาล

## 4. Composition Root (จุดประกอบร่าง)
ในส่วนของการตั้งค่าโปรเจกต์ (เช่น ไฟล์ `Program.cs` ใน .NET หรือการ Setup Dependency Injection Container ใน TS/Node) มักจะเกิดขึ้นที่เลเยอร์นอกสุดนี้
- นี่คือจุดที่ประกาศว่า "ถ้า Application ขอ Interface ตัวนี้นะ ให้เอา Adapter จาก Infrastructure ไปเสียบให้มัน"
- เป็นจุดศูนย์รวมการ Register Service ทำให้วงในยังคงเป็นอุดมคติต่อไป โดยมีเลเยอร์นี้ช่วยประสานให้มันทำงานได้จริงในโลกภายนอก
