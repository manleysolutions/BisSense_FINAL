import sqlite3

DB_FILE = "opportunities.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # opportunities table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT,
        title TEXT,
        agency TEXT,
        source TEXT,
        issue_date TEXT,
        due_date TEXT,
        url TEXT,
        naics TEXT,
        keywords TEXT,
        est_value REAL,
        status TEXT
    )
    """)

    # cache table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sam_cache (
        external_id TEXT PRIMARY KEY,
        payload_json TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # event log
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT,
        action TEXT,
        details TEXT,
        outcome TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized (opportunities.db)")
