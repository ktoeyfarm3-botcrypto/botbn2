import pyodbc
import pandas as pd
from datetime import datetime, timedelta
import requests
import threading
import os
import tkinter as tk
from tkinter import messagebox
import time

# ===== CONFIG Telegram =====
BOT_TOKEN = "8057391570:AAFNkCe2RnjO7LYI4E-wg0KGG1wk56_-MOg"
CHAT_ID_GROUP = "-4967590501"
CHAT_ID_ME = "7736544619"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TELEGRAM_FILE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

branch_ids = [19, 23, 22, 17, 18, 21, 20, 16, 12]

branch_name_map = {
    19: "◾️Beehive",
    23: "◾️Promenade",
    22: "◾️Zpell",
    17: "◾️Portal",
    18: "◾️Cosmo",
    21: "◾️Ratchaphruek",
    20: "◾️Westgate",
    16: "◾️Taishotei",
    12: "◾️Nippon Yokocho"
}

# ===== Global Variables สำหรับ Scheduler =====
scheduler_running = False
scheduler_thread = None


# ===== ฟังก์ชันส่งข้อมูล =====
def run_report_and_send(log_widget=None, save_path=None):
    server = entry_server.get()
    database = entry_db.get()
    username = entry_user.get()
    password = entry_pass.get()

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    first_day_of_month = today.replace(day=1)

    periods = [
        ("Yesterday", f"{yesterday} 00:00:00", f"{yesterday} 23:59:00"),
        ("MonthToYesterday", f"{first_day_of_month} 00:00:00", f"{yesterday} 23:59:00")
    ]
    period_name_map = {
        "Yesterday": "Daily",
        "MonthToYesterday": "MTD"
    }

    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        if log_widget:
            log_widget.insert(tk.END, f"✅ เชื่อมต่อฐานข้อมูลสำเร็จ\n")
            log_widget.see(tk.END)
            
    except Exception as e:
        if log_widget:
            log_widget.insert(tk.END, f"❌ DB connection failed: {e}\n")
            log_widget.see(tk.END)
        return

    all_periods_data = []
    for period_name, from_date, to_date in periods:
        period_data = []
        for branch_id in branch_ids:
            # ===== ดึง GrossSale =====
            cursor.execute("""
                SET NOCOUNT ON;
                EXEC srptGetSystemSaleReport 
                    @FromDate=?, 
                    @ToDate=?, 
                    @TerminalId=N'', 
                    @PaymentCategory=N'', 
                    @BranchId=?, 
                    @CashCountId=N''
            """, from_date, to_date, branch_id)

            if cursor.description:
                columns = [col[0] for col in cursor.description]
                data = cursor.fetchall()
                if data:
                    df = pd.DataFrame.from_records(data, columns=columns)
                    if 'GrossSale' not in df.columns or 'BranchName' not in df.columns:
                        continue

                    df_selected = df[['BranchName', 'GrossSale']].copy()
                    df_selected['GrossSale'] = pd.to_numeric(df_selected['GrossSale'], errors='coerce').fillna(0.00).round(2)

                    # ===== หัก AR จาก Total =====
                    ar_value = 0.0
                    if var_ar.get() == 1:
                        cursor.execute("""
                            SET NOCOUNT ON;
                            EXEC srptGetSystemSaleReport_SubReport 
                                @FromDate=?, @ToDate=?, 
                                @TerminalId=N'', @PaymentCategory=N'', 
                                @BranchId=?, @CashCountId=N''
                        """, from_date, to_date, branch_id)
                        if cursor.description:
                            columns_sub = [col[0] for col in cursor.description]
                            data_sub = cursor.fetchall()
                            if data_sub:
                                df_sub = pd.DataFrame.from_records(data_sub, columns=columns_sub)
                                if 'Total' in df_sub.columns and 'PaymentId' in df_sub.columns:
                                    ar_value = float(df_sub.loc[df_sub['PaymentId'] == 16, 'Total'].sum())
                                    df_selected['GrossSale'] -= ar_value

                    # เพิ่มคอลัมน์ AR Deducted
                    df_selected['AR_Deducted'] = ar_value
                    df_selected['Period'] = period_name_map[period_name]
                    df_selected['BranchId'] = branch_id
                    period_data.append(df_selected)

                    # ===== แสดงค่า AR Deducted ใน GUI =====
                    if log_widget:
                        for _, row in df_selected.iterrows():
                            log_widget.insert(tk.END, f"{row['BranchName']} | GrossSale: {row['GrossSale']:,.2f} | AR Deducted: {row['AR_Deducted']:,.2f}\n")
                        log_widget.see(tk.END)

        if period_data:
            all_periods_data.append(pd.concat(period_data, ignore_index=True))

    cursor.close()
    conn.close()

    if all_periods_data:
        combined_df = pd.concat(all_periods_data, ignore_index=True)
        pivot_df = combined_df.pivot(index=['BranchId', 'BranchName'], columns='Period', values='GrossSale').reset_index()
        pivot_df = pivot_df.fillna(0.00)

        # บันทึก CSV
        if not save_path:
            save_path = os.path.join(os.getcwd(), f"SystemSaleReport_{yesterday.strftime('%Y%m%d')}.csv")
        pivot_df.to_csv(save_path, index=False)

        if log_widget:
            log_widget.insert(tk.END, f"✅ CSV saved: {save_path}\n")
            log_widget.see(tk.END)

        # สร้างข้อความ
        message = f"JP Group Sales\nDate: {yesterday.strftime('%d/%m/%Y')}\n\n"
        total_daily = 0.0
        total_mtd = 0.0
        for branch_id in branch_ids:
            row = pivot_df[pivot_df['BranchId'] == branch_id]
            if not row.empty:
                daily = row['Daily'].values[0] if 'Daily' in row.columns else 0.0
                mtd = row['MTD'].values[0] if 'MTD' in row.columns else 0.0
            else:
                daily = 0.0
                mtd = 0.0
            total_daily += daily
            total_mtd += mtd
            branch_name = branch_name_map.get(branch_id, f"Branch {branch_id}")
            message += f"{branch_name}\nDaily:={daily:,.2f}\nMTD:={mtd:,.2f}\n"
        message += "\n"f"Total JP Groups\nDaily:={total_daily:,.2f}\nMTD:={total_mtd:,.2f}"

        # ===== ส่งข้อความและไฟล์เข้า Telegram =====
        selected_chats = []
        if var_group.get() == 1:
            selected_chats.append(CHAT_ID_GROUP)
        if var_me.get() == 1:
            selected_chats.append(CHAT_ID_ME)

        if not selected_chats:
            if log_widget:
                log_widget.insert(tk.END, "⚠️ กรุณาเลือกปลายทาง (Group/Only Me)\n")
                log_widget.see(tk.END)
            return

        for chat_id in selected_chats:
            # ส่งข้อความ
            payload = {"chat_id": chat_id, "text": message}
            resp_msg = requests.post(TELEGRAM_URL, data=payload)
            if log_widget:
                if resp_msg.status_code == 200:
                    log_widget.insert(tk.END, f"✅ Message sent to {chat_id}\n")
                else:
                    log_widget.insert(tk.END, f"❌ Failed to send message {chat_id}: {resp_msg.text}\n")
                log_widget.see(tk.END)

            # ส่งไฟล์ CSV ถ้าเลือก
            if var_csv.get() == 1:
                with open(save_path, 'rb') as f:
                    files = {'document': f}
                    payload_doc = {"chat_id": chat_id, "caption": f"CSV Report {yesterday.strftime('%d/%m/%Y')}"}
                    resp_file = requests.post(TELEGRAM_FILE_URL, data=payload_doc, files=files)
                    if log_widget:
                        if resp_file.status_code == 200:
                            log_widget.insert(tk.END, f"✅ CSV sent to {chat_id}\n")
                        else:
                            log_widget.insert(tk.END, f"❌ Failed to send CSV {chat_id}: {resp_file.text}\n")
                        log_widget.see(tk.END)
    else:
        if log_widget:
            log_widget.insert(tk.END, f"❌ No data available\n")
            log_widget.see(tk.END)


