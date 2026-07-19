# Design Rule 07: Accessibility & User Feedback (การเข้าถึงและการสื่อสารกับผู้ใช้)
> รวมแนวคิดจาก **Awesome Design Systems** (A11y, Clear Language) และ **Magic UI** (Instant Feedback, Loading States)

---

## หลักการสำคัญ

ระบบต้องสื่อสารกับผู้ใช้อยู่เสมอและทุกคนต้องใช้งานได้ **ไม่มีข้อยกเว้น**

---

## กฎข้อที่ 1: Always Communicate (สื่อสารเสมอ)
ตาม Awesome Design Systems — ผู้ใช้ต้องรู้สถานะของระบบทุกขณะ:
- ✅ กำลังโหลด → แสดง indicator
- ✅ สำเร็จ → แสดงข้อความ ✅ ชัดเจน
- ✅ ผิดพลาด → แสดงข้อความ ⚠️ พร้อมสาเหตุ
- ❌ หน้าจอนิ่งเฉยโดยไม่มีการตอบสนองใดๆ

## กฎข้อที่ 2: Clear & Concise Language (ภาษาที่เข้าใจง่าย)
ตาม Awesome Design Systems:
- ใช้ภาษาที่กระชับ ตรงไปตรงมา
- ✅ "กำลังรีเซ็ตหุ่นยนต์..." แทนที่ "Executing reset procedure..."
- ✅ "ไม่สามารถเชื่อมต่อได้" แทนที่ "Connection refused: ECONNREFUSED"
- ❌ หลีกเลี่ยง Technical Jargon ในข้อความที่ผู้ใช้ต้องอ่าน

## กฎข้อที่ 3: Contrast Ratio (อัตราส่วนความเปรียบต่าง)
ตาม WCAG 2.1 ที่ Awesome Design Systems อ้างอิง:
- ข้อความ Body (ขนาดปกติ): Contrast ≥ **4.5:1**
- ข้อความ Heading (≥18px หรือ Bold ≥14px): Contrast ≥ **3:1**
- ✅ Black text (#0F172A) บน White (#FFFFFF) = **17:1** (ผ่าน)
- ✅ Muted text (#64748B) บน White (#FFFFFF) = **4.6:1** (ผ่านพอดี)
- ❌ Gray text (#9CA3AF) บน White = **2.5:1** (ไม่ผ่าน)

## กฎข้อที่ 4: Error Prevention (การป้องกันข้อผิดพลาด)
ตาม Awesome Design Systems + Magic UI:
- ปุ่ม Danger (RESET) ต้องวางห่างจากปุ่มปกติ (SEND) เพื่อป้องกันกดพลาด
- ปุ่ม Danger ต้องเป็นสีแดงเพื่อเตือนสายตาให้ชะลอลงก่อนกด
- ขณะหุ่นยนต์กำลังเคลื่อนไหว ต้อง Disable ปุ่มทุกปุ่มทันที

## กฎข้อที่ 5: Focus Management (การจัดการ Focus)
ตาม Awesome Design Systems:
- หลังส่งข้อความแล้ว → Focus ควรกลับมาที่ช่อง Input อัตโนมัติ
- เมื่อเปิดแอป → Focus ควรอยู่ที่ช่องกรอกข้อมูลหลัก

## การประยุกต์ใช้กับ ONE ARM
```python
# Pattern: Auto re-focus หลัง enable inputs
def enable_inputs(self):
    self.send_button.config(state=tk.NORMAL, bg=Theme.PRIMARY)
    self.reset_button.config(state=tk.NORMAL, bg=Theme.DANGER)
    self.input_entry.config(state=tk.NORMAL)
    self.input_entry.focus()  # ← สำคัญมาก: focus กลับมาให้ผู้ใช้พิมพ์ต่อได้ทันที

# Pattern: Clear error messages ใน Log
print("⚠️ <ERROR>: ไม่สามารถรีเซ็ตได้ - ตรวจสอบการเชื่อมต่อ COM port")
```
