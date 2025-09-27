# migrate_approvals.py
import sqlite3

DB_FILE = "opportunities.db"

def migrate_approvals():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Create approvals table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opp_id INTEGER NOT NULL,
            approval TEXT DEFAULT 'Ignore',
            reason TEXT DEFAULT '',
            FOREIGN KEY (opp_id) REFERENCES opportunities(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Migration complete: approvals table created/verified.")

if __name__ == "__main__":
    migrate_approvals()