# ===== เพิ่มฟังก์ชัน Daily Scheduler =====
def daily_scheduler():
    """
    ฟังก์ชันสำหรับรัน Daily Schedule - ทำงานทุกวันตามเวลาที่กำหนด
    """
    global scheduler_running
    
    while scheduler_running:
        try:
            target_hour = int(hour_var.get())
            target_minute = int(minute_var.get())
            
            now = datetime.now()
            
            # คำนวณเวลาที่จะต้องรันครั้งต่อไป
            target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            
            # ถ้าเวลาเป้าหมายผ่านไปแล้ววันนี้ ให้เลื่อนไปพรุ่งนี้
            if target_time <= now:
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            
            log.insert(tk.END, f"⏰ Next run scheduled at: {target_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.insert(tk.END, f"⏳ Waiting {wait_seconds/3600:.1f} hours...\n")
            log.see(tk.END)
            
            # รอจนถึงเวลาที่กำหนด (ตรวจสอบทุก 60 วินาที)
            while scheduler_running and datetime.now() < target_time:
                remaining = (target_time - datetime.now()).total_seconds()
                
                # อัปเดต status ทุก 60 วินาที
                if remaining > 0:
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)
                    status_label.config(text=f"⏰ Next run in: {hours:02d}:{minutes:02d}")
                
                time.sleep(60)  # ตรวจสอบทุกนาที
            
            # ถึงเวลาแล้ว ให้รันรายงาน
            if scheduler_running:
                log.insert(tk.END, f"🚀 Running scheduled report at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log.see(tk.END)
                
                # รันรายงานใน thread แยก
                report_thread = threading.Thread(target=run_report_and_send, args=(log,))
                report_thread.start()
                report_thread.join()  # รอให้รายงานเสร็จ
                
                log.insert(tk.END, f"✅ Scheduled report completed\n")
                log.see(tk.END)
                
        except Exception as e:
            log.insert(tk.END, f"❌ Scheduler error: {e}\n")
            log.see(tk.END)
            time.sleep(300)  # รอ 5 นาทีแล้วลองใหม่


def start_daily_schedule():
    """
    เริ่มต้น Daily Scheduler
    """
    global scheduler_running, scheduler_thread
    
    if scheduler_running:
        log.insert(tk.END, "⚠️ Scheduler is already running!\n")
        log.see(tk.END)
        return
    
    try:
        hour = int(hour_var.get())
        minute = int(minute_var.get())
        
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            messagebox.showerror("Error", "เวลาไม่ถูกต้อง! ชั่วโมง: 0-23, นาที: 0-59")
            return
            
    except ValueError:
        messagebox.showerror("Error", "กรุณาใส่ตัวเลขที่ถูกต้อง")
        return
    
    # ยืนยันการเริ่ม Daily Scheduler
    confirm_msg = f"""🕐 เริ่ม Daily Scheduler?

⏰ เวลาที่กำหนด: {hour:02d}:{minute:02d} น.
📅 จะส่งรายงานทุกวันในเวลานี้

✅ ส่งไปยัง: {"Group " if var_group.get() else ""}{"Personal " if var_me.get() else ""}
📄 ส่ง CSV: {"Yes" if var_csv.get() else "No"}
💰 หัก AR: {"Yes" if var_ar.get() else "No"}

ต้องการเริ่มต้นหรือไม่?"""
    
    if not messagebox.askyesno("Confirm Daily Scheduler", confirm_msg):
        return
    
    scheduler_running = True
    scheduler_thread = threading.Thread(target=daily_scheduler, daemon=True)
    scheduler_thread.start()
    
    # อัปเดต UI
    btn_start_schedule.config(text="🛑 Stop Daily Scheduler", bg="#e74c3c", command=stop_daily_schedule)
    btn_run_now.config(state="disabled")
    
    log.insert(tk.END, f"🚀 Daily Scheduler started! Will run every day at {hour:02d}:{minute:02d}\n")
    log.see(tk.END)


def stop_daily_schedule():
    """
    หยุด Daily Scheduler
    """
    global scheduler_running
    
    if not scheduler_running:
        log.insert(tk.END, "⚠️ Scheduler is not running!\n")
        log.see(tk.END)
        return
    
    scheduler_running = False
    
    # อัปเดต UI
    btn_start_schedule.config(text="📅 Start Daily Scheduler", bg="#27ae60", command=start_daily_schedule)
    btn_run_now.config(state="normal")
    status_label.config(text="⏹️ Scheduler stopped")
    
    log.insert(tk.END, f"🛑 Daily Scheduler stopped at {datetime.now().strftime('%H:%M:%S')}\n")
    log.see(tk.END)


def run_report_thread():
    """
    รันรายงานใน thread แยก
    """
    threading.Thread(target=run_report_and_send, args=(log,)).start()


def test_schedule_time():
    """
    ทดสอบเวลาที่ตั้งไว้
    """
    try:
        hour = int(hour_var.get())
        minute = int(minute_var.get())
        
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if target_time <= now:
            target_time += timedelta(days=1)
        
        wait_time = (target_time - now).total_seconds()
        wait_hours = wait_time / 3600
        
        messagebox.showinfo("Schedule Test", 
                           f"⏰ เวลาที่ตั้งไว้: {hour:02d}:{minute:02d}\n"
                           f"🕐 เวลาปัจจุบัน: {now.strftime('%H:%M:%S')}\n"
                           f"📅 รันครั้งต่อไป: {target_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                           f"⏳ เหลือเวลา: {wait_hours:.1f} ชั่วโมง")
                           
    except ValueError:
        messagebox.showerror("Error", "กรุณาใส่ตัวเลขที่ถูกต้อง")


def get_current_status():
    """
    แสดงสถานะปัจจุบันของระบบ
    """
    status_msg = f"""📊 System Status Report
    
⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🕐 Scheduled Time: {hour_var.get()}:{minute_var.get()}
📅 Scheduler Status: {"🟢 Running" if scheduler_running else "🔴 Stopped"}

📧 Telegram Settings:
   • Group: {"✅" if var_group.get() else "❌"}
   • Personal: {"✅" if var_me.get() else "❌"}
   • Send CSV: {"✅" if var_csv.get() else "❌"}
   • Deduct AR: {"✅" if var_ar.get() else "❌"}

🏢 Branches: {len(branch_ids)} branches monitored
📁 Database: {entry_db.get()}
🖥️ Server: {entry_server.get()}"""
    
    messagebox.showinfo("Current Status", status_msg)


# ===== GUI =====
root = tk.Tk()
root.title("🏢 Japanese Group Sales Telegram - Daily Scheduler v2.0")
root.geometry("650x700")
root.configure(bg="#2c3e50")

# Style configuration
style = {
    'bg': "#2c3e50",
    'fg': "white",
    'entry_bg': "#34495e",
    'button_bg': "#3498db",
    'success_bg': "#27ae60",
    'danger_bg': "#e74c3c",
    'warning_bg': "#f39c12"
}

# Header
header_frame = tk.Frame(root, bg="#34495e", height=80)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

title_label = tk.Label(header_frame, text="🏢 JP Group Sales Reporter", 
                      font=("Segoe UI", 18, "bold"), fg="#3498db", bg="#34495e")
title_label.pack(pady=20)

subtitle_label = tk.Label(header_frame, text="📅 Daily Automated Scheduler v2.0", 
                         font=("Segoe UI", 11), fg="#ecf0f1", bg="#34495e")
subtitle_label.pack()

# Main content
main_frame = tk.Frame(root, bg=style['bg'])
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Database Configuration Section
db_frame = tk.LabelFrame(main_frame, text="🗄️ Database Configuration", 
                        font=("Segoe UI", 12, "bold"), fg="#3498db", bg=style['bg'])
db_frame.pack(fill="x", pady=(0, 15))

# Server
tk.Label(db_frame, text="Server:", font=("Segoe UI", 10), fg=style['fg'], bg=style['bg']).grid(row=0, column=0, sticky="e", padx=5, pady=5)
entry_server = tk.Entry(db_frame, width=30, font=("Consolas", 10), bg=style['entry_bg'], fg="white", insertbackground="white")
entry_server.insert(0, "172.28.116.11,4443")
entry_server.grid(row=0, column=1, padx=5, pady=5)

# Database
tk.Label(db_frame, text="Database:", font=("Segoe UI", 10), fg=style['fg'], bg=style['bg']).grid(row=1, column=0, sticky="e", padx=5, pady=5)
entry_db = tk.Entry(db_frame, width=30, font=("Consolas", 10), bg=style['entry_bg'], fg="white", insertbackground="white")
entry_db.insert(0, "HQ_JAPANESE_RESTAURANT_GROUP")
entry_db.grid(row=1, column=1, padx=5, pady=5)

# Username
tk.Label(db_frame, text="Username:", font=("Segoe UI", 10), fg=style['fg'], bg=style['bg']).grid(row=2, column=0, sticky="e", padx=5, pady=5)
entry_user = tk.Entry(db_frame, width=30, font=("Consolas", 10), bg=style['entry_bg'], fg="white", insertbackground="white")
entry_user.insert(0, "japanese")
entry_user.grid(row=2, column=1, padx=5, pady=5)

# Password
tk.Label(db_frame, text="Password:", font=("Segoe UI", 10), fg=style['fg'], bg=style['bg']).grid(row=3, column=0, sticky="e", padx=5, pady=5)
entry_pass = tk.Entry(db_frame, width=30, font=("Consolas", 10), bg=style['entry_bg'], fg="white", insertbackground="white", show="*")
entry_pass.insert(0, "Password@jpsql1")
entry_pass.grid(row=3, column=1, padx=5, pady=5)

# Telegram Settings Section
telegram_frame = tk.LabelFrame(main_frame, text="📱 Telegram Settings", 
                              font=("Segoe UI", 12, "bold"), fg="#3498db", bg=style['bg'])
telegram_frame.pack(fill="x", pady=(0, 15))

# Checkbox Grid
checkbox_frame = tk.Frame(telegram_frame, bg=style['bg'])
checkbox_frame.pack(padx=10, pady=10)

var_group = tk.IntVar()
chk_group = tk.Checkbutton(checkbox_frame, text="📢 ส่งเข้า Group", variable=var_group,
                          font=("Segoe UI", 10), fg=style['fg'], bg=style['bg'], 
                          selectcolor=style['button_bg'], activebackground=style['bg'])
chk_group.grid(row=0, column=0, sticky="w", padx=10, pady=5)

var_me = tk.IntVar()
chk_me = tk.Checkbutton(checkbox_frame, text="👤 ส่งเข้า Only Me", variable=var_me,
                       font=("Segoe UI", 10), fg=style['fg'], bg=style['bg'], 
                       selectcolor=style['button_bg'], activebackground=style['bg'])
chk_me.grid(row=0, column=1, sticky="w", padx=10, pady=5)

var_csv = tk.IntVar()
chk_csv = tk.Checkbutton(checkbox_frame, text="📄 ส่ง CSV แนบไปด้วย", variable=var_csv,
                        font=("Segoe UI", 10), fg=style['fg'], bg=style['bg'], 
                        selectcolor=style['button_bg'], activebackground=style['bg'])
chk_csv.grid(row=1, column=0, sticky="w", padx=10, pady=5)

var_ar = tk.IntVar()
chk_ar = tk.Checkbutton(checkbox_frame, text="💰 หักค่า AR (PaymentId=16)", variable=var_ar,
                       font=("Segoe UI", 10), fg=style['fg'], bg=style['bg'], 
                       selectcolor=style['button_bg'], activebackground=style['bg'])
chk_ar.grid(row=1, column=1, sticky="w", padx=10, pady=5)

# Schedule Settings Section
schedule_frame = tk.LabelFrame(main_frame, text="⏰ Daily Schedule Settings", 
                              font=("Segoe UI", 12, "bold"), fg="#3498db", bg=style['bg'])
schedule_frame.pack(fill="x", pady=(0, 15))

schedule_content = tk.Frame(schedule_frame, bg=style['bg'])
schedule_content.pack(padx=10, pady=10)

tk.Label(schedule_content, text="🕐 Set Daily Time (24h format):", 
         font=("Segoe UI", 11, "bold"), fg=style['fg'], bg=style['bg']).pack(anchor="w", pady=(0, 8))

time_frame = tk.Frame(schedule_content, bg=style['bg'])
time_frame.pack(anchor="w")

tk.Label(time_frame, text="Hour:", font=("Segoe UI", 10), fg=style['fg'], bg=style['bg']).pack(side="left")
hour_var = tk.StringVar(value="09")  # Default 9 AM
hour_spin = tk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=hour_var, 
                      font=("Consolas", 10), bg=style['entry_bg'], fg="white", 
                      insertbackground="white", format="%02.0f")
hour_spin.pack(side="left", padx=(5, 15))

tk.Label(time_frame, text="Minute:", font=("Segoe UI", 10), fg=style['fg'], bg=style['bg']).pack(side="left")
minute_var = tk.StringVar(value="00")  # Default 00 minutes
minute_spin = tk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=minute_var, 
                        font=("Consolas", 10), bg=style['entry_bg'], fg="white", 
                        insertbackground="white", format="%02.0f")
