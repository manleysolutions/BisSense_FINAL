import sqlite3

DB_FILE = "opportunities.db"
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS rfp_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    original_name TEXT,
    mimetype TEXT,
    size_bytes INTEGER,
    uploaded_by INTEGER,
    uploaded_at TEXT,
    extracted_text TEXT
)
""")

conn.commit()
conn.close()
print("✅ rfp_uploads table ready.")
