# Design Rule 06: Visual Depth & Aesthetics (ความลึกและสุนทรียภาพ)
> รวมแนวคิดจาก **Awesome Design Systems** (Hierarchy, Layering) และ **Magic UI** (Glassmorphism, Glow, Gradients)

---

## หลักการสำคัญ

UI ที่ดีต้องมี **ลำดับชั้นที่ชัดเจน** (Awesome Design Systems) และ **ให้ความรู้สึกพรีเมียมด้วยรายละเอียด** (Magic UI)

---

## กฎข้อที่ 1: Layering (การซ้อนทับเพื่อสร้างมิติ)
จัดลำดับชั้นของ Surface ด้วยสีและเส้นขอบ ไม่ใช่ Shadow หนักๆ:

| ชั้น           | สี               | การใช้งาน                   |
|----------------|------------------|-----------------------------|
| Base (ล่างสุด) | `#FFFFFF` White  | Window Background           |
| Surface        | `#FFFFFF` White  | Cards, Panels               |
| Surface Muted  | `#F8FAFC` Gray50 | Input fields, Active tabs   |
| Overlay        | Semi-transparent | Tooltips, Dropdowns         |

## กฎข้อที่ 2: Border as Separator (เส้นขอบแทนเงา)
ตาม Magic UI + Awesome Design Systems — ใช้เส้นขอบบางๆ แทนเงาเข้มๆ:
- ✅ `1px solid #E2E8F0` (Slate 200) สำหรับ Card borders
- ✅ ไม่ใช้ Drop Shadow หนักๆ ในแอปแบบ Desktop
- ❌ หลีกเลี่ยงเส้นขอบที่ดำหรือเข้มจนดึงความสนใจออกจากเนื้อหา

## กฎข้อที่ 3: Subtle Gradients (การไล่สีอย่างละเอียดอ่อน)
ตาม Magic UI:
- พื้นหลังของ Header หรือ Title area อาจมี Gradient อ่อนๆ (เช่น ขาว-ไปเทาอ่อนมาก)
- ปุ่ม Primary สามารถมี Gradient เล็กน้อยเพื่อให้ดูลึกขึ้น (เช่น `#1E293B` → `#0F172A`)
- ✅ ใช้ Gradient ที่ละเอียดมาก จนแทบไม่สังเกตเห็น
- ❌ ไม่ใช้ Gradient ที่เห็นได้ชัดจนรกสายตา

## กฎข้อที่ 4: High-Fidelity Micro-details (รายละเอียดย่อยระดับพรีเมียม)
ตาม Magic UI — ส่วนที่แตกต่างระหว่าง UI ทั่วไปกับ UI พรีเมียม:
- **Inner highlight**: เส้นขาวจางๆ ที่ขอบบนของปุ่มสีเข้ม เพื่อจำลองแสงตกกระทบ
- **Subtle Glow**: รัศมีสีจางๆ รอบปุ่ม Primary เมื่อ hover (ใน tkinter ทำได้ด้วยการใส่ `highlightbackground` สีที่อ่อนกว่า)
- **Consistent Padding**: Padding ด้านในทุก component ต้องเท่ากัน (ใช้ `ipadx`, `ipady`)

## กฎข้อที่ 5: Dark Elements as Anchors (องค์ประกอบสีเข้มเป็นจุดยึดสายตา)
ตาม Awesome Design Systems — ในหน้าจอที่ใช้สีขาวเป็นหลัก องค์ประกอบสีเข้มทำหน้าที่เป็น "สมอ" (Anchor) ที่ดึงสายตา:
- ปุ่ม Primary สีดำ → ดึงสายตาไปที่ Action หลัก
- ปุ่ม Danger สีแดง → เตือนว่ากดแล้วมีผลกระทบสูง
- Title "ONE ARM" สีดำ Bold → เป็น Brand Identity ที่ชัดเจน

## การประยุกต์ใช้กับ ONE ARM
```python
# Card Pattern: ใช้ Border แทน Shadow
card = tk.Frame(parent,
    bg=Theme.SURFACE,               # #FFFFFF
    relief=tk.SOLID, bd=1,
    highlightbackground=Theme.BORDER,   # #E2E8F0
    highlightthickness=1)

# Input Muted Background สำหรับ Active state
value_label = tk.Label(parent,
    bg=Theme.SURFACE_MUTED,         # #F8FAFC
    relief=tk.SOLID, bd=1)
```
