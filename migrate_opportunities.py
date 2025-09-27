import sqlite3

DB_FILE = "opportunities.db"

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Ensure opportunities table has needed columns
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
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

    # Drop old scores table if schema mismatch exists
    cur.execute("PRAGMA table_info(scores)")
    cols = [c[1] for c in cur.fetchall()]
    if "opportunity_id" not in cols or "approval" not in cols:
        cur.execute("DROP TABLE IF EXISTS scores")

    # Recreate scores table with correct schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER UNIQUE,
            score INTEGER,
            approval TEXT,
            reason TEXT,
            breakdown TEXT,
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Migration complete: opportunities and scores tables updated.")

if __name__ == "__main__":
    migrate()
