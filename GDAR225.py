import pyodbc
import pandas as pd
from datetime import datetime, timedelta
import requests
import threading
import os
import tkinter as tk
from tkinter import messagebox

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
                            log_widget.insert(tk.END, f"{row['BranchName']} | GrossSale: {row['GrossSale']:,.2f} | AR Deducted: {row['AR_Deducted']:,.2f}")
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
            log_widget.insert(tk.END, "❌ No data available\n")
            log_widget.see(tk.END)

# ===== GUI =====
def start_schedule():
    hour = int(hour_var.get())
    minute = int(minute_var.get())
    now = datetime.now()
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_time < now:
        target_time += timedelta(days=1)
    delay = (target_time - now).total_seconds()
    log.insert(tk.END, f"⏳ Scheduled next run at {target_time.strftime('%H:%M:%S')}\n")
    threading.Timer(delay, run_report_thread).start()

def run_report_thread():
    threading.Thread(target=run_report_and_send, args=(log,)).start()

root = tk.Tk()
root.title("Japanese Group Sales Telegram")

# DB Config Inputs
tk.Label(root, text="Server:").grid(row=0, column=0, sticky="e")
entry_server = tk.Entry(root, width=30)
entry_server.insert(0, "172.28.116.11,4443")
entry_server.grid(row=0, column=1)

tk.Label(root, text="Database:").grid(row=1, column=0, sticky="e")
entry_db = tk.Entry(root, width=30)
entry_db.insert(0, "HQ_JAPANESE_RESTAURANT_GROUP")
entry_db.grid(row=1, column=1)

tk.Label(root, text="Username:").grid(row=2, column=0, sticky="e")
entry_user = tk.Entry(root, width=30)
entry_user.insert(0, "japanese")
entry_user.grid(row=2, column=1)

tk.Label(root, text="Password:").grid(row=3, column=0, sticky="e")
entry_pass = tk.Entry(root, width=30, show="*")
entry_pass.insert(0, "Password@jpsql1")
entry_pass.grid(row=3, column=1)

# Checkbox เลือกปลายทางส่ง
var_group = tk.IntVar()
chk_group = tk.Checkbutton(root, text="ส่งเข้า Group", variable=var_group)
chk_group.grid(row=4, column=0, sticky="w", padx=5, pady=5)

var_me = tk.IntVar()
chk_me = tk.Checkbutton(root, text="ส่งเข้า Only Me", variable=var_me)
chk_me.grid(row=4, column=1, sticky="w", padx=5, pady=5)

# Checkbox เลือกส่ง CSV
var_csv = tk.IntVar()
chk_csv = tk.Checkbutton(root, text="ส่ง CSV แนบไปด้วย", variable=var_csv)
chk_csv.grid(row=5, column=0, sticky="w", padx=5, pady=5)

# Checkbox เลือกหัก AR
var_ar = tk.IntVar()
chk_ar = tk.Checkbutton(root, text="หักค่า AR (PaymentId=16)", variable=var_ar)
chk_ar.grid(row=5, column=1, sticky="w", padx=5, pady=5)

# Schedule Setting
tk.Label(root, text="Set Schedule (24h)").grid(row=6, column=0, padx=5, pady=5)
hour_var = tk.StringVar(value=str(datetime.now().hour))
minute_var = tk.StringVar(value=str(datetime.now().minute))
tk.Spinbox(root, from_=0, to=23, width=5, textvariable=hour_var).grid(row=6, column=1)
tk.Spinbox(root, from_=0, to=59, width=5, textvariable=minute_var).grid(row=6, column=2)
tk.Button(root, text="Set Schedule", command=start_schedule).grid(row=6, column=3, padx=5)

tk.Button(root, text="Run Now", command=run_report_thread).grid(row=7, column=0, columnspan=4, pady=5)

log = tk.Listbox(root, width=80, height=20)
log.grid(row=8, column=0, columnspan=4, padx=5, pady=5)

root.mainloop()
