# 01 - Unified Architecture Overview

## บทนำ: เมื่อ Clean Architecture พบกับ Domain-Driven Design (DDD)
เอกสารชุดนี้คือการหลอมรวม **Clean Architecture** (โดย Robert C. Martin) และ **Domain-Driven Design (DDD) + Hexagonal Architecture** เข้าด้วยกันอย่างลงตัว เป้าหมายคือการสร้างโครงสร้างที่ **"ทรงพลังระดับ Enterprise แต่จัดระเบียบ Business Logic ได้ลึกซึ้ง และไม่ผูกติดกับภาษาใดภาษาหนึ่ง (Language-Agnostic)"**

สถาปัตยกรรมนี้จะทำให้เราได้ระบบที่:
1. เปลี่ยน Database, UI หรือ Framework ได้โดยที่โค้ด Business Logic ไม่พัง
2. เขียน Unit Test ได้อย่างครอบคลุมโดยไม่ต้องพึ่งพาระบบจำลอง (Mocking) ฐานข้อมูล
3. เมื่อธุรกิจซับซ้อนขึ้น โค้ดจะไม่กลายเป็นขยะ (Big ball of mud)
4. แยกโมดูลกันชัดเจน ทำให้พร้อมสำหรับการขยายร่างไปเป็น Microservices ในอนาคต

---

## หัวใจสำคัญ 2 ประการ

### 1. The Dependency Rule (กฎการพึ่งพาจากนอกเข้าใน)
นำมาจาก Clean Architecture กฎนี้ระบุว่าระบบต้องแบ่งเป็น "วงแหวนซ้อนทับกัน" 
- **วงในสุด (Domain & Application)** คือพื้นที่ศักดิ์สิทธิ์ที่เก็บ Business Rules ไว้ จะไม่รู้จักวงนอกเลย
- **วงนอกสุด (Infrastructure & Presentation)** คือเทคโนโลยี (Database, Web API) จะต้องเป็นฝ่ายพึ่งพาวงในเสมอ
- **ลูกศร Dependency** จะพุ่งจากนอกเข้าในเสมอ!

### 2. Ports and Adapters (ปลั๊กและเต้ารับ)
นำมาจาก Hexagonal Architecture เพื่อใช้แก้ปัญหาว่า "ถ้าวงในห้ามรู้จักวงนอก แล้ววงในจะสั่ง Database ให้บันทึกข้อมูลได้อย่างไร?"
- **Ports (เต้ารับ):** วงในจะสร้าง "Interface" ขึ้นมา (เช่น `UserRepositoryPort`) เพื่อบอกว่า "ฉันต้องการระบบที่สามารถบันทึกและอ่าน User ได้ หน้าตาฟังก์ชันต้องเป็นแบบนี้นะ"
- **Adapters (ปลั๊ก):** วงนอกสุดจะไปสร้างคลาส (เช่น `PostgresUserRepository`) แล้ว Implement Interface นั้น เพื่อทำงานเชื่อม Database จริงๆ ให้

---

## 4 เลเยอร์ของ Unified Architecture

เมื่อจับแนวคิดมาซ้อนทับกัน เราจะได้ 4 เลเยอร์หลัก (ลึกสุดไปผิวนอก):
1. **Domain Layer:** หัวใจของธุรกิจ (Entities, Value Objects, Domain Events)
2. **Application Layer:** คนคุมคิวงานและ Use Cases (Commands, Queries, Ports)
3. **Infrastructure Layer:** การติดต่อระบบภายนอก (Adapters, Repositories, DB Models)
4. **Presentation Layer:** ทางเข้า-ออกของ User (Controllers, APIs, CLI)

---

## การจัดระเบียบโค้ดแบบ Vertical Slicing & Modules
แทนที่จะจัดโครงสร้างแยกไฟล์ตามชนิด (เช่น เอา Controller ทั้งหมดไปกองรวมกัน) เราจะนำแนวคิดของ DDD มาใช้ คือการแบ่งตาม **"Bounded Context / Feature / Module"**

ตัวอย่าง:
```text
src/
└── modules/
    ├── Users/            <-- Module ที่ 1
    │   ├── domain/       <-- กฎทางธุรกิจของ User
    │   ├── application/  <-- Use Cases ของ User
    │   ├── infrastructure/<- การบันทึก DB ของ User
    │   └── presentation/ <-- API Endpoints ของ User
    └── Orders/           <-- Module ที่ 2
        ├── domain/
        ...
```
การหั่นแนวตั้งแบบนี้ (Vertical Slicing) ช่วยให้เวลานักพัฒนาเข้ามาแก้ฟีเจอร์ "Orders" ก็จะทำงานอยู่แค่ในโฟลเดอร์ Orders ไม่ต้องวิ่งกระโดดข้ามโฟลเดอร์ไปมาทั่วทั้งโปรเจกต์
