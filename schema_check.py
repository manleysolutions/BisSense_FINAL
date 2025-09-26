import sqlite3

DB_FILE = "opportunities.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

print("=== Tables in DB ===")
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(row[0])

print("\n=== Events table columns ===")
cur.execute("PRAGMA table_info(events)")
for row in cur.fetchall():
    print(row)

conn.close()
