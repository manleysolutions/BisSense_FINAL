# migrate_notifications.py
import sqlite3

DB_FILE = "opportunities.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER,
    event TEXT,                -- e.g., HIGH_SCORE, DECISION_CHANGED
    channel TEXT,              -- sms, email, both, none
    message TEXT,
    created_at TEXT,
    UNIQUE(opportunity_id, event, created_at)
)
""")

conn.commit()
conn.close()
print("✅ notifications table ready.")
