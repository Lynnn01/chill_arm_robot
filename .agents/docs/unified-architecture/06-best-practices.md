# 06 - Best Practices (The Unified Rules)

## กฎเหล็กและข้อแนะนำในการเขียนโปรแกรมแบบ Unified Architecture

เพื่อรักษาความเป็นระเบียบและทำให้โปรเจกต์ยืนหยัดผ่านกาลเวลา ไม่กลายเป็น Big ball of mud นี่คือข้อแนะนำและ Best Practices ที่ผสมผสานมาจาก DDD, Clean Architecture และแนวทางของ Sairyss / Jason Taylor

---

### 1. ใช้วิธีจัดโครงสร้างแบบ Vertical Slicing เสมอ
ถ้าโปรเจกต์ของคุณไม่ใช่ระบบเล็กๆ ให้หลีกเลี่ยงการรวมทุก Controllers ไว้ในโฟลเดอร์เดียว และทุก Entities ไว้ในโฟลเดอร์เดียว (Horizontal Layering แบบดั้งเดิม)
- ให้แบ่งแอปเป็น **"Modules"** ย่อยๆ (เช่น Users, Orders, Inventory)
- ในแต่ละ Module ค่อยมีโฟลเดอร์ 4 Layer เป็นของตัวเอง (Domain, Application, Infrastructure, Presentation)
- วิธีนี้ทำให้ Feature တစ်ခုมีขอบเขตของมันเอง (Bounded Context) คนทำระบบออร์เดอร์ก็ไม่จำเป็นต้องเข้าไปยุ่งกับระบบผู้ใช้งาน

### 2. หลีกเลี่ยง Anemic Domain Model
Entity ไม่ใช่แค่ที่เก็บตัวแปรที่เต็มไปด้วย Getters และ Setters (นั่นเรียกว่า Anemic - เป็นภาวะเลือดจางทางธุรกิจ)
- เอา Setters ที่เป็น `public` ออกให้หมดจาก Entity 
- ใช้ Method คุมพฤติกรรมแทน เช่น อยากแก้ไขที่อยู่ แทนที่จะใช้ `user.address = newAddress;` ให้ใช้ `user.ChangeAddress(newAddress);` แทน
- วิธีนี้ทำให้เราฝังเงื่อนไข Validation เข้าไปใน `ChangeAddress` ได้ เช่นเช็คว่าที่อยู่ใหม่ห้ามเป็น Null

### 3. จงใช้ Value Objects เพื่อปกป้องตัวเอง (Make Illegal States Unrepresentable)
อย่าใช้ Primitives type สร้างทุกอย่าง
- แทนที่จะรับอีเมลเป็น `string` แล้วต้องมานั่งเช็ค Regex ทุกที่ ให้สร้าง Value Object `Email` ที่เช็ค Regex ไว้ตั้งแต่ตอนทำ Constructor เลย 
- ถ้าระบบโยน `Email` มาให้ หมายความว่ามันถูก Format 100% แน่นอน
- ทำแบบนี้กับรหัสไปรษณีย์, เบอร์โทรศัพท์, หรือจำนวนเงิน 

### 4. การทดสอบแบบเน้นพฤติกรรม (Behavioral Testing)
- Unit Test ฟังก์ชันเล็กๆ อาจจะจุกจิกเกินไป ให้ขยับมาเทสต์ระดับ **Use Case (Application Layer)** 
- สร้าง Fake Repository (In-memory) เอามาเสียบ (Inject) เข้า Use Case แทน Database ของจริง
- จากนั้นลองโยน Command / Query เข้าไป แล้วตรวจสอบผลลัพธ์ (เช่น เช็คว่า Fake DB มีข้อมูลเพิ่มขึ้นไหม, มี Error ถูกต้องตอนเงินไม่พอโอนไหม)
- การเทสต์แบบนี้จะได้ความครอบคลุมเทียบเท่า End-to-End Test ในความเร็วระดับ Unit Test

### 5. ห้ามแชร์ข้อมูลข้าม Module โดยตรง
ถ้าระบบใหญ่มากและแบ่ง Module ชัดเจน ห้ามให้ Module สั่ง Join Table กับ Module อื่นโดยตรง
- ถ้า Order Module อยากได้ข้อมูลชื่อลูกค้า ให้ออกแบบ Event (เช่น `UserCreatedEvent`) ให้ส่งมาอัปเดตชื่อลูกค้าในตารางเล็กๆ ที่ฝั่ง Order เตรียมไว้
- หรือเรียกใช้ "Facade/Public Port" ของ Module อื่นเพื่อขอข้อมูล
- วิธีนี้ทำให้ระบบตัดขาดกันได้สมบูรณ์ (Loose Coupling) พร้อมสกัดเป็น Microservice ได้เสมอ

### 6. สร้างปราการตรวจจับ (Enforcing Architecture)
- โลกความจริงนักพัฒนาอาจจะเผลอ Import โค้ดผิด Layer ได้ เช่น เอาไลบรารีส่งอีเมลไปยัดไว้ใน Entity
- ใช้เครื่องมือช่วยสแกนโค้ดตอน Build เช่น `eslint-plugin-boundaries` (ใน JS/TS) หรือ `NetArchTest` (ใน .NET)
- เครื่องมือเหล่านี้จะสั่งให้ Build Failed ทันทีหากใครละเมิด **The Dependency Rule** ช่วยให้โปรเจกต์สะอาดไปตลอดกาล
