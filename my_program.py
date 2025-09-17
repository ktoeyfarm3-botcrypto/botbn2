# ==================================================
# ไฟล์ที่ 2: my_program.py
# ตัวอย่างซอฟต์แวร์ของคุณ (เปลี่ยนตามต้องการ)
# ==================================================

from license_simple import check_license


def main():
    """ฟังก์ชันหลักของซอฟต์แวร์"""

    print("=== โปรแกรมของคุณ ===")
    print("กรุณาใส่ License เพื่อใช้งาน\n")

    # ขอ License จากผู้ใช้
    user_name = input("ชื่อผู้ใช้: ")
    license_key = input("License Key: ")

    # ตรวจสอบ License
    if check_license(license_key, user_name):
        print("\n" + "=" * 40)
        print("🎉 ยินดีต้อนรับเข้าสู่โปรแกรม!")
        print("=" * 40)

        # โค้ดโปรแกรมหลักของคุณเริ่มที่นี่ ↓
        start_my_software()

    else:
        print("\n🚫 ไม่สามารถเข้าใช้โปรแกรมได้")
        input("กด Enter เพื่อออก...")


def start_my_software():
    """
    ใส่โค้ดซอฟต์แวร์ของคุณที่นี่
    """

    while True:
        print("\n=== เมนูหลัก ===")
        print("1. ฟีเจอร์ที่ 1")
        print("2. ฟีเจอร์ที่ 2")
        print("3. ออกจากโปรแกรม")

        choice = input("เลือก (1-3): ")

        if choice == "1":
            print("🔧 กำลังทำงาน ฟีเจอร์ที่ 1...")
            # ใส่โค้ดฟีเจอร์ 1 ของคุณที่นี่

        elif choice == "2":
            print("🔧 กำลังทำงาน ฟีเจอร์ที่ 2...")
            # ใส่โค้ดฟีเจอร์ 2 ของคุณที่นี่

        elif choice == "3":
            print("👋 ขอบคุณที่ใช้งาน!")
            break
        else:
            print("❌ กรุณาเลือก 1-3")


if __name__ == "__main__":
    main()
