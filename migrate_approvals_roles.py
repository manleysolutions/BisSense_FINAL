import sqlite3

DB_FILE = "opportunities.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

print("⚠️ Rebuilding approvals table with approver + auto_approved columns...")

# Backup old approvals
cur.execute("SELECT opportunity_id, decision, reason, decided_at FROM approvals")
old_data = cur.fetchall()

# Drop + recreate with new schema
cur.execute("DROP TABLE IF EXISTS approvals")
cur.execute("""
    CREATE TABLE approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER,
        decision TEXT,
        reason TEXT,
        decided_at TEXT,
        approver TEXT,
        auto_approved INTEGER,
        UNIQUE(opportunity_id)
    )
""")

# Restore old data with default approver/system
for row in old_data:
    cur.execute("""
        INSERT INTO approvals (opportunity_id, decision, reason, decided_at, approver, auto_approved)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (row[0], row[1], row[2], row[3], "system", 1))

conn.commit()
conn.close()
print("✅ approvals table rebuilt successfully with approver + auto_approved.")
