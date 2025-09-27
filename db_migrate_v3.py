# db_migrate_v3.py
import sqlite3

DB_FILE = "opportunities.db"

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # --- Scores table ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        reasons TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities (id)
    )
    """)

    # --- Approvals table ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL,
        reviewer TEXT,
        decision TEXT CHECK(decision IN ('Select to Bid','Ignore','Hold')) NOT NULL,
        notes TEXT,
        decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities (id)
    )
    """)

    # --- Indexes for performance ---
    cur.execute("CREATE INDEX IF NOT EXISTS idx_scores_opp_id ON scores(opportunity_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_approvals_opp_id ON approvals(opportunity_id)")

    conn.commit()
    conn.close()
    print("✅ Migration v3 complete: scores + approvals tables added.")

if __name__ == "__main__":
    migrate()