minute_spin.pack(side="left", padx=(5, 15))

# Test Time Button
btn_test_time = tk.Button(time_frame, text="🧪 Test Time", command=test_schedule_time,
                         font=("Segoe UI", 9, "bold"), bg=style['warning_bg'], fg="white",
                         relief="flat", padx=15, pady=5, cursor="hand2")
btn_test_time.pack(side="left", padx=(10, 0))

# Control Buttons Section
control_frame = tk.Frame(main_frame, bg=style['bg'])
control_frame.pack(fill="x", pady=(0, 15))

# Start Daily Scheduler Button
btn_start_schedule = tk.Button(control_frame, text="📅 Start Daily Scheduler", command=start_daily_schedule,
                              font=("Segoe UI", 12, "bold"), bg=style['success_bg'], fg="white",
                              relief="flat", padx=20, pady=10, cursor="hand2")
btn_start_schedule.pack(side="left", padx=(0, 10))

# Run Now Button
btn_run_now = tk.Button(control_frame, text="▶️ Run Now", command=run_report_thread,
                       font=("Segoe UI", 12, "bold"), bg=style['button_bg'], fg="white",
                       relief="flat", padx=20, pady=10, cursor="hand2")
btn_run_now.pack(side="left", padx=(0, 10))

# Status Button
btn_status = tk.Button(control_frame, text="📊 Status", command=get_current_status,
                      font=("Segoe UI", 12, "bold"), bg=style['warning_bg'], fg="white",
                      relief="flat", padx=20, pady=10, cursor="hand2")
