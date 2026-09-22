# XAMPP SQL Importer & Data Sanitizer

A simple Windows GUI tool (built with Python + tkinter) for developers using XAMPP.

It solves two common annoyances:

1. **Importing large `.sql` files** without hitting phpMyAdmin's upload size limit, and without manually opening `cmd` and navigating to `mysql/bin` every time.
2. **Sanitizing a copy of a live/production database** — scanning every table for columns that look like emails or phone numbers, and mass-replacing their values so the data is safe to use in dev/test environments.

---

## Features

- Import any size `.sql` file directly through `mysql.exe` (no phpMyAdmin upload limit)
- Live progress bar while importing (based on bytes streamed)
- Dropdown to select an existing database, or create a new one from the app
- Scan a database for columns named like `email`, `Email`, `phone`, `PhoneNumber`, `Contact_number`, `mobile`, `cellphone`, etc.
- Review/uncheck detected columns before replacing anything
- One replacement value for all emails, one for all phone numbers
- Save your connection settings (mysql.exe path, host, port, user) so you don't retype them every time
- Simple colored UI — no command line needed

---

## Requirements

- Windows with **XAMPP** installed (needs `mysql.exe`, normally at `C:\xampp\mysql\bin\mysql.exe`)
- **Python 3** (only needed if running from source or building the `.exe` yourself) — [python.org/downloads](https://www.python.org/downloads/)

---

## Option A: Run directly with Python

```
python xampp_sql_importer.py
```

## Option B: Build a standalone `.exe`

No Python needed on the machine that will run the final `.exe`.

```
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "XAMPP SQL Importer" xampp_sql_importer.py
```

The finished app will be at:

```
dist\XAMPP SQL Importer.exe
```

> If `pip install pyinstaller` fails with `Fatal error in launcher`, use `python -m pip install pyinstaller` instead — this calls pip through Python directly and avoids a broken `pip.exe` shortcut.

---

## How to use

### 1. Set the path to `mysql.exe`
Auto-fills if XAMPP is installed at the default location (`C:\xampp\mysql\bin\mysql.exe`). Otherwise, click **Browse...** and find it manually.

### 2. Connection settings
Defaults match a standard XAMPP setup: `127.0.0.1`, port `3306`, user `root`, no password. Change if yours is different.

### 3. Select the database
Click **Refresh list** to load your existing databases, or **New database...** to create one on the spot.

### 4. Import a `.sql` file
Click **Browse...**, pick your file, then **Import Now**. A confirmation dialog will show which file goes into which database before anything runs. The progress bar tracks bytes sent to MySQL, so it works even for very large dump files.

### 5. Sanitize Data (replace Email & Phone values)
Use this when you've imported a copy of a **live/production** database and want to scrub personal data before using it locally:

1. Make sure the right database is selected in Section 3.
2. Click **Scan Database for Email/Phone Columns** — this checks every table's column names against common email/phone naming patterns.
3. Review the checklist that appears (e.g. `users.email [email]`, `students.Contact_number [phone]`). Uncheck anything that was matched by mistake.
4. Enter the value to use everywhere:
   - *Replace ALL emails with:* (default `test@example.com`)
   - *Replace ALL phone numbers with:* (default `09170000000`)
5. Click **Replace Now**. You'll get a confirmation dialog listing the columns about to be changed — **this action is permanent and cannot be undone**, so double-check the database name before confirming.
6. Progress and per-column results are shown in the **Log** box at the bottom.

---

## Notes & limitations

- Import has no file-size limit because it streams directly to `mysql.exe`, the same as running `mysql -u root dbname < file.sql` in `cmd` — it does not go through phpMyAdmin or PHP's `upload_max_filesize` / `post_max_size` settings.
- The email/phone column detector uses a fixed keyword list (`email`, `phone`, `mobile`, `contact_number`, `cellphone`, `telephone`, etc.) kept deliberately specific to avoid false positives like `hotel` or `intelligence`. If a column isn't detected, you can still write a custom `UPDATE` manually.
- The sanitizer applies **one static value** to every matching row (not unique per row). If your data has `UNIQUE` constraints on the email/phone column, a static replacement value will fail — let the developer know if you need unique-per-row values instead.
- Settings (mysql.exe path, host, port, user) are saved to a local config file in your user folder: `~/.xampp_sql_importer.ini`. Password is **not** saved for security.
- Always back up / keep the original `.sql` dump before running Sanitize — it permanently overwrites data in the selected database.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Fatal error in launcher` when running `pip install` | Use `python -m pip install pyinstaller` instead |
| App says it can't find `mysql.exe` | Browse to it manually, usually `C:\xampp\mysql\bin\mysql.exe` |
| Import fails with an access/connection error | Check XAMPP's MySQL service is running, and that host/port/user/password match your XAMPP config |
| Scan finds 0 columns | Your column names may not match the built-in keyword list — you can extend `EMAIL_KEYWORDS` / `PHONE_KEYWORDS` in the script |