import sqlite3

DB_FILE = "opportunities.db"

def migrate_scores():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Ensure scores table exists with correct schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            score REAL,
            approval TEXT,
            reason TEXT,
            breakdown TEXT,
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
        )
    """)

    # Check for missing columns and add if needed
    existing_cols = {
        row[1] for row in cur.execute("PRAGMA table_info(scores)").fetchall()
    }

    required_cols = ["opportunity_id", "score", "approval", "reason", "breakdown"]

    for col in required_cols:
        if col not in existing_cols:
            if col == "opportunity_id":
                cur.execute("ALTER TABLE scores ADD COLUMN opportunity_id INTEGER")
            elif col == "score":
                cur.execute("ALTER TABLE scores ADD COLUMN score REAL")
            elif col == "approval":
                cur.execute("ALTER TABLE scores ADD COLUMN approval TEXT")
            elif col == "reason":
                cur.execute("ALTER TABLE scores ADD COLUMN reason TEXT")
            elif col == "breakdown":
                cur.execute("ALTER TABLE scores ADD COLUMN breakdown TEXT")

    conn.commit()
    conn.close()
    print("✅ Migration complete: scores table updated.")

if __name__ == "__main__":
    migrate_scores()