btn_status.pack(side="right")

# Status Display
status_frame = tk.Frame(main_frame, bg="#34495e", relief="flat", bd=1)
status_frame.pack(fill="x", pady=(0, 15))

status_label = tk.Label(status_frame, text="⏹️ Scheduler not started", 
                       font=("Segoe UI", 11, "bold"), fg="#3498db", bg="#34495e")
status_label.pack(pady=8)

# Log Display Section
log_frame = tk.LabelFrame(main_frame, text="📋 Activity Log", 
                         font=("Segoe UI", 12, "bold"), fg="#3498db", bg=style['bg'])
log_frame.pack(fill="both", expand=True)

log_container = tk.Frame(log_frame, bg=style['bg'])
log_container.pack(fill="both", expand=True, padx=10, pady=10)

log = tk.Text(log_container, width=70, height=15, 
              font=("Consolas", 9), bg="#1a252f", fg="#ecf0f1",
              insertbackground="white", selectbackground="#3498db")
log.pack(side="left", fill="both", expand=True)

log_scrollbar = tk.Scrollbar(log_container, orient="vertical", command=log.yview)
log.configure(yscrollcommand=log_scrollbar.set)
log_scrollbar.pack(side="right", fill="y")

# Footer
footer_frame = tk.Frame(root, bg="#34495e", height=40)
footer_frame.pack(fill="x", side="bottom")
footer_frame.pack_propagate(False)

