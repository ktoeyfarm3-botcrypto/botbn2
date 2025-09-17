# ==================================================
# ไฟล์ที่ 1: license_simple.py
# คัดลอกไฟล์นี้ไปไว้ในโฟลเดอร์เดียวกับซอฟต์แวร์ของคุณ
# ==================================================

import hashlib
import datetime


def check_license(license_key, user_name):
    """
    ฟังก์ชันตรวจสอบ License แบบง่าย

    Args:
        license_key: รหัส License (เช่น "ABCD1234-20241101")
        user_name: ชื่อผู้ใช้

    Returns:
        True ถ้า License ถูกต้อง, False ถ้าไม่ถูกต้อง
    """

    # รหัสลับ (เปลี่ยนได้ตามต้องการ)
    SECRET = "1234"

    try:
        # แยกรหัส License
        parts = license_key.split("-")
        if len(parts) != 2:
            return False

        code_part = parts[0]  # ABCD1234
        date_part = parts[1]  # 20250917

        # ตรวจสอบวันหมดอายุ
        expire_date = datetime.datetime.strptime(date_part, "%Y%m%d")
        if datetime.datetime.now() > expire_date:
            print("❌ License หมดอายุแล้ว")
            return False

        # สร้างรหัสที่ถูกต้อง
        data = f"{user_name}{date_part}{SECRET}"
        correct_code = hashlib.md5(data.encode()).hexdigest()[:8].upper()

        # เปรียบเทียบ
        if code_part == correct_code:
            days_left = (expire_date - datetime.datetime.now()).days + 1
            print(f"✅ License ถูกต้อง! เหลืออีก {days_left} วัน")
            return True
        else:
            print("❌ License ไม่ถูกต้อง")
            return False

    except:
        print("❌ รูปแบบ License ผิด")
        return False


def generate_license(user_name, days=30):
    """
    ฟังก์ชันสร้าง License (สำหรับผู้ขาย)

    Args:
        user_name: ชื่อผู้ใช้
        days: จำนวนวันที่ใช้ได้

    Returns:
        License Key
    """

    SECRET = "1234"  # ต้องเหมือนกับใน check_license

    # คำนวณวันหมดอายุ
    expire_date = datetime.datetime.now() + datetime.timedelta(days=days)
    date_str = expire_date.strftime("%Y%m%d")

    # สร้างรหัส
    data = f"{user_name}{date_str}{SECRET}"
    code = hashlib.md5(data.encode()).hexdigest()[:8].upper()

    license_key = f"{code}-{date_str}"

    print(f"ผู้ใช้: {user_name}")
    print(f"License: {license_key}")
    print(f"หมดอายุ: {expire_date.strftime('%d/%m/%Y')}")

    return license_key

