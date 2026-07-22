# 08 - Component Architecture (โครงสร้างคอมโพเนนต์)

## 1. Copy-Paste Philosophy (ตามรอย Magic UI / shadcn)
- แนวคิดสมัยใหม่ของการทำ Design System คือ **การไม่ต้องติดตั้งเป็น NPM Package (npm install my-ui)** 
- แต่เป็นการก็อปปี้ไฟล์โค้ด (Copy & Paste) ของคอมโพเนนต์นั้นๆ มาไว้ในโปรเจกต์ของคุณเลย (เช่น ไว้ใน `src/components/ui/`)
- **ข้อดี:** คุณมีอิสระ 100% ในการปรับแต่ง (Customize) โค้ดของคอมโพเนนต์นั้นให้เข้ากับโปรเจกต์คุณโดยไม่ต้องรอ Library อัปเดต หรือต้องไปแฮ็กโค้ดชาวบ้าน

## 2. Self-contained & Modular
- คอมโพเนนต์ที่ดี (เช่น `Card`, `Button`, `Modal`) ควรจะทำงานจบในตัวของมันเอง
- ลดการพึ่งพาไลบรารีภายนอกให้มากที่สุด ถ้าไม่จำเป็นจริงๆ (Minimal dependencies)
- รวมเอา Logic และ Style (Tailwind classes) เก็บไว้ในที่เดียวกัน

## 3. Composition over Configuration
- แทนที่จะสร้าง Component หนึ่งตัวแล้วรับ Props เป็นร้อยๆ อัน (เช่น `<Table data={...} hideHeader={true} color="red" />`)
- ให้แบ่งย่อยเป็นชิ้นส่วนประกอบกัน (Compound Components)
- ตัวอย่าง:
  ```tsx
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Title</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>...</TableBody>
  </Table>
  ```
- วิธีนี้ทำให้โค้ดยืดหยุ่น อ่านง่าย และนำไปประยุกต์ทำหน้าตาตารางแปลกๆ ได้ตามใจชอบ
