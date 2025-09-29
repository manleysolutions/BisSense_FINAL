import sqlite3

DB_FILE = "opportunities.db"
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Add new columns if they don’t exist
new_cols = [
    ("contacts", "TEXT"),
    ("submission_method", "TEXT"),
    ("qna_deadline", "TEXT"),
    ("prebid", "TEXT"),
    ("prebid_required", "TEXT"),
    ("set_aside", "TEXT"),
    ("bonding", "TEXT"),
    ("insurance", "TEXT")
]

for col, col_type in new_cols:
    try:
        cur.execute(f"ALTER TABLE opportunities ADD COLUMN {col} {col_type}")
        print(f"✅ Added column: {col}")
    except sqlite3.OperationalError:
        print(f"ℹ Column {col} already exists, skipping.")

conn.commit()
conn.close()
