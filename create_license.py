# ==================================================
# ไฟล์ที่ 3: create_license.py
# สำหรับผู้ขาย (คุณ) ใช้สร้าง License
# ==================================================

from license_simple import generate_license


def main():
    """เครื่องมือสร้าง License"""

    print("=== เครื่องมือสร้าง License ===")

    user_name = input("ชื่อผู้ใช้: ")

    try:
        days = int(input("จำนวนวันที่ใช้ได้ (30): ") or "30")
    except:
        days = 30

    print("\n" + "=" * 40)
    license_key = generate_license(user_name, days)
    print("=" * 40)

    # บันทึกลงไฟล์
    filename = f"license_{user_name.replace(' ', '_')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"ชื่อผู้ใช้: {user_name}\n")
        f.write(f"License Key: {license_key}\n")
        f.write(f"วันที่สร้าง: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

    print(f"\n📁 บันทึกลงไฟล์: {filename}")
    input("\nกด Enter เพื่อออก...")


if __name__ == "__main__":
    main()

# ==================================================
# คำแนะนำการใช้งาน
# ==================================================

"""
📋 ขั้นตอนการติดตั้ง:

1. สร้างไฟล์ 3 ไฟล์:
   - license_simple.py
   - my_program.py (เปลี่ยนชื่อตามต้องการ)
   - create_license.py

2. วางไฟล์ทั้ง 3 ไว้ในโฟลเดอร์เดียวกัน

3. เปลี่ยนรหัสลับใน license_simple.py:
   SECRET = "รหัสของคุณเอง"

4. ใส่โค้ดซอฟต์แวร์ของคุณในฟังก์ชัน start_my_software()

📋 วิธีใช้งาน:

สำหรับผู้ขาย (คุณ):
> python create_license.py

สำหรับลูกค้า:
> python my_program.py

📋 ตัวอย่าง License:
- ชื่อผู้ใช้: จอห์น
- License Key: A1B2C3D4-20241201
- หมดอายุ: 01/12/2024

📋 ข้อดี:
✅ ง่ายมาก ไม่ซับซ้อน
✅ ไม่ต้องติดตั้ง library เพิ่ม
✅ ตรวจสอบวันหมดอายุอัตโนมัติ
✅ ป้องกันการปลอมแปลง
✅ เชื่อมต่อง่าย เพียง 3 บรรทัด
"""
