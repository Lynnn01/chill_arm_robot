# 01 - Color System (Monochrome Minimal + Magic UI)

## 1. Monochrome First (ขาว-ดำ เป็นหลัก)
- **Background & Foreground:** ใช้สี ขาว-ดำ (หรือเทาเข้มใน Dark mode) เป็นโครงสร้างหลักของหน้าเว็บเสมอ เพื่อสร้างความรู้สึกล้ำสมัย มินิมอล และสะอาดตา (อิงจาก `bg-background` และ `text-foreground`)
- **การแยกสัดส่วน (Hierarchy):** สีหลักของระบบควรมีแค่ 1-2 สีเท่านั้น องค์ประกอบรองๆ ให้ใช้ความโปร่งใส (Opacity) ช่วย เช่น `text-foreground/70` หรือ `bg-foreground/5` แทนที่จะใช้สีเทาหลายๆ เฉด

## 2. Accents for Purpose (ใช้สีสดเพื่อจุดประสงค์ที่ชัดเจน)
- สีสด (Vibrant colors) เช่น แดง เขียว น้ำเงิน จะถูกใช้เพื่อสื่อความหมายเท่านั้น ไม่ใช่เพื่อตกแต่ง
- **ตัวอย่างใน Finance App:** 
  - 🟢 **สีเขียว (Success / Profit):** ใช้กับกำไร หรือสถานะเชิงบวก
  - 🔴 **สีแดง (Danger / Loss):** ใช้กับขาดทุน หรือการแจ้งเตือนสำคัญ
  - 🔵 **สีน้ำเงิน (Brand / Action):** ใช้กับปุ่ม Call to Action หรือจุดที่ต้องการให้ผู้ใช้ Focus อย่างแท้จริง
- ใน Dark mode สี Accent ควรมีความสว่าง (Luminance) สูงเพื่อให้ตัดกับพื้นหลัง หรืออาจใช้ Glow effect แบบบางๆ ช่วย

## 3. High Fidelity Details (ใส่ใจมิติของสี)
- หลีกเลี่ยงการใช้สีทึบแบนๆ (Flat solid color) ในองค์ประกอบใหญ่
- **Gradients:** ใช้ Gradient แบบนุ่มนวล (Subtle gradients) เช่น พื้นหลังของ Card หรือปุ่ม สำคัญคือจุดจบของ Gradient ควรกลมกลืนไปกับ Background ของระบบ
- **Borders:** เส้นขอบควรใช้สีที่โปร่งใสมาก (เช่น `border-foreground/10`) แทนที่จะเป็นสี Solid เพื่อให้เข้ากับระบบ Dark/Light mode ได้อัตโนมัติ
