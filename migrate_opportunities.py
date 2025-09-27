import sqlite3

DB_FILE = "opportunities.db"

def migrate_opportunities():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Add missing columns if not exist
    cur.execute("PRAGMA table_info(opportunities)")
    existing_cols = [row[1] for row in cur.fetchall()]

    if "budget" not in existing_cols:
        cur.execute("ALTER TABLE opportunities ADD COLUMN budget TEXT")

    if "hash" not in existing_cols:
        cur.execute("ALTER TABLE opportunities ADD COLUMN hash TEXT UNIQUE")

    if "category" not in existing_cols:
        cur.execute("ALTER TABLE opportunities ADD COLUMN category TEXT")

    conn.commit()
    conn.close()
    print("✅ Migration complete: opportunities table updated.")

if __name__ == "__main__":
    migrate_opportunities()
