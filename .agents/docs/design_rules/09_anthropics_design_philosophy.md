# Design Rule 09: Anthropics Frontend Design Philosophy (หลักการออกแบบ Anti-Generic)
> ที่มา: [anthropics/skills — frontend-design](https://www.skills.sh/anthropics/skills/frontend-design) (682K+ installs)  
> ผสมผสานกับ สไตล์ Monochrome Minimal ของ CAT CAN'T STOCKS

---

## แก่นกลาง: ออกแบบอย่างมีเจตนา ไม่ใช่แบบสำเร็จรูป

> "Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's."
> — Anthropics Skills

AI agent ที่ทำงานบนโปรเจกต์นี้ต้องไม่สร้างงาน UI ที่ดูเหมือน "ออกจาก template" — ทุก Component ทุกหน้าจอต้องสะท้อนบุคลิกของ **CAT CAN'T STOCKS** อย่างชัดเจน

---

## หลักการ 5 ข้อ (Anthropics × CAT CAN'T STOCKS)

### 1. ยึดโยงกับบริบทของโปรเจกต์ (Ground it in the subject)

**โปรเจกต์นี้คืออะไร:**
- Portfolio Tracker สำหรับนักลงทุนส่วนตัว
- สไตล์: **Monochrome Minimal** — ความเรียบง่ายแบบ editorial finance
- ผู้ใช้: คนที่ต้องการข้อมูลตรง ไม่ต้องการ visual noise

**ดังนั้น:**
- Hero element ของทุกหน้าคือ **ข้อมูลตัวเลข** ที่ชัดเจน ไม่ใช่ banner หรือ gradient ฉูดฉาด
- ทุก Component ต้องถาม: "มันช่วยให้นักลงทุนตัดสินใจได้เร็วขึ้นไหม?"
- ❌ ห้ามใส่ visual element เพื่อความสวยงามล้วนๆ ถ้าไม่มีประโยชน์ต่อ Data Readability

---

### 2. Typography คือบุคลิก (Typography carries the personality)

> "Make the type treatment itself a memorable part of the design, not a neutral delivery vehicle for the content."

**สำหรับ CAT CAN'T STOCKS:**

| Context | Font Weight | เหตุผล |
|---------|------------|--------|
| ตัวเลขกำไร/ขาดทุน | `font-bold` / `font-semibold` | ต้องดึงสายตา ตัดสินใจได้ทันที |
| Symbol ชื่อหุ้น | `font-mono` / `uppercase tracking-wider` | สไตล์ Bloomberg/Reuters |
| Label / Column header | `uppercase tracking-widest text-xs opacity-60` | Editorial finance style |
| Body / Description | `font-normal text-sm` | ไม่แย่งพื้นที่จากตัวเลข |

**กฎ:**
- ❌ ห้ามใช้ font weight เดียวกันหมดทุก Element — ต้องมี Type Hierarchy ที่ชัดเจน
- ✅ ตัวเลขขนาดใหญ่ + Label เล็กมาก = Pattern หลักของ Data Dashboard สไตล์นี้
- ✅ `tracking-wider` + `uppercase` บน Label ทำให้งานดู Professional โดยไม่ต้องใช้สีพิเศษ

---

### 3. โครงสร้างต้องสื่อความหมาย (Structure is information)

> "Structural devices should encode something true about the content, not decorate it."

**ตัวอย่างในโปรเจกต์นี้:**

✅ **ถูกต้อง — ใช้เพราะมีความหมาย:**
```
Summary → Portfolio Table → Transactions
(ลำดับนี้ = User Journey จริงๆ ของนักลงทุน)
```

❌ **ผิด — ใส่โดยไม่มีเหตุผล:**
```
01. Overview
02. Portfolio
03. Transactions
(ตัวเลข 01/02/03 ไม่ได้บอกว่ามัน "sequence" ที่ต้องทำตามลำดับ)
```

**กฎ:**
- Divider เส้นแนวนอน (`border-b border-foreground/10`) ใช้ได้เมื่อแบ่งกลุ่มข้อมูลที่ต่างกัน
- ❌ ห้ามใส่ Section header ถ้าเนื้อหาชัดเจนอยู่แล้ว
- ❌ ห้ามใช้ Numbered labels (01, 02) บน Tab หรือ Navigation ที่ไม่ใช่ Step-by-step process

---

### 4. Motion ต้องมีจุดประสงค์ (Leverage motion deliberately)

> "An orchestrated moment usually lands harder than scattered effects; sometimes less is more."

**ในโปรเจกต์นี้ (Monochrome Minimal):**

| Animation | ✅ ใช้ | ❌ ไม่ใช้ |
|-----------|--------|----------|
| Fade-in ตาราง/ข้อมูล | ✅ Framer Motion `opacity` | ❌ Bounce / Elastic |
| Number change (P/L update) | ✅ Text color transition | ❌ Counter animation เวิ่นเว้อ |
| Modal open/close | ✅ Opacity เท่านั้น (`duration: 0.15s`) | ❌ Scale + slide พร้อมกัน |
| Hover state บนแถว | ✅ `transition-colors` instant | ❌ Transform ที่ทำให้ layout shift |

**กฎสำคัญ:**
- ❌ `backdrop-blur` + animation = ห้ามใช้ (ทำให้กระตุก)
- ✅ Animation เดี่ยวๆ แบบ Purposeful ดีกว่า Animation หลายอัน Staggered กระจัดกระจาย
- ✅ ถ้าสงสัย → อย่าใส่ Animation

---

### 5. ปรับความซับซ้อนให้ตรงกับ Vision (Match complexity to the vision)

> "Elegance is executing the chosen vision well."

**Vision ของ CAT CAN'T STOCKS = Minimal → ต้องการ Precision ไม่ใช่ Decoration:**

- Spacing ต้องใช้ระบบ Grid ที่สม่ำเสมอ (4px / 8px increments)
- ทุก `p-` และ `gap-` ต้องคิดมาแล้ว ไม่ใช่แค่ "ดูดีก็ใส่"
- สีเดียวที่เพิ่มได้คือ **Red/Green สำหรับ P/L** เท่านั้น — เป็นข้อมูล ไม่ใช่ decoration
- ถ้าหน้าดู "complicated" → ลบออก ไม่ใช่ใส่เพิ่ม

---

## Checklist ก่อน Commit UI ใหม่

- [ ] ทุก String บน UI ผ่าน `t("key")` (i18n)
- [ ] ไม่มี Hardcode สี (ใช้ CSS Variables เสมอ)
- [ ] Type hierarchy ชัดเจน — มีอย่างน้อย 2 ระดับ (Primary / Secondary)
- [ ] Uppercase + tracking สำหรับ Label/Header
- [ ] Animation ทุกตัว = Opacity เท่านั้น หรือมีเหตุผลชัดเจน
- [ ] ไม่มี visual element ที่ไม่ได้สื่อข้อมูล (decorative only)
- [ ] Reuse Component ที่มีอยู่ก่อน (`<Modal>`, `<LoadingState>`, ฯลฯ)
