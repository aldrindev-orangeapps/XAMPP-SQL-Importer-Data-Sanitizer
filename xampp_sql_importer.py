import os
import threading
import subprocess
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".xampp_sql_importer.ini")

DEFAULT_MYSQL_PATHS = [
    r"C:\xampp\mysql\bin\mysql.exe",
    r"D:\xampp\mysql\bin\mysql.exe",
]

EMAIL_KEYWORDS = ["email"]
PHONE_KEYWORDS = [
    "phone", "mobile", "phone_number", "contact_number", "contactnumber", "contact_no",
    "cellphone", "cell_number", "cellnumber", "telephone", "mobile_number",
    "mobilenumber", "tel_no", "telno",
]

COLORS = {
    "bg": "#f2f4f7",
    "section_bg": "#ffffff",
    "accent": "#2f6fed",
    "accent_dark": "#1f4fbf",
    "success": "#2f9e44",
    "success_dark": "#227a36",
    "danger": "#e03131",
    "danger_dark": "#b02525",
    "text": "#1f2937",
}


def find_default_mysql_exe():
    for p in DEFAULT_MYSQL_PATHS:
        if os.path.isfile(p):
            return p
    return ""


class SqlImporterApp:
    def __init__(self, root):
        self.root = root
        root.title("XAMPP SQL Importer")
        root.geometry("680x720")
        root.minsize(680, 500)
        root.configure(bg=COLORS["bg"])

        self._setup_styles()

        self.mysql_path = tk.StringVar()
        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="3306")
        self.user = tk.StringVar(value="root")
        self.password = tk.StringVar(value="")
        self.sql_file = tk.StringVar()
        self.selected_db = tk.StringVar()
        self.status = tk.StringVar(value="Ready.")

        self.email_replacement = tk.StringVar(value="test@example.com")
        self.phone_replacement = tk.StringVar(value="09170000000")

        self.databases = []
        self.sanitize_columns = []

        self._load_config()
        self._build_scrollable_container()
        self._build_ui(self.scroll_frame)

        if not self.mysql_path.get():
            auto = find_default_mysql_exe()
            if auto:
                self.mysql_path.set(auto)

    
    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Section.TFrame", background=COLORS["bg"])
        style.configure("TLabelframe", background=COLORS["bg"], bordercolor=COLORS["accent"])
        style.configure("TLabelframe.Label", background=COLORS["bg"], foreground=COLORS["accent_dark"],
                         font=("Segoe UI", 9, "bold"))
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("TButton", padding=5)

        style.configure("Import.TButton", background=COLORS["success"], foreground="white",
                         font=("Segoe UI", 9, "bold"), padding=4)
        style.map("Import.TButton", background=[("active", COLORS["success_dark"])])

        style.configure("Sanitize.TButton", background=COLORS["danger"], foreground="white",
                         font=("Segoe UI", 9, "bold"), padding=4)
        style.map("Sanitize.TButton", background=[("active", COLORS["danger_dark"])])

        style.configure("Accent.TButton", background=COLORS["accent"], foreground="white", padding=4)
        style.map("Accent.TButton", background=[("active", COLORS["accent_dark"])])

    def _build_scrollable_container(self):
        container = tk.Frame(self.root, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    
    def _build_ui(self, parent):
        pad = {"padx": 10, "pady": 6}

        
        frm_path = ttk.LabelFrame(parent, text="1. Location of mysql.exe (inside xampp/mysql/bin)")
        frm_path.pack(fill="x", **pad)
        ttk.Entry(frm_path, textvariable=self.mysql_path, width=55).pack(side="left", padx=6, pady=6)
        ttk.Button(frm_path, text="Browse...", command=self.browse_mysql_exe).pack(side="left", padx=6)

      
        frm_conn = ttk.LabelFrame(parent, text="2. Connection settings")
        frm_conn.pack(fill="x", **pad)

        row1 = ttk.Frame(frm_conn)
        row1.pack(fill="x", padx=6, pady=4)
        ttk.Label(row1, text="Host:", width=10).pack(side="left")
        ttk.Entry(row1, textvariable=self.host, width=15).pack(side="left", padx=4)
        ttk.Label(row1, text="Port:", width=6).pack(side="left")
        ttk.Entry(row1, textvariable=self.port, width=8).pack(side="left", padx=4)

        row2 = ttk.Frame(frm_conn)
        row2.pack(fill="x", padx=6, pady=4)
        ttk.Label(row2, text="User:", width=10).pack(side="left")
        ttk.Entry(row2, textvariable=self.user, width=15).pack(side="left", padx=4)
        ttk.Label(row2, text="Password:", width=10).pack(side="left")
        ttk.Entry(row2, textvariable=self.password, width=15, show="*").pack(side="left", padx=4)

      
        frm_db = ttk.LabelFrame(parent, text="3. Select the database")
        frm_db.pack(fill="x", **pad)
        self.db_combo = ttk.Combobox(frm_db, textvariable=self.selected_db, values=[], width=35, state="readonly")
        self.db_combo.pack(side="left", padx=6, pady=6)
        ttk.Button(frm_db, text="Refresh list", command=self.refresh_databases).pack(side="left", padx=6)
        ttk.Button(frm_db, text="New database...", command=self.create_database).pack(side="left", padx=6)

       
        frm_file = ttk.LabelFrame(parent, text="4. Import a .sql file")
        frm_file.pack(fill="x", **pad)
        row_f = ttk.Frame(frm_file)
        row_f.pack(fill="x", padx=6, pady=6)
        ttk.Entry(row_f, textvariable=self.sql_file, width=45).pack(side="left")
        ttk.Button(row_f, text="Browse...", command=self.browse_sql_file).pack(side="left", padx=6)
        self.import_btn = ttk.Button(frm_file, text="Import Now", style="Import.TButton",
                                      command=self.start_import)
        self.import_btn.pack(anchor="e", padx=6, pady=(0, 8))

       
        frm_prog = ttk.LabelFrame(parent, text="Progress")
        frm_prog.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(frm_prog, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=6, pady=6)
        ttk.Label(frm_prog, textvariable=self.status).pack(anchor="w", padx=6, pady=(0, 6))

       
        frm_san = ttk.LabelFrame(parent, text="5. Sanitize Data (replace Email & Phone Number values)")
        frm_san.pack(fill="x", **pad)

        ttk.Button(frm_san, text="Scan Database for Email/Phone Columns", style="Accent.TButton",
                   command=self.scan_sanitize_columns).pack(anchor="w", padx=6, pady=6)

        self.sanitize_status_label = ttk.Label(frm_san, text="No columns scanned yet.")
        self.sanitize_status_label.pack(anchor="w", padx=6)

        self.sanitize_list_frame = ttk.Frame(frm_san)
        self.sanitize_list_frame.pack(fill="x", padx=6, pady=4)

        row_email = ttk.Frame(frm_san)
        row_email.pack(fill="x", padx=6, pady=4)
        ttk.Label(row_email, text="Replace ALL emails with:", width=24).pack(side="left")
        ttk.Entry(row_email, textvariable=self.email_replacement, width=30).pack(side="left", padx=4)

        row_phone = ttk.Frame(frm_san)
        row_phone.pack(fill="x", padx=6, pady=4)
        ttk.Label(row_phone, text="Replace ALL phone numbers with:", width=24).pack(side="left")
        ttk.Entry(row_phone, textvariable=self.phone_replacement, width=30).pack(side="left", padx=4)

        self.sanitize_btn = ttk.Button(frm_san, text="Replace Now", style="Sanitize.TButton",
                                        command=self.start_sanitize)
        self.sanitize_btn.pack(anchor="e", padx=6, pady=8)

       
        frm_log = ttk.LabelFrame(parent, text="Log")
        frm_log.pack(fill="both", expand=True, **pad)
        self.log_text = tk.Text(frm_log, height=8, wrap="word", bg="white", fg=COLORS["text"])
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)

       
        frm_bottom = ttk.Frame(parent)
        frm_bottom.pack(fill="x", **pad)
        ttk.Button(frm_bottom, text="Save connection settings", command=self._save_config).pack(side="left")

    
    def log(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def browse_mysql_exe(self):
        path = filedialog.askopenfilename(
            title="Select mysql.exe",
            filetypes=[("mysql.exe", "mysql.exe"), ("All files", "*.*")],
        )
        if path:
            self.mysql_path.set(path)

    def browse_sql_file(self):
        path = filedialog.askopenfilename(
            title="Select .sql file",
            filetypes=[("SQL files", "*.sql"), ("All files", "*.*")],
        )
        if path:
            self.sql_file.set(path)

    def _build_base_cmd(self):
        if not self.mysql_path.get() or not os.path.isfile(self.mysql_path.get()):
            raise FileNotFoundError("Could not find mysql.exe. Please check the path above.")
        cmd = [
            self.mysql_path.get(),
            "-h", self.host.get() or "127.0.0.1",
            "-P", self.port.get() or "3306",
            "-u", self.user.get() or "root",
        ]
        if self.password.get():
            cmd.append(f"-p{self.password.get()}")
        return cmd

    def _run_cmd(self, extra_args, timeout=30):
        cmd = self._build_base_cmd() + extra_args
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    @staticmethod
    def _esc(value):
        return value.replace("\\", "\\\\").replace("'", "\\'")

    
    def refresh_databases(self):
        try:
            result = self._run_cmd(["-e", "SHOW DATABASES;"], timeout=15)
            if result.returncode != 0:
                messagebox.showerror("Error", result.stderr or "Could not connect to MySQL.")
                return
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            dbs = [l for l in lines[1:] if l not in ("information_schema", "performance_schema", "mysql", "sys")]
            self.databases = dbs
            self.db_combo["values"] = dbs
            if dbs:
                self.selected_db.set(dbs[0])
            self.status.set(f"Found {len(dbs)} database(s).")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_database(self):
        name = simpledialog.askstring("New database", "Name of the new database:")
        if not name:
            return
        try:
            result = self._run_cmd(["-e", f"CREATE DATABASE IF NOT EXISTS `{name}`;"], timeout=15)
            if result.returncode != 0:
                messagebox.showerror("Error", result.stderr or "Could not create the database.")
                return
            self.log(f"Database created: {name}")
            self.refresh_databases()
            self.selected_db.set(name)
        except Exception as e:
            messagebox.showerror("Error", str(e))

   
    def start_import(self):
        if not self.selected_db.get():
            messagebox.showwarning("Missing info", "Please select a database first.")
            return
        if not self.sql_file.get() or not os.path.isfile(self.sql_file.get()):
            messagebox.showwarning("Missing info", "Please select a valid .sql file first.")
            return
        try:
            self._build_base_cmd()
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
            return

        confirm = messagebox.askyesno(
            "Confirm import",
            f"Import file:\n{self.sql_file.get()}\n\ninto database:\n{self.selected_db.get()}\n\nProceed?",
        )
        if not confirm:
            return

        self.import_btn.config(state="disabled")
        self.progress["value"] = 0
        self.status.set("Importing...")
        threading.Thread(target=self._run_import, daemon=True).start()

    def _run_import(self):
        sql_path = self.sql_file.get()
        db_name = self.selected_db.get()
        total_size = os.path.getsize(sql_path)
        cmd = self._build_base_cmd() + [db_name]

        try:
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            sent = 0
            chunk_size = 1024 * 1024
            with open(sql_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    proc.stdin.write(chunk)
                    sent += len(chunk)
                    pct = int(sent / total_size * 100) if total_size else 100
                    self.root.after(0, self._update_progress, pct)

            proc.stdin.close()
            out, err = proc.communicate()

            if proc.returncode == 0:
                self.root.after(0, self._import_done, True, "")
            else:
                self.root.after(0, self._import_done, False, err.decode(errors="ignore"))
        except Exception as e:
            self.root.after(0, self._import_done, False, str(e))

    def _update_progress(self, pct):
        self.progress["value"] = pct
        self.status.set(f"Importing... {pct}%")

    def _import_done(self, success, error_msg):
        self.import_btn.config(state="normal")
        if success:
            self.progress["value"] = 100
            self.status.set("Done! Import successful.")
            self.log("Import successful.")
            messagebox.showinfo("Done", "Import successful!")
        else:
            self.status.set("Import failed.")
            self.log("Error: " + error_msg)
            messagebox.showerror("Import error", error_msg or "Unknown error.")

   
    def scan_sanitize_columns(self):
        if not self.selected_db.get():
            messagebox.showwarning("Missing info", "Please select a database first (Section 3).")
            return
        try:
            keywords = EMAIL_KEYWORDS + PHONE_KEYWORDS
            like_clauses = " OR ".join([f"LOWER(COLUMN_NAME) LIKE '%{kw}%'" for kw in keywords])
            query = (
                "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.columns "
                f"WHERE TABLE_SCHEMA = '{self.selected_db.get()}' AND ({like_clauses}) "
                "ORDER BY TABLE_NAME, COLUMN_NAME;"
            )
            result = self._run_cmd(["-N", "-B", "-e", query], timeout=30)
            if result.returncode != 0:
                messagebox.showerror("Error", result.stderr or "Could not scan the database.")
                return

            for widget in self.sanitize_list_frame.winfo_children():
                widget.destroy()
            self.sanitize_columns = []

            lines = [l for l in result.stdout.splitlines() if l.strip()]
            if not lines:
                self.sanitize_status_label.config(text="No matching email/phone columns found.")
                return

            for line in lines:
                parts = line.split("\t")
                if len(parts) != 2:
                    continue
                table, column = parts
                col_lower = column.lower()
                col_type = "email" if any(kw in col_lower for kw in EMAIL_KEYWORDS) else "phone"
                var = tk.BooleanVar(value=True)
                cb = ttk.Checkbutton(self.sanitize_list_frame, text=f"{table}.{column}  [{col_type}]", variable=var)
                cb.pack(anchor="w")
                self.sanitize_columns.append({"table": table, "column": column, "type": col_type, "var": var})

            self.sanitize_status_label.config(
                text=f"Found {len(self.sanitize_columns)} column(s). Uncheck any you don't want to replace."
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_sanitize(self):
        selected = [c for c in self.sanitize_columns if c["var"].get()]
        if not selected:
            messagebox.showwarning("Missing info", "Please scan and select at least one column first.")
            return
        if any(c["type"] == "email" for c in selected) and not self.email_replacement.get():
            messagebox.showwarning("Missing info", "Please enter the replacement email value.")
            return
        if any(c["type"] == "phone" for c in selected) and not self.phone_replacement.get():
            messagebox.showwarning("Missing info", "Please enter the replacement phone number value.")
            return

        preview = "\n".join(f"- {c['table']}.{c['column']} ({c['type']})" for c in selected[:15])
        more = f"\n...and {len(selected) - 15} more" if len(selected) > 15 else ""
        confirm = messagebox.askyesno(
            "Confirm replace",
            f"This will PERMANENTLY overwrite data in database:\n{self.selected_db.get()}\n\n"
            f"Columns to update:\n{preview}{more}\n\n"
            "This cannot be undone. Continue?",
        )
        if not confirm:
            return

        self.sanitize_btn.config(state="disabled")
        threading.Thread(target=self._run_sanitize, args=(selected,), daemon=True).start()

    def _run_sanitize(self, selected):
        db_name = self.selected_db.get()
        total = len(selected)
        done = 0
        errors = []

        for col in selected:
            value = self.email_replacement.get() if col["type"] == "email" else self.phone_replacement.get()
            esc_value = self._esc(value)
            query = (
                f"UPDATE `{col['table']}` SET `{col['column']}` = '{esc_value}' "
                f"WHERE `{col['column']}` IS NOT NULL AND `{col['column']}` <> '';"
            )
            try:
                cmd = self._build_base_cmd() + [db_name, "-e", query]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                if result.returncode != 0:
                    errors.append(f"{col['table']}.{col['column']}")
                    self.root.after(0, self.log, f"FAILED {col['table']}.{col['column']} - {result.stderr.strip()}")
                else:
                    self.root.after(0, self.log, f"OK {col['table']}.{col['column']} updated")
            except Exception as e:
                errors.append(f"{col['table']}.{col['column']}")
                self.root.after(0, self.log, f"FAILED {col['table']}.{col['column']} - {e}")

            done += 1
            pct = int(done / total * 100)
            self.root.after(0, self._update_sanitize_progress, pct)

        self.root.after(0, self._sanitize_done, errors)

    def _update_sanitize_progress(self, pct):
        self.status.set(f"Sanitizing data... {pct}%")

    def _sanitize_done(self, errors):
        self.sanitize_btn.config(state="normal")
        if errors:
            self.status.set(f"Sanitize finished with {len(errors)} error(s).")
            messagebox.showwarning("Finished with errors", f"{len(errors)} column(s) had errors. Check the log.")
        else:
            self.status.set("Sanitize complete.")
            messagebox.showinfo("Done", "All selected columns have been replaced.")

  
    def _load_config(self):
        cfg = configparser.ConfigParser()
        if os.path.isfile(CONFIG_FILE):
            cfg.read(CONFIG_FILE)
            if "settings" in cfg:
                s = cfg["settings"]
                self.mysql_path.set(s.get("mysql_path", ""))
                self.host.set(s.get("host", "127.0.0.1"))
                self.port.set(s.get("port", "3306"))
                self.user.set(s.get("user", "root"))

    def _save_config(self):
        cfg = configparser.ConfigParser()
        cfg["settings"] = {
            "mysql_path": self.mysql_path.get(),
            "host": self.host.get(),
            "port": self.port.get(),
            "user": self.user.get(),
        }
        with open(CONFIG_FILE, "w") as f:
            cfg.write(f)
        messagebox.showinfo("Saved", "Your settings have been saved.")


def main():
    root = tk.Tk()
    app = SqlImporterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()