# ==================================================
# สำหรับสร้าง License ให้กับ Sci5.py
# ==================================================

from license_simple import generate_license
import datetime


def main():
    """เครื่องมือสร้าง License สำหรับ Sci5.py Trading Bot"""

    print("=== 🔐 License Generator สำหรับ Sci5.py Trading Bot ===")
    print()

    user_name = input("ชื่อผู้ใช้: ")

    try:
        days = int(input("จำนวนวันที่ใช้ได้ (30): ") or "30")
    except:
        days = 30

    print("\n" + "=" * 50)
    license_key = generate_license(user_name, days)
    print("=" * 50)

    # บันทึกลงไฟล์
    filename = f"license_{user_name.replace(' ', '_')}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"🔐 SCI5.PY TRADING BOT LICENSE\n")
            f.write(f"================================\n")
            f.write(f"ชื่อผู้ใช้: {user_name}\n")
            f.write(f"License Key: {license_key}\n")
            f.write(f"วันที่สร้าง: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"จำนวนวันที่ใช้ได้: {days} วัน\n")
            f.write(f"หมดอายุ: {(datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%d/%m/%Y')}\n")
            f.write(f"\n")
            f.write(f"📋 วิธีใช้งาน:\n")
            f.write(f"1. เปิด Sci5.py\n")
            f.write(f"2. ใส่ชื่อผู้ใช้: {user_name}\n")
            f.write(f"3. ใส่ License Key: {license_key}\n")
            f.write(f"\n")
            f.write(f"⚠️ คำเตือน:\n")
            f.write(f"• เก็บ License Key ให้ปลอดภัย\n")
            f.write(f"• อย่าแชร์ License ให้คนอื่น\n")
            f.write(f"• ตรวจสอบวันหมดอายุ\n")

        print(f"\n📁 บันทึกลงไฟล์: {filename}")
        print(f"✅ สร้าง License สำเร็จ!")

    except Exception as e:
        print(f"❌ Error saving file: {e}")

    input("\nกด Enter เพื่อออก...")


if __name__ == "__main__":
    main()

# ==================================================
# คำแนะนำการใช้งาน
# ==================================================

"""
📋 ขั้นตอนการติดตั้ง License สำหรับ Sci5.py:

1. ไฟล์ที่ต้องมี:
   - license_simple.py (ระบบ License หลัก)
   - create_license.py (ไฟล์นี้ - สร้าง License)
   - Sci5.py (Trading Bot หลัก - มี License check แล้ว)

2. วิธีสร้าง License:
   > python create_license.py

3. ใส่ข้อมูล:
   - ชื่อผู้ใช้
   - จำนวนวันที่ใช้ได้ (ถ้าไม่ใส่จะเป็น 30 วัน)

4. จะได้ไฟล์ license_[ชื่อผู้ใช้].txt ที่มี:
   - License Key
   - วันหมดอายุ
   - วิธีใช้งาน

5. นำ License Key ไปใช้กับ Sci5.py

📋 ตัวอย่าง License:
- ชื่อผู้ใช้: John
- License Key: A1B2C3D4-20241201
- หมดอายุ: 01/12/2024

📋 ข้อดี:
✅ ป้องกันการใช้งานโดยไม่ได้รับอนุญาต
✅ ตรวจสอบวันหมดอายุอัตโนมัติ
✅ ป้องกันการปลอมแปลง License
✅ รองรับภาษาไทย
✅ บันทึกไฟล์อัตโนมัติ
"""
