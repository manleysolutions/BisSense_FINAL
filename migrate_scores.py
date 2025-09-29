import sqlite3

DB_FILE = "opportunities.db"
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE scores ADD COLUMN score INTEGER")
    print("✅ Added column: score")
except sqlite3.OperationalError:
    print("ℹ Column 'score' already exists, skipping.")

conn.commit()
conn.close()
