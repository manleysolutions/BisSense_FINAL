import sqlite3

DB_FILE = "opportunities.db"

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Get existing columns
    cur.execute("PRAGMA table_info(opportunities)")
    cols = [row[1] for row in cur.fetchall()]

    if "hash" in cols:
        print("ℹ️ 'hash' column already exists — no rebuild needed.")
        conn.close()
        return

    print("⚠️ Rebuilding opportunities table with 'hash' column...")

    # 1. Rename old table
    cur.execute("ALTER TABLE opportunities RENAME TO opportunities_old")

    # 2. Create new table with hash column
    cur.execute("""
        CREATE TABLE opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            agency TEXT,
            source TEXT,
            issue_date TEXT,
            due_date TEXT,
            url TEXT,
            category TEXT,
            budget REAL,
            hash TEXT UNIQUE
        )
    """)

    # 3. Copy data (generate hashes for existing rows)
    cur.execute("SELECT id, title, agency, source, issue_date, due_date, url, category, budget FROM opportunities_old")
    rows = cur.fetchall()

    import hashlib
    for r in rows:
        title, agency, due_date = r[1], r[2], r[5]
        hash_input = (title + agency + (due_date or "")).encode("utf-8")
        opp_hash = hashlib.sha256(hash_input).hexdigest()
        cur.execute("""
            INSERT OR IGNORE INTO opportunities
            (id, title, agency, source, issue_date, due_date, url, category, budget, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], opp_hash))

    # 4. Drop old table
    cur.execute("DROP TABLE opportunities_old")

    conn.commit()
    conn.close()
    print("✅ opportunities table rebuilt successfully with 'hash' column.")

if __name__ == "__main__":
    migrate()
