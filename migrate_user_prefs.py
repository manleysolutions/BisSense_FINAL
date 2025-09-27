import sqlite3
from datetime import datetime

DB_FILE = "opportunities.db"
now = datetime.utcnow().isoformat()

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Keywords user cares about (free text, weighted)
cur.execute("""
CREATE TABLE IF NOT EXISTS user_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT
)
""")

# NAICS codes, weighted
cur.execute("""
CREATE TABLE IF NOT EXISTS user_naics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    naics_code TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT
)
""")

# Simple training Q&A to bias scoring (demographics, preferred work)
cur.execute("""
CREATE TABLE IF NOT EXISTS user_training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TEXT
)
""")

conn.commit()
conn.close()
print("✅ user preference tables ready (user_keywords, user_naics, user_training).")
