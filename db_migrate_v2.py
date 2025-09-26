import sqlite3

DB_FILE = "opportunities.db"

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Ensure opportunities table has category + category_weight
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
            est_value TEXT,
            status TEXT,
            description TEXT,
            category TEXT,
            category_weight INTEGER DEFAULT 0
        )
    """)

    # Add missing columns if upgrading
    try:
        cur.execute("ALTER TABLE opportunities ADD COLUMN category TEXT")
    except sqlite3.OperationalError:
        pass  # already exists

    try:
        cur.execute("ALTER TABLE opportunities ADD COLUMN category_weight INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # already exists

    # Ensure events table exists
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

    # Ensure sam_cache table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sam_cache (
            external_id TEXT PRIMARY KEY,
            payload_json TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure source_cache table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS source_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            external_id TEXT,
            payload_json TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Migration complete.")

if __name__ == "__main__":
    migrate()
