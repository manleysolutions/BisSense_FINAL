import sqlite3

DB_FILE = "opportunities.db"

def migrate_all():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # --- OPPORTUNITIES TABLE ---
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

    # Check and add missing columns for opportunities
    opp_existing = {row[1] for row in cur.execute("PRAGMA table_info(opportunities)").fetchall()}
    opp_required = ["title", "agency", "source", "issue_date", "due_date", "url", "category", "budget", "hash"]

    for col in opp_required:
        if col not in opp_existing:
            if col == "budget":
                cur.execute("ALTER TABLE opportunities ADD COLUMN budget REAL")
            elif col == "hash":
                cur.execute("ALTER TABLE opportunities ADD COLUMN hash TEXT UNIQUE")
            else:
                cur.execute(f"ALTER TABLE opportunities ADD COLUMN {col} TEXT")

    # --- SCORES TABLE ---
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

    # Check and add missing columns for scores
    score_existing = {row[1] for row in cur.execute("PRAGMA table_info(scores)").fetchall()}
    score_required = ["opportunity_id", "score", "approval", "reason", "breakdown"]

    for col in score_required:
        if col not in score_existing:
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
    print("✅ Migration complete: opportunities + scores tables updated.")

if __name__ == "__main__":
    migrate_all()