footer_label = tk.Label(footer_frame, text="🚀 Japanese Group Sales Reporter - Enhanced Daily Scheduler", 
                       font=("Segoe UI", 10), fg="#bdc3c7", bg="#34495e")
footer_label.pack(pady=10)

# Initialize log with welcome message
welcome_msg = f"""🏢 Japanese Group Sales Telegram Reporter - Daily Scheduler v2.0

✨ New Features:
📅 Daily automatic scheduling - runs every day at specified time
⏰ Enhanced time management with countdown display
🔄 Continuous monitoring and error recovery
📊 Real-time status updates and logging
🧪 Schedule testing functionality

🏪 Monitoring {len(branch_ids)} branches:
{', '.join([branch_name_map[bid].replace('◾️', '') for bid in branch_ids])}

⚙️ Setup Instructions:
1. Verify database credentials
2. Select Telegram destination (Group/Personal)
3. Choose options (CSV file, AR deduction)
4. Set daily schedule time
5. Click 'Start Daily Scheduler'

📝 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

log.insert(tk.END, welcome_msg)


def on_closing():
    """
    Handle application closing
    """
    global scheduler_running
    
    if scheduler_running:
        if messagebox.askyesno("Confirm Exit", 
                              "Daily Scheduler is running!\n\n"
                              "Stop scheduler and exit application?"):
            scheduler_running = False
            time.sleep(1)  # รอให้ thread หยุด
            root.destroy()
    else:
        root.destroy()


# Set close protocol
root.protocol("WM_DELETE_WINDOW", on_closing)

# Keyboard shortcuts
root.bind('<F1>', lambda e: get_current_status())
root.bind('<F5>', lambda e: run_report_thread())
root.bind('<Escape>', lambda e: stop_daily_schedule())

# Start the application
if __name__ == "__main__":
    log.insert(tk.END, "🚀 Application started successfully!\n")
    log.insert(tk.END, "📱 Ready to configure daily scheduler...\n")
    log.see(tk.END)
    root.mainloop()