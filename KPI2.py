import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime
import json
import os
import base64


class KPIManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("KPI Management System - Japanese Restaurant Group")
        self.root.geometry("1600x900")

        # Employee Information
        self.employee_info = {
            "name": "Mr. Taweesak Johrean",
            "employee_id": "04456",
            "position": "IT Asst Manager",
            "section": "IT",
            "department": "Japanese Restaurant Group",
            "level": "6"
        }

        # KPI Configuration
        self.kpi_config = {
            "KPI1": {"name": "Add new item to POS (5 days before launch)", "weight": 30},
            "KPI2": {"name": "Special case add new item (urgent)", "weight": 10},
            "KPI3": {"name": "Equipment condition (max 15 items/year/branch)", "weight": 30},
            "KPI4": {"name": "Technical support (within 30 minutes)", "weight": 20},
            "KPI5": {"name": "Profitability (EBITDA)", "weight": 10}
        }

        # Data storage
        self.kpi_jobs = {"KPI1": [], "KPI2": [], "KPI3": [], "KPI4": [], "KPI5": []}

        self.load_data()
        self.create_widgets()

    def create_widgets(self):
        # Main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs for each KPI
        for kpi_id, config in self.kpi_config.items():
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=f'{kpi_id} ({config["weight"]}%)')
            self.create_kpi_tab(tab, kpi_id, config)

        # Summary & Report Tab
        self.report_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.report_tab, text='📊 สรุปและรายงาน')
        self.create_report_tab()

    def create_kpi_tab(self, parent, kpi_id, config):
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True, padx=10, pady=10)

        # Header
        ttk.Label(container, text=f"{kpi_id}: {config['name']}",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # Form Frame
        form_frame = ttk.LabelFrame(container, text="บันทึก Job ใหม่", padding="15")
        form_frame.pack(fill='x', pady=10)

        vars_dict = {}

        if kpi_id == "KPI1":
            # Memo Name
            ttk.Label(form_frame, text="ชื่อ Memo:*").grid(row=0, column=0, sticky=tk.W, pady=5)
            vars_dict['memo_name'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['memo_name'], width=50).grid(row=0, column=1, columnspan=3,
                                                                                      sticky=tk.W, pady=5)

            # Dates
            ttk.Label(form_frame, text="วันที่ส่ง:*").grid(row=1, column=0, sticky=tk.W, pady=5)
            vars_dict['sent_date'] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            ttk.Entry(form_frame, textvariable=vars_dict['sent_date'], width=20).grid(row=1, column=1, pady=5)

            ttk.Label(form_frame, text="วันเปิดตัว:*").grid(row=1, column=2, padx=20, sticky=tk.W)
            vars_dict['launch_date'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['launch_date'], width=20).grid(row=1, column=3, pady=5)

            ttk.Label(form_frame, text="วันที่ทำเสร็จ:*").grid(row=2, column=0, sticky=tk.W, pady=5)
            vars_dict['completed_date'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['completed_date'], width=20).grid(row=2, column=1, pady=5)

            # Image
            vars_dict['image_data'] = None
            vars_dict['image_path'] = tk.StringVar()
            ttk.Button(form_frame, text="📎 แนบภาพ", command=lambda: self.select_image(vars_dict)).grid(row=3, column=0,
                                                                                                       pady=10)
            ttk.Label(form_frame, textvariable=vars_dict['image_path']).grid(row=3, column=1, columnspan=3, sticky=tk.W)

        elif kpi_id == "KPI2":
            ttk.Label(form_frame, text="ชื่อ Memo:*").grid(row=0, column=0, sticky=tk.W, pady=5)
            vars_dict['memo_name'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['memo_name'], width=50).grid(row=0, column=1, columnspan=3,
                                                                                      sticky=tk.W, pady=5)

            ttk.Label(form_frame, text="วันเวลาส่ง:*").grid(row=1, column=0, sticky=tk.W, pady=5)
            vars_dict['sent_datetime'] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
            ttk.Entry(form_frame, textvariable=vars_dict['sent_datetime'], width=20).grid(row=1, column=1, pady=5)

            ttk.Label(form_frame, text="กำหนดเวลา:*").grid(row=1, column=2, padx=20, sticky=tk.W)
            vars_dict['required_datetime'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['required_datetime'], width=20).grid(row=1, column=3, pady=5)

            ttk.Label(form_frame, text="วันเวลาเสร็จ:*").grid(row=2, column=0, sticky=tk.W, pady=5)
            vars_dict['completed_datetime'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['completed_datetime'], width=20).grid(row=2, column=1, pady=5)

            vars_dict['image_data'] = None
            vars_dict['image_path'] = tk.StringVar()
            ttk.Button(form_frame, text="📎 แนบภาพ", command=lambda: self.select_image(vars_dict)).grid(row=3, column=0,
                                                                                                       pady=10)
            ttk.Label(form_frame, textvariable=vars_dict['image_path']).grid(row=3, column=1, columnspan=3, sticky=tk.W)

        elif kpi_id == "KPI3":
            ttk.Label(form_frame, text="ชื่ออุปกรณ์:*").grid(row=0, column=0, sticky=tk.W, pady=5)
            vars_dict['equipment_name'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['equipment_name'], width=40).grid(row=0, column=1,
                                                                                           columnspan=3, sticky=tk.W,
                                                                                           pady=5)

            ttk.Label(form_frame, text="สาขา:*").grid(row=1, column=0, sticky=tk.W, pady=5)
            vars_dict['branch'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['branch'], width=30).grid(row=1, column=1, pady=5)

            ttk.Label(form_frame, text="วันที่แจ้ง:*").grid(row=2, column=0, sticky=tk.W, pady=5)
            vars_dict['issue_date'] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            ttk.Entry(form_frame, textvariable=vars_dict['issue_date'], width=20).grid(row=2, column=1, pady=5)

            ttk.Label(form_frame, text="วันซ่อมเสร็จ:*").grid(row=2, column=2, padx=20, sticky=tk.W)
            vars_dict['repair_date'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['repair_date'], width=20).grid(row=2, column=3, pady=5)

            ttk.Label(form_frame, text="รายละเอียด:").grid(row=3, column=0, sticky=tk.W, pady=5)
            vars_dict['description_text'] = tk.Text(form_frame, width=60, height=3)
            vars_dict['description_text'].grid(row=3, column=1, columnspan=3, sticky=tk.W, pady=5)

        elif kpi_id == "KPI4":
            ttk.Label(form_frame, text="Ticket No:*").grid(row=0, column=0, sticky=tk.W, pady=5)
            vars_dict['ticket_no'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['ticket_no'], width=30).grid(row=0, column=1, pady=5)

            ttk.Label(form_frame, text="เวลารับแจ้ง:*").grid(row=1, column=0, sticky=tk.W, pady=5)
            vars_dict['call_time'] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
            ttk.Entry(form_frame, textvariable=vars_dict['call_time'], width=20).grid(row=1, column=1, pady=5)

            ttk.Label(form_frame, text="เวลาแก้ไขเสร็จ:*").grid(row=1, column=2, padx=20, sticky=tk.W)
            vars_dict['resolved_time'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['resolved_time'], width=20).grid(row=1, column=3, pady=5)

            ttk.Label(form_frame, text="ประเภท:").grid(row=2, column=0, sticky=tk.W, pady=5)
            vars_dict['issue_type'] = tk.StringVar()
            ttk.Combobox(form_frame, textvariable=vars_dict['issue_type'], width=28,
                         values=["POS", "Network", "Printer", "Computer", "Other"]).grid(row=2, column=1, pady=5)

            ttk.Label(form_frame, text="วิธีแก้:").grid(row=3, column=0, sticky=tk.W, pady=5)
            vars_dict['solution_text'] = tk.Text(form_frame, width=60, height=3)
            vars_dict['solution_text'].grid(row=3, column=1, columnspan=3, sticky=tk.W, pady=5)

        elif kpi_id == "KPI5":
            ttk.Label(form_frame, text="งวด:*").grid(row=0, column=0, sticky=tk.W, pady=5)
            vars_dict['period'] = tk.StringVar()
            ttk.Combobox(form_frame, textvariable=vars_dict['period'], width=20,
                         values=["Q1", "Q2", "Q3", "Q4", "Mid Year", "Year End"]).grid(row=0, column=1, pady=5)

            ttk.Label(form_frame, text="EBITDA (%):*").grid(row=1, column=0, sticky=tk.W, pady=5)
            vars_dict['ebitda_value'] = tk.StringVar()
            ttk.Entry(form_frame, textvariable=vars_dict['ebitda_value'], width=20).grid(row=1, column=1, pady=5)

        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=10, column=0, columnspan=4, pady=15)
        ttk.Button(button_frame, text="💾 บันทึก", command=lambda: self.save_job(kpi_id, vars_dict)).pack(side=tk.LEFT,
                                                                                                         padx=5)
        ttk.Button(button_frame, text="🗑️ ล้าง", command=lambda: self.clear_form(vars_dict)).pack(side=tk.LEFT, padx=5)

        setattr(self, f'{kpi_id}_vars', vars_dict)

        # Jobs List
        list_frame = ttk.LabelFrame(container, text="รายการ Jobs", padding="15")
        list_frame.pack(fill='both', expand=True)

        self.create_jobs_tree(list_frame, kpi_id)

    def create_jobs_tree(self, parent, kpi_id):
        if kpi_id in ["KPI1", "KPI2"]:
            columns = ("ID", "Memo", "Date", "Days/Hours", "Score", "Image")
        elif kpi_id == "KPI3":
            columns = ("ID", "Equipment", "Branch", "Issue Date", "Repair Date")
        elif kpi_id == "KPI4":
            columns = ("ID", "Ticket", "Call Time", "Minutes", "Score")
        else:
            columns = ("ID", "Period", "EBITDA", "Score")

        tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="ลบ", command=lambda: self.delete_job(kpi_id, tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="รีเฟรช", command=lambda: self.refresh_tree(kpi_id, tree)).pack(side=tk.LEFT, padx=5)

        setattr(self, f'{kpi_id}_tree', tree)
        self.refresh_tree(kpi_id, tree)

    def select_image(self, vars_dict):
        filename = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
        if filename:
            try:
                with open(filename, 'rb') as f:
                    vars_dict['image_data'] = base64.b64encode(f.read()).decode()
                    vars_dict['image_path'].set(os.path.basename(filename))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def clear_form(self, vars_dict):
        for key, var in vars_dict.items():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.Text):
                var.delete(1.0, tk.END)
        if 'image_data' in vars_dict:
            vars_dict['image_data'] = None

    def save_job(self, kpi_id, vars_dict):
        try:
            job = {"id": len(self.kpi_jobs[kpi_id]) + 1}

            if kpi_id == "KPI1":
                memo = vars_dict['memo_name'].get()
                sent = vars_dict['sent_date'].get()
                launch = vars_dict['launch_date'].get()
                completed = vars_dict['completed_date'].get()

                if not all([memo, sent, launch, completed]):
                    messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบ")
                    return

                days = (datetime.strptime(launch, "%Y-%m-%d") - datetime.strptime(completed, "%Y-%m-%d")).days
                score = 5 if days >= 7 else (4 if days >= 6 else (3 if days >= 5 else (2 if days >= 4 else 1)))

                job.update({"memo": memo, "sent": sent, "launch": launch, "completed": completed,
                            "days": days, "score": score, "image": vars_dict.get('image_data')})

            elif kpi_id == "KPI2":
                memo = vars_dict['memo_name'].get()
                sent = vars_dict['sent_datetime'].get()
                required = vars_dict['required_datetime'].get()
                completed = vars_dict['completed_datetime'].get()

                if not all([memo, sent, required, completed]):
                    messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบ")
                    return

                hours = (datetime.strptime(completed, "%Y-%m-%d %H:%M") - datetime.strptime(sent,
                                                                                            "%Y-%m-%d %H:%M")).total_seconds() / 3600
                score = 5 if hours < 6 else (4 if hours <= 11 else (3 if hours <= 12 else (2 if hours <= 24 else 1)))

                job.update({"memo": memo, "sent": sent, "required": required, "completed": completed,
                            "hours": round(hours, 2), "score": score, "image": vars_dict.get('image_data')})

            elif kpi_id == "KPI3":
                equipment = vars_dict['equipment_name'].get()
                branch = vars_dict['branch'].get()
                issue = vars_dict['issue_date'].get()
                repair = vars_dict['repair_date'].get()
                desc = vars_dict['description_text'].get(1.0, tk.END).strip() if 'description_text' in vars_dict else ""

                if not all([equipment, branch, issue, repair]):
                    messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบ")
                    return

                job.update({"equipment": equipment, "branch": branch, "issue_date": issue,
                            "repair_date": repair, "description": desc})

            elif kpi_id == "KPI4":
                ticket = vars_dict['ticket_no'].get()
                call = vars_dict['call_time'].get()
                resolved = vars_dict['resolved_time'].get()
                issue_type = vars_dict['issue_type'].get()
                solution = vars_dict['solution_text'].get(1.0, tk.END).strip() if 'solution_text' in vars_dict else ""

                if not all([ticket, call, resolved]):
                    messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบ")
                    return

                minutes = (datetime.strptime(resolved, "%Y-%m-%d %H:%M") - datetime.strptime(call,
                                                                                             "%Y-%m-%d %H:%M")).total_seconds() / 60
                score = 5 if minutes <= 10 else (
                    4 if minutes <= 15 else (3 if minutes <= 30 else (2 if minutes <= 60 else 1)))

                job.update({"ticket": ticket, "call_time": call, "resolved": resolved, "minutes": round(minutes, 2),
                            "issue_type": issue_type, "solution": solution, "score": score})

            elif kpi_id == "KPI5":
                period = vars_dict['period'].get()
                ebitda = vars_dict['ebitda_value'].get()

                if not all([period, ebitda]):
                    messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบ")
                    return

                ebitda_val = float(ebitda)
                score = 5 if ebitda_val >= 100 else (
                    4 if ebitda_val >= 90 else (3 if ebitda_val >= 80 else (2 if ebitda_val >= 70 else 1)))

                job.update({"period": period, "ebitda": ebitda_val, "score": score})

            self.kpi_jobs[kpi_id].append(job)
            self.save_data()
            self.refresh_tree(kpi_id, getattr(self, f'{kpi_id}_tree'))
            self.clear_form(vars_dict)
            messagebox.showinfo("Success", "บันทึกสำเร็จ")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_tree(self, kpi_id, tree):
        for item in tree.get_children():
            tree.delete(item)

        for job in self.kpi_jobs.get(kpi_id, []):
            if kpi_id == "KPI1":
                vals = (job['id'], job['memo'][:20], job['sent'], job['days'], f"{job['score']}/5",
                        "✓" if job.get('image') else "✗")
            elif kpi_id == "KPI2":
                vals = (job['id'], job['memo'][:20], job['sent'], job['hours'], f"{job['score']}/5",
                        "✓" if job.get('image') else "✗")
            elif kpi_id == "KPI3":
                vals = (job['id'], job['equipment'][:20], job['branch'], job['issue_date'], job['repair_date'])
            elif kpi_id == "KPI4":
                vals = (job['id'], job['ticket'], job['call_time'], job['minutes'], f"{job['score']}/5")
            else:
                vals = (job['id'], job['period'], job['ebitda'], f"{job['score']}/5")

            tree.insert("", tk.END, values=vals)

    def delete_job(self, kpi_id, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "เลือกรายการที่ต้องการลบ")
            return

        if messagebox.askyesno("Confirm", "ลบรายการนี้?"):
            item_id = tree.item(selected[0])['values'][0]
            self.kpi_jobs[kpi_id] = [j for j in self.kpi_jobs[kpi_id] if j['id'] != item_id]
            for i, job in enumerate(self.kpi_jobs[kpi_id], 1):
                job['id'] = i
            self.save_data()
            self.refresh_tree(kpi_id, tree)

    def create_report_tab(self):
        container = ttk.Frame(self.report_tab, padding="20")
        container.pack(fill='both', expand=True)

        self.summary_text = scrolledtext.ScrolledText(container, height=30, font=('Courier', 9))
        self.summary_text.pack(fill='both', expand=True)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="คำนวณ", command=self.calculate_summary).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ส่งออก", command=self.export_report).pack(side=tk.LEFT, padx=5)

        self.calculate_summary()

    def calculate_summary(self):
        summary = []
        summary.append("=" * 100)
        summary.append(f"สรุป KPI - {self.employee_info['name']} ({self.employee_info['position']})")
        summary.append("=" * 100 + "\n")

        total_score = 0

        for kpi_id, config in self.kpi_config.items():
            jobs = self.kpi_jobs.get(kpi_id, [])
            summary.append(f"{kpi_id}: {config['name']} (น้ำหนัก {config['weight']}%)")
            summary.append(f"  Jobs: {len(jobs)}")

            if jobs:
                if kpi_id == "KPI3":
                    branches = {}
                    for j in jobs:
                        branches[j['branch']] = branches.get(j['branch'], 0) + 1
                    avg = sum(branches.values()) / len(branches) if branches else 0
                    score = 5 if avg < 9 else (4 if avg <= 14 else (3 if avg <= 15 else (2 if avg <= 20 else 1)))
                    weighted = (score * config['weight']) / 100
                    summary.append(f"  เฉลี่ย/สาขา: {avg:.1f} | คะแนน: {score}/5")
                else:
                    scored = [j for j in jobs if 'score' in j]
                    if scored:
                        avg_score = sum(j['score'] for j in scored) / len(scored)
                        weighted = (avg_score * config['weight']) / 100
                        summary.append(f"  คะแนนเฉลี่ย: {avg_score:.2f}/5")
                    else:
                        weighted = 0

                summary.append(f"  คะแนนถ่วงน้ำหนัก: {weighted:.2f}")
                total_score += weighted
            else:
                summary.append(f"  คะแนน: N/A")

            summary.append("")

        summary.append(f"\nคะแนนรวม: {total_score:.2f}/5.00")

        if total_score >= 4.5:
            rating = "⭐⭐⭐⭐⭐ Far Exceed"
        elif total_score >= 3.5:
            rating = "⭐⭐⭐⭐ Exceed"
        elif total_score >= 2.5:
            rating = "⭐⭐⭐ Meet"
        elif total_score >= 1.5:
            rating = "⭐⭐ Partially Meet"
        else:
            rating = "⭐ Not Meet"

        summary.append(f"ระดับ: {rating}")
        summary.append("=" * 100)

        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, "\n".join(summary))

    def export_report(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8-sig') as f:
                    f.write(f"KPI Report - {self.employee_info['name']}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n\n")

                    for kpi_id, config in self.kpi_config.items():
                        f.write(f"\n{kpi_id}: {config['name']}\n")
                        jobs = self.kpi_jobs.get(kpi_id, [])
                        f.write(f"Total Jobs: {len(jobs)}\n")

                        for job in jobs:
                            f.write(f"  {job}\n")

                messagebox.showinfo("Success", f"ส่งออกไปที่ {filename}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def save_data(self):
        try:
            with open('kpi_data_full.json', 'w', encoding='utf-8') as f:
                json.dump({"employee": self.employee_info, "kpi_jobs": self.kpi_jobs}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Save error: {e}")

    def load_data(self):
        try:
            if os.path.exists('kpi_data_full.json'):
                with open('kpi_data_full.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.kpi_jobs = data.get('kpi_jobs', {"KPI1": [], "KPI2": [], "KPI3": [], "KPI4": [], "KPI5": []})
        except Exception as e:
            print(f"Load error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = KPIManagementSystem(root)
    root.mainloop()
