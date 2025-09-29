# upgrade_db.py
import sqlite3

DB_FILE = "opportunities.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Add status column if it doesn't exist
try:
    cur.execute("ALTER TABLE opportunities ADD COLUMN status TEXT DEFAULT 'Open'")
    print("✅ Added 'status' column to opportunities table")
except sqlite3.OperationalError as e:
    print("⚠️ Column may already exist:", e)

conn.commit()
conn.close()
