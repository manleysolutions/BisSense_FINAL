import sqlite3

DB_FILE = "opportunities.db"

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Get current columns
    cur.execute("PRAGMA table_info(opportunities)")
    cols = [row[1] for row in cur.fetchall()]

    # Add contract_type
    if "contract_type" not in cols:
        cur.execute("ALTER TABLE opportunities ADD COLUMN contract_type TEXT")
        print("✅ Added 'contract_type' column.")

    # Add naics_code
    if "naics_code" not in cols:
        cur.execute("ALTER TABLE opportunities ADD COLUMN naics_code TEXT")
        print("✅ Added 'naics_code' column.")

    # Add award_date
    if "award_date" not in cols:
        cur.execute("ALTER TABLE opportunities ADD COLUMN award_date TEXT")
        print("✅ Added 'award_date' column.")

    conn.commit()
    conn.close()
    print("🎯 Migration complete.")

if __name__ == "__main__":
    migrate()
