import sqlite3

DB_FILE = "opportunities.db"

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE opportunities ADD COLUMN raw_text TEXT")
        print("✅ Added raw_text column to opportunities")
    except sqlite3.OperationalError:
        print("⚠️ Column raw_text already exists, skipping")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
